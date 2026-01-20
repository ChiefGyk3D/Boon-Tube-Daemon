#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Boon-Tube-Daemon - Monitor TikTok and YouTube for new uploads and post alerts.

Main daemon that coordinates monitoring and notifications.
"""

import logging
import time
import signal
import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from boon_tube_daemon.utils.config import load_config, get_config, get_bool_config, get_int_config, get_float_config
from boon_tube_daemon.media.youtube_videos import YouTubeVideosPlatform
from boon_tube_daemon.social.discord import DiscordPlatform
from boon_tube_daemon.social.matrix import MatrixPlatform
from boon_tube_daemon.social.bluesky import BlueskyPlatform
from boon_tube_daemon.social.mastodon import MastodonPlatform
from boon_tube_daemon.llm.gemini import GeminiLLM
from boon_tube_daemon.llm.ollama import OllamaLLM

# TikTok support is optional (requires Playwright)
try:
    from boon_tube_daemon.media.tiktok import TikTokPlatform
    TIKTOK_AVAILABLE = True
except ImportError:
    TikTokPlatform = None
    TIKTOK_AVAILABLE = False

# Configure logging with local timezone
logging.Formatter.converter = time.localtime
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


class BoonTubeDaemon:
    """Main daemon for monitoring and notifications."""
    
    def __init__(self):
        self.running = False
        self.media_platforms: List = []
        self.social_platforms: List = []
        self.llm = None
        self.check_interval = 900  # Default: 15 minutes (optimized for video uploads, not livestreams)
        
    def initialize(self):
        """Initialize daemon and all platforms."""
        # Show banner
        try:
            banner_path = Path(__file__).parent.parent / "docs" / "BANNER.txt"
            if banner_path.exists():
                print(banner_path.read_text())
        except Exception:
            pass
        
        logger.info("="*60)
        logger.info("🚀 Boon-Tube-Daemon Starting...")
        logger.info("="*60)
        
        # Load configuration
        load_config()
        
        # Get check interval
        self.check_interval = get_int_config('Settings', 'check_interval', default=900)
        logger.info(f"⏰ Check interval: {self.check_interval} seconds ({self.check_interval // 60} minutes)")
        
        # Initialize media platforms
        logger.info("\n📺 Initializing Media Platforms...")
        
        if get_bool_config('YouTube', 'enable_monitoring', default=False):
            youtube = YouTubeVideosPlatform()
            if youtube.authenticate():
                self.media_platforms.append(youtube)
            else:
                logger.warning("  ⚠ YouTube monitoring disabled (authentication failed)")
        
        if get_bool_config('TikTok', 'enable_monitoring', default=False):
            if not TIKTOK_AVAILABLE:
                logger.warning("  ⚠ TikTok monitoring disabled (Playwright not installed)")
            else:
                tiktok = TikTokPlatform()
                if tiktok.authenticate():
                    self.media_platforms.append(tiktok)
                else:
                    logger.warning("  ⚠ TikTok monitoring disabled (authentication failed)")
        
        if not self.media_platforms:
            logger.error("❌ No media platforms configured! Please enable YouTube monitoring.")
            return False
        
        logger.info(f"✓ {len(self.media_platforms)} media platform(s) enabled")
        
        # Initialize LLM (optional)
        logger.info("\n🤖 Initializing LLM...")
        if get_bool_config('LLM', 'enable', default=False):
            # Determine provider
            provider = get_config('LLM', 'provider', default='gemini').lower()
            
            if provider == 'ollama':
                self.llm = OllamaLLM()
                if self.llm.authenticate():
                    logger.info("✓ Ollama LLM enabled")
                else:
                    logger.warning("  ⚠ Ollama LLM initialization failed")
                    self.llm = None
            elif provider == 'gemini':
                self.llm = GeminiLLM()
                if self.llm.authenticate():
                    logger.info("✓ Gemini LLM enabled")
                else:
                    logger.warning("  ⚠ Gemini LLM initialization failed")
                    self.llm = None
            else:
                logger.error("  ✗ Unknown LLM provider configured")
                self.llm = None
        else:
            logger.info("  ⊘ LLM disabled")
        
        # Initialize social platforms
        logger.info("\n📢 Initializing Social Platforms...")
        
        if get_bool_config('Discord', 'enable_posting', default=False):
            discord = DiscordPlatform()
            if discord.authenticate():
                self.social_platforms.append(discord)
        
        if get_bool_config('Matrix', 'enable_posting', default=False):
            matrix = MatrixPlatform()
            if matrix.authenticate():
                self.social_platforms.append(matrix)
        
        if get_bool_config('Bluesky', 'enable_posting', default=False):
            bluesky = BlueskyPlatform()
            if bluesky.authenticate():
                self.social_platforms.append(bluesky)
        
        if get_bool_config('Mastodon', 'enable_posting', default=False):
            mastodon = MastodonPlatform()
            if mastodon.authenticate():
                self.social_platforms.append(mastodon)
        
        if not self.social_platforms:
            logger.warning("⚠ No social platforms configured! Notifications will only be logged.")
        else:
            logger.info(f"✓ {len(self.social_platforms)} social platform(s) enabled")
        
        logger.info("\n" + "="*60)
        logger.info("✅ Boon-Tube-Daemon Initialized Successfully!")
        logger.info("="*60 + "\n")
        
        return True
    
    def check_platforms(self):
        """Check all media platforms for new content."""
        for platform in self.media_platforms:
            try:
                # Check for new video
                is_new, video_data = platform.check_for_new_video()
                
                if is_new and video_data:
                    self.notify_new_video(platform, video_data)
                    
            except Exception as e:
                logger.error(f"Error checking {platform.name}")
    
    def notify_new_video(self, platform, video_data: Dict):
        """Send notifications about new video to all social platforms."""
        logger.info("\n🎉 NEW VIDEO DETECTED!")
        logger.info(f"   Platform: {platform.name}")
        logger.info(f"   Title: {video_data.get('title')}")
        logger.info(f"   URL: {video_data.get('url')}")
        
        # Use LLM to filter if enabled
        if self.llm and self.llm.enabled:
            if not self.llm.should_notify(video_data):
                logger.info("   🚫 Skipped by LLM filter")
                return
        
        # Get platform delay for request spacing (prevents rate limit hammering)
        platform_delay = get_float_config('LLM', 'platform_delay', default=2.0)
        
        # Post to all social platforms (each gets a unique message)
        for idx, social in enumerate(self.social_platforms):
            try:
                # Add delay between platforms (except first one) to space out LLM requests
                if idx > 0 and platform_delay > 0:
                    logger.debug(f"   ⏱ Waiting {platform_delay}s before next platform...")
                    time.sleep(platform_delay)
                
                logger.info(f"   📤 Posting to {social.name}...")
                
                # Generate platform-specific message
                message = self.format_notification(platform, video_data, social.name)
                
                if not message:
                    logger.warning(f"   ⚠ Failed to generate message for {social.name}, skipping...")
                    continue
                
                result = social.post(
                    message=message,
                    platform_name=platform.name.lower(),
                    stream_data=video_data
                )
                if result:
                    logger.info(f"   ✓ Posted to {social.name}")
                else:
                    logger.warning(f"   ✗ Failed to post to {social.name}")
            except Exception as e:
                logger.error(f"   ✗ Error posting to {social.name}")
                logger.exception("Detailed traceback:")
                # Continue to next platform even on error
    
    def format_notification(self, platform, video_data: Dict, social_platform_name: str = None) -> str:
        """
        Format notification message for social platforms.
        Each platform gets a unique, tailored message if LLM is enabled.
        
        Args:
            platform: Media platform object (YouTube, TikTok, etc.)
            video_data: Video information dict
            social_platform_name: Target social platform name (Discord, Bluesky, etc.)
            
        Returns:
            Formatted message string
        """
        title = video_data.get('title', 'Untitled')
        url = video_data.get('url', '')
        
        # Try LLM-enhanced notification (platform-specific)
        if self.llm and self.llm.enabled and get_bool_config('LLM', 'enhance_notifications', default=False):
            if social_platform_name:
                try:
                    # Use unified generate_notification interface (works for both Ollama and Gemini)
                    enhanced_message = self.llm.generate_notification(
                        video_data, 
                        platform.name,
                        social_platform_name
                    )
                    if enhanced_message:
                        logger.info(f"   ✨ Using LLM-enhanced {social_platform_name} post")
                        return enhanced_message
                    else:
                        logger.warning(f"   ⚠ LLM returned empty message for {social_platform_name}, using fallback")
                except Exception as e:
                    logger.error(f"   ✗ LLM enhancement failed for {social_platform_name}")
                    logger.debug("Falling back to template-based notification")
        
        # Fall back to template-based notification
        template = get_config('Settings', 'notification_template', 
                            default="🎬 New {platform} video!\n\n{title}\n\n{url}")
        
        message = template.format(
            platform=platform.name,
            title=title,
            url=url,
            description=video_data.get('description', '')[:200]  # Limit description length
        )
        
        # Add hashtags (LLM-generated or configured)
        if self.llm and self.llm.enabled and get_bool_config('LLM', 'generate_hashtags', default=False):
            hashtags = self.llm.generate_hashtags(video_data)
            if hashtags:
                message += f"\n\n{hashtags}"
        else:
            hashtags = get_config('Settings', 'hashtags', default='')
            if hashtags:
                message += f"\n\n{hashtags}"
        
        return message
    
    def run(self):
        """Main daemon loop."""
        self.running = True
        
        logger.info("🔄 Monitoring started. Press Ctrl+C to stop.\n")
        
        # Initial check
        logger.info("🔍 Performing initial check...")
        self.check_platforms()
        
        # Main loop
        while self.running:
            try:
                # Sleep for check interval
                time.sleep(self.check_interval)
                
                # Check all platforms
                logger.info(f"🔍 Checking platforms... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
                self.check_platforms()
                
            except KeyboardInterrupt:
                logger.info("\n⏹ Received shutdown signal...")
                self.stop()
                break
            except Exception as e:
                logger.error("Error in main loop")
                # Continue running even if there's an error
                continue
    
    def stop(self):
        """Stop the daemon."""
        self.running = False
        logger.info("👋 Boon-Tube-Daemon stopped.")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"\n⚠ Received signal {signum}")
    sys.exit(0)


def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run daemon
    daemon = BoonTubeDaemon()
    
    if daemon.initialize():
        daemon.run()
    else:
        logger.error("❌ Failed to initialize daemon")
        sys.exit(1)


if __name__ == "__main__":
    main()
