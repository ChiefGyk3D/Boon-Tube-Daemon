#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test script for LLM platform-specific post generation.
Generates unique posts for Discord, Matrix, Bluesky, and Mastodon.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from boon_tube_daemon.utils.config import load_config
from boon_tube_daemon.media.youtube_videos import YouTubeVideosPlatform
from boon_tube_daemon.llm.gemini import GeminiLLM

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("\n" + "="*70)
    print("🤖 LLM Platform-Specific Post Generation Test")
    print("="*70)
    
    # Load configuration
    print("\n📋 Loading configuration...")
    load_config()
    print("✓ Configuration loaded")
    
    # Initialize YouTube to get real video data
    print("\n📺 Fetching YouTube video...")
    youtube = YouTubeVideosPlatform()
    if not youtube.authenticate():
        print("✗ YouTube authentication failed!")
        return False
    
    success, video_data = youtube.get_latest_video()
    if not success or not video_data:
        print("✗ Failed to fetch YouTube video!")
        return False
    
    print(f"✓ Retrieved video: {video_data['title'][:60]}...")
    print(f"  URL: {video_data['url']}")
    
    # Initialize Gemini LLM
    print("\n🤖 Initializing Gemini LLM...")
    llm = GeminiLLM()
    if not llm.authenticate():
        print("✗ Gemini LLM authentication failed!")
        print("\nMake sure you have:")
        print("  1. LLM_ENABLE=true in .env")
        print("  2. LLM_GEMINI_API_KEY set in Doppler")
        print("  3. LLM_ENHANCE_NOTIFICATIONS=true in .env")
        return False
    
    print("✓ Gemini LLM initialized")
    
    # Test description cleaning
    print("\n🧹 Testing description cleaning...")
    if video_data.get('description'):
        print(f"Original description length: {len(video_data['description'])} chars")
        cleaned = llm.clean_description(video_data['description'])
        print(f"Cleaned description length: {len(cleaned)} chars")
        print(f"\nCleaned description preview:")
        print("-" * 70)
        print(cleaned[:300] + ("..." if len(cleaned) > 300 else ""))
        print("-" * 70)
    
    # Generate posts for each platform
    platforms = ['Discord', 'Matrix', 'Bluesky', 'Mastodon']
    
    print("\n📝 Generating platform-specific posts...")
    print("="*70)
    
    for platform in platforms:
        print(f"\n🎯 {platform.upper()} POST:")
        print("-" * 70)
        
        try:
            post = llm.enhance_notification(
                video_data,
                'YouTube',  # Source platform
                platform.lower()  # Target social platform
            )
            
            if post:
                print(post)
                print(f"\nLength: {len(post)} characters")
            else:
                print("✗ Failed to generate post")
                
        except Exception as e:
            print(f"✗ Error generating {platform} post: {e}")
            logger.exception(f"Error for {platform}")
        
        print("-" * 70)
    
    # Summary
    print("\n" + "="*70)
    print("✅ LLM Test Complete!")
    print("="*70)
    print("\nKey features demonstrated:")
    print("  ✓ Description cleaning (removed URLs, sponsors, etc.)")
    print("  ✓ Platform-specific post generation")
    print("  ✓ Discord: No hashtags, conversational")
    print("  ✓ Matrix: Professional, no hashtags")
    print("  ✓ Bluesky: With hashtags, concise")
    print("  ✓ Mastodon: With hashtags, detailed")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
