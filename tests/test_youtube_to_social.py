#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test script for YouTube → Social platforms integration.
Fetches latest YouTube video and posts to all enabled social platforms.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from boon_tube_daemon.utils.config import load_config, get_bool_config
from boon_tube_daemon.media.youtube_videos import YouTubeVideosPlatform
from boon_tube_daemon.social.bluesky import BlueskyPlatform
from boon_tube_daemon.social.mastodon import MastodonPlatform
from boon_tube_daemon.social.discord import DiscordPlatform
from boon_tube_daemon.social.matrix import MatrixPlatform

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def format_youtube_message(video_data: dict) -> str:
    """Format a YouTube video notification message."""
    title = video_data.get('title', 'Untitled')
    url = video_data.get('url', '')
    
    message = f"🎬 New YouTube Video!\n\n{title}\n\n{url}\n\n#YouTube #NewVideo"
    return message


def main():
    print("\n" + "="*70)
    print("🧪 YouTube → Social Platforms Integration Test")
    print("="*70)
    
    # Load configuration
    print("\n📋 Loading configuration...")
    load_config()
    print("✓ Configuration loaded")
    
    # Initialize YouTube
    print("\n📺 Initializing YouTube...")
    youtube = YouTubeVideosPlatform()
    if not youtube.authenticate():
        print("✗ YouTube authentication failed!")
        return False
    print(f"✓ YouTube authenticated (channel: {youtube.channel_id})")
    
    # Fetch latest video
    print("\n📹 Fetching latest video...")
    success, video_data = youtube.get_latest_video()
    if not success or not video_data:
        print("✗ Failed to fetch YouTube video!")
        return False
    
    print(f"✓ Retrieved video: {video_data['title'][:60]}...")
    print(f"  URL: {video_data['url']}")
    print(f"  Views: {video_data.get('view_count', 0):,}")
    
    # Format message
    message = format_youtube_message(video_data)
    print(f"\n📝 Formatted message:")
    print("-" * 70)
    print(message)
    print("-" * 70)
    
    # Initialize and test social platforms
    social_platforms = []
    
    print("\n📢 Initializing social platforms...")
    
    # Bluesky
    if get_bool_config('Bluesky', 'enable_posting', default=False):
        bluesky = BlueskyPlatform()
        if bluesky.authenticate():
            social_platforms.append(bluesky)
        else:
            print("  ⚠ Bluesky authentication failed")
    else:
        print("  ⊘ Bluesky posting disabled")
    
    # Mastodon
    if get_bool_config('Mastodon', 'enable_posting', default=False):
        mastodon = MastodonPlatform()
        if mastodon.authenticate():
            social_platforms.append(mastodon)
        else:
            print("  ⚠ Mastodon authentication failed")
    else:
        print("  ⊘ Mastodon posting disabled")
    
    # Discord
    if get_bool_config('Discord', 'enable_posting', default=False):
        discord = DiscordPlatform()
        if discord.authenticate():
            social_platforms.append(discord)
        else:
            print("  ⚠ Discord authentication failed")
    else:
        print("  ⊘ Discord posting disabled")
    
    # Matrix
    if get_bool_config('Matrix', 'enable_posting', default=False):
        matrix = MatrixPlatform()
        if matrix.authenticate():
            social_platforms.append(matrix)
        else:
            print("  ⚠ Matrix authentication failed")
    else:
        print("  ⊘ Matrix posting disabled")
    
    if not social_platforms:
        print("\n⚠ No social platforms enabled!")
        print("Enable platforms in .env:")
        print("  BLUESKY_ENABLE_POSTING=true")
        print("  MASTODON_ENABLE_POSTING=true")
        print("  DISCORD_ENABLE_POSTING=true")
        print("  MATRIX_ENABLE_POSTING=true")
        return False
    
    print(f"\n✓ {len(social_platforms)} platform(s) enabled")
    
    # Post to all platforms
    print("\n📤 Posting to social platforms...")
    success_count = 0
    
    for platform in social_platforms:
        try:
            print(f"\n  Posting to {platform.name}...")
            result = platform.post(
                message=message,
                platform_name="youtube",
                stream_data=video_data
            )
            
            if result:
                print(f"  ✓ Posted to {platform.name} (ID: {result})")
                success_count += 1
            else:
                print(f"  ✗ Failed to post to {platform.name}")
                
        except Exception as e:
            print(f"  ✗ Error posting to {platform.name}: {e}")
            logger.exception(f"Error posting to {platform.name}")
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    print(f"YouTube: ✓ Fetched latest video")
    print(f"Social Platforms: {success_count}/{len(social_platforms)} successful")
    
    if success_count == len(social_platforms):
        print("\n✅ All tests passed!")
        return True
    elif success_count > 0:
        print("\n⚠ Some platforms failed")
        return False
    else:
        print("\n✗ All platforms failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
