# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
The hypeman-social migration: the old import paths must keep working, and
the new VideoPostGenerator must drive the shared library correctly.
"""

import pytest

import hypeman_social.social.bluesky
import hypeman_social.social.discord
import hypeman_social.social.mastodon
import hypeman_social.social.matrix
from boon_tube_daemon.llm.gemini import GeminiLLM
from boon_tube_daemon.llm.generator import VideoPostGenerator
from boon_tube_daemon.llm.ollama import OllamaLLM
from boon_tube_daemon.social.bluesky import BlueskyPlatform
from boon_tube_daemon.social.discord import DiscordPlatform
from boon_tube_daemon.social.mastodon import MastodonPlatform
from boon_tube_daemon.social.matrix import MatrixPlatform
from boon_tube_daemon.utils.config import get_bool_config, get_config, get_secret


class TestSharedLibraryReexports:
    """The daemon's platform classes ARE the hypeman ones, not copies."""

    def test_social_platforms_come_from_hypeman(self):
        assert DiscordPlatform is hypeman_social.social.discord.DiscordPlatform
        assert MatrixPlatform is hypeman_social.social.matrix.MatrixPlatform
        assert BlueskyPlatform is hypeman_social.social.bluesky.BlueskyPlatform
        assert MastodonPlatform is hypeman_social.social.mastodon.MastodonPlatform

    def test_config_comes_from_hypeman(self):
        import hypeman_social.config
        assert get_config is hypeman_social.config.get_config
        assert get_bool_config is hypeman_social.config.get_bool_config
        assert get_secret is hypeman_social.config.get_secret

    def test_pinned_wrappers_are_generators(self):
        assert issubclass(OllamaLLM, VideoPostGenerator)
        assert issubclass(GeminiLLM, VideoPostGenerator)


class FakeEngine:
    """Stands in for LLMManager: canned generations, permissive guardrails."""

    def __init__(self, response='A great new video about servers! #Homelab #Proxmox #Tech'):
        self.enabled = True
        self.response = response
        self.prompts = []
        self.guardrail_calls = []

    def authenticate(self):
        return True

    def is_available(self):
        return True

    def generate(self, prompt, max_tokens=None):
        self.prompts.append(prompt)
        return self.response

    def apply_guardrails(self, message, **kwargs):
        self.guardrail_calls.append((message, kwargs))
        return message, []

    def status(self):
        return {'enabled': True}


@pytest.fixture
def generator():
    instance = VideoPostGenerator.__new__(VideoPostGenerator)
    instance._engine = FakeEngine()
    return instance


VIDEO = {
    'title': 'Building a Home Server with Proxmox',
    'description': 'Full walkthrough',
    'url': 'https://youtube.com/watch?v=abc123',
    'channel_name': 'ChiefGyk3D',
}


class TestVideoPostGenerator:
    def test_notification_appends_url(self, generator):
        message = generator.generate_notification(VIDEO, 'YouTube', 'bluesky')
        assert message.endswith('\n\nhttps://youtube.com/watch?v=abc123')

    def test_platform_limits_reach_guardrails(self, generator):
        generator.generate_notification(VIDEO, 'YouTube', 'bluesky')
        _, kwargs = generator._engine.guardrail_calls[0]
        assert kwargs['char_limit'] == 240
        assert kwargs['expected_hashtag_count'] == 3
        assert kwargs['platform'] == 'bluesky'

        generator.generate_notification(VIDEO, 'YouTube', 'discord')
        _, kwargs = generator._engine.guardrail_calls[1]
        assert kwargs['char_limit'] == 300
        assert kwargs['expected_hashtag_count'] == 0

    def test_meta_text_and_urls_stripped_before_guardrails(self, generator):
        generator._engine.response = (
            'Here\'s your post: "Great video! https://spam.example/x #Tech #AI #Dev"'
        )
        generator.generate_notification(VIDEO, 'YouTube', 'mastodon')
        cleaned, _ = generator._engine.guardrail_calls[0]
        assert 'Here' not in cleaned
        assert 'https://spam.example' not in cleaned
        assert cleaned.startswith('Great video!')

    def test_guardrail_failure_returns_none(self, generator):
        generator._engine.apply_guardrails = lambda m, **k: (None, ['too spammy'])
        assert generator.generate_notification(VIDEO, 'YouTube', 'bluesky') is None

    def test_empty_generation_returns_none(self, generator):
        generator._engine.response = None
        assert generator.generate_notification(VIDEO, 'YouTube', 'bluesky') is None

    def test_disabled_generator_short_circuits(self, generator):
        generator._engine.enabled = False
        assert generator.generate_notification(VIDEO, 'YouTube', 'bluesky') is None
        assert generator.generate_hashtags(VIDEO) is None
        assert generator.should_notify(VIDEO) is True  # fail open

    def test_should_notify_defaults_to_true_without_filtering(self, generator, monkeypatch):
        monkeypatch.delenv('LLM_ENABLE_FILTERING', raising=False)
        assert generator.should_notify(VIDEO) is True
        assert generator._engine.prompts == []  # no LLM call when filter is off

    def test_should_notify_respects_llm_no(self, generator, monkeypatch):
        monkeypatch.setenv('LLM_ENABLE_FILTERING', 'true')
        generator._engine.response = 'no'
        assert generator.should_notify(VIDEO) is False

    def test_should_notify_fails_open_on_llm_outage(self, generator, monkeypatch):
        monkeypatch.setenv('LLM_ENABLE_FILTERING', 'true')
        generator._engine.response = None
        assert generator.should_notify(VIDEO) is True

    def test_hashtags_generated(self, generator):
        generator._engine.response = '#Homelab #Proxmox #SelfHosted'
        assert generator.generate_hashtags(VIDEO) == '#Homelab #Proxmox #SelfHosted'

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError):
            VideoPostGenerator(provider='clippy')
