# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Google Gemini Flash 2.0 Lite integration for Boon-Tube-Daemon.

Provides intelligent content analysis, summary generation, and enhanced
notifications using Google's Gemini AI model.
"""

import logging
import re
import time
import threading
from typing import Optional, Dict, Any
import google.generativeai as genai

from boon_tube_daemon.utils.config import get_config, get_secret, get_bool_config, get_int_config
from boon_tube_daemon.utils.rate_limiter import RateLimiter
from boon_tube_daemon.llm.validator import LLMValidator
from boon_tube_daemon.llm.prompts import build_video_notification_prompt

logger = logging.getLogger(__name__)

# Global rate limiting: max 4 concurrent requests, 2-second minimum delay between calls
# Because apparently we need a traffic cop for our AI API calls
# Without this, 10 videos going live at once = instant quota exceeded
# It's like rush hour for robots. Beep beep, motherfuckers.
_api_semaphore = threading.Semaphore(4)
_last_api_call_time = 0
_api_call_lock = threading.Lock()
_min_delay_between_calls = 2.0  # seconds (30 requests/min = one every 2 seconds)


class GeminiLLM:
    """
    Google Gemini Flash 2.0 Lite integration.
    
    Features:
    - Video content analysis from titles and descriptions
    - Intelligent summary generation
    - Sentiment analysis
    - Hashtag suggestions
    - Enhanced notification text generation
    """
    
    def __init__(self):
        self.name = "Gemini-Flash-2.0-Lite"
        self.enabled = False
        self.model = None
        self.api_key = None
        self.rate_limiter = None
        
        # Retry configuration for handling transient API errors (503, 429, etc.)
        # Because even Google's servers have bad days
        self.max_retries = int(get_config('LLM', 'max_retries', default='3'))
        self.retry_delay_base = int(get_config('LLM', 'retry_delay_base', default='2'))
        
        # Generation parameters for better control with small LLMs
        # Temperature: Because even AI needs a chill pill to stop hallucinating
        # We set it low so the model doesn't get "creative" and start making shit up
        # about giveaways and premieres that don't exist
        self.temperature = float(get_config('LLM', 'temperature', default='0.3'))
        self.top_p = float(get_config('LLM', 'top_p', default='0.9'))
        self.max_tokens = int(get_config('LLM', 'max_tokens', default='150'))
        
        # Character limits for different platforms
        # Because each social media site is a special snowflake
        self.bluesky_max_chars = 300
        self.mastodon_max_chars = 500
        
        # Initialize guardrails validator
        # Because even billion-parameter neural networks need a fucking babysitter
        self.validator = LLMValidator()
        
    def authenticate(self) -> bool:
        """
        Initialize Gemini API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Check if LLM is enabled
            if not get_bool_config('LLM', 'enable', default=False):
                logger.info("⊘ Gemini LLM disabled in config")
                return False
            
            # Get API key
            self.api_key = get_secret('LLM', 'gemini_api_key')
            
            if not self.api_key:
                logger.warning("✗ Gemini API key not found")
                return False
            
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            
            # Initialize model
            model_name = get_config('LLM', 'model', default='gemini-2.5-flash-lite')
            self.model = genai.GenerativeModel(model_name)
            
            # Initialize rate limiter
            # Gemini Free Tier: 15 requests per minute
            # https://ai.google.dev/pricing#1_5flash
            rate_limit = get_int_config('LLM', 'rate_limit', default=15)
            self.rate_limiter = RateLimiter(max_requests=rate_limit, time_window=60.0)
            
            self.enabled = True
            logger.info(f"✓ Gemini LLM initialized ({model_name}, {rate_limit} req/min)")
            return True
            
        except Exception as e:
            logger.error("✗ Gemini LLM initialization failed")
            self.enabled = False
            return False
    
    def _generate_with_retry(self, prompt: str, max_retries: int = None) -> Optional[str]:
        """
        Generate content with exponential backoff retry logic and GLOBAL rate limiting.
        
        Handles transient errors like:
        - 503 Service Unavailable (model overloaded)
        - 429 Rate Limit Exceeded
        - Network timeouts
        
        Uses a global semaphore to limit concurrent API calls (max 4) and enforces
        minimum 2-second delay between requests to prevent quota exhaustion when
        multiple videos drop simultaneously.
        
        Because apparently we need a traffic cop for our API calls. It's like rush hour
        for robots. Without this, 10 videos at once = instant quota exceeded.
        Welcome to the distributed systems clusterfuck.
        
        Args:
            prompt: The prompt to send to Gemini
            max_retries: Maximum retry attempts (defaults to self.max_retries)
        
        Returns:
            Generated text or None if all retries fail
        """
        global _last_api_call_time
        
        if max_retries is None:
            max_retries = self.max_retries
        
        last_error = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                # Rate limiting: wait for semaphore slot (max 4 concurrent)
                # This prevents us from DOSing ourselves. Self-inflicted wounds, the best kind.
                with _api_semaphore:
                    # Enforce minimum delay between API calls
                    # Like a speed limit, but for robots talking to other robots
                    with _api_call_lock:
                        time_since_last_call = time.time() - _last_api_call_time
                        if time_since_last_call < _min_delay_between_calls:
                            sleep_time = _min_delay_between_calls - time_since_last_call
                            logger.debug(f"⏱ Rate limiting: waiting {sleep_time:.2f}s before API call...")
                            time.sleep(sleep_time)
                        _last_api_call_time = time.time()
                    
                    # Make API call with generation config for better control
                    # Teaching the AI to behave with temperature and top_p
                    response = self.model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=self.temperature,
                            top_p=self.top_p,
                            max_output_tokens=self.max_tokens,
                        )
                    )
                    result = response.text.strip()
                
                # Fix escaped newlines and other escape sequences
                # Sometimes LLM returns strings with literal \n instead of actual newlines
                # This is a common issue when LLM treats the output as a string representation
                # Note: This is safe for our use case (social media posts) as we don't expect
                # file paths or other content with legitimate backslash-n sequences
                if '\\n' in result:
                    logger.debug("Detected escaped newlines in LLM response, decoding...")
                    
                    # First, remove quotes if response is wrapped (indicates string representation)
                    if (result.startswith('"') and result.endswith('"')) or \
                       (result.startswith("'") and result.endswith("'")):
                        result = result[1:-1]
                    
                    # Then decode common escape sequences
                    result = result.replace('\\n', '\n')
                    result = result.replace('\\t', '\t')
                    result = result.replace('\\r', '\r')
                    
                    result = result.strip()
                
                return result
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check if it's a retryable error
                # Some errors mean "try again", others mean "fuck off, you're blocked"
                is_retryable = (
                    '503' in error_str or  # Service Unavailable
                    '429' in error_str or  # Rate Limit
                    '500' in error_str or  # Internal Server Error
                    'overloaded' in error_str or
                    'quota' in error_str or
                    'timeout' in error_str or
                    'connection' in error_str
                )
                
                if not is_retryable or attempt >= max_retries:
                    # Non-retryable error or final attempt - give up
                    # The AI has spoken: "No."
                    logger.error(f"✗ Failed to generate content: {e}")
                    return None
                
                # Calculate exponential backoff delay
                # Wait a bit, then wait longer, then wait even longer
                # Like a teenager snoozing their alarm
                delay = self.retry_delay_base ** attempt
                logger.warning(
                    f"⚠ API error (attempt {attempt + 1}/{max_retries + 1}): {error_str}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
        
        # Should not reach here, but just in case
        logger.error(f"✗ Failed after {max_retries + 1} attempts: {last_error}")
        return None
    
    def clean_description(self, description: str, max_length: int = 500) -> str:
        """
        Clean video description by removing URLs, sponsor links, social media handles,
        tip jar links, and other promotional content.
        
        Args:
            description: Raw video description
            max_length: Maximum length to return
            
        Returns:
            Cleaned description text
        """
        if not description:
            return ""
        
        # Remove URLs (http/https)
        cleaned = re.sub(r'https?://[^\s]+', '', description)
        
        # Remove social media handles (@username, @handle)
        cleaned = re.sub(r'@\w+', '', cleaned)
        
        # Remove common sponsor/tip keywords and their surrounding text
        sponsor_patterns = [
            r'(?i)sponsor(?:ed|s)?\s*(?:by|:)?[^\n]*',
            r'(?i)support\s+(?:me|us)\s+on[^\n]*',
            r'(?i)patreon[^\n]*',
            r'(?i)ko-fi[^\n]*',
            r'(?i)buy\s+me\s+a\s+coffee[^\n]*',
            r'(?i)tip\s+jar[^\n]*',
            r'(?i)donate[^\n]*',
            r'(?i)merch[^\n]*',
            r'(?i)affiliate[^\n]*',
            r'(?i)discord\s+server[^\n]*',
            r'(?i)join\s+(?:my|our)\s+discord[^\n]*',
        ]
        
        for pattern in sponsor_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Remove "Follow me on" type lines
        cleaned = re.sub(r'(?i)follow\s+(?:me|us)\s+on[^\n]*', '', cleaned)
        cleaned = re.sub(r'(?i)find\s+me\s+on[^\n]*', '', cleaned)
        cleaned = re.sub(r'(?i)connect\s+with\s+me[^\n]*', '', cleaned)
        
        # Remove multiple newlines and excessive whitespace
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        # Truncate to max length
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length].rsplit(' ', 1)[0] + "..."
        
        return cleaned
    
    def generate_summary(self, video_data: Dict[str, Any], max_length: int = 200) -> Optional[str]:
        """
        Generate a concise summary of video content.
        
        Args:
            video_data: Video information dict (title, description, etc.)
            max_length: Maximum summary length in characters
            
        Returns:
            Generated summary or None on error
        """
        if not self.enabled or not self.model:
            return None
        
        try:
            title = video_data.get('title', '')
            description = video_data.get('description', '')
            
            prompt = f"""Analyze this video and create a brief, engaging summary in {max_length} characters or less:

Title: {title}
Description: {LLMValidator.safe_trim(description, 500)}

Create a concise summary that captures the main topic and would make people want to watch. Be enthusiastic but professional."""

            summary = self._generate_with_retry(prompt)
            
            if summary:
                # Ensure length limit
                # Use safe_trim to not cut hashtags mid-word like a savage
                if len(summary) > max_length:
                    summary = LLMValidator.safe_trim(summary, max_length)
                
                logger.debug(f"Generated summary: {summary[:50]}...")
                return summary
            
            return None
            
        except Exception as e:
            logger.error("Error generating summary")
            return None
    
    def generate_hashtags(self, video_data: Dict[str, Any], max_tags: int = 5) -> Optional[str]:
        """
        Generate relevant hashtags for the video.
        
        Args:
            video_data: Video information dict
            max_tags: Maximum number of hashtags to generate
            
        Returns:
            Space-separated hashtags or None on error
        """
        if not self.enabled or not self.model:
            return None
        
        try:
            title = video_data.get('title', '')
            description = video_data.get('description', '')
            
            prompt = f"""Generate {max_tags} relevant, popular hashtags for this video. Return ONLY the hashtags separated by spaces, with # prefix.

Title: {title}
Description: {LLMValidator.safe_trim(description, 300)}

Example format: #Tech #Gaming #Tutorial #AI #Programming"""

            hashtags = self._generate_with_retry(prompt)
            
            if hashtags:
                logger.debug(f"Generated hashtags: {hashtags}")
                return hashtags
            
            return None
            
        except Exception as e:
            logger.error("Error generating hashtags")
            return None
    
    def generate_notification(self, video_data: dict, platform_name: str, social_platform: str) -> Optional[str]:
        """
        Generate a platform-specific notification message (unified interface).
        Alias for enhance_notification for consistency with Ollama provider.
        
        Args:
            video_data: Video information dict (title, description, url, etc.)
            platform_name: Source platform name (YouTube, TikTok, etc.)
            social_platform: Target social platform (discord, matrix, bluesky, mastodon)
            
        Returns:
            Generated notification text or None on error
        """
        return self.enhance_notification(video_data, platform_name, social_platform)
    
    def enhance_notification(self, video_data: Dict[str, Any], platform_name: str, social_platform: str) -> Optional[str]:
        """
        Generate a platform-specific enhanced notification message with AI.
        Each social platform gets a unique, tailored post.
        
        Args:
            video_data: Video information dict (title, description, url, etc.)
            platform_name: Source platform name (YouTube, TikTok, etc.)
            social_platform: Target social platform (discord, matrix, bluesky, mastodon)
            
        Returns:
            Enhanced notification text or None on error
        """
        if not self.enabled or not self.model:
            return None
        
        try:
            title = video_data.get('title', '')
            description = video_data.get('description', '')
            url = video_data.get('url', '')
            
            # Clean description to remove sponsor links, URLs, etc.
            cleaned_desc = self.clean_description(description, max_length=400)
            # Trim description to safe length for prompts
            trimmed_desc = LLMValidator.safe_trim(cleaned_desc, 300)
            
            # Platform-specific configuration
            social_platform_lower = social_platform.lower()
            
            # Get platform-specific posting style from config (with sensible defaults)
            default_styles = {
                'discord': 'conversational',
                'matrix': 'professional',
                'bluesky': 'conversational',
                'mastodon': 'detailed'
            }
            
            post_style = get_config(
                social_platform.title(),
                'post_style',
                default=default_styles.get(social_platform_lower, 'conversational')
            ).lower()
            
            # Determine character limits and hashtag usage
            if social_platform_lower == 'discord':
                max_chars = 300
                use_hashtags = False
            elif social_platform_lower == 'matrix':
                max_chars = 350
                use_hashtags = False
            elif social_platform_lower == 'bluesky':
                # Bluesky: 300 total - 43 URL - 5 buffer = 250 for content
                max_chars = 250
                use_hashtags = True
            elif social_platform_lower == 'mastodon':
                # Mastodon: 500 total - 43 URL - 5 buffer = 450 for content
                max_chars = 450
                use_hashtags = True
            else:
                max_chars = 300
                use_hashtags = False
            
            # Build sophisticated prompt using template system
            # This is peak humanity: writing instruction manuals for robots
            prompt = build_video_notification_prompt(
                platform_name=platform_name,
                creator_name=platform_name,  # Using platform as creator context
                title=title,
                description=trimmed_desc,
                social_platform=social_platform_lower,
                max_chars=max_chars,
                use_hashtags=use_hashtags,
                strict_mode=False,
                post_style=post_style  # Pass the style configuration
            )
            
            notification = self._generate_with_retry(prompt)
            if not notification:
                logger.warning(f"Failed to generate enhanced notification for {social_platform}, using fallback")
                return None
            
            # GUARDRAILS: Quality validation and retry logic
            # Because teaching a robot to count to three is apparently harder than building the robot
            # Mastodon gets a flexible range (3-5), others get exactly 3
            max_validation_retries = 2
            if social_platform_lower == 'mastodon' and use_hashtags:
                expected_hashtag_count = "3-5"  # Flexible range for Mastodon
            else:
                expected_hashtag_count = 3 if use_hashtags else 0
            
            for retry in range(max_validation_retries):
                # Run the gauntlet of guardrails
                is_valid, issues = self.validator.validate_full_message(
                    notification,
                    expected_hashtag_count=expected_hashtag_count,
                    title=title,
                    username=platform_name,
                    platform=social_platform_lower
                )
                
                if is_valid:
                    # Victory! The AI followed instructions (for once)
                    if retry > 0:
                        logger.info(f"✅ Retry #{retry} produced valid message after quality checks")
                    else:
                        logger.debug(f"✓ Message passed all guardrail checks on first try")
                    break
                else:
                    # AI fucked up. Shocking, I know.
                    logger.warning(f"⚠ Generated message has quality issues (attempt {retry + 1}/{max_validation_retries}): {', '.join(issues)}")
                    
                    if retry < max_validation_retries - 1:
                        # Try again with strict_mode enabled
                        # This adds extra "⚠️ CRITICAL" warnings to scare the AI into compliance
                        logger.info(f"🔄 Retrying with strict mode enabled...")
                        strict_prompt = build_video_notification_prompt(
                            platform_name=platform_name,
                            creator_name=platform_name,
                            title=title,
                            description=trimmed_desc,
                            social_platform=social_platform_lower,
                            max_chars=max_chars,
                            use_hashtags=use_hashtags,
                            strict_mode=True,  # Enable strict mode for retry
                            post_style=post_style  # Maintain consistent style
                        )
                        notification = self._generate_with_retry(strict_prompt)
                        if not notification:
                            logger.warning(f"Retry failed to generate, using original despite issues")
                            break
                    else:
                        # All retries exhausted, use what we got
                        logger.warning(f"⚠ Validation retries exhausted, using message with issues")
            
            # Remove username-derived hashtags (post-generation cleanup)
            # Because the AI loves to use people's names as hashtags like a fucking amateur
            notification = self.validator.validate_hashtags_against_username(notification, platform_name)
            
            # Add to deduplication cache for future checks
            self.validator.add_to_message_cache(notification)
            
            # Clean up common LLM meta-text patterns
            meta_patterns = [
                r'^(?:Here\'?s|Okay,? here\'?s|Alright,? here\'?s)\s+(?:a|an|your)\s+(?:Bluesky|Mastodon|Discord|Matrix)?\s*(?:post|toot|announcement|draft).*?:?\s*',
                r'^(?:Here you go|Sure thing|Certainly).*?:?\s*',
                r'^Draft.*?:?\s*',
            ]
            
            for pattern in meta_patterns:
                notification = re.sub(pattern, '', notification, flags=re.IGNORECASE | re.MULTILINE)
            notification = notification.strip()
            
            # Remove any URLs the LLM might have included (we add the real one)
            notification = re.sub(r'https?://[^\s]+', '', notification).strip()
            
            # BLUESKY: Enforce hard character limit BEFORE adding URL
            # Bluesky limit is 300 graphemes. URL is ~43 chars + 2 newlines = 45
            # Leave buffer for grapheme counting differences (emojis, etc.)
            if social_platform_lower == 'bluesky':
                max_content_length = 250  # 300 - 43 URL - 2 newlines - 5 buffer
                if len(notification) > max_content_length:
                    logger.warning(f"Bluesky content too long ({len(notification)} chars), truncating to {max_content_length}")
                    # Try to truncate at a word boundary before the limit
                    truncated = notification[:max_content_length]
                    # Find last space to avoid cutting mid-word
                    last_space = truncated.rfind(' ')
                    if last_space > max_content_length - 50:  # Only if we don't lose too much
                        truncated = truncated[:last_space]
                    # Try to preserve hashtags if they were at the end
                    hashtag_match = re.search(r'((?:\s*#\w+)+)\s*$', notification)
                    if hashtag_match and len(truncated) + len(hashtag_match.group(1)) <= max_content_length:
                        truncated = truncated.rstrip() + hashtag_match.group(1)
                    notification = truncated.strip()
            
            # Ensure URL is included (should be from LLM, but double-check)
            if url and url not in notification:
                notification += f"\n\n{url}"
            
            logger.info(f"✨ Generated {social_platform} post ({post_style} style): {notification[:60]}...")
            return notification
            
        except Exception as e:
            logger.error(f"Error generating enhanced notification for {social_platform}")
            return None
    
    def analyze_sentiment(self, video_data: Dict[str, Any]) -> Optional[str]:
        """
        Analyze the sentiment/tone of the video content.
        
        Args:
            video_data: Video information dict
            
        Returns:
            Sentiment label (positive, negative, neutral, informative, etc.)
        """
        if not self.enabled or not self.model:
            return None
        
        try:
            title = video_data.get('title', '')
            description = video_data.get('description', '')
            
            prompt = f"""Analyze the tone/sentiment of this video content. Return ONE WORD only from: positive, negative, neutral, educational, entertainment, news, tutorial, review, comedy, dramatic.

Title: {title}
Description: {LLMValidator.safe_trim(description, 300)}"""

            sentiment = self._generate_with_retry(prompt)
            if not sentiment:
                logger.warning("Failed to analyze sentiment, returning None")
                return None
            
            sentiment = sentiment.lower()
            logger.debug(f"Analyzed sentiment: {sentiment}")
            return sentiment
            
        except Exception as e:
            logger.error("Error analyzing sentiment")
            return None
    
    def should_notify(self, video_data: Dict[str, Any]) -> bool:
        """
        Use AI to determine if this video is worth notifying about.
        Can filter out spam, low-quality, or off-topic content.
        
        Args:
            video_data: Video information dict
            
        Returns:
            True if should notify, False if should skip
        """
        if not self.enabled or not self.model:
            return True  # Default to notifying if LLM not available
        
        # Check if filtering is enabled
        if not get_bool_config('LLM', 'enable_filtering', default=False):
            return True
        
        try:
            title = video_data.get('title', '')
            description = video_data.get('description', '')
            
            # Get filter criteria from config
            filter_keywords = get_config('LLM', 'filter_keywords', default='')
            
            prompt = f"""Determine if this video should trigger a notification based on quality and relevance.

Title: {title}
Description: {LLMValidator.safe_trim(description, 300)}

Filter out:
- Spam or clickbait
- Low-quality content
- Off-topic videos
{f'- Content containing: {filter_keywords}' if filter_keywords else ''}

Return ONLY "yes" or "no"."""

            decision = self._generate_with_retry(prompt)
            if not decision:
                logger.warning("Failed to get LLM filtering decision, defaulting to notify")
                return True
            
            decision = decision.lower()
            should_notify = 'yes' in decision
            
            if not should_notify:
                logger.info(f"🚫 LLM filtered out video: {title[:50]}...")
            
            return should_notify
            
        except Exception as e:
            logger.error("Error in LLM filtering")
            return True  # Default to notifying on error
