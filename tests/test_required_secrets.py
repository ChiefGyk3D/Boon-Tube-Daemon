# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Required secrets: one placeholder rule, and fail closed on empty or
placeholder values, without ever printing the value.
"""

import logging
import os

import pytest

from boon_tube_daemon import main as daemon_main
from boon_tube_daemon.utils import required_secrets as rs

# Every style that appears in .env.example, plus the ones the old rule missed.
PLACEHOLDERS = [
    "YOUR_YOUTUBE_API_KEY",
    "your_vault_token",
    "Your_Mixed_Case",
    "dp.st.your_token_here",
    "DP.ST.YOUR_TOKEN",
    "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN",
    "https://discord.com/api/webhooks/your_id/your_token",
    "YOUR_HANDLE.bsky.social",
    "changeme",
    "ChangeMe123",
    "xxx",
    "XXXXXXXX",
    "<your token>",
    "<token>",
    "example",
    "Placeholder",
    "  YOUR_PADDED  ",
]

EMPTY = ["", "   ", None]

REAL = [
    "AIza" + "SyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY",  # split so no token-shaped literal is in the source
    "s3cr3t-Tok3n_value",
    "https://discord.com/api/webhooks/123456789012345678/abcDEF_ghiJKL-mno",
    "alice.bsky.social",
    "dp.st.prd.abcdef0123456789",
    "yours_truly_token",  # starts with 'your' but not the template 'your_'
]

SENTINEL = "SENTINEL-do-not-log-0451"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """No ambient secrets, no secret managers, no .env file."""
    for name in list(os.environ):
        if name.startswith(("YOUTUBE_", "TIKTOK_", "DISCORD_", "MATRIX_", "BLUESKY_",
                            "MASTODON_", "LLM_", "SECRETS_", "DOPPLER_")) or name == "GEMINI_API_KEY":
            monkeypatch.delenv(name)
    monkeypatch.setattr(daemon_main, "load_config", lambda *a, **k: True)


class TestPlaceholderRule:
    @pytest.mark.parametrize("value", PLACEHOLDERS)
    def test_placeholder_rejected(self, value):
        assert rs.is_placeholder(value)
        assert not rs.is_usable(value)

    @pytest.mark.parametrize("value", EMPTY)
    def test_empty_rejected(self, value):
        assert not rs.is_usable(value)

    @pytest.mark.parametrize("value", REAL)
    def test_real_looking_value_accepted(self, value):
        assert not rs.is_placeholder(value)
        assert rs.is_usable(value)


class TestScrub:
    def test_placeholder_env_is_removed_and_named_not_valued(self, monkeypatch, caplog):
        monkeypatch.setenv("SECRETS_VAULT_TOKEN", "your_vault_token")
        monkeypatch.setenv("DOPPLER_TOKEN", "dp.st.your_token_here")
        monkeypatch.setenv("YOUTUBE_API_KEY", "real-looking-key-123")
        with caplog.at_level(logging.WARNING):
            scrubbed = rs.scrub_placeholder_env()
        assert set(scrubbed) == {"SECRETS_VAULT_TOKEN", "DOPPLER_TOKEN"}
        assert "SECRETS_VAULT_TOKEN" not in os.environ
        assert "DOPPLER_TOKEN" not in os.environ
        assert os.environ["YOUTUBE_API_KEY"] == "real-looking-key-123"
        assert "SECRETS_VAULT_TOKEN" in caplog.text
        assert "your_vault_token" not in caplog.text
        assert "dp.st.your" not in caplog.text

    def test_empty_env_is_left_alone_and_not_reported(self, monkeypatch):
        monkeypatch.setenv("TIKTOK_CLIENT_KEY", "")
        assert rs.scrub_placeholder_env() == []


class TestMissingForFeature:
    def test_youtube_all_missing(self):
        assert rs.missing_for("youtube") == ["YOUTUBE_API_KEY", "YOUTUBE_USERNAME or YOUTUBE_CHANNEL_ID"]

    def test_youtube_placeholder_key_is_missing(self, monkeypatch):
        monkeypatch.setenv("YOUTUBE_API_KEY", "YOUR_YOUTUBE_API_KEY")
        monkeypatch.setenv("YOUTUBE_USERNAME", "YOUR_YOUTUBE_CHANNEL")
        rs.scrub_placeholder_env()
        assert rs.missing_for("youtube") == ["YOUTUBE_API_KEY", "YOUTUBE_USERNAME or YOUTUBE_CHANNEL_ID"]

    def test_youtube_real_values_pass(self, monkeypatch):
        monkeypatch.setenv("YOUTUBE_API_KEY", "real-looking-key-123")
        monkeypatch.setenv("YOUTUBE_CHANNEL_ID", "UC1234567890abcdefghijkl")
        assert rs.missing_for("youtube") == []

    def test_discord_placeholder_url_is_missing(self, monkeypatch):
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN")
        rs.scrub_placeholder_env()
        assert rs.missing_for("discord") == ["DISCORD_WEBHOOK_URL"]

    def test_matrix_needs_token_or_login(self, monkeypatch):
        monkeypatch.setenv("MATRIX_HOMESERVER", "https://matrix.example.org")
        monkeypatch.setenv("MATRIX_ROOM_ID", "!abc123")
        assert rs.missing_for("matrix") == ["MATRIX_ACCESS_TOKEN or MATRIX_USERNAME and MATRIX_PASSWORD"]
        monkeypatch.setenv("MATRIX_ACCESS_TOKEN", "real-looking-token")
        assert rs.missing_for("matrix") == []

    def test_bluesky_and_mastodon(self, monkeypatch):
        assert rs.missing_for("bluesky") == ["BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD"]
        assert rs.missing_for("mastodon") == ["MASTODON_ACCESS_TOKEN", "MASTODON_API_BASE_URL"]
        monkeypatch.setenv("MASTODON_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")
        monkeypatch.setenv("MASTODON_API_BASE_URL", "https://mastodon.example")
        rs.scrub_placeholder_env()
        assert rs.missing_for("mastodon") == ["MASTODON_ACCESS_TOKEN"]

    def test_gemini_key_only_when_provider_is_gemini(self, monkeypatch):
        assert rs.missing_for("llm") == []  # LLM disabled
        monkeypatch.setenv("LLM_ENABLE", "true")
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        assert rs.missing_for("llm") == []
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        assert rs.missing_for("llm") == ["LLM_GEMINI_API_KEY (or GEMINI_API_KEY)"]
        monkeypatch.setenv("GEMINI_API_KEY", "real-looking-key-123")
        assert rs.missing_for("llm") == []


class TestDaemonFailsClosed:
    def _fail_if_built(self, name):
        def factory(*a, **k):
            raise AssertionError(f"{name} must not be constructed on a missing secret")
        return factory

    def test_youtube_enabled_with_placeholder_refuses_to_start(self, monkeypatch, caplog):
        monkeypatch.setenv("YOUTUBE_ENABLE_MONITORING", "true")
        monkeypatch.setenv("YOUTUBE_API_KEY", "YOUR_" + SENTINEL)
        monkeypatch.setenv("YOUTUBE_USERNAME", "YOUR_YOUTUBE_CHANNEL")
        monkeypatch.setattr(daemon_main, "YouTubeVideosPlatform", self._fail_if_built("YouTube"))
        with caplog.at_level(logging.INFO):
            ok = daemon_main.BoonTubeDaemon().initialize()
        assert ok is False
        assert "YOUTUBE_API_KEY" in caplog.text
        assert SENTINEL not in caplog.text

    def test_youtube_enabled_with_empty_key_refuses_to_start(self, monkeypatch, caplog):
        monkeypatch.setenv("YOUTUBE_ENABLE_MONITORING", "true")
        monkeypatch.setenv("YOUTUBE_API_KEY", "")
        monkeypatch.setenv("YOUTUBE_USERNAME", "somechannel")
        monkeypatch.setattr(daemon_main, "YouTubeVideosPlatform", self._fail_if_built("YouTube"))
        with caplog.at_level(logging.INFO):
            assert daemon_main.BoonTubeDaemon().initialize() is False
        assert "YOUTUBE_API_KEY" in caplog.text

    def test_discord_with_placeholder_webhook_is_not_enabled(self, monkeypatch, caplog):
        built = []

        class FakeYouTube:
            name = "YouTube"

            def authenticate(self):
                return True

        monkeypatch.setenv("YOUTUBE_ENABLE_MONITORING", "true")
        monkeypatch.setenv("YOUTUBE_API_KEY", "real-looking-key-123")
        monkeypatch.setenv("YOUTUBE_CHANNEL_ID", "UC1234567890abcdefghijkl")
        monkeypatch.setenv("DISCORD_ENABLE_POSTING", "true")
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/YOUR_" + SENTINEL)
        monkeypatch.setattr(daemon_main, "YouTubeVideosPlatform", FakeYouTube)

        def discord_factory(*a, **k):
            built.append(1)
            raise AssertionError("Discord must not be constructed on a missing secret")

        monkeypatch.setattr(daemon_main, "DiscordPlatform", discord_factory)
        with caplog.at_level(logging.INFO):
            ok = daemon_main.BoonTubeDaemon().initialize()
        assert ok is True  # social is optional; YouTube is fine
        assert built == []
        assert "DISCORD_WEBHOOK_URL" in caplog.text
        assert SENTINEL not in caplog.text

    def test_placeholder_vault_token_never_reaches_the_library(self, monkeypatch):
        monkeypatch.setenv("SECRETS_VAULT_TOKEN", "your_vault_token")
        monkeypatch.setenv("YOUTUBE_ENABLE_MONITORING", "false")
        daemon_main.BoonTubeDaemon().initialize()
        assert "SECRETS_VAULT_TOKEN" not in os.environ
