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

Features:
- Local LLM server (no cloud API costs - your electricity bill is another story)
- Privacy-first (data never leaves your network)
- Sophisticated prompts optimized for small LLMs (4B-12B params)
- Quality guardrails (deduplication, emoji limits, profanity filter)
- Platform-specific validation
- Qwen3 thinking mode support
"""

import logging
import re
import time
from typing import Optional, List, Set, Tuple

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
    - Quality guardrails (deduplication, emoji limits, profanity filter, validation)
    
    Why use local AI? Because sending your video titles to Google is like
    shouting your diary entries in a crowded mall. Sure, it works, but at what cost?
    """
    
    def __init__(self):
        self.name = "Ollama"
        self.enabled = False
        self.model = None
        self.ollama_client = None
        self.ollama_host = None
        
        # Qwen3 thinking mode support
        self.thinking_mode_enabled = False
        self.thinking_token_multiplier = 4.0
        
        # Generation parameters (because even AI needs tuning knobs)
        self.temperature = 0.3
        self.top_p = 0.9
        self.max_tokens = 150
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay_base = 2
        
        # Guardrails configuration
        # Because we need rules to govern the rule-following machine. Meta as fuck.
        self.enable_deduplication = True
        self.dedup_cache_size = 20
        self.enable_quality_scoring = False
        self.min_quality_score = 6
        self.max_emoji_count = 1
        self.enable_profanity_filter = False
        self.profanity_severity = 'moderate'
        self.enable_platform_validation = True
        
        # Deduplication cache: stores recent messages to prevent repeats
        # Because variety is the spice of life, even for robot-generated content
        self._message_cache: List[str] = []
        
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
            
            # Generation parameters
            self.temperature = float(get_config('LLM', 'temperature', default='0.3'))
            self.top_p = float(get_config('LLM', 'top_p', default='0.9'))
            self.max_tokens = int(get_config('LLM', 'max_tokens', default='150'))
            
            # Retry configuration
            self.max_retries = int(get_config('LLM', 'max_retries', default='3'))
            self.retry_delay_base = int(get_config('LLM', 'retry_delay_base', default='2'))
            
            # Guardrails configuration
            self.enable_deduplication = get_bool_config('LLM', 'enable_deduplication', default=True)
            self.dedup_cache_size = int(get_config('LLM', 'dedup_cache_size', default='20'))
            self.enable_quality_scoring = get_bool_config('LLM', 'enable_quality_scoring', default=False)
            self.min_quality_score = int(get_config('LLM', 'min_quality_score', default='6'))
            self.max_emoji_count = int(get_config('LLM', 'max_emoji_count', default='1'))
            self.enable_profanity_filter = get_bool_config('LLM', 'enable_profanity_filter', default=False)
            self.profanity_severity = get_config('LLM', 'profanity_severity', default='moderate')
            self.enable_platform_validation = get_bool_config('LLM', 'enable_platform_validation', default=True)
            
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
    
    # =========================================================================
    # GUARDRAILS & VALIDATION METHODS
    # =========================================================================
    # "We built machines that can think, now we need machines to watch the thinking machines.
    #  It's supervision turtles all the way down." - George Carlin (probably)
    
    @staticmethod
    def _extract_hashtags(message: str) -> List[str]:
        """
        Extract all hashtags from a message.
        
        Because we need to teach a computer to recognize words that start with #.
        In the history of human civilization, this is where we ended up.
        
        Args:
            message: The generated message
            
        Returns:
            List of hashtags (without # prefix, lowercase)
        """
        # Match hashtags: # followed by a letter, then any alphanumeric characters
        hashtags = re.findall(r'#([a-zA-Z]\w*)', message)
        return [tag.lower() for tag in hashtags]
    
    @staticmethod
    def _contains_forbidden_words(message: str) -> Tuple[bool, List[str]]:
        """
        Check if message contains clickbait/forbidden words.
        
        We built a machine that can process language at superhuman levels, and we use it
        to generate social media posts. Then we have to check if the machine used the words
        "INSANE" or "EPIC" because apparently we can't trust it to follow basic instructions.
        
        It's like hiring a PhD to write greeting cards, then having to make sure they didn't
        write anything too smart. Welcome to the goddamn future.
        
        Args:
            message: The generated message
            
        Returns:
            tuple: (has_forbidden_words, list_of_found_words)
        """
        # Forbidden words we explicitly tell the AI not to use
        forbidden_words = [
            'insane', 'epic', 'crazy', 'smash', 'unmissable', 
            'incredible', 'amazing', 'lit', 'fire', 'legendary',
            'mind-blowing', 'jaw-dropping', 'unbelievable'
        ]
        
        message_lower = message.lower()
        found_words = []
        
        for word in forbidden_words:
            # Use word boundaries to avoid false positives
            if re.search(rf'\b{word}\b', message_lower):
                found_words.append(word)
        
        return (len(found_words) > 0, found_words)
    
    @staticmethod
    def _count_emojis(message: str) -> int:
        """
        Count emoji characters in a message.
        
        Because apparently some people think more emojis = more engagement.
        Spoiler alert: It doesn't. You just look like you're 12.
        
        Args:
            message: The message to check
            
        Returns:
            Number of emoji characters
        """
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # enclosed characters
            "]", flags=re.UNICODE
        )
        return len(emoji_pattern.findall(message))
    
    @staticmethod
    def _contains_profanity(message: str, severity: str = 'moderate') -> Tuple[bool, List[str]]:
        """
        Check if message contains profanity.
        
        Ironic, considering this entire codebase is written with Carlin-style commentary.
        But apparently we draw the line at the AI dropping F-bombs about your cat videos.
        
        Args:
            message: The message to check
            severity: 'mild', 'moderate', or 'severe'
            
        Returns:
            tuple: (has_profanity, list_of_found_words)
        """
        # Profanity lists by severity
        mild_words = ['damn', 'hell', 'crap', 'suck', 'sucks', 'piss', 'pissed']
        moderate_words = ['ass', 'bastard', 'bitch', 'dick', 'cock', 'pussy', 'slut', 'whore']
        severe_words = ['fuck', 'fucking', 'shit', 'shitty', 'motherfucker', 'asshole', 'cunt']
        
        if severity == 'severe':
            check_words = mild_words + moderate_words + severe_words
        elif severity == 'moderate':
            check_words = mild_words + moderate_words
        else:  # mild
            check_words = mild_words
        
        message_lower = message.lower()
        found_words = []
        
        for word in check_words:
            if re.search(rf'\b{word}\b', message_lower):
                found_words.append(word)
        
        return (len(found_words) > 0, found_words)
    
    def _is_duplicate_message(self, message: str) -> bool:
        """
        Check if message is too similar to recent messages.
        
        Because nobody wants to read the same notification 5 times.
        At least the AI has the decency to pretend it's trying to be different.
        
        Args:
            message: The generated message to check
            
        Returns:
            True if message is a duplicate or too similar
        """
        if not self.enable_deduplication:
            return False
        
        # Normalize message for comparison
        normalized = message.lower()
        normalized = re.sub(r'#\w+', '', normalized)  # Remove hashtags
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation/emoji
        normalized = re.sub(r'\s+', ' ', normalized).strip()  # Normalize whitespace
        
        for cached in self._message_cache:
            cached_normalized = cached.lower()
            cached_normalized = re.sub(r'#\w+', '', cached_normalized)
            cached_normalized = re.sub(r'[^\w\s]', '', cached_normalized)
            cached_normalized = re.sub(r'\s+', ' ', cached_normalized).strip()
            
            # Exact match
            if normalized == cached_normalized:
                return True
            
            # Calculate word overlap (>80% = duplicate)
            msg_words = set(normalized.split())
            cached_words = set(cached_normalized.split())
            if len(msg_words) > 0 and len(cached_words) > 0:
                overlap = len(msg_words & cached_words) / max(len(msg_words), len(cached_words))
                if overlap > 0.8:
                    return True
        
        return False
    
    def _add_to_message_cache(self, message: str):
        """
        Add message to deduplication cache.
        
        Uses a simple FIFO queue. Old messages get pushed out.
        It's not rocket science, just a fucking list.
        """
        if not self.enable_deduplication:
            return
        
        self._message_cache.append(message)
        
        # Keep cache size limited
        if len(self._message_cache) > self.dedup_cache_size:
            self._message_cache.pop(0)
    
    def _validate_platform_specific(self, message: str, platform: str) -> List[str]:
        """
        Platform-specific validation rules.
        
        Because each social media platform is a special snowflake
        with its own rules and quirks that we have to account for.
        
        Args:
            message: The generated message
            platform: Platform name (bluesky, mastodon, discord, matrix)
            
        Returns:
            list_of_issues (empty if valid)
        """
        if not self.enable_platform_validation:
            return []
        
        issues = []
        platform_lower = platform.lower()
        
        if platform_lower == 'discord':
            # Check for mass pings
            if '@everyone' in message or '@here' in message:
                issues.append("Contains @everyone or @here mention")
            
            # Check for unmatched markdown
            unmatched_markdown = (
                message.count('**') % 2 != 0 or
                message.count('__') % 2 != 0
            )
            if unmatched_markdown:
                issues.append("Unmatched markdown formatting")
        
        elif platform_lower == 'bluesky':
            # Check for URLs in content (we add URL separately)
            urls_in_content = re.findall(r'https?://\S+', message)
            if urls_in_content:
                issues.append("URL found in content (should be added separately)")
        
        elif platform_lower == 'mastodon':
            # Check for HTML entities
            if re.search(r'&[a-z]+;', message):
                issues.append("HTML entities detected (should be plain text)")
        
        return issues
    
    @staticmethod
    def _safe_trim(message: str, limit: int) -> str:
        """
        Safely trim message to character limit without cutting words mid-token.
        
        Args:
            message: The message to trim
            limit: Maximum character limit
        
        Returns:
            Trimmed message at word boundary
        """
        message = message.strip()
        if len(message) <= limit:
            return message
        
        # Try to trim at a word boundary
        trimmed = message[:limit].rsplit(' ', 1)[0].rstrip()
        
        # If we trimmed too aggressively, hard cut
        return trimmed if trimmed else message[:limit]
    
    def _generate_with_retry(self, prompt: str, max_retries: int = None, initial_delay: float = None, max_tokens: int = None) -> Optional[str]:
        """
        Generate content with Ollama, with retry logic and thinking mode support.
        
        Args:
            prompt: The prompt to send to Ollama
            max_retries: Maximum number of retry attempts (defaults to self.max_retries)
            initial_delay: Initial delay in seconds (defaults to self.retry_delay_base)
            max_tokens: Maximum tokens for response (defaults to self.max_tokens)
            
        Returns:
            Generated text or None on failure
            
        The retry logic here is like dating - if at first you don't succeed,
        wait a bit longer between attempts. Exponential backoff is just
        "playing hard to get" but for API calls.
        """
        if not self.enabled or not self.ollama_client:
            return None
        
        # Use instance defaults if not specified
        if max_retries is None:
            max_retries = self.max_retries
        if initial_delay is None:
            initial_delay = float(self.retry_delay_base)
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        last_error = None
        delay = initial_delay
        
        # Apply thinking mode token multiplier if enabled
        actual_max_tokens = max_tokens
        if self.thinking_mode_enabled:
            actual_max_tokens = int(max_tokens * self.thinking_token_multiplier)
            logger.debug(f"Thinking mode: {max_tokens} * {self.thinking_token_multiplier} = {actual_max_tokens} tokens")
        
        for attempt in range(max_retries):
            try:
                # Make API call to Ollama with configurable options
                response = self.ollama_client.generate(
                    model=self.model,
                    prompt=prompt,
                    options={
                        'num_predict': actual_max_tokens,
                        'temperature': self.temperature,
                        'top_p': self.top_p,
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
            
        This is where the magic happens. Or the illusion of magic, anyway.
        We take your video title and ask a robot to make it sound exciting.
        George Carlin would've had a field day with this.
        """
        if not self.enabled:
            return None
        
        try:
            title = video_data.get('title', '')
            description = video_data.get('description', '')
            url = video_data.get('url', '')
            channel_name = video_data.get('channel_name', platform_name)
            
            # Platform-specific character limits and hashtag settings
            social_platform_lower = social_platform.lower()
            
            if social_platform_lower == 'bluesky':
                max_chars = 250  # Conservative for Bluesky's 300 grapheme limit
                use_hashtags = True
                hashtag_count = 3
            elif social_platform_lower == 'mastodon':
                max_chars = 400  # Leave room for URL and hashtags
                use_hashtags = True
                hashtag_count = 3
            elif social_platform_lower == 'discord':
                max_chars = 300
                use_hashtags = False
                hashtag_count = 0
            elif social_platform_lower == 'matrix':
                max_chars = 350
                use_hashtags = False
                hashtag_count = 0
            else:
                max_chars = 300
                use_hashtags = False
                hashtag_count = 0
            
            # Build the optimized prompt
            prompt = self._build_notification_prompt(
                platform_name=platform_name,
                channel_name=channel_name,
                title=title,
                description=description,
                max_chars=max_chars,
                use_hashtags=use_hashtags,
                hashtag_count=hashtag_count,
                social_platform=social_platform
            )
            
            # Generate with retry logic
            notification = self._generate_with_retry(prompt)
            
            if not notification:
                logger.warning(f"Failed to generate notification for {social_platform}")
                return None
            
            # Apply guardrails and validation
            notification = self._apply_guardrails(
                notification,
                max_chars=max_chars,
                social_platform=social_platform,
                use_hashtags=use_hashtags
            )
            
            if not notification:
                logger.warning(f"Notification failed guardrails for {social_platform}")
                return None
            
            # Add to deduplication cache
            self._add_to_message_cache(notification)
            
            # Add URL
            if url:
                notification += f"\n\n{url}"
            
            logger.info(f"✨ Generated {social_platform} post with Ollama: {notification[:60]}...")
            return notification
            
        except Exception as e:
            logger.error(f"Error generating Ollama notification for {social_platform}: {e}")
            return None
    
    def _build_notification_prompt(
        self,
        platform_name: str,
        channel_name: str,
        title: str,
        description: str,
        max_chars: int,
        use_hashtags: bool,
        hashtag_count: int,
        social_platform: str
    ) -> str:
        """
        Build an optimized prompt for video notification generation.
        
        Designed for small LLMs (4B-12B params) with explicit constraints
        to prevent hallucinations and ensure quality output.
        
        George Carlin would've loved this: We spent thousands of years teaching humans
        to write, and now we're teaching machines to sound like humans who can barely write.
        "Don't say EPIC! Don't say INSANE!" - like training a puppy not to shit on the rug.
        """
        # Clean up description (first 200 chars, remove URLs)
        clean_description = description[:200] if description else ''
        clean_description = re.sub(r'https?://\S+', '', clean_description).strip()
        
        # Build hashtag instructions
        hashtag_instruction = ""
        if use_hashtags:
            hashtag_instruction = f"""

STEP 3 - HASHTAG RULES (CRITICAL):
You MUST include EXACTLY {hashtag_count} hashtags at the end.
- Extract hashtags from key words/topics in the title
- NEVER use generic tags like #Video, #YouTube, #New, #Content
- Format: space before each hashtag"""
        
        prompt = f"""You are a social media assistant that writes engaging video announcements with personality.

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
        
        return prompt
    
    def _apply_guardrails(
        self,
        notification: str,
        max_chars: int,
        social_platform: str,
        use_hashtags: bool
    ) -> Optional[str]:
        """
        Apply quality guardrails and validation to generated notification.
        
        This is the post-generation quality check. Because even robots need supervision.
        
        Yes, we have to fact-check the robot. The robot that we programmed. That we gave
        explicit instructions to. And it STILL fucks up about 10% of the time.
        
        It's like having a calculator that's right 90% of the time. Great job, humanity.
        
        Returns:
            Cleaned notification or None if it fails validation
        """
        if not notification:
            return None
        
        # Clean up common meta-text patterns
        meta_patterns = [
            r'^(?:Here\'?s|Okay,? here\'?s|Alright,? here\'?s)\s+.*?:?\s*',
            r'^(?:Here you go|Sure thing|Certainly).*?:?\s*',
            r'^(?:Post|Draft|Output).*?:?\s*',
            r'^"',  # Leading quote
            r'"$',  # Trailing quote
        ]
        
        for pattern in meta_patterns:
            notification = re.sub(pattern, '', notification, flags=re.IGNORECASE | re.MULTILINE)
        notification = notification.strip()
        
        # Remove any URLs the LLM might have included
        notification = re.sub(r'https?://[^\s]+', '', notification).strip()
        
        # Check for forbidden words
        has_forbidden, found_words = self._contains_forbidden_words(notification)
        if has_forbidden:
            logger.warning(f"⚠ Notification contains forbidden words: {', '.join(found_words)}")
            # Don't fail, just log - the message might still be usable
        
        # Check emoji count
        emoji_count = self._count_emojis(notification)
        if emoji_count > self.max_emoji_count:
            logger.warning(f"⚠ Too many emojis ({emoji_count}, max: {self.max_emoji_count})")
        
        # Check for profanity if filter is enabled
        if self.enable_profanity_filter:
            has_profanity, found_profanity = self._contains_profanity(notification, self.profanity_severity)
            if has_profanity:
                logger.warning(f"⚠ Notification contains profanity: {', '.join(found_profanity)}")
                return None  # Fail the notification
        
        # Check for duplicates
        if self._is_duplicate_message(notification):
            logger.warning("⚠ Notification is too similar to recent messages")
            # Don't fail, let it through but log
        
        # Platform-specific validation
        platform_issues = self._validate_platform_specific(notification, social_platform)
        if platform_issues:
            logger.warning(f"⚠ Platform validation issues: {', '.join(platform_issues)}")
        
        # Enforce character limit
        if len(notification) > max_chars:
            logger.warning(f"Notification too long ({len(notification)} chars), trimming to {max_chars}")
            notification = self._safe_trim(notification, max_chars)
        
        return notification
