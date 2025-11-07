#!/usr/bin/env python3
"""
Test social platform integrations.

Usage:
    python3 test_social.py --platform bluesky
    python3 test_social.py --platform mastodon
    python3 test_social.py --platform discord
    python3 test_social.py --platform matrix
    python3 test_social.py --all
    python3 test_social.py --platform discord --message "Custom message"

With Doppler:
    doppler run -- python3 test_social.py --platform discord
"""

import argparse
import logging
import sys
from datetime import datetime
from boon_tube_daemon.social.bluesky import BlueskyPlatform
from boon_tube_daemon.social.mastodon import MastodonPlatform
from boon_tube_daemon.social.discord import DiscordPlatform
from boon_tube_daemon.social.matrix import MatrixPlatform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_bluesky(message: str = None):
    """Test Bluesky platform."""
    print("\n" + "="*60)
    print("🦋 Testing Bluesky")
    print("="*60)
    
    platform = BlueskyPlatform()
    
    # Test authentication
    print("\n1. Testing authentication...")
    if platform.authenticate():
        print("   ✓ Bluesky authentication successful")
    else:
        print("   ✗ Bluesky authentication failed")
        print("\n   Troubleshooting:")
        print("   • Check BLUESKY_ENABLE_POSTING=true in .env")
        print("   • Verify BLUESKY_HANDLE is correct (e.g., yourname.bsky.social)")
        print("   • Check BLUESKY_APP_PASSWORD in Doppler or .env")
        print("   • Make sure you're using an app password, not your main password")
        return False
    
    # Test posting
    print("\n2. Testing post...")
    test_message = message or f"""🧪 Test post from Boon-Tube-Daemon

This is an automated test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Testing features:
• Rich text formatting
• Hashtags: #BoonTube #Testing
• Links: https://github.com/ChiefGyk3D/Boon-Tube-Daemon

If you see this, the integration is working! ✨"""
    
    post_id = platform.post(test_message)
    
    if post_id:
        print(f"   ✓ Post created successfully")
        print(f"   Post URI: {post_id}")
        print(f"\n   View at: https://bsky.app/profile/{platform.client.me.handle}")
        return True
    else:
        print("   ✗ Post failed")
        return False


def test_mastodon(message: str = None):
    """Test Mastodon platform."""
    print("\n" + "="*60)
    print("🐘 Testing Mastodon")
    print("="*60)
    
    platform = MastodonPlatform()
    
    # Test authentication
    print("\n1. Testing authentication...")
    if platform.authenticate():
        print("   ✓ Mastodon authentication successful")
    else:
        print("   ✗ Mastodon authentication failed")
        print("\n   Troubleshooting:")
        print("   • Check MASTODON_ENABLE_POSTING=true in .env")
        print("   • Verify MASTODON_API_BASE_URL in .env (e.g., https://mastodon.social)")
        print("   • Check MASTODON_CLIENT_ID in Doppler or .env")
        print("   • Check MASTODON_CLIENT_SECRET in Doppler or .env")
        print("   • Check MASTODON_ACCESS_TOKEN in Doppler or .env")
        return False
    
    # Test posting
    print("\n2. Testing post...")
    test_message = message or f"""🧪 Test post from Boon-Tube-Daemon

This is an automated test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Testing features:
• Rich text formatting
• Hashtags: #BoonTube #Testing
• Links: https://github.com/ChiefGyk3D/Boon-Tube-Daemon

If you see this, the integration is working! ✨"""
    
    post_id = platform.post(test_message)
    
    if post_id:
        print(f"   ✓ Post created successfully")
        print(f"   Post ID: {post_id}")
        if platform.client:
            status = platform.client.status(post_id)
            print(f"   View at: {status['url']}")
        return True
    else:
        print("   ✗ Post failed")
        return False


def test_discord(message: str = None):
    """Test Discord platform."""
    print("\n" + "="*60)
    print("💬 Testing Discord")
    print("="*60)
    
    platform = DiscordPlatform()
    
    # Test authentication
    print("\n1. Testing authentication...")
    if platform.authenticate():
        print("   ✓ Discord webhook configured")
        if platform.webhook_url:
            print("   • Default webhook: configured")
        if platform.webhook_urls:
            for platform_name in platform.webhook_urls:
                print(f"   • {platform_name.upper()} webhook: configured")
        if platform.role_id:
            print(f"   • Default role: {platform.role_id}")
        if platform.role_mentions:
            for platform_name, role_id in platform.role_mentions.items():
                print(f"   • {platform_name.upper()} role: {role_id}")
    else:
        print("   ✗ Discord webhook configuration failed")
        print("\n   Troubleshooting:")
        print("   • Check DISCORD_ENABLE_POSTING=true in .env")
        print("   • Verify DISCORD_WEBHOOK_URL in Doppler or .env")
        print("   • Webhook format: https://discord.com/api/webhooks/...")
        print("   • Optional: Set per-platform webhooks (DISCORD_WEBHOOK_YOUTUBE, etc.)")
        return False
    
    # Test posting
    print("\n2. Testing post...")
    test_message = message or f"""🧪 **Test post from Boon-Tube-Daemon**

This is an automated test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Testing features:
• **Bold text** and *italic text*
• Links: https://github.com/ChiefGyk3D/Boon-Tube-Daemon
• Emojis: 🎉 ✨ 🚀

If you see this, the integration is working!"""
    
    message_id = platform.post(test_message)
    
    if message_id:
        print(f"   ✓ Message posted successfully")
        print(f"   Message ID: {message_id}")
        return True
    else:
        print("   ✗ Post failed")
        return False


def test_matrix(message: str = None):
    """Test Matrix platform."""
    print("\n" + "="*60)
    print("🔐 Testing Matrix")
    print("="*60)
    
    platform = MatrixPlatform()
    
    # Test authentication
    print("\n1. Testing authentication...")
    if platform.authenticate():
        print("   ✓ Matrix authentication successful")
        print(f"   • Homeserver: {platform.homeserver}")
        print(f"   • Room ID: {platform.room_id}")
        if platform.username:
            print(f"   • Username: {platform.username}")
        if platform.access_token:
            print("   • Access token: configured")
    else:
        print("   ✗ Matrix authentication failed")
        print("\n   Troubleshooting:")
        print("   • Check MATRIX_ENABLE_POSTING=true in .env")
        print("   • Verify MATRIX_HOMESERVER in .env (e.g., https://matrix.org)")
        print("   • Verify MATRIX_ROOM_ID in .env (e.g., !abc123:matrix.org)")
        print("   • Check MATRIX_USERNAME and MATRIX_PASSWORD in Doppler/env")
        print("   • OR check MATRIX_ACCESS_TOKEN in Doppler/.env")
        return False
    
    # Test posting
    print("\n2. Testing post...")
    test_message = message or f"""🧪 Test post from Boon-Tube-Daemon

This is an automated test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Testing features:
• Rich text formatting (HTML)
• Links: https://github.com/ChiefGyk3D/Boon-Tube-Daemon
• Emojis: 🎉 ✨ 🚀

If you see this, the integration is working!

⚠️ Note: Matrix does NOT support editing messages like Discord."""
    
    event_id = platform.post(test_message)
    
    if event_id:
        print(f"   ✓ Message posted successfully")
        print(f"   Event ID: {event_id}")
        return True
    else:
        print("   ✗ Post failed")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test social platform integrations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --platform bluesky
  %(prog)s --platform discord --message "Hello from Boon-Tube!"
  %(prog)s --all
  doppler run -- %(prog)s --platform mastodon
        """
    )
    parser.add_argument(
        '--platform',
        choices=['bluesky', 'mastodon', 'discord', 'matrix'],
        help='Platform to test'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Test all platforms'
    )
    parser.add_argument(
        '--message',
        type=str,
        help='Custom test message'
    )
    
    args = parser.parse_args()
    
    if not args.platform and not args.all:
        parser.print_help()
        sys.exit(1)
    
    results = {}
    
    print("🚀 Boon-Tube-Daemon Social Platform Tester")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if args.all or args.platform == 'bluesky':
        results['Bluesky'] = test_bluesky(args.message)
    
    if args.all or args.platform == 'mastodon':
        results['Mastodon'] = test_mastodon(args.message)
    
    if args.all or args.platform == 'discord':
        results['Discord'] = test_discord(args.message)
    
    if args.all or args.platform == 'matrix':
        results['Matrix'] = test_matrix(args.message)
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    for platform, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{platform:12} {status}")
    
    print("\n")
    
    # Exit code
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
