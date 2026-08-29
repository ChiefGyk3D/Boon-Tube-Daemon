# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Compatibility wrapper: Gemini-backed video announcements.

The Gemini provider itself (API client, rate limiting, retries, guardrails)
lives in hypeman-social. This class pins the generator to Gemini for callers
and tests that target the cloud backend specifically; new code should prefer
VideoPostGenerator, which follows LLM_PROVIDER config and supports failover.
"""

from boon_tube_daemon.llm.generator import VideoPostGenerator

__all__ = ['GeminiLLM']


class GeminiLLM(VideoPostGenerator):
    """Video announcement generation pinned to the Gemini API."""

    def __init__(self):
        super().__init__(provider='gemini')
