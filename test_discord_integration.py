#!/usr/bin/env python3
"""
Integration test for Discord notifications with real YouTube/TikTok content.

This test uses the actual media monitoring modules to fetch real content
and test Discord notifications with per-platform webhooks and roles.

Usage:
    python3 test_discord_integration.py
"""

import logging
import sys
from dotenv import load_dotenv

# Load .env for configuration
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Import actual modules
from boon_tube_daemon.social.discord import DiscordPlatform
from boon_tube_daemon.media.youtube_videos import YouTubeVideosPlatform
from boon_tube_daemon.media.tiktok import TikTokPlatform


def test_discord_with_youtube():
    """Test Discord with real YouTube content."""
    print("\n" + "="*70)
    print("🎬 Testing Discord with Real YouTube Content")
    print("="*70)
    
    # Initialize YouTube monitoring
    print("\n1. Initializing YouTube monitoring...")
    youtube = YouTubeVideosPlatform()
    
    if not youtube.authenticate():
        print("   ✗ YouTube authentication failed")
        print("   Check YOUTUBE_API_KEY in Doppler and YOUTUBE_USERNAME in .env")
        return False
    
    print(f"   ✓ YouTube authenticated for channel: {youtube.channel_id}")
    
    # Get latest video
    print("\n2. Fetching latest YouTube video...")
    has_new, latest_video = youtube.check_for_new_video()
    
    if not latest_video:
        print("   ⚠ No video found (channel may be empty or API error)")
        return False
    
    print(f"   ✓ Found video: {latest_video['title']}")
    print(f"   Video ID: {latest_video['video_id']}")
    print(f"   URL: {latest_video['url']}")
    print(f"   Is New: {has_new}")
    
    # Initialize Discord
    print("\n3. Initializing Discord...")
    discord = DiscordPlatform()
    
    if not discord.authenticate():
        print("   ✗ Discord authentication failed")
        return False
    
    print("   ✓ Discord authenticated")
    if 'youtube' in discord.webhook_urls:
        print("   • Using YouTube-specific webhook")
    else:
        print("   • Using default webhook")
    
    if 'youtube' in discord.role_mentions:
        print(f"   • Will mention YouTube role: {discord.role_mentions['youtube']}")
    elif discord.role_id:
        print(f"   • Will mention default role: {discord.role_id}")
    
    # Format notification message
    print("\n4. Posting to Discord with platform_name='youtube'...")
    
    # Build message - only include stats if they exist and are valid
    message = f"""🎬 New YouTube video!

**{latest_video['title']}**

{latest_video['url']}"""
    
    # Only add stats line if we have real data
    stats = []
    views = latest_video.get('view_count')
    if views and str(views).isdigit() and int(views) > 0:
        stats.append(f"📊 {int(views):,} views")
    
    likes = latest_video.get('like_count')
    if likes and str(likes).isdigit() and int(likes) > 0:
        stats.append(f"👍 {int(likes):,} likes")
    
    if stats:
        message += f"\n\n{' | '.join(stats)}"
    
    # Post with platform_name='youtube' to trigger YouTube-specific webhook/role
    message_id = discord.post(
        message, 
        platform_name='youtube',
        stream_data=latest_video
    )
    
    if message_id:
        print(f"   ✓ Posted to Discord successfully!")
        print(f"   Message ID: {message_id}")
        return True
    else:
        print("   ✗ Discord post failed")
        return False


def test_discord_with_tiktok():
    """Test Discord with real TikTok content."""
    print("\n" + "="*70)
    print("📱 Testing Discord with Real TikTok Content")
    print("="*70)
    
    # Initialize TikTok monitoring
    print("\n1. Initializing TikTok monitoring...")
    tiktok = TikTokPlatform()
    
    if not tiktok.authenticate():
        print("   ✗ TikTok authentication failed")
        print("   Check TIKTOK_USERNAME in .env")
        return False
    
    print(f"   ✓ TikTok authenticated for user: {tiktok.username}")
    
    # Get latest video
    print("\n2. Fetching latest TikTok video...")
    print("   ⏳ This may take 10-15 seconds (loading browser)...")
    
    has_new, latest_video = tiktok.check_for_new_video()
    
    if not latest_video:
        print("   ⚠ No video found (user may have no videos or network error)")
        return False
    
    print(f"   ✓ Found video: {latest_video['title'][:60]}...")
    print(f"   Video ID: {latest_video['video_id']}")
    print(f"   URL: {latest_video['url']}")
    print(f"   Is New: {has_new}")
    
    # Initialize Discord
    print("\n3. Initializing Discord...")
    discord = DiscordPlatform()
    
    if not discord.authenticate():
        print("   ✗ Discord authentication failed")
        return False
    
    print("   ✓ Discord authenticated")
    if 'tiktok' in discord.webhook_urls:
        print("   • Using TikTok-specific webhook")
    else:
        print("   • Using default webhook")
    
    if 'tiktok' in discord.role_mentions:
        print(f"   • Will mention TikTok role: {discord.role_mentions['tiktok']}")
    elif discord.role_id:
        print(f"   • Will mention default role: {discord.role_id}")
    
    # Format notification message
    print("\n4. Posting to Discord with platform_name='tiktok'...")
    
    # Build message - only include stats if they exist and are valid
    message = f"""📱 New TikTok!

**{latest_video['title'][:100]}**

{latest_video['url']}"""
    
    # Only add stats line if we have real data
    stats = []
    likes = latest_video.get('like_count')
    if likes and str(likes).isdigit() and int(likes) > 0:
        stats.append(f"❤️ {int(likes):,}")
    
    views = latest_video.get('view_count')
    if views and str(views).isdigit() and int(views) > 0:
        stats.append(f"� {int(views):,}")
    
    if stats:
        message += f"\n\n{' | '.join(stats)}"
    
    # Post with platform_name='tiktok' to trigger TikTok-specific webhook/role
    message_id = discord.post(
        message,
        platform_name='tiktok',
        stream_data=latest_video
    )
    
    if message_id:
        print(f"   ✓ Posted to Discord successfully!")
        print(f"   Message ID: {message_id}")
        return True
    else:
        print("   ✗ Discord post failed")
        return False


def main():
    print("🧪 Boon-Tube-Daemon Discord Integration Test")
    print("Testing with REAL content from YouTube and TikTok")
    print("This will post actual notifications to your Discord server!\n")
    
    results = {}
    
    # Test YouTube
    try:
        results['YouTube'] = test_discord_with_youtube()
    except Exception as e:
        print(f"\n✗ YouTube test failed with error: {e}")
        import traceback
        traceback.print_exc()
        results['YouTube'] = False
    
    # Wait between tests
    print("\n⏸️  Waiting 3 seconds before TikTok test...\n")
    import time
    time.sleep(3)
    
    # Test TikTok
    try:
        results['TikTok'] = test_discord_with_tiktok()
    except Exception as e:
        print(f"\n✗ TikTok test failed with error: {e}")
        import traceback
        traceback.print_exc()
        results['TikTok'] = False
    
    # Summary
    print("\n" + "="*70)
    print("📊 Integration Test Summary")
    print("="*70)
    
    for platform, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{platform:12} {status}")
    
    print("\n")
    
    if all(results.values()):
        print("🎉 All tests passed! Check your Discord server for:")
        print("   • YouTube notification (with @YouTube role mention if configured)")
        print("   • TikTok notification (with @TikTok role mention if configured)")
        print("\n✓ Per-platform webhooks and roles are working correctly!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    # Exit code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
