# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
YouTube video upload monitoring platform.

This module monitors YouTube channels for new video uploads (not live streams).
Uses the YouTube Data API v3 with efficient quota management.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from googleapiclient.discovery import build

from boon_tube_daemon.utils.config import get_config, get_secret
from boon_tube_daemon.media.base import MediaPlatform

logger = logging.getLogger(__name__)


class YouTubeVideosPlatform(MediaPlatform):
    """YouTube platform for monitoring new video uploads."""
    
    def __init__(self):
        super().__init__("YouTube-Videos")
        self.client = None
        self.channel_id = None
        self.username = None
        self.quota_exceeded = False
        self.quota_exceeded_time = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        self.last_video_id = None
        
    def authenticate(self) -> bool:
        """Authenticate with YouTube API."""
        try:
            api_key = get_secret('YouTube', 'api_key')
            self.username = get_config('YouTube', 'username')
            self.channel_id = get_config('YouTube', 'channel_id')
            
            if not api_key:
                logger.warning("✗ YouTube API key not found")
                return False
                
            if not self.username and not self.channel_id:
                logger.warning("✗ YouTube username or channel_id not configured")
                return False
                
            self.client = build('youtube', 'v3', developerKey=api_key)
            
            # If channel_id not provided, look it up by username/handle
            if not self.channel_id:
                self.channel_id = self._get_channel_id_from_username()
                if not self.channel_id:
                    logger.warning(f"✗ Could not find YouTube channel for username: {self.username}")
                    return False
            
            self.enabled = True
            self.consecutive_errors = 0
            logger.info(f"✓ YouTube Videos authenticated for channel: {self.channel_id}")
            return True
            
        except Exception as e:
            logger.error(f"✗ YouTube authentication failed: {e}")
            self.enabled = False
            return False
    
    def _get_channel_id_from_username(self) -> Optional[str]:
        """Convert username/handle to channel ID."""
        try:
            lookup_username = self.username if self.username.startswith('@') else f'@{self.username}'
            
            # Try modern handle format first (@username)
            try:
                request = self.client.channels().list(
                    part="id",
                    forHandle=lookup_username
                )
                response = request.execute()
                if response.get('items'):
                    channel_id = response['items'][0]['id']
                    logger.info(f"✓ Resolved YouTube channel ID: {channel_id}")
                    return channel_id
            except Exception as e:
                logger.debug(f"Handle lookup failed for {lookup_username}: {e}")
            
            # Try legacy username
            if not self.username.startswith('@'):
                try:
                    request = self.client.channels().list(
                        part="id",
                        forUsername=self.username
                    )
                    response = request.execute()
                    if response.get('items'):
                        channel_id = response['items'][0]['id']
                        logger.info(f"✓ Resolved YouTube channel ID: {channel_id}")
                        return channel_id
                except Exception as e:
                    logger.debug(f"Username lookup failed for {self.username}: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error resolving YouTube channel ID: {e}")
            return None
    
    def get_latest_video(self, username: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
        """
        Get the latest video from a YouTube channel.
        
        Args:
            username: Optional username/handle to check
            
        Returns:
            Tuple of (success, video_data)
        """
        if not self.enabled or not self.client:
            return False, None
        
        # Check quota cooldown
        if self.quota_exceeded:
            if self.quota_exceeded_time:
                time_since_quota_error = datetime.now() - self.quota_exceeded_time
                if time_since_quota_error < timedelta(hours=1):
                    logger.debug(f"YouTube API quota exceeded, skipping check")
                    return False, None
                else:
                    self.quota_exceeded = False
                    self.quota_exceeded_time = None
                    self.consecutive_errors = 0
        
        # Determine which channel to check
        channel_id_to_check = None
        
        if username and username != self.username:
            channel_id_to_check = self._resolve_channel_id(username)
            if not channel_id_to_check:
                logger.warning(f"Could not resolve YouTube channel ID for: {username}")
                return False, None
        else:
            channel_id_to_check = self.channel_id
        
        if not channel_id_to_check:
            logger.error("No YouTube channel ID available")
            return False, None
        
        try:
            # Get channel's uploads playlist (1 unit)
            request = self.client.channels().list(
                part="contentDetails",
                id=channel_id_to_check
            )
            response = request.execute()
            
            if not response.get('items'):
                logger.debug(f"No YouTube channel found for ID: {channel_id_to_check}")
                return False, None
            
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get the most recent upload (1 unit)
            playlist_request = self.client.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=1
            )
            playlist_response = playlist_request.execute()
            
            if not playlist_response.get('items'):
                logger.debug(f"No uploads found for YouTube channel")
                return False, None
            
            video_id = playlist_response['items'][0]['snippet']['resourceId']['videoId']
            
            # Get video details (1 unit)
            video_request = self.client.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
            )
            video_response = video_request.execute()
            
            if not video_response.get('items'):
                return False, None
            
            video_data = video_response['items'][0]
            snippet = video_data.get('snippet', {})
            statistics = video_data.get('statistics', {})
            
            # Extract video information
            video_info = {
                'video_id': video_id,
                'title': snippet.get('title', 'Untitled'),
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url'),
                'published_at': datetime.fromisoformat(snippet.get('publishedAt', '').replace('Z', '+00:00')) if snippet.get('publishedAt') else None,
                'description': snippet.get('description', ''),
                'view_count': int(statistics.get('viewCount', 0)) if statistics.get('viewCount') else None,
                'like_count': int(statistics.get('likeCount', 0)) if statistics.get('likeCount') else None,
                'comment_count': int(statistics.get('commentCount', 0)) if statistics.get('commentCount') else None,
            }
            
            # Reset error counter on success
            self.consecutive_errors = 0
            return True, video_info
            
        except Exception as e:
            self.consecutive_errors += 1
            error_str = str(e)
            if 'quotaExceeded' in error_str or 'quota' in error_str.lower():
                if not self.quota_exceeded:
                    self.quota_exceeded = True
                    self.quota_exceeded_time = datetime.now()
                    logger.error(f"❌ YouTube API quota exceeded! Pausing checks for 1 hour.")
            else:
                logger.error(f"⚠ Error checking YouTube: {e}")
            return False, None
    
    def check_for_new_video(self, username: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
        """
        Check if there's a new video since last check.
        
        Args:
            username: YouTube username to check
            
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
            logger.info(f"📹 YouTube: Initialized tracking for channel")
            self.last_video_id = current_video_id
            return False, None
        
        if current_video_id != self.last_video_id:
            # New video detected!
            logger.info(f"🎬 YouTube: New video: {video_data.get('title')[:50]}...")
            self.last_video_id = current_video_id
            return True, video_data
        
        # Same video as before
        return False, None
    
    def _resolve_channel_id(self, username: str) -> Optional[str]:
        """Resolve a channel ID from a username/handle."""
        try:
            lookup_username = username if username.startswith('@') else f'@{username}'
            
            request = self.client.channels().list(
                part="id",
                forHandle=lookup_username
            )
            response = request.execute()
            if response.get('items'):
                return response['items'][0]['id']
            
            if not username.startswith('@'):
                request = self.client.channels().list(
                    part="id",
                    forUsername=username
                )
                response = request.execute()
                if response.get('items'):
                    return response['items'][0]['id']
            
            return None
        except Exception as e:
            logger.warning(f"Error resolving YouTube channel ID for {username}: {e}")
            return None
