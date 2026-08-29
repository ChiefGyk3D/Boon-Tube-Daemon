# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
LLM integration for Boon-Tube-Daemon, built on hypeman-social.

VideoPostGenerator is the class the daemon uses: it follows LLM_PROVIDER
config, supports LLM_FALLBACK_PROVIDER failover, and knows what a video
announcement should look like. OllamaLLM and GeminiLLM remain as pinned
compatibility wrappers.
"""

from boon_tube_daemon.llm.gemini import GeminiLLM
from boon_tube_daemon.llm.generator import VideoPostGenerator
from boon_tube_daemon.llm.ollama import OllamaLLM

__all__ = [
    'VideoPostGenerator',
    'GeminiLLM',
    'OllamaLLM',
]
