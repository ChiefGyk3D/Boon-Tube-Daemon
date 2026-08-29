# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Social platform notification modules.

Implementations live in hypeman-social (shared with stream-daemon,
Star-Daemon, and yomama-as-a-service); these re-exports keep Boon-Tube's
historical import paths working.
"""

from boon_tube_daemon.social.bluesky import BlueskyPlatform
from boon_tube_daemon.social.discord import DiscordPlatform
from boon_tube_daemon.social.mastodon import MastodonPlatform
from boon_tube_daemon.social.matrix import MatrixPlatform

__all__ = [
    'DiscordPlatform',
    'MatrixPlatform',
    'BlueskyPlatform',
    'MastodonPlatform',
]
