#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Automatic test script for posting to all configured platforms.
Posts automatically without user confirmation.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from boon_tube_daemon.utils.config import load_config
import os
from boon_tube_daemon.media.youtube_videos import YouTubeVideosPlatform
from boon_tube_daemon.social.discord import DiscordPlatform
from boon_tube_daemon.social.matrix import MatrixPlatform
from boon_tube_daemon.social.bluesky import BlueskyPlatform
from boon_tube_daemon.social.mastodon import MastodonPlatform
from boon_tube_daemon.llm.gemini import GeminiLLM

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("\n" + "="*70)
    print("🚀 Automatic Multi-Platform Posting Test")
    print("="*70)
    
    # Load configuration
    print("\n📋 Loading configuration...")
    load_config()
    print("✓ Configuration loaded")
    
    # Show configured styles
    print("\n🎨 Configured Posting Styles:")
    print(f"  • Discord:  {os.getenv('DISCORD_POST_STYLE', 'conversational')}")
    print(f"  • Matrix:   {os.getenv('MATRIX_POST_STYLE', 'professional')}")
    print(f"  • Bluesky:  {os.getenv('BLUESKY_POST_STYLE', 'conversational')}")
    print(f"  • Mastodon: {os.getenv('MASTODON_POST_STYLE', 'detailed')}")
    
    # Initialize YouTube to get real video data
    print("\n📺 Fetching latest YouTube video...")
    youtube = YouTubeVideosPlatform()
    if not youtube.authenticate():
        print("✗ YouTube authentication failed!")
        return False
    
    success, video_data = youtube.get_latest_video()
    if not success or not video_data:
        print("✗ Failed to fetch YouTube video!")
        return False
    
    print(f"✓ Retrieved video: {video_data['title'][:60]}...")
    print(f"  Video ID: {video_data['video_id']}")
    print(f"  URL: {video_data['url']}")
    
    # Initialize LLM if enabled
    llm = None
    if os.getenv('LLM_ENABLE') == 'true' and os.getenv('LLM_ENHANCE_NOTIFICATIONS') == 'true':
        print("\n🤖 Initializing Gemini LLM for enhanced posts...")
        llm = GeminiLLM()
        if llm.authenticate():
            print("✓ Gemini LLM initialized")
        else:
            print("⚠ LLM authentication failed, will use basic posts")
            llm = None
    else:
        print("\n⚠ LLM enhancement disabled, using basic posts")
    
    # Initialize platforms
    platforms = {}
    
    # Discord
    if os.getenv('DISCORD_ENABLE_POSTING') == 'true':
        print("\n🔷 Initializing Discord...")
        discord = DiscordPlatform()
        if discord.authenticate():
            platforms['discord'] = discord
            print("✓ Discord ready")
        else:
            print("✗ Discord authentication failed")
    
    # Matrix
    if os.getenv('MATRIX_ENABLE_POSTING') == 'true':
        print("\n🟪 Initializing Matrix...")
        matrix = MatrixPlatform()
        if matrix.authenticate():
            platforms['matrix'] = matrix
            print("✓ Matrix ready")
        else:
            print("✗ Matrix authentication failed")
    
    # Bluesky
    if os.getenv('BLUESKY_ENABLE_POSTING') == 'true':
        print("\n🟦 Initializing Bluesky...")
        bluesky = BlueskyPlatform()
        if bluesky.authenticate():
            platforms['bluesky'] = bluesky
            print("✓ Bluesky ready")
        else:
            print("✗ Bluesky authentication failed")
    
    # Mastodon
    if os.getenv('MASTODON_ENABLE_POSTING') == 'true':
        print("\n🟣 Initializing Mastodon...")
        mastodon = MastodonPlatform()
        if mastodon.authenticate():
            platforms['mastodon'] = mastodon
            print("✓ Mastodon ready")
        else:
            print("✗ Mastodon authentication failed")
    
    if not platforms:
        print("\n✗ No platforms are configured and authenticated!")
        return False
    
    print(f"\n✓ {len(platforms)} platform(s) ready to test")
    
    # Post to each platform automatically
    print("\n" + "="*70)
    print("📤 Posting to platforms (automatic)...")
    print("="*70)
    
    results = {}
    
    for platform_name, platform in platforms.items():
        print(f"\n{'='*70}")
        print(f"Platform: {platform_name.upper()}")
        print('='*70)
        
        # Generate message
        if llm:
            style = os.getenv(f'{platform_name.upper()}_POST_STYLE', 'conversational')
            print(f"🎨 Style: {style}")
            message = llm.enhance_notification(
                video_data,
                'YouTube',
                platform_name
            )
        else:
            # Basic message
            message = f"🎬 New YouTube video!\n\n{video_data['title']}\n\n{video_data['url']}"
        
        if not message:
            print(f"✗ Failed to generate message for {platform_name}")
            results[platform_name] = False
            continue
        
        print(f"\n📝 Generated message ({len(message)} chars):")
        print("-" * 70)
        print(message)
        print("-" * 70)
        
        # Post automatically
        try:
            print(f"\n📤 Posting to {platform_name}...")
            success = platform.post(
                message=message,
                platform_name='youtube',
                stream_data=video_data
            )
            
            if success:
                print(f"✅ Successfully posted to {platform_name}!")
                results[platform_name] = True
            else:
                print(f"✗ Failed to post to {platform_name}")
                results[platform_name] = False
                
        except Exception as e:
            print(f"✗ Error posting to {platform_name}: {e}")
            logger.exception(f"Error posting to {platform_name}")
            results[platform_name] = False
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Results Summary")
    print("="*70)
    
    for platform_name, result in results.items():
        status = "✅ SUCCESS" if result else "✗ FAILED"
        print(f"  {platform_name.upper():10s} {status}")
    
    successful = sum(1 for r in results.values() if r is True)
    print(f"\n✓ {successful}/{len(platforms)} platforms posted successfully")
    
    return successful > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
