#!/usr/bin/env python3
"""Test script to verify Bluesky hashtag formatting is fixed."""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from boon_tube_daemon.social.bluesky import BlueskyPlatform
from boon_tube_daemon.utils.config import load_config

def main():
    # Load configuration
    load_config()
    
    # Initialize Bluesky
    bluesky = BlueskyPlatform()
    
    try:
        bluesky.authenticate()
        
        if not bluesky.enabled:
            print("❌ Bluesky is not enabled in config. Enable it in your .env file:")
            print("   BLUESKY_ENABLE_POSTING=true")
            return 1
        
        # Test message with hashtags
        test_message = """🧪 TEST POST - Verifying hashtag fix

This is a test to confirm hashtags display correctly without duplication.

#TestPost #BoonTubeDaemon #Bluesky

https://github.com/ChiefGyk3D/Boon-Tube-Daemon"""
        
        print("📤 Posting test message to Bluesky...")
        print(f"\nMessage content:\n{test_message}\n")
        
        post_id = bluesky.post(test_message)
        
        if post_id:
            print(f"✅ Test post successful!")
            print(f"Post ID: {post_id}")
            print("\n👀 Check your Bluesky feed to verify hashtags appear as:")
            print("   #TestPost #BoonTubeDaemon #Bluesky")
            print("   (NOT ##TestPost ##BoonTubeDaemon ##Bluesky)")
            return 0
        else:
            print("❌ Test post failed - no post ID returned")
            return 1
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
