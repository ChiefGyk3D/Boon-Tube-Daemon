# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
LLM Guardrails & Quality Validation for Boon-Tube-Daemon.

Because even AI needs adult supervision.

Or: "How I Learned to Stop Trusting the Robot and Love the Validation"

Let's be crystal fucking clear about something:
This is NOT about teaching the AI to swear or sound like George Carlin.
Your video notifications will be normal, professional posts like:
- "New video: How to Build a PC! Check it out 🖥️ #PC #Hardware #Tutorial"
- "Just uploaded: Minecraft Survival Tips #Minecraft #Gaming"

The profanity and Carlin-esque humor is in the CODE COMMENTS and DOCUMENTATION.
Because if you're going to write software, you might as well be honest about what 
you're doing: Teaching robots to fake enthusiasm about YouTube videos.

This module implements post-generation quality validation that catches when small LLMs 
fuck up and:
- Use the wrong number of hashtags (can't count to three)
- Include forbidden clickbait words we explicitly told them not to use
- Accidentally include URLs in the content
- Hallucinate details that weren't in the video title
- Spam too many emojis
- Repeat the same message over and over
- Generate profanity (ironic, I know)
- Violate platform-specific formatting rules

George Carlin would have a field day: "We built robots that can write, but we still 
need to teach them how to count to three. THREE! Not quantum physics. Not the meaning 
of life. THREE HASHTAGS. And you know what the best part is? The tests are MORE 
RELIABLE than the AI. Welcome to the future."
"""

import re
import logging
from typing import List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class LLMValidator:
    """
    Validation system for LLM-generated content.
    
    Implements comprehensive guardrails to catch AI fuckups before they hit social media.
    
    Features:
    - Hashtag count validation (yes, we teach computers to count)
    - Forbidden word detection (clickbait filter)
    - URL contamination check (URLs go at the end, not in content)
    - Hallucination detection (when AI invents shit)
    - Message deduplication (variety is the spice of life)
    - Emoji limits (prevents emoji spam)
    - Profanity filter (ironic AF given this codebase)
    - Quality scoring (grading AI's homework)
    - Platform-specific validation (each platform's special rules)
    
    Because apparently we need rules to govern the rule-following machine. Meta as fuck.
    """
    
    def __init__(self):
        """Initialize validator with configurable guardrails."""
        # Deduplication cache: stores recent messages to prevent repeats
        # Because variety is the spice of life, even for robot-generated bullshit
        self._message_cache: List[str] = []
        self.dedup_cache_size = 20
        
        # Guardrail toggles (all enabled by default)
        self.enable_deduplication = True
        self.enable_quality_scoring = False  # Disabled by default (can be slow)
        self.max_emoji_count = 2
        self.enable_profanity_filter = False  # Disabled by default
        self.profanity_severity = 'moderate'  # mild, moderate, severe
        self.enable_platform_validation = True
        self.min_quality_score = 6
    
    @staticmethod
    def tokenize_username(username: str) -> Set[str]:
        """
        Tokenize username into parts that should not appear in hashtags.
        
        Handles various username formats:
        - CamelCase: CoolCreator99 -> ['cool', 'creator', '99', 'coolcreator99']
        - Underscores: Cool_Creator_99 -> ['cool', 'creator', 'cool_creator_99']
        - Numbers: Creator123 -> ['creator', '123', 'creator123']
        - Prefixes: @username, #username -> removes prefix
        
        Args:
            username: The creator's username
            
        Returns:
            Set of lowercase username parts (min 3 chars to avoid false positives)
        """
        if not username:
            return set()
        
        # Remove common prefixes (@, #)
        clean_username = username.lstrip('@#').strip()
        
        # Add the full username (lowercased) to the set
        parts = {clean_username.lower()}
        
        # Split on underscores, hyphens, dots
        for separator in ['_', '-', '.']:
            if separator in clean_username:
                parts.update(p.lower() for p in clean_username.split(separator) if len(p) >= 3)
        
        # Split CamelCase: CoolCreator99 -> Cool, Creator, 99
        # Use regex to find transitions: lowercase->uppercase, letter->number, number->letter
        camel_parts = re.findall(r'[A-Z]*[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+', clean_username)
        parts.update(p.lower() for p in camel_parts if len(p) >= 3)
        
        # Also add consecutive parts for partial matches (up to 3 consecutive)
        for i in range(len(camel_parts)):
            for j in range(i + 1, min(i + 4, len(camel_parts) + 1)):
                combined = ''.join(camel_parts[i:j]).lower()
                if len(combined) >= 3:
                    parts.add(combined)
        
        return parts
    
    @staticmethod
    def extract_hashtags(message: str) -> List[str]:
        """
        Extract all hashtags from a message.
        
        Because we need to teach a computer to recognize words that start with #.
        In the history of human civilization, this is where we ended up.
        Peak fucking humanity right here.
        
        Args:
            message: The generated message
            
        Returns:
            List of hashtags (without # prefix, lowercase)
        """
        # Match hashtags: # followed by a letter, then any alphanumeric characters
        # This excludes things like #50 (just numbers) which aren't valid hashtags
        hashtags = re.findall(r'#([a-zA-Z]\w*)', message)
        return [tag.lower() for tag in hashtags]
    
    @staticmethod
    def contains_forbidden_words(message: str) -> Tuple[bool, List[str]]:
        """
        Check if message contains clickbait/forbidden words.
        
        This catches when the LLM ignores our prompt instructions and uses words like
        "INSANE" or "EPIC" that we explicitly told it not to use.
        
        We built a machine that can process language at superhuman levels, and we use it
        to generate social media posts. Then we have to check if the machine used the words
        "INSANE" or "EPIC" because apparently we can't trust it to follow basic fucking 
        instructions.
        
        It's like hiring a PhD to write greeting cards, then having to make sure they didn't
        write anything too smart. Welcome to the goddamn future.
        
        Args:
            message: The generated message
            
        Returns:
            tuple: (has_forbidden_words, list_of_found_words)
        """
        # Forbidden words we explicitly tell the AI not to use
        # These are clickbait/cringe words that make you sound like a YouTuber circa 2016
        forbidden_words = [
            'insane', 'epic', 'crazy', 'smash', 'unmissable',
            'incredible', 'amazing', 'lit', 'fire', 'legendary',
            'mind-blowing', 'jaw-dropping', 'unbelievable', 'viral'
        ]
        
        message_lower = message.lower()
        found_words = [word for word in forbidden_words if word in message_lower]
        
        return (len(found_words) > 0, found_words)
    
    @staticmethod
    def validate_message_quality(
        message: str,
        expected_hashtag_count: int,
        title: str,
        username: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate that generated message follows our rules.
        
        This is a post-generation quality check to catch when the LLM:
        - Uses wrong number of hashtags (can't count)
        - Includes forbidden clickbait words (ignores instructions)
        - Accidentally includes the URL in content (formatting fail)
        - Hallucinates details not in the title (makes shit up)
        
        Yes, we have to fact-check the robot. The robot that we programmed. That we gave
        explicit instructions to. And it STILL fucks up about 10% of the time.
        
        It's like having a calculator that's right 90% of the time. Great job, humanity.
        We've achieved artificial intelligence that needs a fucking babysitter.
        
        George Carlin would lose his shit: "We can't trust people, so we built machines.
        Now we can't trust the machines either. What's next, we build machines to watch
        the machines? It's mistrust all the way down!"
        
        Args:
            message: The generated message (without URL)
            expected_hashtag_count: Expected number of hashtags (3 for new video, 2 for shorts)
            title: Original video title
            username: Creator username
            
        Returns:
            tuple: (is_valid, list_of_issues)
        """
        issues = []
        
        # Check hashtag count
        # Yes, we're teaching a computer to count. To THREE.
        hashtags = LLMValidator.extract_hashtags(message)
        if len(hashtags) != expected_hashtag_count:
            issues.append(f"Wrong hashtag count: {len(hashtags)} (expected {expected_hashtag_count})")
        
        # Check for forbidden words
        has_forbidden, found_words = LLMValidator.contains_forbidden_words(message)
        if has_forbidden:
            issues.append(f"Contains forbidden words: {', '.join(found_words)}")
        
        # Check if message accidentally includes a URL (should be added separately)
        if re.search(r'https?://', message):
            issues.append("Message contains URL (should be added separately)")
        
        # Check for common hallucinations
        # Small LLMs sometimes "remember" patterns from training data and insert them
        # even when not relevant. Like your drunk uncle at Thanksgiving making shit up.
        hallucination_patterns = [
            r'drops?\s+enabled',
            r'giveaway',
            r'tonight\s+at\s+\d',
            r'starting\s+at\s+\d',
            r'\d+\s*pm',
            r'\d+\s*am',
            r'vod\s+coming',
            r'vod\s+soon',
            r'next\s+video',
            r'\d+\s+views?',
            r'sponsored\s+',
            r'special\s+guest',
            r'premiere'
        ]
        
        for pattern in hallucination_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                issues.append(f"Possible hallucination detected: '{pattern}'")
                break  # Only report first hallucination
        
        return (len(issues) == 0, issues)
    
    def is_duplicate_message(self, message: str) -> bool:
        """
        Check if message is too similar to recent messages.
        
        Because nobody wants to read the same fucking announcement 5 times.
        Although to be fair, humans already do this manually. "New video! Check it out!"
        "New video! Check it out!" "New video! Check it out!" - Real creative there, chief.
        
        At least the AI has the decency to pretend it's trying to be different.
        
        Args:
            message: The generated message to check
            
        Returns:
            True if message is a duplicate or too similar
        """
        if not self.enable_deduplication:
            return False
        
        # Normalize message for comparison (lowercase, no emojis, no hashtags)
        normalized = message.lower()
        normalized = re.sub(r'#\w+', '', normalized)  # Remove hashtags
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation/emoji
        normalized = re.sub(r'\s+', ' ', normalized).strip()  # Normalize whitespace
        
        # Check against cache
        for cached in self._message_cache:
            cached_normalized = cached.lower()
            cached_normalized = re.sub(r'#\w+', '', cached_normalized)
            cached_normalized = re.sub(r'[^\w\s]', '', cached_normalized)
            cached_normalized = re.sub(r'\s+', ' ', cached_normalized).strip()
            
            # If messages are >80% similar, consider it a duplicate
            if normalized == cached_normalized:
                return True
            
            # Calculate simple similarity (word overlap)
            msg_words = set(normalized.split())
            cached_words = set(cached_normalized.split())
            if len(msg_words) > 0 and len(cached_words) > 0:
                overlap = len(msg_words & cached_words) / max(len(msg_words), len(cached_words))
                if overlap > 0.8:
                    return True
        
        return False
    
    def add_to_message_cache(self, message: str):
        """
        Add message to deduplication cache.
        
        Uses a simple FIFO queue. Old messages get pushed out.
        It's not rocket science, just a fucking list.
        
        Args:
            message: The message to cache
        """
        if not self.enable_deduplication:
            return
        
        self._message_cache.append(message)
        
        # Keep cache size limited
        if len(self._message_cache) > self.dedup_cache_size:
            self._message_cache.pop(0)
    
    @staticmethod
    def count_emojis(message: str) -> int:
        """
        Count emoji characters in a message.
        
        Because apparently some people think more emojis = more engagement.
        Spoiler alert: It doesn't. You just look like you're 12.
        
        But hey, who am I to judge? I'm just here teaching robots not to spam emojis.
        Living the dream.
        
        Args:
            message: The message to check
            
        Returns:
            Number of emoji characters
        """
        # Unicode emoji ranges (basic coverage, not exhaustive)
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
    def contains_profanity(message: str, severity: str = 'moderate') -> Tuple[bool, List[str]]:
        """
        Check if message contains profanity.
        
        Ironic, considering this entire codebase is written by the ghost of George Carlin.
        But apparently we draw the line at the AI dropping F-bombs about Minecraft videos.
        
        "You can't say fuck on television!" - George Carlin, probably rolling in his grave
        that we're now censoring robots too.
        
        The Seven Words You Can't Say... to an AI, apparently.
        
        Args:
            message: The message to check
            severity: 'mild', 'moderate', or 'severe'
            
        Returns:
            tuple: (has_profanity, list_of_found_words)
        """
        # Profanity lists by severity (from mildest to most severe)
        mild_words = ['damn', 'hell', 'crap', 'suck', 'sucks', 'piss', 'pissed']
        moderate_words = ['ass', 'bastard', 'bitch', 'dick', 'cock', 'pussy', 'slut', 'whore']
        severe_words = ['fuck', 'fucking', 'shit', 'shitty', 'motherfucker', 'asshole', 'cunt']
        
        # Build word list based on severity
        if severity == 'severe':
            check_words = mild_words + moderate_words + severe_words
        elif severity == 'moderate':
            check_words = mild_words + moderate_words
        else:  # mild
            check_words = mild_words
        
        message_lower = message.lower()
        found_words = []
        
        for word in check_words:
            # Use word boundaries to avoid false positives (e.g., 'bass' shouldn't match 'ass')
            if re.search(rf'\b{word}\b', message_lower):
                found_words.append(word)
        
        return (len(found_words) > 0, found_words)
    
    @staticmethod
    def score_message_quality(message: str, title: str) -> Tuple[int, List[str]]:
        """
        Score message quality on a scale of 1-10.
        
        We're literally grading the AI's homework. Like it's in school.
        "Sorry robot, you get a C-. Try harder next time."
        
        This is what we've become. Quality control for artificial enthusiasm.
        George Carlin would have a 30-minute bit about this shit.
        
        Scoring criteria:
        - 10: Perfect (natural, engaging, unique)
        - 7-9: Good (clear, interesting)
        - 4-6: Mediocre (generic, boring)
        - 1-3: Bad (very generic, poor grammar, wrong info)
        
        Args:
            message: The generated message
            title: Original video title
            
        Returns:
            tuple: (score 1-10, list_of_issues)
        """
        score = 10
        issues = []
        
        # Check for generic/overused phrases (deduct 2 points each)
        generic_phrases = [
            'check it out',
            'check this out',
            'watch now',
            'click the link',
            'new video',
            'just uploaded',
            'latest video'
        ]
        
        message_lower = message.lower()
        generic_count = sum(1 for phrase in generic_phrases if phrase in message_lower)
        if generic_count > 2:
            score -= 2
            issues.append(f"Too many generic phrases ({generic_count})")
        
        # Check length (too short = lazy, too long = rambling)
        content_without_hashtags = re.sub(r'#\w+', '', message).strip()
        word_count = len(content_without_hashtags.split())
        
        if word_count < 4:
            score -= 3
            issues.append("Too short (feels lazy)")
        elif word_count > 30:
            score -= 2
            issues.append("Too long (rambling)")
        
        # Check for repeated words (sign of poor generation)
        words = content_without_hashtags.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.7:  # >30% repeated words
                score -= 2
                issues.append("Too many repeated words")
        
        # Check for title integration (should reference video content)
        title_words = set(title.lower().split())
        message_words = set(message_lower.split())
        overlap = len(title_words & message_words)
        
        if overlap == 0:
            score -= 3
            issues.append("Doesn't reference video title/content")
        
        # Check for personality/engagement (exclamation marks, questions, emojis)
        has_personality = bool(
            re.search(r'[!?]', message) or
            re.search(r'[\U0001F600-\U0001F64F]', message)  # emoji
        )
        
        if not has_personality:
            score -= 1
            issues.append("Lacks personality (no punctuation variety or emoji)")
        
        # Clamp score to 1-10
        score = max(1, min(10, score))
        
        return (score, issues)
    
    def validate_platform_specific(self, message: str, platform: str) -> List[str]:
        """
        Platform-specific validation rules.
        
        Because each social media platform is a special fucking snowflake
        with its own rules and quirks that we have to account for.
        
        Discord wants mentions and embeds formatted just so.
        Bluesky has its fancy "facets" and AT Protocol nonsense.
        Mastodon... well, Mastodon is pretty chill actually.
        Matrix is like Discord but more complicated.
        
        But we still need to validate all this shit because apparently
        "just post some text" was too simple. Had to complicate it.
        
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
            # Discord: Check for @everyone and @here (mass pings)
            if '@everyone' in message or '@here' in message:
                issues.append("Contains @everyone or @here mention")
            
            # Check for malformed mentions
            if re.search(r'@\d+>', message):
                issues.append("Malformed Discord mention detected")
            
            # Check for markdown that might break
            unmatched_markdown = (
                message.count('**') % 2 != 0 or
                message.count('__') % 2 != 0
            )
            if unmatched_markdown:
                issues.append("Unmatched markdown formatting")
        
        elif platform_lower == 'bluesky':
            # Bluesky: Check for issues that would break facets/link cards
            # Facets are their fancy word for "rich text annotations"
            
            # Check for URLs that aren't at the end (we add URL separately)
            urls_in_content = re.findall(r'https?://\S+', message)
            if urls_in_content:
                issues.append("URL found in content (should be added separately for facets)")
            
            # Check for @ mentions without handle format
            if '@' in message and not re.search(r'@[a-zA-Z0-9][a-zA-Z0-9-]*\.', message):
                issues.append("Malformed Bluesky handle (needs .domain)")
        
        elif platform_lower == 'mastodon':
            # Mastodon: Pretty forgiving, but check for HTML entities
            if re.search(r'&[a-z]+;', message):
                issues.append("HTML entities detected (should be plain text)")
        
        elif platform_lower == 'matrix':
            # Matrix: Similar to Discord but with HTML support
            # Check for unmatched HTML tags
            if '<' in message or '>' in message:
                # Basic HTML tag balance check
                open_tags = len(re.findall(r'<\w+>', message))
                close_tags = len(re.findall(r'</\w+>', message))
                if open_tags != close_tags:
                    issues.append("Unmatched HTML tags")
        
        return issues
    
    @staticmethod
    def remove_hashtag_from_message(message: str, hashtag: str) -> str:
        """
        Remove a specific hashtag from the message.
        
        Args:
            message: The message to modify
            hashtag: The hashtag to remove (without #)
            
        Returns:
            Message with the hashtag removed, cleaned up
        """
        # Remove the hashtag (case insensitive)
        pattern = r'#' + re.escape(hashtag) + r'\b'
        message = re.sub(pattern, '', message, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        message = re.sub(r'\s+', ' ', message).strip()
        
        return message
    
    @staticmethod
    def safe_trim(message: str, limit: int) -> str:
        """
        Safely trim message to character limit without cutting words/hashtags mid-token.
        
        This is the civilized way to truncate text. We don't just chop it off like
        a fucking barbarian cutting hashtags in half. We find a word boundary.
        We respect the hashtags. We have STANDARDS, goddammit.
        
        Without this, you get shit like: "Check out my new #PCBuild #Hardware #Tu"
        With this, you get: "Check out my new #PCBuild #Hardware"
        
        See the difference? One looks professional. The other looks like someone 
        had a stroke mid-tweet.
        
        Args:
            message: The message to trim
            limit: Maximum character limit
        
        Returns:
            Trimmed message at word boundary, or hard cut if unavoidable
        """
        message = message.strip()
        if len(message) <= limit:
            return message
        
        # Try to trim at a word boundary to avoid cutting hashtags in half
        # Find the last space before the limit
        trimmed = message[:limit].rsplit(' ', 1)[0].rstrip()
        
        # If we trimmed too aggressively (e.g., single long token), hard cut
        # Better to cut a word than lose half the message
        return trimmed if trimmed else message[:limit]
    
    def validate_hashtags_against_username(self, message: str, username: str) -> str:
        """
        Remove hashtags that are derived from the username.
        
        This is a post-generation guardrail to filter out username-derived hashtags
        that the LLM may have incorrectly generated despite prompt instructions.
        
        Because apparently teaching a computer "don't use the person's name as a hashtag"
        is like explaining to your uncle why #MAGA isn't a personality trait.
        It should be simple. It's not.
        
        Args:
            message: The generated message
            username: The creator's username
            
        Returns:
            Message with username-derived hashtags removed
        """
        # Get username parts
        username_parts = self.tokenize_username(username)
        
        if not username_parts:
            return message
        
        # Extract hashtags from message
        hashtags = self.extract_hashtags(message)
        
        # Check each hashtag against username parts
        for hashtag in hashtags:
            should_remove = False
            
            # Direct match (exact match with any username part)
            if hashtag in username_parts:
                should_remove = True
                logger.debug(f"Removing hashtag #{hashtag} - direct match with username part")
            else:
                # Check if hashtag contains username parts (substring matching)
                # For 3-char parts, require exact match to avoid false positives
                # For 4+ char parts, allow substring matching for broader coverage
                for part in username_parts:
                    if len(part) >= 4 and part in hashtag:
                        should_remove = True
                        logger.debug(f"Removing hashtag #{hashtag} - contains username part '{part}'")
                        break
            
            if should_remove:
                message = self.remove_hashtag_from_message(message, hashtag)
                logger.warning(f"⚠ Removed username-derived hashtag: #{hashtag}")
        
        return message
    
    def validate_full_message(
        self,
        message: str,
        expected_hashtag_count: int,
        title: str,
        username: str,
        platform: str = ''
    ) -> Tuple[bool, List[str]]:
        """
        Run all enabled guardrails on a message.
        
        This is the master validation function that runs everything:
        - Base quality checks (hashtags, forbidden words, URLs, hallucinations)
        - Deduplication check
        - Emoji count
        - Profanity filter
        - Quality scoring
        - Platform-specific validation
        - Username hashtag filtering
        
        It's like TSA for AI-generated content. Security theater, but sometimes
        it actually catches shit.
        
        Args:
            message: The generated message
            expected_hashtag_count: Expected number of hashtags
            title: Original video title
            username: Creator username
            platform: Target social platform (optional)
            
        Returns:
            tuple: (is_valid, list_of_all_issues)
        """
        all_issues = []
        
        # 1. Base quality validation
        is_valid, issues = self.validate_message_quality(
            message, expected_hashtag_count, title, username
        )
        all_issues.extend(issues)
        
        # 2. Deduplication check
        if self.enable_deduplication and self.is_duplicate_message(message):
            all_issues.append("Message is too similar to recent posts")
        
        # 3. Emoji count check
        emoji_count = self.count_emojis(message)
        if emoji_count > self.max_emoji_count:
            all_issues.append(f"Too many emojis: {emoji_count} (max: {self.max_emoji_count})")
        
        # 4. Profanity filter
        if self.enable_profanity_filter:
            has_profanity, profane_words = self.contains_profanity(message, self.profanity_severity)
            if has_profanity:
                all_issues.append(f"Contains profanity: {', '.join(profane_words)}")
        
        # 5. Quality scoring
        if self.enable_quality_scoring:
            quality_score, quality_issues = self.score_message_quality(message, title)
            if quality_score < self.min_quality_score:
                all_issues.append(f"Low quality score: {quality_score}/10")
                all_issues.extend(quality_issues)
        
        # 6. Platform-specific validation
        if platform:
            platform_issues = self.validate_platform_specific(message, platform)
            all_issues.extend(platform_issues)
        
        return (len(all_issues) == 0, all_issues)
