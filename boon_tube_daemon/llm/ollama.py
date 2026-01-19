# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Ollama local LLM integration for Boon-Tube-Daemon.

Provides privacy-first, cost-free AI message generation using local LLM server.
"""

import logging
from typing import Optional

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

from boon_tube_daemon.utils.config import get_config, get_bool_config

logger = logging.getLogger(__name__)


class OllamaLLM:
    """
    Ollama local LLM integration.
    
    Features:
    - Local LLM server (no cloud API costs)
    - Privacy-first (data never leaves your network)
    - No rate limits
    - Support for various models (gemma2, llama3, mistral, etc.)
    """
    
    def __init__(self):
        self.name = "Ollama"
        self.enabled = False
        self.model = None
        self.ollama_client = None
        self.ollama_host = None
        
    def authenticate(self) -> bool:
        """
        Initialize Ollama connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Check if LLM is enabled
            if not get_bool_config('LLM', 'enable', default=False):
                logger.info("⊘ Ollama LLM disabled in config")
                return False
            
            # Check if Ollama provider is selected
            provider = get_config('LLM', 'provider', default='gemini').lower()
            if provider != 'ollama':
                logger.info(f"⊘ Ollama not selected (current provider: {provider})")
                return False
            
            if not OLLAMA_AVAILABLE:
                logger.error("✗ Ollama Python client not installed. Run: pip install ollama")
                return False
            
            # Get Ollama configuration
            ollama_host = get_config('LLM', 'ollama_host', default='http://localhost')
            ollama_port = get_config('LLM', 'ollama_port', default='11434')
            model_name = get_config('LLM', 'model', default='gemma2:2b')
            
            # Build full host URL if port is specified separately
            if not ollama_host.startswith('http'):
                ollama_host = f"http://{ollama_host}"
            
            # Add port if not already in host URL
            if ':' not in ollama_host.split('//')[-1]:
                self.ollama_host = f"{ollama_host}:{ollama_port}"
            else:
                self.ollama_host = ollama_host
            
            self.model = model_name
            
            # Test connection by listing models
            try:
                self.ollama_client = ollama.Client(host=self.ollama_host)
                models_response = self.ollama_client.list()
                logger.debug(f"Connected to Ollama at {self.ollama_host}")
                
                # Check if requested model exists
                # Handle different response formats from ollama library
                available_models = []
                if hasattr(models_response, 'models'):
                    available_models = [m.get('name') or m.get('model') for m in models_response.models if m.get('name') or m.get('model')]
                elif isinstance(models_response, dict) and 'models' in models_response:
                    available_models = [m.get('name') or m.get('model') for m in models_response['models'] if m.get('name') or m.get('model')]
                
                if available_models and model_name not in available_models:
                    logger.warning(
                        f"⚠ Model '{model_name}' not found on Ollama server. "
                        f"Available models: {', '.join(available_models)}. "
                        f"To pull the model, run: ollama pull {model_name}"
                    )
                    # Don't fail - Ollama will auto-pull on first use
                
            except Exception as e:
                logger.error(f"✗ Failed to connect to Ollama at {self.ollama_host}")
                logger.debug(f"Connection error details: {e}")  # Debug level for sensitive details
                return False
            
            self.enabled = True
            logger.info(f"✓ Ollama LLM initialized (host: {self.ollama_host}, model: {model_name})")
            return True
            
        except Exception as e:
            logger.error("✗ Failed to initialize Ollama")
            logger.debug(f"Initialization error details: {e}")  # Debug level for sensitive details
            self.enabled = False
            return False
    
    def _generate_with_retry(self, prompt: str, max_retries: int = 3, initial_delay: float = 2.0) -> Optional[str]:
        """
        Generate content with Ollama.
        
        Args:
            prompt: The prompt to send to Ollama
            max_retries: Maximum number of retry attempts (default: 3)
            initial_delay: Initial delay in seconds between retries (default: 2.0)
            
        Returns:
            Generated text or None on failure
        """
        if not self.enabled or not self.ollama_client:
            return None
        
        import time
        
        last_error = None
        delay = initial_delay
        
        for attempt in range(max_retries):
            try:
                # Make API call to Ollama
                response = self.ollama_client.generate(
                    model=self.model,
                    prompt=prompt
                )
                
                # Extract response text
                if isinstance(response, dict) and 'response' in response:
                    result = response['response'].strip()
                elif hasattr(response, 'response'):
                    result = response.response.strip()
                else:
                    result = str(response).strip()
                
                return result
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Don't retry on permanent errors
                if any(perm in error_str for perm in ['not found', 'invalid', 'unauthorized']):
                    logger.error(f"Ollama API permanent error: {e}")
                    return None
                
                # Retry on transient errors
                if attempt < max_retries - 1:
                    logger.warning(f"Ollama API error (attempt {attempt + 1}/{max_retries})")
                    logger.debug(f"Error details: {e}")  # Debug level for sensitive details
                    logger.debug(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Ollama API failed after {max_retries} attempts")
                    logger.debug(f"Final error details: {last_error}")  # Debug level for sensitive details
        
        return None
    
    def generate_notification(self, video_data: dict, platform_name: str, social_platform: str) -> Optional[str]:
        """
        Generate a platform-specific notification message.
        
        Args:
            video_data: Video information dict (title, description, url, etc.)
            platform_name: Source platform name (YouTube, TikTok, etc.)
            social_platform: Target social platform (discord, matrix, bluesky, mastodon)
            
        Returns:
            Generated notification text or None on error
        """
        if not self.enabled:
            return None
        
        try:
            title = video_data.get('title', '')
            description = video_data.get('description', '')
            url = video_data.get('url', '')
            
            # Platform-specific character limits
            social_platform_lower = social_platform.lower()
            
            if social_platform_lower == 'bluesky':
                max_chars = 250  # Conservative for Bluesky's 300 grapheme limit
                use_hashtags = True
            elif social_platform_lower == 'mastodon':
                max_chars = 400  # Leave room for URL and hashtags
                use_hashtags = True
            elif social_platform_lower == 'discord':
                max_chars = 300
                use_hashtags = False
            elif social_platform_lower == 'matrix':
                max_chars = 350
                use_hashtags = False
            else:
                max_chars = 300
                use_hashtags = False
            
            # Build platform-specific prompt
            hashtag_instruction = ""
            if use_hashtags:
                hashtag_instruction = "\n- Include 2-3 SHORT relevant hashtags at the end"
            
            prompt = f"""Create a SHORT notification post for a new {platform_name} video.

Title: {title}
Description (summary): {description[:200] if description else 'No description available'}

RULES:
- ABSOLUTE MAXIMUM: {max_chars} characters total
- Output ONLY the post text (no quotes, no labels, no "Here's...")
- DO NOT include the URL (it will be added automatically)
- Be conversational and engaging
- Focus on the video title/topic
- NO greetings like "Hey everyone!" - get straight to the content
- NO placeholder URLs or "[VIDEO_ID]" text{hashtag_instruction}

Write ONLY the post text (under {max_chars} chars, no URL):"""

            notification = self._generate_with_retry(prompt)
            
            if not notification:
                return None
            
            # Clean up common meta-text patterns
            import re
            meta_patterns = [
                r'^(?:Here\'?s|Okay,? here\'?s|Alright,? here\'?s)\s+.*?:?\s*',
                r'^(?:Here you go|Sure thing|Certainly).*?:?\s*',
                r'^Draft.*?:?\s*',
            ]
            
            for pattern in meta_patterns:
                notification = re.sub(pattern, '', notification, flags=re.IGNORECASE | re.MULTILINE)
            notification = notification.strip()
            
            # Remove any URLs the LLM might have included
            notification = re.sub(r'https?://[^\s]+', '', notification).strip()
            
            # Enforce character limit
            if len(notification) > max_chars:
                logger.warning(f"Notification too long ({len(notification)} chars), truncating to {max_chars}")
                # Truncate at word boundary
                truncated = notification[:max_chars]
                last_space = truncated.rfind(' ')
                if last_space > max_chars - 50:
                    truncated = truncated[:last_space]
                notification = truncated.strip()
            
            # Add URL
            if url:
                notification += f"\n\n{url}"
            
            logger.info(f"✨ Generated {social_platform} post with Ollama: {notification[:60]}...")
            return notification
            
        except Exception as e:
            logger.error(f"Error generating Ollama notification for {social_platform}")
            logger.debug(f"Error details: {e}")  # Debug level for sensitive details
            return None
