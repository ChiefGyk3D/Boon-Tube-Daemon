# LLM Guardrails & Quality Checks

## Overview

Because even AI needs adult supervision.

**Or: "How I Learned to Stop Trusting the Robot and Love the Validation"**

### IMPORTANT: What George Carlin Jokes Are Doing Here

Let's be crystal fucking clear about something:

**The AI does NOT generate messages in George Carlin's voice.**

Your video notifications will be normal, professional posts like:
- "New video: How to Build a PC! Check it out 🖥️ #PC #Hardware #Tutorial"
- "Just uploaded: Minecraft Survival Tips #Minecraft #Gaming #Tutorial"

They will NOT be:
- "New fucking video about some PC bullshit #PC #Hardware"
- "I made a video. Watch it if you give a shit."

The profanity and Carlin-esque humor is in the **CODE COMMENTS** and **DOCUMENTATION**.
Because if you're going to write software, you might as well be honest about what you're doing:
Teaching robots to fake enthusiasm about YouTube videos on the internet.

This is what we do with Computer Science degrees now. Your parents are so proud.

This document explains the **post-generation quality validation** system that catches when small LLMs fuck up and:
- Use the wrong number of hashtags
- Include forbidden clickbait words we explicitly told them not to use
- Accidentally include URLs in the content
- Hallucinate details that weren't in the video title

George Carlin would have a field day: "We built robots that can write, but we still need to teach them how to count to three."

## Guardrail Types

### 1. Username Hashtag Removal (Enabled by Default)
**Purpose**: Prevents AI from using parts of the username as hashtags.

**Example**:
- Username: `TechCreator99`
- Bad: `#Tech #Creator #Tutorial`
- Good: `#PC #Hardware #Tutorial`

**Implementation**: `validate_hashtags_against_username()` tokenizes the username and removes any hashtags that match.

**George says**: "Teaching a computer 'don't use the person's name as a hashtag' is like explaining to your uncle why #MAGA isn't a personality trait. It should be simple. It's not."

### 2. Hashtag Count Validation (Enabled by Default)
**Purpose**: Ensures exactly the right number of hashtags are used.

**Rules**:
- **New videos**: Exactly 3 hashtags
- **Shorts**: Exactly 2 hashtags (optional)

**Why**: Small LLMs struggle with counting. Without this, you get anywhere from 1-6 hashtags.

Let that sink in. A computer. That can do billions of calculations per second. Can't consistently count to three.

Your iPhone can render photorealistic 3D graphics, simulate physics, and predict the weather.
But asking it for exactly 3 hashtags? "Best I can do is somewhere between 1 and 6, chief."

Fucking magnificent.

**Example Failures Caught**:
```
❌ "New PC build video! #PC #Hardware" (only 2, needs 3)
❌ "New PC build video! #PC #Hardware #Tutorial #Tech" (4, needs 3)
✅ "New PC build video! #PC #Hardware #Tutorial" (exactly 3)
```

### 3. Forbidden Word Detection (Enabled by Default)
**Purpose**: Catches when AI ignores our prompt and uses clickbait/cringe words.

**Forbidden Words List**:
- insane, epic, crazy, smash, unmissable
- incredible, amazing, lit, fire, legendary
- mind-blowing, jaw-dropping, unbelievable, viral

**Why**: We explicitly tell the AI not to use these. If it does anyway, we retry with stricter instructions.

**Example Failures Caught**:
```
❌ "This tutorial is INSANE! #PC #Hardware #Tutorial"
❌ "Epic build guide incoming! #PC #Hardware #Tutorial"
✅ "Complete PC building guide! #PC #Hardware #Tutorial"
```

### 4. URL Contamination Check (Enabled by Default)
**Purpose**: Ensures URLs aren't accidentally included in message content.

**Why**: URLs are added separately after generation. If the AI includes them, formatting breaks.

**Example Failures Caught**:
```
❌ "New video! https://youtube.com/watch?v=xyz #PC #Hardware #Tutorial"
✅ "New video! #PC #Hardware #Tutorial"
     (URL added after: "...\n\nhttps://youtube.com/watch?v=xyz")
```

### 5. Hallucination Detection (Enabled by Default)
**Purpose**: Catches when AI invents details not in the video title.

**Common Hallucinations**:
- "drops enabled"
- "giveaway"
- "tonight at 8pm" / "starting at 7"
- "premiere"
- "sponsored"
- "special guest"
- "new series"

**Why**: Small LLMs sometimes "remember" patterns from training data and insert them even when not relevant.

**Example Failures Caught**:
```
Title: "PC Build Tutorial"
❌ "PC build tutorial with giveaway! #PC #Hardware #Tutorial"
❌ "Sponsored PC build guide! #PC #Hardware #Tutorial"
✅ "Complete PC build tutorial! #PC #Hardware #Tutorial"
```

### 6. Message Deduplication (Configurable - Enabled by Default)
**Purpose**: Prevents identical or very similar messages across multiple announcements.

**Configuration**:
```bash
# In your .env or config
LLM_ENABLE_DEDUPLICATION=True  # Enable/disable
LLM_DEDUP_CACHE_SIZE=20        # How many messages to remember
```

**How it works**:
- Caches last N messages (default: 20)
- Normalizes messages (removes hashtags, emojis, punctuation)
- Calculates word overlap similarity
- >80% similar = considered duplicate
- Triggers retry if duplicate detected

**Why**: When posting to multiple platforms (Discord + Matrix + Bluesky + Mastodon), you don't want the same exact announcement posted 4 times.

**Example**:
```
First announcement: "New PC build tutorial is here! Check it out #PC #Hardware #Tutorial"
Duplicate (rejected): "New PC build tutorial is here! Check it out now #PC #Hardware #Building"
Different (accepted): "Complete guide to building your first PC! #PC #Hardware #Tutorial"
```

**George says**: "Because nobody wants to read the same fucking announcement 5 times. Although to be fair, humans already do this manually."

### 7. Emoji Count Limits (Configurable)
**Purpose**: Prevents emoji spam in generated messages.

**Configuration**:
```bash
LLM_MAX_EMOJI_COUNT=2  # 0-10 allowed, default: 2
```

**Why**: Too many emojis = looks like a teenager's Instagram post. Too few = boring corporate speak. Sweet spot: 1-2 emojis.

**Example Failures Caught**:
```
Max emoji: 2
❌ "New PC video! 🖥️💻🔧🎮 #PC #Hardware #Tutorial" (4 emojis)
✅ "New PC build video! Check it out 🖥️ #PC #Hardware #Tutorial" (1 emoji)
✅ "Complete PC building guide! 🖥️🔧 #PC #Hardware #Tutorial" (2 emojis)
```

**George says**: "Too many emojis = looks like you're 12. We're literally teaching robots not to spam emojis. Living the dream."

### 8. Profanity Filter (Configurable - Disabled by Default)
**Purpose**: Blocks profanity in AI-generated messages (while keeping Carlin's code commentary).

**Configuration**:
```bash
LLM_ENABLE_PROFANITY_FILTER=False  # Default: disabled
LLM_PROFANITY_SEVERITY=moderate    # mild, moderate, severe
```

**Severity Levels**:
- **mild**: Blocks hard profanity (fuck, shit, etc.)
- **moderate**: + sexual references, slurs
- **severe**: + mild profanity (damn, hell, crap)

**Why**: You might not want the AI dropping F-bombs about your Minecraft videos. Note: This only affects GENERATED content, not our beautiful Carlin commentary.

**George says**: "'You can't say fuck on television!' - George Carlin, probably rolling in his grave that we're now censoring robots too. The Seven Words You Can't Say... to an AI."

### 9. Quality Scoring System (Configurable - Disabled by Default)
**Purpose**: Scores messages 1-10 and retries if quality is too low.

**Configuration**:
```bash
LLM_ENABLE_QUALITY_SCORING=False  # Default: disabled (for picky users)
LLM_MIN_QUALITY_SCORE=6           # Minimum acceptable score
```

**Scoring Criteria**:
- **10**: Perfect (natural, engaging, unique)
- **7-9**: Good (clear, interesting)
- **4-6**: Mediocre (generic, boring)
- **1-3**: Bad (very generic, poor grammar, wrong info)

**Deductions**:
- Generic phrases (check it out, new video, etc.): -2 points each
- Too short (<4 words): -3 points
- Too long (>30 words): -2 points
- Repeated words (>30%): -2 points
- Doesn't reference title: -3 points
- Lacks personality (no !, ?, emoji): -1 point

**Example**:
```
Message: "check it out new video just uploaded" 
Score: 3/10 (too many generic phrases, very short, no hashtags)
Action: ⚠ Retry with stricter prompt

Message: "Complete guide to building your first PC! 🖥️ #PC #Hardware #Tutorial"
Score: 8/10 (clear, engaging, good length, references topic)
Action: ✅ Accept
```

**George says**: "We're literally grading the AI's homework. 'Sorry robot, you get a C-. Try harder next time.' This is what we've become."

### 10. Platform-Specific Validation (Configurable - Enabled by Default)
**Purpose**: Validates platform-specific formatting rules.

**Configuration**:
```bash
LLM_ENABLE_PLATFORM_VALIDATION=True  # Default: enabled
```

**Platform Rules**:

**Discord**:
- Checks for malformed mentions (e.g., `@123>` without `<`)
- Validates markdown pairing (`**`, `__`, `*`)
- Ensures embed-safe formatting

**Bluesky**:
- Validates AT Protocol handle format (`@user.domain`)
- Checks for URLs in content (should be separate for facets/link cards)
- Ensures proper "facet" structure

**Mastodon**:
- Checks for HTML entities (should be plain text)
- Validates content warnings if configured

**Matrix**:
- Checks for unmatched HTML tags
- Validates formatting markup

**Example Failures Caught**:
```
Discord: "Check @123> for updates" → ❌ Malformed mention
Discord: "**bold text* #Tutorial" → ❌ Unmatched markdown

Bluesky: "Follow @username #Tech" → ❌ Needs .domain (@username.bsky.social)
Bluesky: "Video https://youtube.com #Tech" → ❌ URL should be added separately

Mastodon: "Video &nbsp; time!" → ❌ HTML entity detected
```

**George says**: "Each social media platform is a special fucking snowflake with its own rules. Discord wants mentions just so. Bluesky has its fancy 'facets' nonsense. 'Just post some text' was too simple. Had to complicate it."

## Auto-Retry System

When validation fails, the system **automatically retries up to 2 times** with a stricter prompt.

### Retry Flow

```
1. Generate message with normal prompt
2. Validate quality (run all enabled guardrails)
3. If validation fails:
   - Log issues: "⚠ Generated message has quality issues: Wrong hashtag count: 2 (expected 3)"
   - Retry with strict_mode=True
   - Add issue context to prompt
4. If retry succeeds:
   - Use new message
   - Log: "✅ Retry produced valid message"
5. If retry fails:
   - Use original message (better than nothing)
   - Log: "⚠ Validation retries exhausted, using message with issues"
```

### Strict Mode Prompt

When retrying, the prompt is prefixed with:

```
CRITICAL: Previous attempt violated rules. FOLLOW INSTRUCTIONS EXACTLY.

Issues found: Wrong hashtag count: 2 (expected 3), Contains forbidden words: epic

[Original prompt]
```

This gives the LLM extra context that it needs to pay more attention.

## Usage Examples

### Normal Message (Passes All Checks)

```python
# Input
platform_name = "YouTube"
title = "How to Build a PC - Complete Beginner's Guide"
url = "https://youtube.com/watch?v=xyz"
social_platform = "mastodon"

# Generated message
"Complete guide to building your first PC! 🖥️ #PC #Hardware #Tutorial"

# Validation
✅ 3 hashtags (correct)
✅ No forbidden words
✅ No URL in content
✅ No hallucinations detected
✅ Emoji count OK (1)
✅ No duplicates
✅ Platform validation passed

# Final output
"Complete guide to building your first PC! 🖥️ #PC #Hardware #Tutorial\n\nhttps://youtube.com/watch?v=xyz"
```

### Failed Message (Auto-Retried)

```python
# Input (same as above)

# First attempt
"Epic PC tutorial! This is INSANE! #PC #Hardware"

# Validation
❌ 2 hashtags (expected 3)
❌ Forbidden words: epic, insane

# Auto-retry with strict mode
"Complete PC building guide for beginners! #PC #Hardware #Tutorial"

# Validation (retry)
✅ 3 hashtags (correct)
✅ No forbidden words
✅ Passes all checks

# Final output (using retry)
"Complete PC building guide for beginners! #PC #Hardware #Tutorial\n\nhttps://youtube.com/watch?v=xyz"
```

## Configuration

All guardrails work out of the box with sensible defaults. Optional configuration:

```bash
# .env or environment variables

# Deduplication
LLM_ENABLE_DEDUPLICATION=True  # Default: True
LLM_DEDUP_CACHE_SIZE=20        # Default: 20

# Emoji limits
LLM_MAX_EMOJI_COUNT=2          # Default: 2

# Profanity filter
LLM_ENABLE_PROFANITY_FILTER=False   # Default: False
LLM_PROFANITY_SEVERITY=moderate     # Default: moderate

# Quality scoring
LLM_ENABLE_QUALITY_SCORING=False  # Default: False
LLM_MIN_QUALITY_SCORE=6           # Default: 6

# Platform validation
LLM_ENABLE_PLATFORM_VALIDATION=True  # Default: True
```

To disable AI generation entirely:
```bash
LLM_ENABLE=False
```

## Logging

Validation results are logged with clear indicators:

```
# Success (first try)
✨ Generated mastodon post (conversational style): Complete guide to building your first PC! 🖥️...
✓ Message passed all guardrail checks on first try

# Warning (issues found, retrying)
⚠ Generated message has quality issues (attempt 1/2): Wrong hashtag count: 2 (expected 3), Contains forbidden words: epic, insane
🔄 Retrying with stricter validation...
✅ Retry #1 produced valid message after quality checks

# Warning (all retries exhausted)
⚠ Generated message has quality issues (attempt 2/2): Wrong hashtag count: 4 (expected 3)
⚠ Validation retries exhausted, using message with issues

# Username hashtag removal
⚠ Removed username-derived hashtag: #Tech (from TechCreator99)

# Error (generation failed completely)
✗ Failed to generate enhanced notification for discord, using fallback
```

## Testing

Tests are located in `tests/test_llm_guardrails.py` and `tests/test_llm_quality_checks.py`.

**Run tests**:
```bash
# Install pytest if needed
pip install pytest

# Run all guardrail tests
pytest tests/test_llm_guardrails.py -v
pytest tests/test_llm_quality_checks.py -v

# Run specific test
pytest tests/test_llm_guardrails.py::TestHashtagValidation -v
```

**Test coverage**:
- ✅ Hashtag extraction
- ✅ Hashtag count validation
- ✅ Forbidden word detection
- ✅ URL contamination check
- ✅ Hallucination detection
- ✅ Emoji counting
- ✅ Profanity detection
- ✅ Deduplication logic
- ✅ Quality scoring
- ✅ Platform-specific validation
- ✅ Username hashtag removal
- ✅ Multiple issues reporting
- ✅ Case-insensitive matching
- ✅ Edge cases

## Performance Impact

**Minimal**: Validation adds ~1ms per message.

**Retry overhead**: If validation fails (~5-10% of cases), one additional API call is made:
- **Ollama**: 1-3 seconds (local, depends on model size)
- **Gemini**: 0.5-1 second (cloud API)

**Trade-off**: Slightly longer generation time (when retry needed) for significantly better quality.

## When Guardrails Activate

Based on real-world testing with small LLMs (2B-4B params):

- **Hashtag count issues**: ~8% of generations
- **Forbidden words**: ~3% of generations
- **Hallucinations**: ~1-2% of generations
- **URL contamination**: <1% of generations
- **Username hashtags**: ~2% of generations

**Total retry rate**: ~10-12% of messages trigger auto-retry.

**Retry success rate**: ~70% of retries produce valid messages.

## Best Practices

1. **Use sensible generation parameters**:
   ```bash
   # Lower temperature = more consistent
   LLM_TEMPERATURE=0.3
   
   # Limit output length
   LLM_MAX_TOKENS=150
   ```

2. **Monitor logs** for frequent validation failures:
   ```bash
   # Check for quality issues
   grep "quality issues" logs/boon-tube-daemon.log
   
   # Check for validation retries
   grep "Retrying with stricter" logs/boon-tube-daemon.log
   ```

3. **Test with your specific video titles**:
   - Some topics trigger more issues than others
   - Generic titles ("Tutorial", "Guide") are harder for small LLMs
   - Specific titles ("Building a Gaming PC") work better

4. **Consider larger models** if issues persist:
   - 7B+ params have much better instruction following
   - Gemini Flash (cloud) is very reliable
   - Ollama with llama3.2:3b or gemma2:9b works well

## Limitations

These guardrails are **post-generation checks**, not perfect prevention:

- **Can't fix everything**: Some issues are unfixable without regenerating (which we do via retry)
- **Tone/style issues**: Can't validate if message sounds "genuine" or "engaging"
- **Context appropriateness**: Can't know if message is appropriate for the actual video content
- **Language/grammar**: No spelling or grammar checking (though LLMs are usually good at this)

For maximum quality, consider:
- Using larger models (7B+)
- Cloud LLMs (Gemini) for critical announcements
- Manual messages for important videos
- Custom notification templates

## The Bigger Picture (A Carlin Rant)

Let's step back and appreciate the absurdity of what we've built here:

We created **artificial intelligence** - machines that can understand language, generate text,
and communicate with humans. This is science fiction shit. This is Star Trek.

And what are we using it for? To announce when someone uploads a fucking YouTube video.

Then, because the AI isn't quite good enough at pretending to be excited about PC tutorials,
we built **TEN DIFFERENT SYSTEMS** to check its work:

1. Count the hashtags (can you count to three, robot?)
2. Check for forbidden words (don't say EPIC!)
3. Verify it didn't make shit up (no, there's no giveaway)
4. Make sure it's not using too many emojis (you're not 12)
5. Check for duplicate messages (variety is the spice of life)
6. Filter out profanity (even though this code is full of it)
7. Grade its quality (C+, try harder)
8. Validate platform-specific bullshit (because nothing can be simple)
9. Remove URLs it shouldn't have included (reading comprehension: F)
10. Check username hashtags (don't use the person's name, dipshit)

We've built an artificial intelligence babysitter. An AI nanny. A robot chaperone.

**And it's all so you don't have to manually post "new video!" on Discord every time you upload.**

This is either the pinnacle of human achievement or proof that we've lost the fucking plot.
I honestly can't tell anymore.

But hey, at least the code comments are funny.

---

## Advanced Features

### Sophisticated Prompt Engineering

Because apparently we need to write fucking instruction manuals for robots to announce YouTube videos.

The prompt system uses **step-by-step instructions, examples, and anti-cringe warnings** designed for small LLMs (2B-4B params) that need their hands held like toddlers learning to write.

**Features**:
- ✅ Step-by-step task breakdown (STEP 1: Do X, STEP 2: Do Y)
- ✅ Good/bad examples showing proper format
- ✅ Explicit "DO NOT" warnings for common mistakes
- ✅ Strict mode for retries (⚠️ CRITICAL: FOLLOW INSTRUCTIONS)
- ✅ Platform-specific templates (Discord, Bluesky, Mastodon, Matrix)

**Example Prompt Structure**:
```
TASK: Write a short post for this video.

STEP 1 - CONTENT RULES:
✓ Length: MUST be 250 characters or less
✓ Tone: Casual, friendly
✗ DO NOT use cringe words: "INSANE", "EPIC", "CRAZY"
✗ DO NOT include URLs (added automatically)

STEP 2 - HASHTAG RULES:
You MUST include EXACTLY 3 hashtags.
Count: 1, 2, 3. Not 2. Not 4. Exactly 3.

EXAMPLES:
Good: "New PC build guide! #PC #Hardware #Tutorial"
Bad: "EPIC video! #INSANE #HYPE" (cringe words)

NOW: Write the post...
```

**Why this works**: Small LLMs learn by imitation. Show them examples, they copy the pattern. Tell them "count to three," they might give you four. Show them "1, 2, 3 hashtags. Not 2. Not 4. Exactly 3," suddenly they can count.

It's like teaching a dog to shake hands, but the dog is a billion-parameter neural network that cost millions to train. Progress!

### Quality Scoring System (Optional)

We're literally grading the AI's homework. Like it's in school.

**Scoring Criteria (1-10 scale)**:
- **10**: Perfect (natural, engaging, unique)
- **7-9**: Good (clear, interesting)  
- **4-6**: Mediocre (generic, boring)
- **1-3**: Bad (very generic, poor grammar)

**What Gets Points Deducted**:
- Too many generic phrases ("check it out", "new video") → -2 points
- Too short (<4 words) or too long (>30 words) → -2-3 points
- Repeated words (>30% repeats) → -2 points
- No reference to title/content → -3 points
- No personality (no punctuation variety/emoji) → -1 point

**Configuration**:
```ini
[LLM]
enable_quality_scoring = True
min_quality_score = 6  # Reject messages scoring below this
```

**Example**:
```python
message = "New video! Check it out! #PC #Hardware #Tutorial"
score, issues = validator.score_message_quality(message, title)
# Score: 5/10
# Issues: ['Too many generic phrases (2)', 'Too short (feels lazy)']
```

**George says**: "We're teaching a computer to grade another computer's writing. Then we judge BOTH of them. This is what we've become. Quality control for artificial enthusiasm. I could do 30 minutes on this shit alone."

### Deduplication Cache

Because variety is the spice of life, even for robot-generated bullshit.

**Purpose**: Prevents posting nearly identical messages multiple times.

**How It Works**:
- Maintains a cache of recent messages (default: last 20)
- Compares new messages to cache using word overlap
- Rejects if >80% similar to a recent message
- FIFO queue (old messages drop off)

**Configuration**:
```ini
[LLM]
enable_deduplication = True
dedup_cache_size = 20
```

**Example Deduplication**:
```python
# Message 1: "New PC building tutorial! #PC #Hardware #Tutorial"
# Message 2: "New PC building guide! #PC #Hardware #Tutorial"
# → 85% similar, REJECTED

# Message 3: "Complete motherboard installation guide! #PC #Hardware #Tutorial"  
# → 45% similar, ACCEPTED
```

**Why This Matters**: Without deduplication, you can get repetitive posts:
```
❌ "New video is up! #PC #Hardware #Tutorial"
❌ "New video is live! #PC #Hardware #Tutorial"  
❌ "Latest video posted! #PC #Hardware #Tutorial"
```

All saying the same thing with slightly different words. Boring as fuck.

With deduplication:
```
✅ "New PC building tutorial! #PC #Hardware #Tutorial"
✅ "Complete guide to motherboard installation! #PC #Hardware #Tutorial"
✅ "Step-by-step RAM upgrade walkthrough! #PC #Hardware #Tutorial"
```

Variety! Excitement! Or at least not putting your audience to sleep with identical posts!

### Username Tokenization (Advanced)

CamelCase splitting, underscore handling, partial matches - the whole smart username detection system.

**Handles Various Username Formats**:
- **CamelCase**: `TechCreator99` → `['tech', 'creator', '99', 'techcreator', 'techcreator99']`
- **Underscores**: `Tech_Creator_99` → `['tech', 'creator', 'tech_creator_99']`
- **Mixed**: `Cool_Gamer123` → `['cool', 'gamer', '123', 'coolgamer', 'coolgamer123']`
- **Partial Matches**: Catches username parts in longer hashtags

**Why Complex Tokenization**:
Simple check: Does hashtag == username? Too easy to bypass.

Smart check: Does hashtag contain any username parts? Catches:
- Username: `TechCreator` → Blocks `#TechCreatorGaming`, `#CreatorTech`, `#TechTips`
- Username: `GameDev_Pro` → Blocks `#GameDev`, `#ProGaming`, `#GameDevPro`

**George says**: "We wrote an algorithm to parse usernames like we're the NSA tracking terrorists. Except instead of national security, we're just trying to stop robots from using someone's name as a hashtag. Priorities."

---

*"We created machines that can think, but we still need to teach them not to be assholes."*  
*- The Ghost of George Carlin, somewhere laughing his spectral ass off*

## Summary

The LLM guardrail system provides **automatic quality enforcement** with:

✅ **Post-generation validation** - Catches common AI mistakes  
✅ **Auto-retry with strict mode** - Second chance for better output  
✅ **Comprehensive logging** - Clear visibility into issues  
✅ **Minimal performance impact** - <1ms validation, ~10% retry rate  
✅ **Sensible defaults** - Works out of the box  
✅ **Configurable guardrails** - Enable/disable as needed

Combined with well-tuned generation parameters and good prompts, this creates a robust system for reliable AI-generated video notifications that don't sound like they were written by a clickbait-loving robot with a counting problem.

---

*"Teaching robots to write is easy. Teaching them to write WELL? That's the hard part. Teaching them not to spam hashtags and say 'EPIC' every five seconds? Apparently fucking impossible without 10 layers of validation. Welcome to the future."* - George Carlin's Ghost, 2026
