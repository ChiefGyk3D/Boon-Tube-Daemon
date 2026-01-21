# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Ollama local LLM integration for Boon-Tube-Daemon.

Provides privacy-first, cost-free AI message generation using local LLM server.
"""

import logging
import time
import threading
from typing import Optional

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

from boon_tube_daemon.utils.config import get_config, get_bool_config
from boon_tube_daemon.llm.validator import LLMValidator
from boon_tube_daemon.llm.prompts import build_video_notification_prompt

logger = logging.getLogger(__name__)

# Global rate limiting: Shared with Gemini to prevent concurrent overload
# Because local LLMs can also choke if you hit them with 10 requests at once
# Spoiler: They choke HARDER than cloud APIs. Way harder.
_api_semaphore = threading.Semaphore(4)
_last_api_call_time = 0
_api_call_lock = threading.Lock()
_min_delay_between_calls = 0.5  # Local is faster, but still needs breathing room


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
        
        # Retry configuration
        # Local LLMs fail less often, but when they do, boy do they fail HARD
        self.max_retries = int(get_config('LLM', 'max_retries', default='3'))
        self.retry_delay_base = int(get_config('LLM', 'retry_delay_base', default='2'))
        
        # Generation parameters for better control
        # Same babysitting parameters as Gemini
        # Local models need just as much hand-holding, they're just cheaper about it
        self.temperature = float(get_config('LLM', 'temperature', default='0.3'))
        self.top_p = float(get_config('LLM', 'top_p', default='0.9'))
        self.max_tokens = int(get_config('LLM', 'max_tokens', default='150'))
        
        # Character limits
        self.bluesky_max_chars = 300
        self.mastodon_max_chars = 500
        
        # Initialize guardrails validator
        # Local LLMs get the same babysitting treatment. Equal opportunity supervision.
        self.validator = LLMValidator()
        
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
                return False
            
            self.enabled = True
            logger.info(f"✓ Ollama LLM initialized (host: {self.ollama_host}, model: {model_name})")
            return True
            
        except Exception as e:
            logger.error("✗ Failed to initialize Ollama")
            self.enabled = False
            return False
    
    def _generate_with_retry(self, prompt: str, max_retries: int = None) -> Optional[str]:
        """
        Generate content with Ollama and GLOBAL rate limiting.
        
        Even local LLMs need rate limiting. Hit them with 10 concurrent requests
        and watch your GPU cry. Or your CPU. Probably both. Definitely both.
        
        It's like trying to make your grandma use 10 apps at once. She can technically
        do it, but she's gonna be pissed and everything will be slow as fuck.
        
        Args:
            prompt: The prompt to send to Ollama
            max_retries: Maximum retry attempts (defaults to self.max_retries)
        
        Returns:
            Generated text or None on failure
        """
        global _last_api_call_time
        
        if not self.enabled or not self.ollama_client:
            return None
        
        if max_retries is None:
            max_retries = self.max_retries
        
        last_error = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                # Rate limiting: Share the semaphore with Gemini
                # Because we don't want BOTH APIs getting hammered simultaneously
                with _api_semaphore:
                    # Enforce minimum delay (shorter for local)
                    with _api_call_lock:
                        time_since_last_call = time.time() - _last_api_call_time
                        if time_since_last_call < _min_delay_between_calls:
                            sleep_time = _min_delay_between_calls - time_since_last_call
                            logger.debug(f"⏱ Rate limiting: waiting {sleep_time:.2f}s before Ollama call...")
                            time.sleep(sleep_time)
                        _last_api_call_time = time.time()
                    
                    # Make API call to Ollama with generation options
                    # Teaching local LLMs to behave, one parameter at a time
                    response = self.ollama_client.generate(
                        model=self.model,
                        prompt=prompt,
                        options={
                            'temperature': self.temperature,
                            'top_p': self.top_p,
                            'num_predict': self.max_tokens,
                        }
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
                
                # Check if it's a retryable error
                is_retryable = (
                    'timeout' in error_str or
                    'connection' in error_str or
                    'overloaded' in error_str or
                    'busy' in error_str
                )
                
                if not is_retryable or attempt >= max_retries:
                    # Non-retryable or final attempt
                    logger.error(f"✗ Ollama API failed: {e}")
                    return None
                
                # Exponential backoff
                delay = self.retry_delay_base ** attempt
                logger.warning(
                    f"⚠ Ollama error (attempt {attempt + 1}/{max_retries + 1}): {error_str}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
        
        logger.error(f"✗ Ollama failed after {max_retries + 1} attempts: {last_error}")
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
            
            if social_platform_lower == 'bluesky':
                max_chars = 250  # Conservative for Bluesky's 300 grapheme limit
                use_hashtags = True
            elif social_platform_lower == 'mastodon':
                max_chars = 450  # 500 total - 43 URL - buffer
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
            
            # Trim description for prompt
            trimmed_desc = LLMValidator.safe_trim(description, 300) if description else 'No description available'
            
            # Build sophisticated prompt using template system
            # Local LLMs get the same instruction manual as cloud ones
            prompt = build_video_notification_prompt(
                platform_name=platform_name,
                creator_name=platform_name,
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
                return None
            
            # GUARDRAILS: Quality validation and retry logic
            # Teaching local LLMs to count is just as hard as teaching cloud LLMs
            # At least these ones are free. You get what you pay for, I guess.
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
                    # The AI figured it out! Miracles do happen.
                    if retry > 0:
                        logger.info(f"✅ Retry #{retry} produced valid message after quality checks")
                    else:
                        logger.debug(f"✓ Message passed all guardrail checks on first try")
                    break
                else:
                    # Local LLM needs remedial counting lessons
                    logger.warning(f"⚠ Generated message has quality issues (attempt {retry + 1}/{max_validation_retries}): {', '.join(issues)}")
                    
                    if retry < max_validation_retries - 1:
                        # Try again with strict_mode enabled
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
                        # All retries exhausted
                        logger.warning(f"⚠ Validation retries exhausted, using message with issues")
            
            # Remove username-derived hashtags (post-generation cleanup)
            notification = self.validator.validate_hashtags_against_username(notification, platform_name)
            
            # Add to deduplication cache
            self.validator.add_to_message_cache(notification)
            
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
            return None
