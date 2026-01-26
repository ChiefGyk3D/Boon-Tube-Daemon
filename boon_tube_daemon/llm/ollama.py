# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Ollama local LLM integration for Boon-Tube-Daemon.

Provides privacy-first, cost-free AI message generation using local LLM server.

George Carlin would've loved this: We built computers to do our thinking for us,
and now we're using them to write notifications about cat videos. What a time to be alive.
The AI doesn't judge your content - it just generates the post and moves on with its life.
Unlike your relatives who still don't understand what you do for a living.
"""

import logging
import re
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
    - Local LLM server (no cloud API costs - your electricity bill is another story)
    - Privacy-first (data never leaves your network, unlike your personal info on social media)
    - No rate limits (go wild, you beautiful content creator)
    - Support for various models (gemma3, qwen2.5, llama3, mistral, etc.)
    - Qwen3 thinking mode support (for when your AI needs to philosophize before tweeting)
    
    Why use local AI? Because sending your video titles to Google is like
    shouting your diary entries in a crowded mall. Sure, it works, but at what cost?
    """
    
    def __init__(self):
        self.name = "Ollama"
        self.enabled = False
        self.model = None
        self.ollama_client = None
        self.ollama_host = None
        self.thinking_mode_enabled = False
        self.thinking_token_multiplier = 4.0
        
    def authenticate(self) -> bool:
        """
        Initialize Ollama connection.
        
        Returns:
            True if connection successful, False otherwise
            
        George Carlin note: "Authentication" sounds so official, like we're
        entering Fort Knox. Really we're just checking if the robot is awake.
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
            model_name = get_config('LLM', 'model', default='gemma3:4b')  # Updated default
            
            # Qwen3 thinking mode support
            self.thinking_mode_enabled = get_bool_config('LLM', 'enable_thinking_mode', default=False)
            self.thinking_token_multiplier = float(get_config('LLM', 'thinking_token_multiplier', default='4.0'))
            
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
                
                # Log thinking mode status
                if self.thinking_mode_enabled:
                    logger.info(f"🧠 Qwen3 thinking mode enabled (token multiplier: {self.thinking_token_multiplier}x)")
                
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
    
    def _extract_from_thinking(self, thinking_content: str, max_chars: int) -> Optional[str]:
        """
        Extract the actual notification from Qwen3's thinking mode output.
        
        Qwen3 models have this delightful habit of showing their work like a
        nervous student at a math exam. The actual answer is buried somewhere
        in their stream of consciousness. This method digs it out.
        
        Args:
            thinking_content: The raw thinking field content
            max_chars: Maximum expected length for the final post
            
        Returns:
            Extracted notification text or None if extraction fails
        """
        if not thinking_content:
            return None
        
        lines = thinking_content.strip().split('\n')
        
        # Strategy 1: Look for quoted text (lines starting with >)
        quoted_lines = [line.lstrip('> ').strip() for line in lines if line.strip().startswith('>')]
        if quoted_lines:
            result = '\n'.join(quoted_lines)
            if 30 <= len(result) <= max_chars + 50:
                return result
        
        # Strategy 2: Look for explicit markers
        markers = [
            r'(?:final\s+)?(?:post|notification|message|announcement):\s*["\']?(.+?)["\']?\s*$',
            r'here\'?s?\s+(?:the|my)\s+(?:post|notification):\s*["\']?(.+?)["\']?\s*$',
            r'(?:output|result):\s*["\']?(.+?)["\']?\s*$',
        ]
        
        full_text = thinking_content.lower()
        for marker in markers:
            match = re.search(marker, full_text, re.IGNORECASE | re.MULTILINE)
            if match:
                result = match.group(1).strip().strip('"\'')
                if 30 <= len(result) <= max_chars + 50:
                    return result
        
        # Strategy 3: Look for lines with hashtags (likely the actual post)
        for line in reversed(lines):
            line = line.strip()
            if '#' in line and 30 <= len(line) <= max_chars + 50:
                # Clean up any leading markers
                cleaned = re.sub(r'^(?:post|notification|message):\s*', '', line, flags=re.IGNORECASE)
                return cleaned
        
        # Strategy 4: Take the last substantial paragraph
        paragraphs = [p.strip() for p in thinking_content.split('\n\n') if p.strip()]
        if paragraphs:
            last_para = paragraphs[-1]
            if 30 <= len(last_para) <= max_chars + 50:
                return last_para
        
        logger.warning("Could not extract notification from thinking mode output")
        return None
    
    def _generate_with_retry(self, prompt: str, max_retries: int = 3, initial_delay: float = 2.0, max_tokens: int = 150) -> Optional[str]:
        """
        Generate content with Ollama, with retry logic and thinking mode support.
        
        Args:
            prompt: The prompt to send to Ollama
            max_retries: Maximum number of retry attempts (default: 3)
            initial_delay: Initial delay in seconds between retries (default: 2.0)
            max_tokens: Maximum tokens for response (default: 150)
            
        Returns:
            Generated text or None on failure
            
        The retry logic here is like dating - if at first you don't succeed,
        wait a bit longer between attempts. Exponential backoff is just
        "playing hard to get" but for API calls.
        """
        if not self.enabled or not self.ollama_client:
            return None
        
        import time
        
        last_error = None
        delay = initial_delay
        
        # Apply thinking mode token multiplier if enabled
        actual_max_tokens = max_tokens
        if self.thinking_mode_enabled:
            actual_max_tokens = int(max_tokens * self.thinking_token_multiplier)
            logger.debug(f"Thinking mode: {max_tokens} * {self.thinking_token_multiplier} = {actual_max_tokens} tokens")
        
        for attempt in range(max_retries):
            try:
                # Make API call to Ollama with options
                response = self.ollama_client.generate(
                    model=self.model,
                    prompt=prompt,
                    options={
                        'num_predict': actual_max_tokens,
                        'temperature': 0.3,
                        'top_p': 0.9,
                    }
                )
                
                # Extract response text - handle thinking mode
                result = None
                thinking_content = None
                
                if isinstance(response, dict):
                    result = response.get('response', '').strip()
                    # Check for thinking field (Qwen3)
                    if 'message' in response and isinstance(response['message'], dict):
                        thinking_content = response['message'].get('thinking', '')
                        if not result:
                            result = response['message'].get('content', '').strip()
                elif hasattr(response, 'response'):
                    result = response.response.strip()
                    if hasattr(response, 'message') and hasattr(response.message, 'thinking'):
                        thinking_content = response.message.thinking
                else:
                    result = str(response).strip()
                
                # If content is empty but thinking has content, extract from thinking
                if (not result or len(result) < 20) and thinking_content and self.thinking_mode_enabled:
                    logger.info("Content empty, extracting from thinking field...")
                    extracted = self._extract_from_thinking(thinking_content, max_tokens * 3)
                    if extracted:
                        result = extracted
                        logger.info(f"Extracted {len(result)} chars from thinking mode")
                
                if result:
                    return result
                else:
                    logger.warning("Empty response from Ollama")
                    return None
                
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Don't retry on permanent errors
                if any(perm in error_str for perm in ['not found', 'invalid', 'unauthorized']):
                    logger.error("Ollama API permanent error")
                    return None
                
                # Retry on transient errors
                if attempt < max_retries - 1:
                    logger.warning(f"Ollama API error (attempt {attempt + 1}/{max_retries})")
                    logger.debug(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Ollama API failed after {max_retries} attempts")
        
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
            return None
