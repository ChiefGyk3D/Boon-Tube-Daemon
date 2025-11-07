#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Integration tests for Boon-Tube-Daemon.
Tests the full workflow: initialization -> monitoring -> detection
"""

import pytest
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from boon_tube_daemon.main import BoonTubeDaemon


class TestDaemonIntegration:
    """Integration tests for the complete daemon workflow."""
    
    @pytest.fixture(scope="class")
    def daemon(self):
        """Create and initialize a daemon instance for testing."""
        daemon = BoonTubeDaemon()
        # Don't fail if initialization has issues in test environment
        # Just return the daemon so we can test what we can
        daemon.initialize()
        return daemon
    
    def test_daemon_creation(self):
        """Test that daemon can be instantiated."""
        daemon = BoonTubeDaemon()
        assert daemon is not None
        assert hasattr(daemon, 'media_platforms')
        assert hasattr(daemon, 'social_platforms')
        assert hasattr(daemon, 'check_interval')
    
    def test_daemon_initialization(self, daemon):
        """Test that daemon initializes its platforms."""
        # Check that media platforms list exists (may be empty in test env)
        assert hasattr(daemon, 'media_platforms')
        assert isinstance(daemon.media_platforms, list)
        
        # Check that social platforms list exists
        assert hasattr(daemon, 'social_platforms')
        assert isinstance(daemon.social_platforms, list)
    
    def test_daemon_has_check_method(self, daemon):
        """Test that daemon has the check_platforms method."""
        assert hasattr(daemon, 'check_platforms')
        assert callable(daemon.check_platforms)
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_platform_check_cycle(self, daemon, request):
        """
        Test a complete check cycle (requires real credentials).
        This test is slow and requires actual platform access.
        Run with: pytest -v --run-integration
        """
        # Skip if --run-integration flag not provided
        if not request.config.getoption("--run-integration"):
            pytest.skip("Requires --run-integration flag")
        
        if not daemon.media_platforms:
            pytest.skip("No media platforms configured")
        
        # First check to establish baseline
        daemon.check_platforms()
        
        # Second check should not find new videos
        time.sleep(3)
        daemon.check_platforms()
