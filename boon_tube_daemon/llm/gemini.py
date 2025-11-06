# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Google Gemini Flash 2.0 Lite integration for Boon-Tube-Daemon.

Provides intelligent content analysis, summary generation, and enhanced
notifications using Google's Gemini AI model.
"""

import logging
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
            model_name = get_config('LLM', 'model', default='gemini-2.0-flash-exp')
            self.model = genai.GenerativeModel(model_name)
            
            self.enabled = True
            logger.info(f"✓ Gemini LLM initialized ({model_name})")
            return True
            
        except Exception as e:
            logger.error(f"✗ Gemini LLM initialization failed: {e}")
            self.enabled = False
            return False
    
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
    
    def enhance_notification(self, video_data: Dict[str, Any], platform_name: str) -> Optional[str]:
        """
        Generate an enhanced notification message with AI.
        
        Args:
            video_data: Video information dict
            platform_name: Name of the video platform (YouTube, TikTok)
            
        Returns:
            Enhanced notification text or None on error
        """
        if not self.enabled or not self.model:
            return None
        
        try:
            title = video_data.get('title', '')
            description = video_data.get('description', '')
            url = video_data.get('url', '')
            
            prompt = f"""Create an engaging social media notification for this new video. Make it exciting and clickable while being concise (under 280 characters).

Platform: {platform_name}
Title: {title}
Description: {description[:300]}

Include:
- An attention-grabbing emoji
- Brief description of what the video is about
- A call to action
- The URL on a new line

Format as plain text suitable for social media."""

            response = self.model.generate_content(prompt)
            notification = response.text.strip()
            
            # Ensure URL is included
            if url not in notification:
                notification += f"\n\n{url}"
            
            logger.debug(f"Generated notification: {notification[:50]}...")
            return notification
            
        except Exception as e:
            logger.error(f"Error generating enhanced notification: {e}")
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
