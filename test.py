#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test script for Boon-Tube-Daemon.
Verifies configuration and API connectivity without running the full daemon.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported."""
    print("\n" + "="*60)
    print("🧪 Testing Module Imports")
    print("="*60)
    
    required_modules = [
        ('requests', 'requests'),
        ('googleapiclient', 'google-api-python-client'),
        ('atproto', 'atproto'),
        ('mastodon', 'Mastodon.py'),
    ]
    
    optional_modules = [
        ('TikTokApi', 'TikTokApi'),
        ('playwright', 'playwright'),
    ]
    
    all_ok = True
    
    for module, package in required_modules:
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING (required)")
            all_ok = False
    
    for module, package in optional_modules:
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            print(f"⚠ {package} - MISSING (optional, needed for TikTok)")
    
    return all_ok

def test_config():
    """Test configuration file."""
    print("\n" + "="*60)
    print("🧪 Testing Configuration")
    print("="*60)
    
    config_path = Path(".env")
    
    if not config_path.exists():
        print("✗ .env not found")
        print("  Run: cp config.example.ini .env")
        return False
    
    print("✓ .env exists")
    
    try:
        from boon_tube_daemon.utils.config import load_config, get_bool_config, get_config
        load_config()
        print("✓ Configuration loaded successfully")
        
        # Check for at least one media platform enabled
        youtube_enabled = get_bool_config('YouTube', 'enable_monitoring', False)
        tiktok_enabled = get_bool_config('TikTok', 'enable_monitoring', False)
        
        if not youtube_enabled and not tiktok_enabled:
            print("⚠ No media platforms enabled")
            print("  Enable YouTube or TikTok in .env")
        else:
            if youtube_enabled:
                print("✓ YouTube monitoring enabled")
            if tiktok_enabled:
                print("✓ TikTok monitoring enabled")
        
        # Check for at least one social platform enabled
        discord_enabled = get_bool_config('Discord', 'enable_posting', False)
        matrix_enabled = get_bool_config('Matrix', 'enable_posting', False)
        bluesky_enabled = get_bool_config('Bluesky', 'enable_posting', False)
        mastodon_enabled = get_bool_config('Mastodon', 'enable_posting', False)
        
        if not any([discord_enabled, matrix_enabled, bluesky_enabled, mastodon_enabled]):
            print("⚠ No social platforms enabled (notifications will only be logged)")
        else:
            if discord_enabled:
                print("✓ Discord posting enabled")
            if matrix_enabled:
                print("✓ Matrix posting enabled")
            if bluesky_enabled:
                print("✓ Bluesky posting enabled")
            if mastodon_enabled:
                print("✓ Mastodon posting enabled")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_youtube():
    """Test YouTube API connection."""
    print("\n" + "="*60)
    print("🧪 Testing YouTube API")
    print("="*60)
    
    try:
        from boon_tube_daemon.utils.config import get_bool_config, get_config, get_secret
        
        if not get_bool_config('YouTube', 'enable_monitoring', False):
            print("⊘ YouTube monitoring disabled - skipping test")
            return True
        
        api_key = get_secret('YouTube', 'api_key')
        username = get_config('YouTube', 'username')
        
        if not api_key:
            print("✗ YouTube API key not configured")
            return False
        
        if not username:
            print("✗ YouTube username not configured")
            return False
        
        print(f"✓ YouTube API key configured")
        print(f"✓ YouTube username: {username}")
        
        # Try to initialize
        from boon_tube_daemon.media.youtube_videos import YouTubeVideosPlatform
        youtube = YouTubeVideosPlatform()
        
        if youtube.authenticate():
            print("✓ YouTube authentication successful")
            
            # Try to fetch latest video
            success, video_data = youtube.get_latest_video()
            if success and video_data:
                print(f"✓ Successfully fetched latest video:")
                print(f"  Title: {video_data.get('title', 'N/A')[:60]}...")
                print(f"  URL: {video_data.get('url', 'N/A')}")
                return True
            else:
                print("⚠ Could not fetch latest video (may be normal if channel is empty)")
                return True
        else:
            print("✗ YouTube authentication failed")
            return False
            
    except Exception as e:
        print(f"✗ YouTube test failed: {e}")
        return False

def test_tiktok():
    """Test TikTok connection."""
    print("\n" + "="*60)
    print("🧪 Testing TikTok")
    print("="*60)
    
    try:
        from boon_tube_daemon.utils.config import get_bool_config, get_config
        
        if not get_bool_config('TikTok', 'enable_monitoring', False):
            print("⊘ TikTok monitoring disabled - skipping test")
            return True
        
        username = get_config('TikTok', 'username')
        
        if not username:
            print("✗ TikTok username not configured")
            return False
        
        print(f"✓ TikTok username: @{username}")
        
        # Try to initialize
        from boon_tube_daemon.media.tiktok import TikTokPlatform
        tiktok = TikTokPlatform()
        
        if tiktok.authenticate():
            print("✓ TikTok initialized successfully")
            print("⚠ Note: First run may take a while (downloading browsers)")
            
            # Note: Actually fetching videos can be slow, so we skip that in tests
            print("✓ TikTok connection ready")
            return True
        else:
            print("✗ TikTok initialization failed")
            return False
            
    except Exception as e:
        print(f"✗ TikTok test failed: {e}")
        print("  Make sure to run: playwright install")
        return False

def test_social_platforms():
    """Test social platform configurations."""
    print("\n" + "="*60)
    print("🧪 Testing Social Platforms")
    print("="*60)
    
    from boon_tube_daemon.utils.config import get_bool_config
    
    results = []
    
    # Test Discord
    if get_bool_config('Discord', 'enable_posting', False):
        try:
            from boon_tube_daemon.social.discord import DiscordPlatform
            discord = DiscordPlatform()
            if discord.authenticate():
                print("✓ Discord configured")
                results.append(True)
            else:
                print("✗ Discord configuration failed")
                results.append(False)
        except Exception as e:
            print(f"✗ Discord error: {e}")
            results.append(False)
    
    # Test Matrix
    if get_bool_config('Matrix', 'enable_posting', False):
        try:
            from boon_tube_daemon.social.matrix import MatrixPlatform
            matrix = MatrixPlatform()
            if matrix.authenticate():
                print("✓ Matrix configured")
                results.append(True)
            else:
                print("✗ Matrix configuration failed")
                results.append(False)
        except Exception as e:
            print(f"✗ Matrix error: {e}")
            results.append(False)
    
    # Test Bluesky
    if get_bool_config('Bluesky', 'enable_posting', False):
        try:
            from boon_tube_daemon.social.bluesky import BlueskyPlatform
            bluesky = BlueskyPlatform()
            if bluesky.authenticate():
                print("✓ Bluesky configured")
                results.append(True)
            else:
                print("✗ Bluesky configuration failed")
                results.append(False)
        except Exception as e:
            print(f"✗ Bluesky error: {e}")
            results.append(False)
    
    # Test Mastodon
    if get_bool_config('Mastodon', 'enable_posting', False):
        try:
            from boon_tube_daemon.social.mastodon import MastodonPlatform
            mastodon = MastodonPlatform()
            if mastodon.authenticate():
                print("✓ Mastodon configured")
                results.append(True)
            else:
                print("✗ Mastodon configuration failed")
                results.append(False)
        except Exception as e:
            print(f"✗ Mastodon error: {e}")
            results.append(False)
    
    if not results:
        print("⚠ No social platforms enabled")
        return True
    
    return all(results)

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 Boon-Tube-Daemon Test Suite")
    print("="*60)
    
    results = {
        'imports': test_imports(),
        'config': test_config(),
        'youtube': test_youtube(),
        'tiktok': test_tiktok(),
        'social': test_social_platforms(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name.capitalize()}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ All tests passed! Ready to run main.py")
    else:
        print("⚠ Some tests failed. Please fix configuration before running.")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
