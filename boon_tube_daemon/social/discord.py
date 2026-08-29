# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Discord posting now lives in hypeman-social; this module keeps the old
import path working. Construct with default_event_kind=EVENT_UPLOAD so
announcements get the "New Video" embed rather than the "Live" one.
"""

from hypeman_social.social.base import EVENT_UPLOAD
from hypeman_social.social.discord import DiscordPlatform

__all__ = ['DiscordPlatform', 'EVENT_UPLOAD']
