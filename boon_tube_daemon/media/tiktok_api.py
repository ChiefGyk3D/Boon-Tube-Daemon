"""
TikTok Official API implementation for monitoring video uploads.

Uses TikTok's official Developer API (https://developers.tiktok.com/)
Requires:
- TIKTOK_CLIENT_KEY (from Doppler)
- TIKTOK_CLIENT_SECRET (from Doppler)
- TIKTOK_USERNAME (from .env)

API Documentation: https://developers.tiktok.com/doc/login-kit-web
"""

import logging
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Tuple
from boon_tube_daemon.media.base import MediaPlatform
from boon_tube_daemon.utils.config import get_config, get_secret

logger = logging.getLogger(__name__)


class TikTokAPIPlatform(MediaPlatform):
    """TikTok platform using official API for monitoring new video uploads."""
    
    def __init__(self):
        super().__init__("TikTok")
        self.username = None
        self.client_key = None
        self.client_secret = None
        self.access_token = None
        self.last_video_id = None
        
    def authenticate(self) -> bool:
        """
        Initialize TikTok API monitoring.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Get configuration
            self.username = get_config("TikTok", "username")
            self.client_key = get_secret("TikTok", "client_key")
            self.client_secret = get_secret("TikTok", "client_secret")
            
            if not self.username:
                logger.warning("✗ TikTok username not configured")
                return False
            
            # Remove @ prefix if present
            if self.username.startswith("@"):
                self.username = self.username[1:]
            
            if not self.client_key or not self.client_secret:
                logger.warning("✗ TikTok API credentials not configured (TIKTOK_CLIENT_KEY/SECRET)")
                logger.info("  Falling back to Playwright scraping (if available)")
                return False
            
            self.enabled = True
            logger.info(f"✓ TikTok API configured for @{self.username}")
            return True
            
        except Exception as e:
            logger.error(f"✗ TikTok API authentication failed: {e}")
            self.enabled = False
            return False
    
    def _get_access_token(self) -> Optional[str]:
        """
        Get access token using client credentials flow.
        
        For TikTok API, you typically need to:
        1. Get authorization code via OAuth flow (requires user interaction)
        2. Exchange code for access token
        
        Since this is a server-side daemon, we'll need to handle this differently.
        TikTok requires manual OAuth flow first time to get refresh token.
        
        Returns:
            Access token or None
        """
        # TODO: Implement OAuth flow
        # For now, we'll need to store the access token in Doppler after manual OAuth
        token = get_secret("TikTok", "access_token")
        if token:
            logger.debug("Using stored TikTok access token")
            return token
        
        logger.warning("No TikTok access token found. Please complete OAuth flow first.")
        return None
    
    def get_latest_video(self, username: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
        """
        Get the latest video from a TikTok account using official API.
        
        Args:
            username: Optional username to check (defaults to configured username)
            
        Returns:
            Tuple of (success, video_data)
        """
        if not self.enabled:
            return False, None
        
        # Get access token
        access_token = self._get_access_token()
        if not access_token:
            logger.error("No TikTok access token available")
            return False, None
        
        username_to_check = username if username else self.username
        
        try:
            # TikTok API endpoint for user videos
            # https://developers.tiktok.com/doc/display-api-get-user-info
            url = "https://open.tiktokapis.com/v2/video/list/"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "fields": "id,title,video_description,duration,cover_image_url,create_time,like_count,view_count,share_count,comment_count"
            }
            
            response = requests.post(url, headers=headers, json=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("data") or not data["data"].get("videos"):
                logger.debug(f"No videos found for @{username_to_check}")
                return False, None
            
            # Get the most recent video
            videos = data["data"]["videos"]
            latest_video = videos[0]  # API returns sorted by create_time desc
            
            # Build video info
            video_info = {
                "video_id": latest_video.get("id"),
                "title": latest_video.get("title") or latest_video.get("video_description", "")[:100],
                "description": latest_video.get("video_description", ""),
                "url": f"https://www.tiktok.com/@{username_to_check}/video/{latest_video.get('id')}",
                "thumbnail_url": latest_video.get("cover_image_url"),
                "published_at": datetime.fromtimestamp(latest_video.get("create_time", 0), tz=timezone.utc),
                "author": username_to_check,
                "stats": {
                    "plays": latest_video.get("view_count", 0),
                    "likes": latest_video.get("like_count", 0),
                    "comments": latest_video.get("comment_count", 0),
                    "shares": latest_video.get("share_count", 0),
                }
            }
            
            logger.debug(f"✓ Found video: {video_info['title'][:50]}")
            return True, video_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"TikTok API request failed: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error getting TikTok video: {e}")
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
        
        current_video_id = video_data.get("video_id")
        
        # Check if this is a new video
        if self.last_video_id is None:
            # First run - don't notify, just track
            logger.info(f"📱 TikTok: Initialized tracking for @{self.username}")
            self.last_video_id = current_video_id
            return False, None
        
        if current_video_id != self.last_video_id:
            # New video detected!
            logger.info(f"📱 TikTok: New video: {video_data.get('title', '')[:50]}...")
            self.last_video_id = current_video_id
            return True, video_data
        
        # Same video as before
        return False, None
