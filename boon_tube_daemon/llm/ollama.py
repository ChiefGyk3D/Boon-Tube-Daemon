# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Compatibility wrapper: Ollama-backed video announcements.

The Ollama provider itself (connection handling, retries, auto-reconnect,
guardrails) lives in hypeman-social. This class pins the generator to Ollama
for callers and tests that target the local backend specifically; new code
should prefer VideoPostGenerator, which follows LLM_PROVIDER config and
supports failover.
"""

from boon_tube_daemon.llm.generator import VideoPostGenerator

__all__ = ['OllamaLLM']


class OllamaLLM(VideoPostGenerator):
    """Video announcement generation pinned to a local Ollama server."""

    def __init__(self):
        super().__init__(provider='ollama')
