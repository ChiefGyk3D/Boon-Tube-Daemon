"""
Tests for LLM post-generation quality validation.

Tests the guardrails that catch when small LLMs fuck up and:
- Use wrong number of hashtags
- Include forbidden clickbait words we explicitly told them not to use
- Accidentally include URLs in the content
- Hallucinate details that weren't in the video title

Because apparently we need to teach AI how to count and read instructions.
George Carlin would have a field day with this shit.

"We spent billions of dollars and decades of research to build artificial intelligence.
And now we're writing unit tests to make sure it can count to fucking three.
THREE! Not quantum physics. Not the meaning of life. THREE HASHTAGS.

And you know what the best part is? The tests are MORE RELIABLE than the AI.
A bunch of if-statements written by a hungover programmer at 3am is more trustworthy
than a neural network trained on the entire fucking internet. Beautiful.

Welcome to the future, folks. It's exactly as stupid as the past, but now it's
automated stupid. We've achieved stupidity at scale. Congratulations, humanity."
- The Ghost of George Carlin, probably laughing his ass off in the afterlife
"""

import pytest
from boon_tube_daemon.llm.validator import LLMValidator


class TestMessageQualityValidation:
    """Test post-generation quality checks.
    
    Or: "How we learned to stop trusting the AI and love the validation."
    """
    
    def test_correct_hashtag_count_passes(self):
        """Valid messages with correct hashtag count pass validation."""
        validator = LLMValidator()
        
        # New video with 3 hashtags
        message = "New PC build tutorial! Check it out #PC #Hardware #Tutorial"
        is_valid, issues = validator.validate_message_quality(
            message, expected_hashtag_count=3, title="PC Build Tutorial", username="TechCreator"
        )
        assert is_valid
        assert len(issues) == 0
        
        # Short/clip with 2 hashtags (if using different rules)
        message = "Quick PC tip! #PC #Hardware"
        is_valid, issues = validator.validate_message_quality(
            message, expected_hashtag_count=2, title="PC Tip", username="TechCreator"
        )
        assert is_valid
        assert len(issues) == 0
    
    def test_wrong_hashtag_count_fails(self):
        """Messages with wrong number of hashtags fail validation."""
        validator = LLMValidator()
        
        # Only 2 hashtags when we need 3
        message = "New PC tutorial! #PC #Hardware"
        is_valid, issues = validator.validate_message_quality(
            message, expected_hashtag_count=3, title="PC Tutorial", username="TechCreator"
        )
        assert not is_valid
        assert any("hashtag count" in issue.lower() for issue in issues)
        
        # 4 hashtags when we need 3
        message = "New PC tutorial! #PC #Hardware #Tutorial #Tech"
        is_valid, issues = validator.validate_message_quality(
            message, expected_hashtag_count=3, title="PC Tutorial", username="TechCreator"
        )
        assert not is_valid
        assert any("hashtag count" in issue.lower() for issue in issues)
    
    def test_forbidden_words_detected(self):
        """Messages with clickbait/forbidden words are detected.
        
        We literally have to check if the AI used the word "INSANE".
        Peak civilization, folks.
        """
        validator = LLMValidator()
        
        forbidden_tests = [
            ("This tutorial is INSANE! #PC #Hardware #Tutorial", "insane"),
            ("Epic PC build incoming! #PC #Hardware #Tutorial", "epic"),
            ("Crazy hardware guide! #PC #Hardware #Tutorial", "crazy"),
            ("Smash that subscribe button! #PC #Hardware #Tutorial", "smash"),
            ("Most incredible guide ever! #PC #Hardware #Tutorial", "incredible"),
            ("This build is LIT 🔥 #PC #Hardware #Tutorial", "lit"),
            ("Legendary PC guide! #PC #Hardware #Tutorial", "legendary"),
        ]
        
        for message, expected_word in forbidden_tests:
            is_valid, issues = validator.validate_message_quality(
                message, expected_hashtag_count=3, title="PC Tutorial", username="TechCreator"
            )
            assert not is_valid, f"Should detect forbidden word '{expected_word}' in: {message}"
            assert any("forbidden" in issue.lower() for issue in issues)
            assert any(expected_word in issue.lower() for issue in issues)
    
    def test_url_in_content_detected(self):
        """Messages that include URLs (should be added separately) are detected."""
        validator = LLMValidator()
        
        message = "New PC tutorial! https://youtube.com/watch?v=xyz #PC #Hardware #Tutorial"
        is_valid, issues = validator.validate_message_quality(
            message, expected_hashtag_count=3, title="PC Tutorial", username="TechCreator"
        )
        assert not is_valid
        assert any("url" in issue.lower() for issue in issues)
        
        # Also test http://
        message = "New PC tutorial! http://youtu.be/xyz #PC #Hardware #Tutorial"
        is_valid, issues = validator.validate_message_quality(
            message, expected_hashtag_count=3, title="PC Tutorial", username="TechCreator"
        )
        assert not is_valid
        assert any("url" in issue.lower() for issue in issues)
    
    def test_hallucination_detection(self):
        """Common hallucinations (invented details) are detected.
        
        The AI makes shit up. Just completely fabricates details.
        "Giveaway!" - No there isn't.
        "Premiere tonight!" - No there's not.
        "Sponsored by..." - No it fucking isn't.
        
        It's like that friend who can't tell a story without embellishing.
        Except this friend cost millions of dollars to create.
        """
        validator = LLMValidator()
        
        hallucination_tests = [
            "PC tutorial with giveaway! #PC #Hardware #Tutorial",
            "Sponsored PC build guide! #PC #Hardware #Tutorial",
            "Premiere tonight at 8pm! #PC #Hardware #Tutorial",
            "New video tonight at 7! #PC #Hardware #Tutorial",
            "Special guest appearance! #PC #Hardware #Tutorial",
        ]
        
        for message in hallucination_tests:
            is_valid, issues = validator.validate_message_quality(
                message, expected_hashtag_count=3, title="PC Tutorial", username="TechCreator"
            )
            # Should detect hallucination
            if not is_valid:
                assert any("hallucination" in issue.lower() for issue in issues), \
                    f"Expected hallucination detection in: {message}"
    
    def test_extract_hashtags(self):
        """Hashtag extraction works correctly."""
        validator = LLMValidator()
        
        tests = [
            ("Tutorial #PC with #Hardware #Tutorial", ["pc", "hardware", "tutorial"]),
            ("No hashtags here", []),
            ("#SingleTag", ["singletag"]),
            ("Mixed #Case #TAGS #LowerCase", ["case", "tags", "lowercase"]),
            ("With #emoji 🖥️ and #numbers123", ["emoji", "numbers123"]),
        ]
        
        for message, expected in tests:
            result = validator.extract_hashtags(message)
            assert result == expected, f"Failed for: {message}"
    
    def test_forbidden_words_check(self):
        """Forbidden word detection works correctly."""
        validator = LLMValidator()
        
        # Should find forbidden words
        has_forbidden, found = validator.contains_forbidden_words("This is INSANE!")
        assert has_forbidden
        assert "insane" in found
        
        has_forbidden, found = validator.contains_forbidden_words("Epic and crazy video!")
        assert has_forbidden
        assert "epic" in found
        assert "crazy" in found
        
        # Should not flag normal words
        has_forbidden, found = validator.contains_forbidden_words("Tutorial about PC hardware!")
        assert not has_forbidden
        assert len(found) == 0
    
    def test_multiple_issues_reported(self):
        """Messages with multiple issues report all of them."""
        validator = LLMValidator()
        
        # Wrong hashtag count + forbidden word + URL
        message = "INSANE tutorial! https://youtube.com/xyz #PC #Hardware"
        is_valid, issues = validator.validate_message_quality(
            message, expected_hashtag_count=3, title="PC Tutorial", username="TechCreator"
        )
        assert not is_valid
        assert len(issues) >= 2  # Should catch at least hashtag count and forbidden word
        
        # Check specific issues
        issue_text = " ".join(issues).lower()
        assert "hashtag" in issue_text
        assert "forbidden" in issue_text or "insane" in issue_text


class TestHashtagExtraction:
    """Test hashtag parsing and counting."""
    
    def test_hashtag_extraction_edge_cases(self):
        """Hashtag extraction handles edge cases correctly."""
        validator = LLMValidator()
        
        tests = [
            # Multiple spaces between hashtags
            ("Test   #tag1   #tag2", ["tag1", "tag2"]),
            # Hashtags at start/end
            ("#start middle #end", ["start", "end"]),
            # Adjacent hashtags
            ("#tag1#tag2", ["tag1", "tag2"]),
            # Numbers in hashtags
            ("Tutorial #test123", ["test123"]),
            # Empty string
            ("", []),
            # Just whitespace
            ("   ", []),
            # Hashtag-like but not hashtags (# without alphanum)
            ("Price is #50 #test", ["test"]),  # #50 won't match, #test will
        ]
        
        for message, expected in tests:
            result = validator.extract_hashtags(message)
            assert result == expected, f"Failed for: '{message}'"


class TestForbiddenWords:
    """Test forbidden word detection.
    
    Because we have to explicitly program a list of words the AI isn't allowed to say.
    It's like the FCC, but for robots. George would fucking love this.
    """
    
    def test_case_insensitive(self):
        """Forbidden word detection is case-insensitive."""
        validator = LLMValidator()
        
        test_cases = [
            "INSANE tutorial",
            "insane tutorial",
            "InSaNe tutorial",
        ]
        
        for message in test_cases:
            has_forbidden, found = validator.contains_forbidden_words(message)
            assert has_forbidden
            assert "insane" in found
    
    def test_partial_word_matching(self):
        """Forbidden words are detected even within other words."""
        validator = LLMValidator()
        
        # "insane" should be found in "insanely"
        has_forbidden, found = validator.contains_forbidden_words("This is insanely good!")
        assert has_forbidden
        assert "insane" in found
        
        # But normal words should be fine
        has_forbidden, found = validator.contains_forbidden_words("Tutorial about PC building")
        assert not has_forbidden
    
    def test_all_forbidden_words(self):
        """All forbidden words are properly detected."""
        validator = LLMValidator()
        
        forbidden_list = [
            'insane', 'epic', 'crazy', 'smash', 'unmissable',
            'incredible', 'amazing', 'lit', 'fire', 'legendary',
            'mind-blowing', 'jaw-dropping', 'unbelievable'
        ]
        
        for word in forbidden_list:
            message = f"This is {word} content!"
            has_forbidden, found = validator.contains_forbidden_words(message)
            assert has_forbidden, f"Failed to detect: {word}"
            assert word in found


class TestUsernameHashtagRemoval:
    """Test username hashtag filtering.
    
    Because the AI loves to use people's names as hashtags like a fucking amateur.
    """
    
    def test_simple_username_removal(self):
        """Simple username parts are removed from hashtags."""
        validator = LLMValidator()
        
        message = "New video! #Tech #Creator #Tutorial"
        cleaned = validator.validate_hashtags_against_username(message, "TechCreator")
        
        # Should remove #Tech and #Creator, keep #Tutorial
        assert "#Tech" not in cleaned
        assert "#Creator" not in cleaned
        assert "#Tutorial" in cleaned
    
    def test_camelcase_username_tokenization(self):
        """CamelCase usernames are properly tokenized."""
        validator = LLMValidator()
        
        # TechCreator99 should tokenize to: tech, creator, techcreator, techcreator99, 99
        username_parts = validator.tokenize_username("TechCreator99")
        
        assert "tech" in username_parts
        assert "creator" in username_parts
        assert "techcreator" in username_parts
        assert "techcreator99" in username_parts
    
    def test_underscore_username_tokenization(self):
        """Underscore-separated usernames are properly tokenized."""
        validator = LLMValidator()
        
        username_parts = validator.tokenize_username("Tech_Creator_99")
        
        assert "tech" in username_parts
        assert "creator" in username_parts
        assert "tech_creator_99" in username_parts
    
    def test_short_parts_not_removed(self):
        """Short username parts (<3 chars) don't cause false positives."""
        validator = LLMValidator()
        
        # "PC" in username shouldn't remove #PC hashtag (too short)
        username_parts = validator.tokenize_username("PCGamer")
        
        # Should have 'pcgamer' but not 'pc' (too short)
        assert "pcgamer" in username_parts


class TestEmojiCounting:
    """Test emoji counting.
    
    Teaching computers to count tiny pictures. Peak civilization.
    """
    
    def test_no_emojis(self):
        """Message with no emojis should return 0."""
        validator = LLMValidator()
        message = "Tutorial about PC hardware! #PC #Hardware"
        
        assert validator.count_emojis(message) == 0
    
    def test_single_emoji(self):
        """Message with one emoji should return 1."""
        validator = LLMValidator()
        message = "Tutorial about PC hardware! 🖥️ #PC"
        
        assert validator.count_emojis(message) == 1
    
    def test_multiple_emojis(self):
        """Message with multiple emojis should count them all."""
        validator = LLMValidator()
        message = "Tutorial! 🖥️💻🔧 #PC #Hardware"
        
        assert validator.count_emojis(message) == 3
    
    def test_emoji_mixed_with_text(self):
        """Emojis mixed with regular text are counted correctly."""
        validator = LLMValidator()
        message = "PC 🖥️ tutorial with 💻 hardware 🔧 guide"
        
        assert validator.count_emojis(message) == 3


class TestDeduplication:
    """Test message deduplication.
    
    Because nobody wants to read the same fucking announcement 5 times.
    """
    
    def test_exact_duplicate_detected(self):
        """Exact same message should be flagged as duplicate."""
        validator = LLMValidator()
        
        message1 = "New PC tutorial! Check it out #PC #Hardware #Tutorial"
        message2 = "New PC tutorial! Check it out #PC #Hardware #Tutorial"
        
        # Add first message to cache
        validator.add_to_message_cache(message1)
        
        # Check if second message is duplicate
        assert validator.is_duplicate_message(message2) is True
    
    def test_similar_message_detected(self):
        """Very similar messages should be flagged as duplicates."""
        validator = LLMValidator()
        
        message1 = "New PC build tutorial! Check it out #PC #Hardware #Tutorial"
        message2 = "New PC build tutorial! Check it out now #PC #Building #Tutorial"
        
        validator.add_to_message_cache(message1)
        
        # Should detect >80% similarity
        assert validator.is_duplicate_message(message2) is True
    
    def test_different_message_not_duplicate(self):
        """Different messages should not be flagged as duplicates."""
        validator = LLMValidator()
        
        message1 = "PC build tutorial! #PC #Hardware #Tutorial"
        message2 = "Minecraft survival guide! #Minecraft #Gaming #Tutorial"
        
        validator.add_to_message_cache(message1)
        
        assert validator.is_duplicate_message(message2) is False
    
    def test_cache_size_limit(self):
        """Cache should respect size limit (FIFO)."""
        validator = LLMValidator()
        validator.dedup_cache_size = 3  # Set small cache for testing
        
        messages = [
            "Message 1 #Gaming",
            "Message 2 #Tutorial",
            "Message 3 #PC",
            "Message 4 #Hardware"
        ]
        
        # Add all messages
        for msg in messages:
            validator.add_to_message_cache(msg)
        
        # Cache should only have last 3
        assert len(validator._message_cache) == 3
        assert "Message 1 #Gaming" not in validator._message_cache
        assert "Message 4 #Hardware" in validator._message_cache


class TestProfanityFilter:
    """Test profanity detection.
    
    Ironic, considering this codebase. But we draw the line somewhere.
    """
    
    def test_mild_profanity_detected(self):
        """Mild profanity is detected at all severity levels."""
        validator = LLMValidator()
        
        has_profanity, found = validator.contains_profanity("This is damn good!", "mild")
        assert has_profanity
        assert "damn" in found
    
    def test_severe_profanity_detected(self):
        """Severe profanity is only detected at appropriate severity."""
        validator = LLMValidator()
        
        # Should be detected at 'severe' level
        has_profanity, found = validator.contains_profanity("This is fucking great!", "severe")
        assert has_profanity
        assert "fuck" in found or "fucking" in found
        
        # Should NOT be detected at 'mild' level
        has_profanity, found = validator.contains_profanity("This is fucking great!", "mild")
        assert not has_profanity
    
    def test_no_false_positives(self):
        """Normal words shouldn't trigger profanity filter."""
        validator = LLMValidator()
        
        # "bass" shouldn't match "ass"
        has_profanity, found = validator.contains_profanity("Bass guitar tutorial", "severe")
        assert not has_profanity


class TestQualityScoring:
    """Test message quality scoring.
    
    Grading the AI's homework. This is what we do now.
    """
    
    def test_high_quality_message(self):
        """High quality messages get good scores."""
        validator = LLMValidator()
        
        message = "Complete guide to building your first gaming PC! 🖥️ #PC #Hardware #Tutorial"
        title = "How to Build a Gaming PC"
        
        score, issues = validator.score_message_quality(message, title)
        
        assert score >= 7, f"Expected high score, got {score}"
        assert len(issues) <= 1  # Should have few or no issues
    
    def test_low_quality_message(self):
        """Low quality messages get poor scores."""
        validator = LLMValidator()
        
        # Generic, short, no personality
        message = "New video check it out new video"
        title = "PC Tutorial"
        
        score, issues = validator.score_message_quality(message, title)
        
        assert score < 6, f"Expected low score, got {score}"
        assert len(issues) > 0  # Should have issues


class TestPlatformValidation:
    """Test platform-specific validation.
    
    Because each platform is a special fucking snowflake.
    """
    
    def test_discord_malformed_mention(self):
        """Discord malformed mentions are detected."""
        validator = LLMValidator()
        
        message = "Check @123> for updates"
        issues = validator.validate_platform_specific(message, "discord")
        
        assert len(issues) > 0
        assert any("malformed" in issue.lower() for issue in issues)
    
    def test_discord_unmatched_markdown(self):
        """Discord unmatched markdown is detected."""
        validator = LLMValidator()
        
        message = "**bold text* #Tutorial"
        issues = validator.validate_platform_specific(message, "discord")
        
        assert len(issues) > 0
        assert any("markdown" in issue.lower() for issue in issues)
    
    def test_bluesky_url_in_content(self):
        """Bluesky URLs in content are detected."""
        validator = LLMValidator()
        
        message = "Tutorial https://youtube.com/xyz #Tutorial"
        issues = validator.validate_platform_specific(message, "bluesky")
        
        assert len(issues) > 0
        assert any("url" in issue.lower() for issue in issues)
    
    def test_mastodon_html_entities(self):
        """Mastodon HTML entities are detected."""
        validator = LLMValidator()
        
        message = "Tutorial &nbsp; time!"
        issues = validator.validate_platform_specific(message, "mastodon")
        
        assert len(issues) > 0
        assert any("html" in issue.lower() for issue in issues)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
