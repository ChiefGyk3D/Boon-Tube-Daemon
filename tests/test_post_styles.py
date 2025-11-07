#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test script for LLM posting style variations.
Tests professional, conversational, detailed, and concise styles.
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
    print("🎨 LLM Posting Style Variations Test")
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
    
    # Initialize Gemini LLM
    print("\n🤖 Initializing Gemini LLM...")
    llm = GeminiLLM()
    if not llm.authenticate():
        print("✗ Gemini LLM authentication failed!")
        return False
    
    print("✓ Gemini LLM initialized")
    
    # Test different styles
    styles = ['professional', 'conversational', 'detailed', 'concise']
    platforms = ['Discord', 'Bluesky']
    
    print("\n📝 Testing different posting styles...")
    print("="*70)
    
    for platform in platforms:
        print(f"\n{'='*70}")
        print(f"PLATFORM: {platform.upper()}")
        print('='*70)
        
        for style in styles:
            print(f"\n🎨 Style: {style.upper()}")
            print("-" * 70)
            
            # Temporarily override config for this test
            import os
            os.environ[f'{platform.upper()}_POST_STYLE'] = style
            
            try:
                post = llm.enhance_notification(
                    video_data,
                    'YouTube',
                    platform.lower()
                )
                
                if post:
                    print(post)
                    print(f"\nLength: {len(post)} characters")
                else:
                    print("✗ Failed to generate post")
                    
            except Exception as e:
                print(f"✗ Error: {e}")
            
            print("-" * 70)
    
    print("\n" + "="*70)
    print("✅ Style Variations Test Complete!")
    print("="*70)
    print("\nStyles tested:")
    print("  • professional: Formal, business-like")
    print("  • conversational: Casual, friendly")
    print("  • detailed: Comprehensive, thorough")
    print("  • concise: Brief, to-the-point")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
