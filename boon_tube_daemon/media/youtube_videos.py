# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
YouTube video upload monitoring platform.

This module monitors YouTube channels for new video uploads (not live streams).
Uses the YouTube Data API v3 with efficient quota management.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from googleapiclient.discovery import build

from boon_tube_daemon.utils.config import get_config, get_int_config, get_secret
from boon_tube_daemon.media.base import MediaPlatform

logger = logging.getLogger(__name__)

# Default state file location (can be overridden by config)
DEFAULT_STATE_DIR = Path("/app/config")
STATE_FILENAME = "youtube_state.json"


class YouTubeVideosPlatform(MediaPlatform):
    """YouTube platform for monitoring new video uploads."""
    
    # Default: 0 = off (don't post on first run). Set YOUTUBE_RECENT_VIDEO_HOURS to enable.
    DEFAULT_RECENT_VIDEO_HOURS = 0
    
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
        self._state_file_path = None
        self.recent_video_hours = self.DEFAULT_RECENT_VIDEO_HOURS
        self.recent_video_window = timedelta(hours=self.recent_video_hours)
        
    def _get_state_file_path(self) -> Path:
        """Get the path to the state file, creating directory if needed."""
        if self._state_file_path:
            return self._state_file_path
            
        # Try config directory first (for Docker), fall back to local
        state_dir = get_config('Settings', 'state_dir', default=str(DEFAULT_STATE_DIR))
        state_path = Path(state_dir)
        
        # Fall back to current directory if config dir doesn't exist
        if not state_path.exists():
            state_path = Path(".")
            
        self._state_file_path = state_path / STATE_FILENAME
        return self._state_file_path
    
    def _load_state(self) -> dict:
        """Load persisted state from disk."""
        try:
            state_file = self._get_state_file_path()
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    logger.debug(f"📂 Loaded YouTube state from {state_file}")
                    return state
        except Exception:
            logger.warning("⚠ Could not load YouTube state")
        return {}
    
    def _save_state(self):
        """Persist current state to disk."""
        try:
            state_file = self._get_state_file_path()
            state = {
                'last_video_id': self.last_video_id,
                'channel_id': self.channel_id,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug(f"💾 Saved YouTube state to {state_file}")
        except Exception:
            logger.warning("⚠ Could not save YouTube state")

    def mark_posted(self, video_data: dict):
        """Advance and persist the last-posted marker after a video is posted.

        Called by the daemon after each video is successfully handled so that an
        interrupted batch resumes from the next unposted video rather than
        silently skipping the remainder.
        """
        video_id = video_data.get('video_id')
        if video_id:
            self.last_video_id = video_id
            self._save_state()
        
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
            
            # Load persisted state (last_video_id)
            state = self._load_state()
            if state.get('last_video_id'):
                # Verify the state is for the same channel
                if state.get('channel_id') == self.channel_id:
                    self.last_video_id = state['last_video_id']
                    logger.info(f"📂 Restored last video ID: {self.last_video_id}")
                else:
                    logger.info("📂 State file is for different channel, starting fresh")
            
            # Configure recent video window (for first-run / restart catch-up)
            self.recent_video_hours = get_int_config('YouTube', 'recent_video_hours', default=self.DEFAULT_RECENT_VIDEO_HOURS)
            self.recent_video_window = timedelta(hours=self.recent_video_hours)
            
            self.enabled = True
            self.consecutive_errors = 0
            logger.info(f"✓ YouTube Videos authenticated for channel: {self.channel_id}")
            if self.recent_video_hours > 0:
                logger.info(f"⏰ Recent video window: {self.recent_video_hours}h (post on first run if within this window)")
            else:
                logger.info("⏰ Recent video window: disabled (won't post on first run)")
            return True
            
        except Exception:
            logger.error("✗ YouTube authentication failed")
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
            
        except Exception:
            logger.error("Error resolving YouTube channel ID")
            return None
    
    def _check_quota_cooldown(self) -> bool:
        """Check if we're in quota cooldown. Returns True if we should skip."""
        if self.quota_exceeded:
            if self.quota_exceeded_time:
                time_since_quota_error = datetime.now() - self.quota_exceeded_time
                if time_since_quota_error < timedelta(hours=1):
                    logger.debug("YouTube API quota exceeded, skipping check")
                    return True
                else:
                    self.quota_exceeded = False
                    self.quota_exceeded_time = None
                    self.consecutive_errors = 0
        return False

    def _resolve_check_channel(self, username: Optional[str] = None) -> Optional[str]:
        """Determine which channel ID to use for a check."""
        if username and username != self.username:
            channel_id = self._resolve_channel_id(username)
            if not channel_id:
                logger.warning(f"Could not resolve YouTube channel ID for: {username}")
            return channel_id
        return self.channel_id

    def _extract_video_info(self, video: dict) -> dict:
        """Extract standardized video info from a YouTube API video resource."""
        snippet = video.get('snippet', {})
        statistics = video.get('statistics', {})
        video_id = video['id']
        return {
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

    def _fetch_recent_uploads(self, channel_id: str) -> Tuple[bool, List[dict]]:
        """
        Fetch recent non-livestream uploads for a channel.
        
        Returns:
            Tuple of (success, list_of_video_info) ordered newest-first
        """
        try:
            # Get channel's uploads playlist (1 unit)
            request = self.client.channels().list(
                part="contentDetails",
                id=channel_id
            )
            response = request.execute()
            
            if not response.get('items'):
                logger.debug(f"No YouTube channel found for ID: {channel_id}")
                return False, []
            
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get recent uploads (up to 10)
            playlist_request = self.client.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=10
            )
            playlist_response = playlist_request.execute()
            
            if not playlist_response.get('items'):
                logger.debug("No uploads found for YouTube channel")
                return False, []
            
            # Get video IDs for batch lookup
            video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_response['items']]
            
            # Get video details for all videos (1 unit)
            video_request = self.client.videos().list(
                part="snippet,contentDetails,statistics,liveStreamingDetails",
                id=','.join(video_ids)
            )
            video_response = video_request.execute()
            
            if not video_response.get('items'):
                return False, []
            
            # Filter out livestreams, keep order (newest first)
            videos = []
            for video in video_response['items']:
                if 'liveStreamingDetails' in video:
                    logger.debug(f"Skipping livestream: {video['snippet']['title'][:50]}")
                    continue
                videos.append(self._extract_video_info(video))
            
            self.consecutive_errors = 0
            return True, videos
            
        except Exception as e:
            self.consecutive_errors += 1
            error_str = str(e)
            if 'quotaExceeded' in error_str or 'quota' in error_str.lower():
                if not self.quota_exceeded:
                    self.quota_exceeded = True
                    self.quota_exceeded_time = datetime.now()
                    logger.error("❌ YouTube API quota exceeded! Pausing checks for 1 hour.")
            else:
                logger.error("⚠ Error checking YouTube")
            return False, []

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
        
        if self._check_quota_cooldown():
            return False, None
        
        channel_id = self._resolve_check_channel(username)
        if not channel_id:
            logger.error("No YouTube channel ID available")
            return False, None
        
        success, videos = self._fetch_recent_uploads(channel_id)
        if not success or not videos:
            return False, None
        
        return True, videos[0]

    def get_video_by_id(self, video_id: str) -> Tuple[bool, Optional[dict]]:
        """
        Fetch details for a specific video by ID (for one-off posting).
        
        Args:
            video_id: YouTube video ID (e.g. 'dFzv3XCiio8')
            
        Returns:
            Tuple of (success, video_data)
        """
        if not self.enabled or not self.client:
            return False, None
        
        if self._check_quota_cooldown():
            return False, None
        
        try:
            video_request = self.client.videos().list(
                part="snippet,contentDetails,statistics,liveStreamingDetails",
                id=video_id
            )
            video_response = video_request.execute()
            
            if not video_response.get('items'):
                logger.warning(f"Video not found: {video_id}")
                return False, None
            
            video = video_response['items'][0]
            video_info = self._extract_video_info(video)
            self.consecutive_errors = 0
            return True, video_info
            
        except Exception:
            self.consecutive_errors += 1
            logger.error(f"⚠ Error fetching video {video_id}")
            return False, None
    
    def check_for_new_video(self, username: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
        """
        Check if there's a new video since last check (single-video compat).
        Returns the newest new video only. Use check_for_new_videos() to get all.
        """
        new_videos = self.check_for_new_videos(username)
        if new_videos:
            return True, new_videos[-1]  # newest
        return False, None

    def check_for_new_videos(self, username: Optional[str] = None) -> List[dict]:
        """
        Check for ALL new videos since last check.
        
        Returns videos in chronological order (oldest first) so they can be
        posted in the order they were published.
        
        Args:
            username: YouTube username to check
            
        Returns:
            List of video_data dicts (empty if none new)
        """
        if not self.enabled or not self.client:
            return []
        
        if self._check_quota_cooldown():
            return []
        
        channel_id = self._resolve_check_channel(username)
        if not channel_id:
            logger.error("No YouTube channel ID available")
            return []
        
        success, videos = self._fetch_recent_uploads(channel_id)
        if not success or not videos:
            return []
        
        newest_video = videos[0]
        newest_id = newest_video.get('video_id')
        
        # First run: initialize tracking
        if self.last_video_id is None:
            published_at = newest_video.get('published_at')
            if self.recent_video_hours > 0 and published_at:
                now = datetime.now(timezone.utc)
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=timezone.utc)
                time_since_published = now - published_at
                if time_since_published < self.recent_video_window:
                    logger.info(f"📹 YouTube: First check - found recent video (published {time_since_published.total_seconds() / 60:.0f} min ago)")
                    logger.info(f"🎬 YouTube: Posting recent video: {newest_video.get('title')[:50]}...")
                    self.last_video_id = newest_id
                    self._save_state()
                    return [newest_video]
                logger.info(f"📹 YouTube: Initialized tracking (video published {time_since_published.total_seconds() / 3600:.1f}h ago)")
            else:
                logger.info("📹 YouTube: Initialized tracking for channel" + 
                           (" (recent video window disabled)" if self.recent_video_hours <= 0 else ""))
            self.last_video_id = newest_id
            self._save_state()
            return []
        
        # Same video as last time — nothing new
        if newest_id == self.last_video_id:
            return []
        
        # Find ALL new videos since last_video_id
        # videos is newest-first; collect until we hit the one we already posted
        new_videos = []
        for video in videos:
            if video.get('video_id') == self.last_video_id:
                break
            new_videos.append(video)
        
        if not new_videos:
            # last_video_id wasn't found in the list (scrolled off), treat newest as new
            new_videos = [newest_video]
        
        # Reverse to chronological order (oldest first)
        new_videos.reverse()
        
        for v in new_videos:
            logger.info(f"🎬 YouTube: New video: {v.get('title')[:50]}...")
        
        if len(new_videos) > 1:
            logger.info(f"📦 YouTube: {len(new_videos)} new videos detected since last check")
        
        # NOTE: Do NOT advance last_video_id here. State is advanced per-video via
        # mark_posted() after each video is successfully posted, so an interrupted
        # batch (e.g. container restart) resumes from the next unposted video
        # instead of silently skipping the remainder.
        return new_videos
    
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
        except Exception:
            logger.warning(f"Error resolving YouTube channel ID for {username}")
            return None
