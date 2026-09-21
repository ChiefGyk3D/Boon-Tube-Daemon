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
    TikTokPlatform,
    YouTubeVideosPlatform,
)
from boon_tube_daemon.social import (
    BlueskyPlatform,
    DiscordPlatform,
    MastodonPlatform,
    MatrixPlatform,
)
from boon_tube_daemon.utils.config import (
    get_bool_config,
    get_config,
    get_int_config,
    get_secret,
    load_config,
)

__all__ = [
    'BlueskyPlatform',
    'DiscordPlatform',
    'MastodonPlatform',
    'MatrixPlatform',
    'MediaPlatform',
    'TikTokPlatform',
    'YouTubeVideosPlatform',
    '__author__',
    '__license__',
    '__version__',
    'get_bool_config',
    'get_config',
    'get_int_config',
    'get_secret',
    'load_config',
]
