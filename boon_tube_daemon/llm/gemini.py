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
from typing import Optional, Dict, Any
import google.generativeai as genai

from boon_tube_daemon.utils.config import get_config, get_secret, get_bool_config

logger = logging.getLogger(__name__)


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
            
            self.enabled = True
            logger.info(f"✓ Gemini LLM initialized ({model_name})")
            return True
            
        except Exception as e:
            logger.error(f"✗ Gemini LLM initialization failed: {e}")
            self.enabled = False
            return False
    
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
Description: {description[:500]}

Create a concise summary that captures the main topic and would make people want to watch. Be enthusiastic but professional."""

            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            
            # Ensure length limit
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            logger.debug(f"Generated summary: {summary[:50]}...")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
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
Description: {description[:300]}

Example format: #Tech #Gaming #Tutorial #AI #Programming"""

            response = self.model.generate_content(prompt)
            hashtags = response.text.strip()
            
            logger.debug(f"Generated hashtags: {hashtags}")
            return hashtags
            
        except Exception as e:
            logger.error(f"Error generating hashtags: {e}")
            return None
    
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
            
            # Get platform-specific posting style from config
            social_platform_lower = social_platform.lower()
            style_key = f"{social_platform_lower.title()}_post_style"
            
            # Default styles per platform
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
            
            # Style-specific instructions
            style_instructions = {
                'professional': "Use a formal, clear, business-like tone. Be informative and direct.",
                'conversational': "Use a casual, friendly, community-focused tone. Be warm and approachable.",
                'detailed': "Provide comprehensive context and explanation. Be thorough and informative.",
                'concise': "Be brief and to-the-point. Use minimal text while staying engaging."
            }
            
            style_instruction = style_instructions.get(post_style, style_instructions['conversational'])
            
            # Platform-specific prompts
            if social_platform_lower == 'discord':
                prompt = f"""Create an engaging Discord announcement for this new {platform_name} video.

Title: {title}
Description: {cleaned_desc}

Style: {post_style}
{style_instruction}

Discord-specific guidelines:
- NO hashtags (Discord doesn't use them)
- NO platform greetings like "Hey Discord!" or "Hello everyone!" - just get to the content
- NO placeholder URLs like "[YouTube Link]" or "youtu.be/your_youtube_link_here" - the actual URL will be added automatically
- End with an invitation to watch/discuss
- Keep it under 300 characters (URL will be added separately)

Write the announcement now WITHOUT including any URLs:"""

            elif social_platform_lower == 'matrix':
                prompt = f"""Create a Matrix/Element announcement for this new {platform_name} video.

Title: {title}
Description: {cleaned_desc}

Style: {post_style}
{style_instruction}

Matrix-specific guidelines:
- NO hashtags (Matrix doesn't use them)
- NO platform greetings like "Hey Matrix!" - just get to the content
- NO placeholder URLs like "[VIDEO_ID]" or "youtube.com/watch?v=[VIDEO_ID]" - the actual URL will be added automatically
- Focus on the content value
- Keep it under 350 characters (URL will be added separately)

Write the announcement now WITHOUT including any URLs:"""

            elif social_platform_lower == 'bluesky':
                prompt = f"""Create an engaging Bluesky post for this new {platform_name} video.

Title: {title}
Description: {cleaned_desc}

Style: {post_style}
{style_instruction}

Bluesky-specific guidelines:
- CRITICAL: ABSOLUTE MAXIMUM 300 characters TOTAL (Bluesky will reject anything longer)
- Count EVERY character including spaces, emojis, URL, and hashtags
- NO platform greetings like "Hey Bluesky!" - wastes precious characters
- NO meta text like "Here's a post:" or "Bluesky draft:" - just write the actual post
- NO placeholder URLs like "youtube.com/watch/example" or "[YouTube Link]" - the actual URL will be added automatically
- Include 2-3 SHORT hashtags (#Linux not #LinuxForBeginners)
- Put hashtags at the end
- Keep main text to ~250 chars to leave room for hashtags

Write ONLY the post content WITHOUT any URLs (must be under 300 chars total):"""

            elif social_platform_lower == 'mastodon':
                prompt = f"""Create an engaging Mastodon toot for this new {platform_name} video.

Title: {title}
Description: {cleaned_desc}

Style: {post_style}
{style_instruction}

Mastodon-specific guidelines:
- CRITICAL: ABSOLUTE MAXIMUM 500 characters TOTAL (Mastodon will reject anything longer)
- Count EVERY character including spaces, hashtags, punctuation
- NO platform greetings like "Hey Mastodon!" - wastes characters
- NO placeholder URLs like "YOUR_VIDEO_ID" - the actual URL will be added automatically
- Include 3-5 SHORT hashtags at the end (#Linux not #LinuxForBeginners)
- Keep main text to ~380 chars MAX to leave room for hashtags (URL added separately)
- If style is 'detailed', be comprehensive but STAY UNDER 500 chars total

Write the toot now WITHOUT including any URLs (MUST be under 500 chars total):"""

            else:
                # Fallback for unknown platforms
                prompt = f"""Create an engaging social media post for this new {platform_name} video.

Title: {title}
Description: {cleaned_desc}

Style: {post_style}
{style_instruction}

Keep it under 280 characters, include the URL, and make it clickable.

Write the post now:"""

            response = self.model.generate_content(prompt)
            notification = response.text.strip()
            
            # Clean up common LLM meta-text patterns
            meta_patterns = [
                r'^(?:Here\'?s|Okay,? here\'?s|Alright,? here\'?s)\s+(?:a|an|your)\s+(?:Bluesky|Mastodon|Discord|Matrix)?\s*(?:post|toot|announcement|draft).*?:?\s*',
                r'^(?:Here you go|Sure thing|Certainly).*?:?\s*',
                r'^Draft.*?:?\s*',
            ]
            
            for pattern in meta_patterns:
                notification = re.sub(pattern, '', notification, flags=re.IGNORECASE | re.MULTILINE)
            notification = notification.strip()
            
            # Ensure URL is included (should be from LLM, but double-check)
            if url and url not in notification:
                notification += f"\n\n{url}"
            
            logger.info(f"✨ Generated {social_platform} post ({post_style} style): {notification[:60]}...")
            return notification
            
        except Exception as e:
            logger.error(f"Error generating enhanced notification for {social_platform}: {e}")
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
Description: {description[:300]}"""

            response = self.model.generate_content(prompt)
            sentiment = response.text.strip().lower()
            
            logger.debug(f"Analyzed sentiment: {sentiment}")
            return sentiment
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
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
Description: {description[:300]}

Filter out:
- Spam or clickbait
- Low-quality content
- Off-topic videos
{f'- Content containing: {filter_keywords}' if filter_keywords else ''}

Return ONLY "yes" or "no"."""

            response = self.model.generate_content(prompt)
            decision = response.text.strip().lower()
            
            should_notify = 'yes' in decision
            
            if not should_notify:
                logger.info(f"🚫 LLM filtered out video: {title[:50]}...")
            
            return should_notify
            
        except Exception as e:
            logger.error(f"Error in LLM filtering: {e}")
            return True  # Default to notifying on error
