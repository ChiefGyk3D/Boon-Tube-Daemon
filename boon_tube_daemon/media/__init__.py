# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Media platform monitoring modules."""

from boon_tube_daemon.media.base import MediaPlatform
from boon_tube_daemon.media.youtube_videos import YouTubeVideosPlatform

# TikTok support is optional (requires Playwright)
try:
    from boon_tube_daemon.media.tiktok import TikTokPlatform
    _TIKTOK_AVAILABLE = True
except ImportError:
    TikTokPlatform = None
    _TIKTOK_AVAILABLE = False

__all__ = [
    'MediaPlatform',
    'YouTubeVideosPlatform',
    'TikTokPlatform',
]
