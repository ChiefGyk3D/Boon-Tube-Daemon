# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Base class for media platform monitoring.
"""

from typing import Optional, Tuple
from abc import ABC, abstractmethod


class MediaPlatform(ABC):
    """Base class for media platforms (YouTube, TikTok, etc.)."""
    
    def __init__(self, name: str):
        """
        Initialize platform.
        
        Args:
            name: Platform name (e.g., "YouTube", "TikTok")
        """
        self.name = name
        self.enabled = False
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the platform API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_latest_video(self, username: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
        """
        Get the latest video from a channel/user.
        
        Args:
            username: Username/handle to check
            
        Returns:
            Tuple of (success, video_data) where video_data contains:
            - video_id: Unique video identifier
            - title: Video title
            - url: Video URL
            - thumbnail_url: Video thumbnail URL
            - published_at: Publication timestamp
            - description: Video description (optional)
        """
        raise NotImplementedError
