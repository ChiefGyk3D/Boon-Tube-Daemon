#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Unit tests for Boon-Tube-Daemon
These tests don't require API keys or external services.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestImports:
    """Test that all modules can be imported."""
    
    def test_import_main(self):
        """Test that main module can be imported."""
        from boon_tube_daemon import main
        assert hasattr(main, 'BoonTubeDaemon')
    
    def test_import_config(self):
        """Test that config utils can be imported."""
        from boon_tube_daemon.utils import config
        assert hasattr(config, 'load_config')
        assert hasattr(config, 'get_config')
    
    def test_import_youtube(self):
        """Test that YouTube platform can be imported."""
        from boon_tube_daemon.media import youtube_videos
        assert hasattr(youtube_videos, 'YouTubeVideosPlatform')
    
    def test_import_discord(self):
        """Test that Discord platform can be imported."""
        from boon_tube_daemon.social import discord
        assert hasattr(discord, 'DiscordPlatform')
    
    def test_import_matrix(self):
        """Test that Matrix platform can be imported."""
        from boon_tube_daemon.social import matrix
        assert hasattr(matrix, 'MatrixPlatform')
    
    def test_import_bluesky(self):
        """Test that Bluesky platform can be imported."""
        from boon_tube_daemon.social import bluesky
        assert hasattr(bluesky, 'BlueskyPlatform')
    
    def test_import_mastodon(self):
        """Test that Mastodon platform can be imported."""
        from boon_tube_daemon.social import mastodon
        assert hasattr(mastodon, 'MastodonPlatform')
    
    def test_import_gemini_llm(self):
        """Test that Gemini LLM can be imported."""
        from boon_tube_daemon.llm import gemini
        assert hasattr(gemini, 'GeminiLLM')


class TestDaemonInitialization:
    """Test daemon initialization without authentication."""
    
    def test_daemon_instance(self):
        """Test that daemon can be instantiated."""
        from boon_tube_daemon.main import BoonTubeDaemon
        daemon = BoonTubeDaemon()
        assert daemon is not None
        assert daemon.running == False
        assert daemon.media_platforms == []
        assert daemon.social_platforms == []
        assert daemon.check_interval == 900  # 15 minutes default


class TestConfiguration:
    """Test configuration handling."""
    
    def test_config_defaults(self):
        """Test that config functions work with defaults."""
        from boon_tube_daemon.utils.config import get_bool_config, get_int_config
        
        # Test with non-existent values (should return defaults)
        assert get_bool_config('NonExistent', 'test', default=True) == True
        assert get_bool_config('NonExistent', 'test', default=False) == False
        assert get_int_config('NonExistent', 'test', default=42) == 42


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
