#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test script for YouTube video monitoring.
Tests the YouTube Data API integration and video detection.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pytest

from boon_tube_daemon.utils.config import load_config, get_config
from boon_tube_daemon.media.youtube_videos import YouTubeVideosPlatform

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.mark.youtube
def test_youtube_authentication():
    """Test YouTube API authentication."""
    print("\n" + "="*70)
    print("🔐 Testing YouTube Authentication")
    print("="*70)
    
    youtube = YouTubeVideosPlatform()
    
    if youtube.authenticate():
        print(f"✓ Authentication successful!")
        print(f"  Channel ID: {youtube.channel_id}")
        print(f"  Username: {youtube.username}")
        return youtube
    else:
        print("✗ Authentication failed!")
        print("\nPossible issues:")
        print("  1. YOUTUBE_API_KEY not set in .env")
        print("  2. YOUTUBE_USERNAME or YOUTUBE_CHANNEL_ID not set")
        print("  3. API key is invalid or expired")
        print("  4. YouTube Data API v3 not enabled in Google Cloud Console")
        print("\nTo fix:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create a project and enable YouTube Data API v3")
        print("  3. Create API credentials (API Key)")
        print("  4. Add to .env: YOUTUBE_API_KEY=your_key_here")
        print("  5. Add to .env: YOUTUBE_USERNAME=your_channel_handle")
        return None


@pytest.mark.youtube
@pytest.mark.integration
def test_get_latest_video(youtube):
    """Test getting the latest video."""
    print("\n" + "="*70)
    print("📹 Testing Latest Video Retrieval")
    print("="*70)
    
    success, video_data = youtube.get_latest_video()
    
    if success and video_data:
        print("✓ Successfully retrieved latest video!")
        print(f"\n  Video ID: {video_data.get('video_id')}")
        print(f"  Title: {video_data.get('title')}")
        print(f"  URL: {video_data.get('url')}")
        print(f"  Published: {video_data.get('published_at')}")
        
        if video_data.get('description'):
            desc = video_data['description']
            print(f"  Description: {desc[:100]}{'...' if len(desc) > 100 else ''}")
        
        if video_data.get('view_count') is not None:
            print(f"  Views: {video_data['view_count']:,}")
        if video_data.get('like_count') is not None:
            print(f"  Likes: {video_data['like_count']:,}")
        if video_data.get('comment_count') is not None:
            print(f"  Comments: {video_data['comment_count']:,}")
        
        return video_data
    else:
        print("✗ Failed to retrieve latest video!")
        print("\nPossible issues:")
        print("  1. Channel has no uploaded videos")
        print("  2. API quota exceeded")
        print("  3. Channel ID is incorrect")
        return None


@pytest.mark.youtube
@pytest.mark.integration
def test_new_video_detection(youtube):
    """Test new video detection mechanism."""
    print("\n" + "="*70)
    print("🎬 Testing New Video Detection")
    print("="*70)
    
    # First check - should establish baseline
    print("\nFirst check (establishing baseline)...")
    is_new, video_data = youtube.check_for_new_video()
    
    if video_data:
        print(f"✓ Baseline established: {video_data.get('title')[:50]}")
        print(f"  Stored video ID: {youtube.last_video_id}")
        
        if is_new:
            print("  ⚠ Warning: First check should not trigger notification")
        else:
            print("  ✓ Correctly marked as not new (baseline)")
    else:
        print("✗ Failed to establish baseline")
        return
    
    # Second check - should detect no change
    print("\nSecond check (testing duplicate detection)...")
    is_new, video_data = youtube.check_for_new_video()
    
    if is_new:
        print("✗ Incorrectly detected new video (should be duplicate)")
    else:
        print("✓ Correctly detected no new video")
    
    print("\n💡 To test new video detection:")
    print("  1. Upload a new video to your YouTube channel")
    print("  2. Run this test again")
    print("  3. The new video should be detected on first check after upload")


@pytest.mark.youtube
@pytest.mark.integration
def test_quota_management(youtube):
    """Test API quota management."""
    print("\n" + "="*70)
    print("📊 Testing API Quota Management")
    print("="*70)
    
    print("\nYouTube Data API v3 quota information:")
    print("  Daily quota: 10,000 units")
    print("  Cost per check:")
    print("    - channels().list: 1 unit")
    print("    - playlistItems().list: 1 unit")
    print("    - videos().list: 1 unit")
    print("    - Total per check: 3 units")
    print(f"\n  Maximum checks per day: ~3,333")
    print(f"  Recommended check interval: 5-15 minutes")
    
    if youtube.quota_exceeded:
        print(f"\n⚠ Quota currently exceeded!")
        print(f"  Exceeded at: {youtube.quota_exceeded_time}")
        print(f"  Cooldown: 1 hour from quota exceeded time")
    else:
        print("\n✓ Quota available")
        print(f"  Consecutive errors: {youtube.consecutive_errors}/{youtube.max_consecutive_errors}")


def test_channel_resolution():
    """Test channel ID resolution from username."""
    print("\n" + "="*70)
    print("🔍 Testing Channel Resolution")
    print("="*70)
    
    test_channels = [
        "@YouTube",  # Official YouTube channel
        "YouTube",   # Legacy username
    ]
    
    youtube = YouTubeVideosPlatform()
    if not youtube.authenticate():
        print("✗ Cannot test without authentication")
        return
    
    for channel in test_channels:
        print(f"\nResolving: {channel}")
        channel_id = youtube._resolve_channel_id(channel)
        if channel_id:
            print(f"  ✓ Resolved to: {channel_id}")
        else:
            print(f"  ✗ Could not resolve")


def main():
    """Run all YouTube tests."""
    print("\n" + "="*70)
    print("🎥 YouTube Video Monitoring Test Suite")
    print("="*70)
    
    # Load configuration
    print("\n📋 Loading configuration...")
    env_file = project_root / '.env'
    if not env_file.exists():
        print(f"✗ .env file not found at: {env_file}")
        print("\nPlease create .env from .env.example and configure:")
        print("  YOUTUBE_API_KEY=your_api_key")
        print("  YOUTUBE_USERNAME=your_channel_handle")
        print("  YOUTUBE_ENABLE_MONITORING=true")
        return 1
    
    load_config(str(env_file))
    print("✓ Configuration loaded")
    
    # Run tests
    youtube = test_youtube_authentication()
    if not youtube:
        return 1
    
    video_data = test_get_latest_video(youtube)
    if not video_data:
        return 1
    
    test_new_video_detection(youtube)
    test_quota_management(youtube)
    test_channel_resolution()
    
    # Summary
    print("\n" + "="*70)
    print("✅ YouTube Tests Complete!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Configure your YouTube channel credentials in .env")
    print("  2. Test with: python3 test_youtube.py")
    print("  3. Once working, integrate with daemon: python3 main.py")
    print("  4. Monitor logs for new video notifications")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
