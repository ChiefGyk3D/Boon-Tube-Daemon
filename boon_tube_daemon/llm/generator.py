# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Video announcement generation for Boon-Tube-Daemon.

The provider plumbing (Ollama, Gemini, retries, reconnection, failover,
guardrails) lives in hypeman-social now. What stays here is the part that is
genuinely Boon-Tube's: what a *video upload* announcement should say, which
platforms get hashtags, and the prompts tuned for small local models.

Configure with the same env vars as before (LLM_ENABLE, LLM_PROVIDER,
LLM_OLLAMA_HOST, ...), plus the new LLM_FALLBACK_PROVIDER for automatic
failover between a local Ollama box and Gemini.
"""

import logging
import re
from typing import Optional

from hypeman_social.llm import VIDEO_PROFILE, LLMManager, build_provider

from boon_tube_daemon.utils.config import get_bool_config, get_config

logger = logging.getLogger(__name__)


#: Per-network message shaping: (max_chars, use_hashtags, hashtag_count).
_PLATFORM_LIMITS = {
    'bluesky': (240, True, 3),    # Conservative for Bluesky's 300-grapheme limit
    'mastodon': (400, True, 3),   # Leave room for URL and hashtags
    'discord': (300, False, 0),
    'matrix': (350, False, 0),
}
_DEFAULT_LIMITS = (300, False, 0)

# Meta-text a model wraps around its answer ("Here's your post: ...").
# When the chatter ends in a colon, everything up to and including it goes;
# a bare "Here's"/"Here you go" opener goes too.
_META_PATTERNS = [
    r'^(?:Here\'?s|Okay,? here\'?s|Alright,? here\'?s|Here you go|Sure thing|Certainly)[^:\n]*:\s*',
    r'^(?:Here\'?s|Here you go|Sure thing|Certainly)[,!.]?\s+',
    r'^(?:Post|Draft|Output)\s*:\s*',
    r'^"',
    r'"$',
]


class VideoPostGenerator:
    """
    Generates video announcements through hypeman's LLM manager.

    Exposes the same interface the daemon has always used (enabled,
    should_notify, generate_notification, generate_hashtags), so main.py
    barely changed in the migration.

    Args:
        provider: Force a specific provider ('ollama' or 'gemini') instead of
            reading LLM_PROVIDER. Used by the OllamaLLM/GeminiLLM
            compatibility wrappers and by tests that target one backend.
    """

    def __init__(self, provider: Optional[str] = None):
        if provider:
            self._engine = build_provider(provider, VIDEO_PROFILE)
            if self._engine is None:
                raise ValueError(f"Unknown LLM provider: {provider}")
        else:
            self._engine = LLMManager(profile=VIDEO_PROFILE)

    @property
    def enabled(self) -> bool:
        return bool(self._engine and self._engine.enabled)

    def authenticate(self) -> bool:
        """Bring up the configured provider(s). Safe to call when disabled."""
        return self._engine.authenticate()

    def is_available(self) -> bool:
        """True if a provider can generate right now. May heal a downed one."""
        return self._engine.is_available()

    def status(self) -> dict:
        """Provider state for logs and health endpoints."""
        return self._engine.status()

    # ─────────────────────────────────────────────────────────────────────
    # Domain methods
    # ─────────────────────────────────────────────────────────────────────

    def should_notify(self, video_data: dict) -> bool:
        """
        Ask the model whether this video merits an announcement.

        Fails open: any doubt, outage, or disabled filter means "notify".
        Missing an announcement is worse than posting a mediocre one.
        """
        if not self.enabled:
            return True
        if not get_bool_config('LLM', 'enable_filtering', default=False):
            return True

        title = video_data.get('title', '')
        description = video_data.get('description', '')
        filter_keywords = get_config('LLM', 'filter_keywords', default='')

        prompt = f"""Determine if this video should trigger a notification based on quality and relevance.

Title: {title}
Description: {description[:300]}

Filter out:
- Spam or clickbait
- Low-quality content
- Off-topic videos
{f'- Content containing: {filter_keywords}' if filter_keywords else ''}

Return ONLY "yes" or "no"."""

        decision = self._engine.generate(prompt)
        if not decision:
            logger.warning("Failed to get LLM filtering decision, defaulting to notify")
            return True

        should = 'yes' in decision.lower()
        if not should:
            logger.info(f"🚫 LLM filtered out video: {title[:50]}...")
        return should

    def generate_hashtags(self, video_data: dict, max_tags: int = 5) -> Optional[str]:
        """Generate space-separated hashtags for a video, or None."""
        if not self.enabled:
            return None

        title = video_data.get('title', '')
        description = video_data.get('description', '')

        prompt = f"""Generate {max_tags} relevant, popular hashtags for this video. Return ONLY the hashtags separated by spaces, with # prefix.

Title: {title}
Description: {description[:300]}

Example format: #Tech #Gaming #Tutorial #AI #Programming"""

        hashtags = self._engine.generate(prompt)
        if hashtags:
            logger.debug(f"Generated hashtags: {hashtags}")
        return hashtags or None

    def generate_notification(
        self,
        video_data: dict,
        platform_name: str,
        social_platform: str,
    ) -> Optional[str]:
        """
        Generate a platform-tailored announcement for a new video.

        Returns the finished message with the URL appended, or None when
        generation failed or the message didn't survive the guardrails —
        the caller falls back to its template either way.
        """
        if not self.enabled:
            return None

        title = video_data.get('title', '')
        url = video_data.get('url', '')
        channel_name = video_data.get('channel_name', platform_name)
        max_chars, use_hashtags, hashtag_count = _PLATFORM_LIMITS.get(
            social_platform.lower(), _DEFAULT_LIMITS)

        prompt = self._build_notification_prompt(
            platform_name=platform_name,
            channel_name=channel_name,
            title=title,
            description=video_data.get('description', ''),
            max_chars=max_chars,
            use_hashtags=use_hashtags,
            hashtag_count=hashtag_count,
        )

        notification = self._engine.generate(prompt)
        if not notification:
            logger.warning(f"Failed to generate notification for {social_platform}")
            return None

        notification = self._strip_meta_text(notification)

        cleaned, issues = self._engine.apply_guardrails(
            notification,
            title=title,
            username=channel_name,
            platform=social_platform,
            char_limit=max_chars,
            expected_hashtag_count=hashtag_count if use_hashtags else 0,
        )
        if not cleaned:
            logger.warning(
                f"Notification failed guardrails for {social_platform}: "
                f"{'; '.join(issues)}"
            )
            return None

        if url:
            cleaned += f"\n\n{url}"

        logger.info(f"✨ Generated {social_platform} post: {cleaned[:60]}...")
        return cleaned

    # ─────────────────────────────────────────────────────────────────────
    # Internals
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _strip_meta_text(notification: str) -> str:
        """Remove model chatter and inline URLs before validation."""
        for pattern in _META_PATTERNS:
            notification = re.sub(pattern, '', notification,
                                  flags=re.IGNORECASE | re.MULTILINE)
        # Any URL the model invented gets dropped; the real one is appended
        # after guardrails (and inline URLs fail validation).
        notification = re.sub(r'https?://[^\s]+', '', notification)
        notification = re.sub(r'[ \t]{2,}', ' ', notification)
        return notification.strip()

    @staticmethod
    def _build_notification_prompt(
        platform_name: str,
        channel_name: str,
        title: str,
        description: str,
        max_chars: int,
        use_hashtags: bool,
        hashtag_count: int,
    ) -> str:
        """
        Prompt tuned for small local models (4B-12B params): explicit steps,
        worked examples, and a list of the exact ways they usually screw up.
        """
        clean_description = description[:200] if description else ''
        clean_description = re.sub(r'https?://\S+', '', clean_description).strip()

        hashtag_instruction = ""
        if use_hashtags:
            hashtag_instruction = f"""

STEP 3 - HASHTAG RULES (CRITICAL):
You MUST include EXACTLY {hashtag_count} hashtags at the end.
- Extract hashtags from key words/topics in the title
- NEVER use generic tags like #Video, #YouTube, #New, #Content
- Format: space before each hashtag"""

        return f"""You are a social media assistant that writes engaging video announcements with personality.

TASK: Write a short, engaging post announcing a new {platform_name} video from {channel_name}.

VIDEO TITLE: "{title}"
{f'DESCRIPTION: "{clean_description}"' if clean_description else ''}

STEP 1 - STYLE & TONE:
✓ Match the vibe: Read the title and match its energy (technical, gaming, tutorial, entertainment, etc.)
✓ Be personality-driven: Write like a real person with character, not a corporate bot
✓ Add interest: Make people want to click - build curiosity without being cringe
✓ Use formatting: Short lines or natural flow work great
✓ Emoji: Use 0-1 emoji that fits the vibe (🎬 for video, 🎮 for gaming, 💻 for tech, etc.)

STEP 2 - CONTENT RULES (FOLLOW EXACTLY):
✓ Length: MUST be {max_chars} characters or less (including hashtags)
✓ Output: ONLY the post text (no quotes, no meta-commentary, no "Here's...")
✓ Based on title: Reference what the video is about BUT don't just copy/paste the title
✓ Call-to-action: Natural invite like "check it out", "link below", "new video"
✗ DO NOT repost the title verbatim - the link already shows it
✗ DO NOT include the URL (it's added automatically)
✗ DO NOT invent details not in the title (no "giveaways", "premiering tonight", etc.)
✗ DO NOT use cringe words: "INSANE", "EPIC", "smash that", "unmissable", "legendary", "incredible"{hashtag_instruction}

EXAMPLES OF GOOD POSTS:

Example 1 - Tech Tutorial:
Title: "Building a Home Server with Proxmox"
Good: "New video! Building out a home server with Proxmox. Full walkthrough from hardware to config 💻 #Homelab #Proxmox #SelfHosted"

Example 2 - Gaming:
Title: "Elden Ring Boss Guide - Malenia"
Good: "Finally beat Malenia and made a guide about it. Tips that actually work. #EldenRing #BossGuide #Gaming"

Example 3 - Casual/Vlog:
Title: "Day in My Life - Remote Worker Edition"
Good: "New vlog is up! A day in my life working remote. Coffee, code, and questionable time management 🎬 #RemoteWork #Vlog #DayInMyLife"

BAD examples to AVOID:
✗ "EPIC new video just dropped! INSANE content! #AMAZING #EPIC" (cringe, forbidden words)
✗ Just copying: "Building a Home Server with Proxmox #Server #Home #Build" (lazy, no personality)
✗ "Check out my new video at https://..." (don't include URL)

NOW: Write the post for "{title}" from {channel_name}. Match the title's energy. {f'Exactly {hashtag_count} hashtags. ' if use_hashtags else 'No hashtags needed. '}Under {max_chars} characters.

Post:"""
