#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Pytest configuration and fixtures for Boon-Tube-Daemon tests.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run slow integration tests that require real credentials"
    )


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests requiring credentials"
    )


@pytest.fixture(scope="module")
def youtube():
    """
    Create a YouTube platform instance for testing.
    Requires YOUTUBE_API_KEY and YOUTUBE_USERNAME/YOUTUBE_CHANNEL_ID.
    """
    from boon_tube_daemon.media.youtube_videos import YouTubeVideosPlatform
    
    yt = YouTubeVideosPlatform()
    if not yt.authenticate():
        pytest.skip("YouTube authentication failed - check API credentials")
    
    return yt
