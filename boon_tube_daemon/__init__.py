# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Boon-Tube-Daemon - YouTube and TikTok Upload Monitor

A daemon for monitoring YouTube and TikTok video uploads and posting
notifications to Discord, Matrix, Bluesky, and Mastodon.
"""

__version__ = "1.0.0"
__author__ = "chiefgyk3d"
__license__ = "MIT"

from boon_tube_daemon.media import (
    MediaPlatform,
    YouTubeVideosPlatform,
    TikTokPlatform,
)

from boon_tube_daemon.social import (
    DiscordPlatform,
    MatrixPlatform,
    BlueskyPlatform,
    MastodonPlatform,
)

from boon_tube_daemon.utils.config import (
    load_config,
    get_config,
    get_bool_config,
    get_int_config,
    get_secret,
)

__all__ = [
    # Media platforms
    'MediaPlatform',
    'YouTubeVideosPlatform',
    'TikTokPlatform',
    # Social platforms
    'DiscordPlatform',
    'MatrixPlatform',
    'BlueskyPlatform',
    'MastodonPlatform',
    # Configuration
    'load_config',
    'get_config',
    'get_bool_config',
    'get_int_config',
    'get_secret',
    # Metadata
    '__version__',
    '__author__',
    '__license__',
]
