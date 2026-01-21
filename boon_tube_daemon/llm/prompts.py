# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Advanced prompt templates for LLM message generation.

Because apparently we need to write a fucking instruction manual for robots
to announce YouTube videos on social media.

These prompts use step-by-step instructions, examples, and anti-cringe warnings
because small LLMs (2B-4B params) need their hands held like toddlers learning to write.

George Carlin would've had a field day: "We built machines that can process billions
of operations per second, but we still need to tell them 'Don't say INSANE!' like
we're teaching a teenager not to embarrass themselves on TikTok."

NOTE: This is for VIDEO UPLOAD notifications, not live stream announcements.
Videos are permanent content (tutorials, reviews, walkthroughs), not ephemeral streams.
"""


def build_video_notification_prompt(
    platform_name: str,
    creator_name: str,
    title: str,
    description: str,
    social_platform: str,
    max_chars: int,
    use_hashtags: bool = True,
    strict_mode: bool = False,
    post_style: str = 'conversational'
) -> str:
    """
    Build sophisticated prompt for VIDEO upload notifications with step-by-step instructions.
    
    Designed for YouTube/TikTok/etc VIDEO content (not live streams).
    Uses explicit constraints to prevent hallucinations and examples for better enforcement.
    
    Args:
        platform_name: Source platform (YouTube, TikTok, etc.)
        creator_name: Creator's username
        title: Video title
        description: Video description (already cleaned/truncated)
        social_platform: Target platform (discord, bluesky, mastodon, matrix)
        max_chars: Maximum character count
        use_hashtags: Whether to include hashtags
        strict_mode: If True, adds extra emphasis (used for retries)
        post_style: Tone style (professional, conversational, detailed, concise)
    
    Returns:
        Formatted prompt string
        
    This is peak human achievement: Writing essays to teach robots how to announce videos.
    """
    strict_prefix = ""
    if strict_mode:
        strict_prefix = """⚠️ CRITICAL: Previous attempt violated rules. FOLLOW INSTRUCTIONS EXACTLY. ⚠️

"""
    
    # Style-specific instructions
    style_instructions = {
        'professional': "Use a formal, clear, business-like tone. Be informative and direct.",
        'conversational': "Use a casual, friendly tone. Sound like a real person sharing something cool.",
        'detailed': "Provide comprehensive context. Explain what viewers will learn or see in detail.",
        'concise': "Be brief and punchy. Minimal words, maximum impact."
    }
    
    style_instruction = style_instructions.get(post_style, style_instructions['conversational'])
    
    # Mastodon gets more flexible hashtag count (3-5), others get exactly 3
    if social_platform == 'mastodon' and use_hashtags:
        hashtag_count = '3-5'
        hashtag_instruction = f"""
STEP 2 - HASHTAG RULES:
Include 3-5 SHORT, relevant hashtags at the end.

Hashtag guidelines:
- Use 3-5 hashtags (not 2, not 6, somewhere in that range)
- Extract from words in the video title: "{title}"
- NEVER use the creator name "{creator_name}" or any part of it as a hashtag
- NEVER use generic tags (#Video, #NewVideo, #Content) unless in the title
- Keep hashtags SHORT: #Linux not #LinuxForBeginners
- Format: space before each hashtag"""
    elif use_hashtags:
        hashtag_count = 3
        hashtag_instruction = f"""
STEP 2 - HASHTAG RULES (CRITICAL):
You MUST include EXACTLY 3 hashtags at the end.

Count: 1, 2, 3 hashtags. Not 2. Not 4. Exactly 3.
(Yes, we have to teach a computer how to count. Welcome to the future.)

Hashtag source rules:
- Extract hashtags ONLY from words in the video title: "{title}"
- NEVER use the creator name "{creator_name}" or any part of it as a hashtag
- NEVER use generic tags (#Gaming, #Live, #Video) unless in the title
- Format: space before each hashtag
- SHORT hashtags only: #Tech not #TechnologyReview"""
    else:
        hashtag_count = 0
        hashtag_instruction = ""
    
    examples = ""
    if social_platform == 'bluesky':
        examples = f"""
EXAMPLES:

Example 1:
Title: "How to Build a Gaming PC"
Good post: "New guide on building your first gaming PC! Perfect for beginners 🖥️ #Gaming #PC #Tutorial"
({hashtag_count} hashtags from title words)

Example 2:
Title: "Cooking Easy Pasta Carbonara"
Good post: "Just dropped a super easy carbonara recipe! #Cooking #Pasta #Recipe"
({hashtag_count} hashtags from title)

Bad examples to AVOID:
✗ "INSANE new video! EPIC build guide!" (cringe words)
✗ "Check out my video #Subscribe #Like" (generic tags, not from title)
✗ Using only 2 hashtags or using 4+ hashtags"""

    elif social_platform == 'mastodon':
        examples = f"""
EXAMPLES:

Example 1:
Title: "Linux Server Setup for Beginners"
Good post: "New video: Setting up your first Linux server! Step-by-step guide for beginners #Linux #Server #Tutorial #SysAdmin"
(4 hashtags - flexible range)

Example 2:
Title: "Photography Tips - Golden Hour Shooting"
Good post: "Just uploaded tips for shooting during golden hour! Check it out 📸 #Photography #Tips #GoldenHour"
(3 hashtags - minimum is fine)

Example 3:
Title: "Python Data Science Tutorial"
Good post: "Complete guide to data analysis with Python! Covers pandas, numpy, visualization #Python #DataScience #Tutorial #Programming #Analytics"
(5 hashtags - maximum allowed)

Bad examples to AVOID:
✗ "MUST WATCH! Amazing tutorial!" (clickbait, no real content)
✗ "New video is live! #YouTube #NewVideo #Content" (generic tags)
✗ Using only 2 hashtags or using 6+ hashtags"""
    
    elif social_platform == 'discord':
        examples = """
EXAMPLES:

Example 1:
Title: "Minecraft Survival Series - Episode 5"
Good post: "Episode 5 of the survival series is up! Building the mega base continues 🏰"
(No hashtags, conversational)

Example 2:
Title: "Speedrun World Record Attempt"
Good post: "Just posted my world record attempt run! It was intense"
(Casual, no hashtags)

Bad examples to AVOID:
✗ "Hey Discord! New video!" (greeting waste)
✗ "Check it out at youtube.com/watch?v=FAKE_ID" (no placeholder URLs)"""
    
    elif social_platform == 'matrix':
        examples = """
EXAMPLES:

Example 1:
Title: "Software Tutorial - Getting Started with Docker"
Good post: "New Docker tutorial for beginners. Covers installation and first containers."
(Professional, no hashtags)

Example 2:
Title: "Game Review - Latest RPG Analysis"
Good post: "Posted my analysis of the new RPG. Spoiler-free review with gameplay insights."
(Informative, no hashtags)"""
    
    return f"""{strict_prefix}You are a social media assistant that announces new {platform_name} video uploads.

TASK: Write a SHORT, engaging post announcing this NEW VIDEO.

VIDEO TITLE: "{title}"
VIDEO DESCRIPTION: {description}

STYLE: {post_style.title()}
{style_instruction}

STEP 1 - CONTENT RULES (FOLLOW EXACTLY):
✓ Length: MUST be {max_chars} characters or less (this is NON-NEGOTIABLE)
✓ Output: ONLY the post text (no quotes, no labels, no "Here's...")
✓ Tone: Match the {post_style} style described above
✓ Content: Highlight what the video covers - what viewers will learn or see
✓ Context: Use BOTH the title AND description to understand the video content
✓ Emoji: Use 0-1 emoji maximum (optional, relevant to content)
✗ DO NOT include the URL (it's added automatically)
✗ DO NOT invent details not in title/description (no "limited time", "special offer", "exclusive", fake timestamps)
✗ DO NOT use cringe words: "INSANE", "EPIC", "CRAZY", "UNMISSABLE", "smash that like button"
✗ DO NOT use greetings like "Hey everyone!" or "What's up {social_platform}!" - announce the video directly{hashtag_instruction}{examples}

NOW: Write the announcement for "{title}". Remember: {"exactly 3 hashtags, " if hashtag_count == 3 else f"{hashtag_count} hashtags, " if use_hashtags else ""}under {max_chars} characters, NO URLs, {post_style} style.

Post:"""
