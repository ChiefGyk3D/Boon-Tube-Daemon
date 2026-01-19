# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
TikTok platform integration using Playwright network interception.

Monitors TikTok creators for new video uploads without requiring TikTokApi package.
Uses browser automation to intercept API calls and extract video data.
"""

import asyncio
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from boon_tube_daemon.utils.config import get_config
from boon_tube_daemon.media.base import MediaPlatform

logger = logging.getLogger(__name__)


class TikTokPlatform(MediaPlatform):
    """TikTok platform for monitoring new video uploads."""
    
    def __init__(self):
        super().__init__("TikTok")
        self.username = None
        self.playwright_instance = None
        self.browser = None
        self.video_data = []
        self.last_video_id = None
        
    def authenticate(self) -> bool:
        """
        Initialize TikTok monitoring.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.username = get_config("TikTok", "username")
            
            if not self.username:
                logger.warning("✗ TikTok username not configured")
                return False
            
            # Remove @ prefix if present
            if self.username.startswith("@"):
                self.username = self.username[1:]
            
            self.enabled = True
            logger.info(f"✓ TikTok monitoring configured for @{self.username}")
            return True
            
        except Exception as e:
            logger.error("✗ TikTok authentication failed")
            logger.debug(f"Error details: {e}")  # Debug level for sensitive details
            self.enabled = False
            return False
    
    async def _ensure_browser(self):
        """Launch browser if not already running."""
        if not self.browser:
            self.playwright_instance = await async_playwright().start()
            self.browser = await self.playwright_instance.chromium.launch(headless=True)
            logger.debug("Playwright browser launched")
    
    async def _cleanup_browser(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright_instance:
            await self.playwright_instance.stop()
            self.playwright_instance = None
    
    async def _get_latest_video_async(self, username: str) -> Optional[Dict]:
        """
        Get the latest video from a TikTok user (async).
        
        Args:
            username: TikTok username (without @)
            
        Returns:
            Dictionary with video info or None
        """
        self.video_data = []
        await self._ensure_browser()
        
        try:
            # Get ms_token cookie if available (helps avoid bot detection)
            ms_token = get_config("TikTok", "ms_token", default="")
            
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            # Add TikTok cookies if ms_token is available
            if ms_token:
                await context.add_cookies([{
                    'name': 'ms_token',
                    'value': ms_token,
                    'domain': '.tiktok.com',
                    'path': '/'
                }])
                logger.debug("Added ms_token cookie for TikTok authentication")
            
            # Intercept API responses to capture video data
            # Intercept API responses to capture video data
            async def handle_response(response):
                try:
                    # ONLY look for post/item_list (user's own videos, NOT reposts)
                    if "api/post/item_list" in response.url:
                        try:
                            data = await response.json()
                            if "itemList" in data and data["itemList"]:
                                # Filter to ONLY videos actually by this user
                                user_videos = [
                                    item for item in data["itemList"]
                                    if item.get("author", {}).get("uniqueId", "").lower() == username.lower()
                                ]
                                if user_videos:
                                    logger.debug(f"Found {len(user_videos)} videos by @{username}")
                                    self.video_data = user_videos
                                else:
                                    logger.debug(f"API returned {len(data['itemList'])} videos but none by @{username}")
                        except:
                            pass
                except:
                    pass

            
            page.on("response", handle_response)
            
            # Navigate to user profile
            url = f"https://www.tiktok.com/@{username}"
            logger.debug(f"Fetching TikTok videos for @{username}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for page to load
            await page.wait_for_timeout(3000)
            
            # Scroll to trigger lazy loading of videos
            logger.debug("Scrolling to trigger video loading...")
            await page.evaluate('window.scrollBy(0, 300)')
            await page.wait_for_timeout(2000)
            await page.evaluate('window.scrollBy(0, 300)')
            await page.wait_for_timeout(3000)
            
            await context.close()
            
            # Process collected video data
            if self.video_data:
                item = self.video_data[0]  # Get the latest video
                author_id = item.get("author", {}).get("uniqueId", username)
                video_id = item.get("id", "")
                
                video_info = {
                    "video_id": video_id,
                    "title": item.get("desc", "")[:100],  # Use description as title
                    "description": item.get("desc", ""),
                    "url": f"https://www.tiktok.com/@{author_id}/video/{video_id}",
                    "thumbnail_url": item.get("video", {}).get("cover", ""),
                    "published_at": datetime.fromtimestamp(item.get("createTime", 0)),
                    "author": author_id,
                    "stats": {
                        "plays": item.get("stats", {}).get("playCount", 0),
                        "likes": item.get("stats", {}).get("diggCount", 0),
                        "comments": item.get("stats", {}).get("commentCount", 0),
                        "shares": item.get("stats", {}).get("shareCount", 0),
                    }
                }
                
                logger.debug(f"✓ Found latest video: {video_id}")
                return video_info
            
            logger.warning(f"✗ No videos found for @{username}")
            return None
            
        except PlaywrightTimeout:
            logger.error(f"✗ Timeout loading TikTok page for @{username}")
            return None
        except Exception as e:
            logger.error("✗ Error fetching TikTok videos")
            logger.debug(f"Error details: {e}")  # Debug level for sensitive details
            return None
    
    def get_latest_video(self, username: Optional[str] = None) -> Tuple[bool, Optional[Dict]]:
        """
        Get the latest video from a TikTok user (sync wrapper).
        
        Args:
            username: TikTok username (without @). If not provided, uses configured username.
            
        Returns:
            Tuple of (success, video_data)
        """
        target_username = username or self.username
        if not target_username:
            logger.error("No TikTok username provided or configured")
            return False, None
        
        # Remove @ if present
        if target_username.startswith("@"):
            target_username = target_username[1:]
        
        try:
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                video_data = loop.run_until_complete(self._get_latest_video_async(target_username))
                if video_data:
                    return True, video_data
                return False, None
            finally:
                loop.close()
        except Exception as e:
            logger.error("Error in get_latest_video")
            logger.debug(f"Error details: {e}")  # Debug level for sensitive details
            return False, None
    
    def check_for_new_video(self, username: Optional[str] = None) -> Tuple[bool, Optional[Dict]]:
        """
        Check if there's a new video since the last check.
        
        Args:
            username: TikTok username (without @). If not provided, uses configured username.
            
        Returns:
            Tuple of (is_new, video_data)
        """
        success, video_data = self.get_latest_video(username)
        
        if not success or not video_data:
            return False, None
        
        video_id = video_data.get("video_id")
        
        # If we have no last_video_id, this is the first check
        if not self.last_video_id:
            logger.info(f"First check for @{self.username}, storing video ID: {video_id}")
            self.last_video_id = video_id
            return False, video_data  # Not "new" on first check
        
        # Check if this is a new video
        if video_id != self.last_video_id:
            logger.info(f"  Previous ID: {self.last_video_id}")
            logger.info(f"  New ID: {video_id}")
            self.last_video_id = video_id
            return True, video_data
        
        logger.debug(f"No new video for @{self.username}")
        return False, None
    
    def cleanup(self):
        """Clean up resources (sync wrapper)."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._cleanup_browser())
            finally:
                loop.close()
        except Exception as e:
            logger.error("Error during cleanup")
            logger.debug(f"Error details: {e}")  # Debug level for sensitive details
