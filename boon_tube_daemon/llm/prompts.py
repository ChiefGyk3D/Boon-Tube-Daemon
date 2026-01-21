# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Advanced prompt templates for LLM message generation.

Because apparently we need to write a fucking instruction manual for robots
to sound like humans announcing YouTube videos.

These prompts use step-by-step instructions, examples, and anti-cringe warnings
because small LLMs (2B-4B params) need their hands held like toddlers learning to write.

George Carlin would've had a field day: "We built machines that can process billions
of operations per second, but we still need to tell them 'Don't say INSANE!' like
we're teaching a teenager not to embarrass themselves on TikTok."
"""


def build_video_notification_prompt(
    platform_name: str,
    creator_name: str,
    title: str,
    description: str,
    social_platform: str,
    max_chars: int,
    use_hashtags: bool = True,
    strict_mode: bool = False
) -> str:
    """
    Build sophisticated prompt for video notifications with step-by-step instructions.
    
    Designed for small LLMs with explicit constraints to prevent hallucinations.
    Uses examples for better enforcement because AI learns by copying, not understanding.
    
    Args:
        platform_name: Source platform (YouTube, TikTok, etc.)
        creator_name: Creator's username
        title: Video title
        description: Video description (already cleaned/truncated)
        social_platform: Target platform (discord, bluesky, mastodon, matrix)
        max_chars: Maximum character count
        use_hashtags: Whether to include hashtags
        strict_mode: If True, adds extra emphasis (used for retries)
    
    Returns:
        Formatted prompt string
        
    This is peak human achievement: Writing essays to teach robots how to count to three.
    """
    strict_prefix = ""
    if strict_mode:
        strict_prefix = """⚠️ CRITICAL: Previous attempt violated rules. FOLLOW INSTRUCTIONS EXACTLY. ⚠️

"""
    
    hashtag_count = 3 if use_hashtags and social_platform in ['bluesky', 'mastodon'] else 0
    hashtag_instruction = ""
    
    if hashtag_count > 0:
        hashtag_instruction = f"""
STEP 2 - HASHTAG RULES (CRITICAL):
You MUST include EXACTLY {hashtag_count} hashtags at the end.

Count: 1, 2, 3 hashtags. Not 2. Not 4. Exactly {hashtag_count}.
(Yes, we have to teach a computer how to count. Welcome to the future.)

Hashtag source rules:
- Extract hashtags ONLY from words in the video title: "{title}"
- NEVER use the creator name "{creator_name}" or any part of it as a hashtag
- NEVER use generic tags (#Gaming, #Live, #Video) unless in the title
- Format: space before each hashtag
- SHORT hashtags only: #Tech not #TechnologyReview"""
    
    examples = ""
    if social_platform == 'bluesky':
        examples = f"""
EXAMPLES:

Example 1:
Title: "How to Build a Gaming PC"
Good post: "New guide on building your first gaming PC! Perfect for beginners 🖥️ #Gaming #PC #Tutorial"
({hashtag_count} hashtags from title words)

Example 2:
Title: "Cooking Easy Pasta Carbonara"
Good post: "Just dropped a super easy carbonara recipe! #Cooking #Pasta #Recipe"
({hashtag_count} hashtags from title)

Bad examples to AVOID:
✗ "INSANE new video! EPIC build guide!" (cringe words)
✗ "Check out my video #Subscribe #Like" (generic tags, not from title)
✗ Using only 2 hashtags or using 4+ hashtags"""

    elif social_platform == 'mastodon':
        examples = f"""
EXAMPLES:

Example 1:
Title: "Linux Server Setup for Beginners"
Good post: "New video: Setting up your first Linux server! Step-by-step guide for beginners #Linux #Server #Tutorial"
({hashtag_count} hashtags)

Example 2:
Title: "Photography Tips - Golden Hour Shooting"
Good post: "Just uploaded tips for shooting during golden hour! Check it out 📸 #Photography #Tips #GoldenHour"
({hashtag_count} hashtags)

Bad examples to AVOID:
✗ "MUST WATCH! Amazing tutorial!" (clickbait, no real content)
✗ "New video is live! #YouTube #NewVideo #Content" (generic tags)"""
    
    elif social_platform == 'discord':
        examples = """
EXAMPLES:

Example 1:
Title: "Minecraft Survival Series - Episode 5"
Good post: "Episode 5 of the survival series is up! Building the mega base continues 🏰"
(No hashtags, conversational)

Example 2:
Title: "Speedrun World Record Attempt"
Good post: "Just posted my world record attempt run! It was intense"
(Casual, no hashtags)

Bad examples to AVOID:
✗ "Hey Discord! New video!" (greeting waste)
✗ "Check it out at youtube.com/watch?v=FAKE_ID" (no placeholder URLs)"""
    
    elif social_platform == 'matrix':
        examples = """
EXAMPLES:

Example 1:
Title: "Software Tutorial - Getting Started with Docker"
Good post: "New Docker tutorial for beginners. Covers installation and first containers."
(Professional, no hashtags)

Example 2:
Title: "Game Review - Latest RPG Analysis"
Good post: "Posted my analysis of the new RPG. Spoiler-free review with gameplay insights."
(Informative, no hashtags)"""
    
    return f"""{strict_prefix}You are a social media assistant that writes {social_platform.title()} posts announcing new {platform_name} videos.

TASK: Write a SHORT, engaging post for this new video by {creator_name}.

VIDEO TITLE: "{title}"
VIDEO DESCRIPTION: {description}

STEP 1 - CONTENT RULES (FOLLOW EXACTLY):
✓ Length: MUST be {max_chars} characters or less (this is NON-NEGOTIABLE)
✓ Output: ONLY the post text (no quotes, no labels, no "Here's...")
✓ Tone: Casual, friendly, genuine (like a real person, not a bot)
✓ Content: Focus on what the video is about based on the title
✓ Emoji: Use 0-1 emoji maximum (optional, don't spam)
✗ DO NOT include the URL (it's added automatically)
✗ DO NOT invent details not in title/description (no "special guests", "limited time", "tonight at 7pm")
✗ DO NOT use cringe words: "INSANE", "EPIC", "CRAZY", "UNMISSABLE", "smash that"
✗ DO NOT use greetings like "Hey everyone!" or "What's up {social_platform}!" - just get to the content{hashtag_instruction}{examples}

NOW: Write the post for "{title}". Remember: {"exactly " + str(hashtag_count) + " hashtags, " if hashtag_count > 0 else ""}under {max_chars} characters, NO URLs.

Post:"""


def build_stream_start_prompt(
    platform_name: str,
    username: str,
    title: str,
    content_max: int,
    strict_mode: bool = False
) -> str:
    """
    Build optimized prompt for stream start messages (live notifications).
    
    This is for when someone goes LIVE (streaming), not uploading a video.
    Different energy, different phrasing.
    
    Args:
        platform_name: Streaming platform (Twitch, YouTube, Kick)
        username: Streamer username
        title: Stream title
        content_max: Maximum character count for generated content
        strict_mode: If True, adds extra emphasis for rule compliance
    
    Returns:
        Formatted prompt string
    """
    strict_prefix = ""
    if strict_mode:
        strict_prefix = """⚠️ CRITICAL: Previous attempt violated rules. FOLLOW INSTRUCTIONS EXACTLY. ⚠️

"""
    
    return f"""{strict_prefix}You are a social media assistant that writes go-live stream announcements.

TASK: Write a short, engaging post announcing that {username} is live on {platform_name}.

STREAM TITLE: "{title}"

STEP 1 - CONTENT RULES (FOLLOW EXACTLY):
✓ Length: MUST be {content_max} characters or less
✓ Output: ONLY the post text (no quotes, no meta-commentary, no labels)
✓ Tone: Casual, friendly, genuine (like a real person, not a bot)
✓ Call-to-action: Include ONE phrase like "come hang out", "join me", or "let's go"
✓ Emoji: Use 0-1 emoji maximum (optional)
✗ DO NOT include the URL (it's added automatically)
✗ DO NOT invent details not in the title (no "drops enabled", "giveaways", "tonight at 7pm")
✗ DO NOT use cringe words: "INSANE", "EPIC", "smash that", "UNMISSABLE"

STEP 2 - HASHTAG RULES (CRITICAL):
You MUST include EXACTLY 3 hashtags at the end.

Count: 1, 2, 3 hashtags. Not 2. Not 4. Exactly 3.

Hashtag source rules:
- Extract hashtags ONLY from words in the stream title: "{title}"
- NEVER use the username "{username}" or any part of it as a hashtag
- NEVER use generic tags (#Gaming, #Live, #Stream) unless in the title
- Format: space before each hashtag

EXAMPLES:

Example 1:
Title: "Minecraft Creative Building"
Good post: "Building something cool in Minecraft! Come hang out and share ideas 🏗️ #Minecraft #Creative #Building"

Example 2:
Title: "Valorant Competitive"
Good post: "Ranked grind time! Let's climb together #Valorant #Competitive #FPS"

Bad examples to AVOID:
✗ "Epic stream starting NOW! #LIVE #INSANE #HYPE" (cringe words, generic tags)
✗ Using only 2 hashtags or using 4+ hashtags

NOW: Write the post for "{title}" on {platform_name}. Remember: exactly 3 hashtags, under {content_max} characters.

Post:"""
