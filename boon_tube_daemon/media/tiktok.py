# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
TikTok platform integration for detecting new video uploads.

Note: TikTok doesn't provide an official public API for monitoring uploads.
This implementation uses the unofficial TikTokApi library which may break
if TikTok changes their internal API.

Alternative approaches:
1. RSS feeds (if available for the user)
2. Web scraping (less reliable)
3. Official TikTok API (requires business account and approval)
"""

import logging
from datetime import datetime
from typing import Optional, Tuple
from TikTokApi import TikTokApi
import asyncio

from boon_tube_daemon.utils.config import get_config, get_secret
from boon_tube_daemon.media.base import MediaPlatform

logger = logging.getLogger(__name__)


class TikTokPlatform(MediaPlatform):
    """TikTok platform for monitoring new video uploads."""
    
    def __init__(self):
        super().__init__("TikTok")
        self.api = None
        self.username = None
        self.last_video_id = None
        
    def authenticate(self) -> bool:
        """
        Initialize TikTok API.
        
        Note: TikTok unofficial API doesn't require authentication,
        but may require playwright browser setup.
        """
        try:
            self.username = get_config('TikTok', 'username')
            
            if not self.username:
                logger.warning("✗ TikTok username not configured")
                return False
            
            # Initialize TikTok API (playwright will be installed via requirements.txt)
            # Note: First run will download browser binaries
            self.api = TikTokApi()
            
            self.enabled = True
            logger.info(f"✓ TikTok initialized for @{self.username}")
            return True
            
        except Exception as e:
            logger.error(f"✗ TikTok initialization failed: {e}")
            logger.info("  Make sure playwright is installed: playwright install")
            self.enabled = False
            return False
    
    async def _get_latest_video_async(self, username: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
        """
        Get the latest video from a TikTok user (async).
        
        Args:
            username: TikTok username (without @). If not provided, uses configured username.
            
        Returns:
            Tuple of (success, video_data)
        """
        if not self.enabled or not self.api:
            return False, None
        
        target_username = username or self.username
        if not target_username:
            logger.error("No TikTok username provided")
            return False, None
        
        # Remove @ if present
        target_username = target_username.lstrip('@')
        
        try:
            # Create async context
            async with self.api:
                # Get user object
                user = self.api.user(target_username)
                
                # Get user's videos
                videos = []
                async for video in user.videos(count=5):  # Get last 5 videos
                    videos.append(video)
                
                if not videos:
                    logger.debug(f"No videos found for TikTok user: @{target_username}")
                    return False, None
                
                # Get the most recent video
                latest = videos[0]
                
                # Extract video data
                video_data = {
                    'video_id': latest.id,
                    'title': latest.desc or 'No description',  # TikTok uses 'desc' for caption
                    'url': f"https://www.tiktok.com/@{target_username}/video/{latest.id}",
                    'thumbnail_url': latest.video.cover if hasattr(latest, 'video') else None,
                    'published_at': datetime.fromtimestamp(latest.create_time) if hasattr(latest, 'create_time') else None,
                    'description': latest.desc,
                    'view_count': latest.stats.get('playCount') if hasattr(latest, 'stats') else None,
                    'like_count': latest.stats.get('diggCount') if hasattr(latest, 'stats') else None,
                    'comment_count': latest.stats.get('commentCount') if hasattr(latest, 'stats') else None,
                    'share_count': latest.stats.get('shareCount') if hasattr(latest, 'stats') else None,
                }
                
                return True, video_data
                
        except Exception as e:
            logger.error(f"Error fetching TikTok videos for @{target_username}: {e}")
            return False, None
    
    def get_latest_video(self, username: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
        """
        Get the latest video from a TikTok user (sync wrapper).
        
        Args:
            username: TikTok username (without @). If not provided, uses configured username.
            
        Returns:
            Tuple of (success, video_data)
        """
        try:
            # Run async function in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create new loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            return loop.run_until_complete(self._get_latest_video_async(username))
            
        except Exception as e:
            logger.error(f"Error in TikTok sync wrapper: {e}")
            return False, None
    
    def check_for_new_video(self, username: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
        """
        Check if there's a new video since last check.
        
        Args:
            username: TikTok username to check
            
        Returns:
            Tuple of (is_new, video_data) - is_new is True only if video is newer than last check
        """
        success, video_data = self.get_latest_video(username)
        
        if not success or not video_data:
            return False, None
        
        current_video_id = video_data.get('video_id')
        
        # Check if this is a new video
        if self.last_video_id is None:
            # First run - don't notify, just track
            logger.info(f"📹 TikTok: Initialized tracking for @{username or self.username}")
            self.last_video_id = current_video_id
            return False, None
        
        if current_video_id != self.last_video_id:
            # New video detected!
            logger.info(f"🎬 TikTok: New video from @{username or self.username}: {video_data.get('title')[:50]}...")
            self.last_video_id = current_video_id
            return True, video_data
        
        # Same video as before
        return False, None


# Alternative implementation using web scraping (more reliable but less data)
class TikTokScraperPlatform(MediaPlatform):
    """
    Alternative TikTok implementation using web scraping.
    More reliable but provides less data and may be blocked.
    """
    
    def __init__(self):
        super().__init__("TikTok-Scraper")
        self.username = None
        self.last_video_id = None
        self.session = None
        
    def authenticate(self) -> bool:
        """Initialize web scraper."""
        try:
            import requests
            
            self.username = get_config('TikTok', 'username')
            if not self.username:
                logger.warning("✗ TikTok username not configured")
                return False
            
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            self.enabled = True
            logger.info(f"✓ TikTok scraper initialized for @{self.username}")
            return True
            
        except Exception as e:
            logger.error(f"✗ TikTok scraper initialization failed: {e}")
            return False
    
    def get_latest_video(self, username: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
        """
        Scrape latest video from TikTok profile page.
        
        Note: This is a simplified implementation. TikTok's page structure
        may change and break this scraper.
        """
        if not self.enabled or not self.session:
            return False, None
        
        target_username = username or self.username
        if not target_username:
            return False, None
        
        target_username = target_username.lstrip('@')
        
        try:
            # Try to fetch user's profile page
            url = f"https://www.tiktok.com/@{target_username}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"TikTok profile fetch failed: HTTP {response.status_code}")
                return False, None
            
            # Parse HTML to extract video data
            # This is a placeholder - actual implementation would need to parse
            # JavaScript or use an HTML parser like BeautifulSoup
            # TikTok renders content with JavaScript, making scraping difficult
            
            logger.warning("TikTok scraper needs implementation - use TikTokApi instead")
            return False, None
            
        except Exception as e:
            logger.error(f"Error scraping TikTok: {e}")
            return False, None
