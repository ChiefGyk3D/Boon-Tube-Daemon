# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
LLM integration module for Boon-Tube-Daemon.

Integrates Google Gemini Flash 2.0 Lite for intelligent content analysis,
summary generation, and enhanced notifications.
"""

from boon_tube_daemon.llm.gemini import GeminiLLM

__all__ = [
    'GeminiLLM',
]
