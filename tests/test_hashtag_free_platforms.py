"""Platforms that expect zero hashtags (Discord, Matrix) must not lose the
AI post because the model tacked hashtags on anyway. Measured on gemma4:12b:
9 of 30 Discord/Matrix generations were rejected for 'Wrong hashtag count'."""

import pytest

from boon_tube_daemon.llm.generator import VideoPostGenerator
from tests.test_hypeman_migration import VIDEO, FakeEngine


@pytest.fixture
def generator():
    instance = VideoPostGenerator.__new__(VideoPostGenerator)
    instance._engine = FakeEngine()
    return instance


@pytest.mark.parametrize('platform', ['discord', 'matrix'])
def test_hashtags_stripped_before_guardrails_when_zero_expected(generator, platform):
    generator._engine.response = 'Rebuilding my lab on Proxmox 💻 #Homelab #Proxmox #Tech'
    message = generator.generate_notification(VIDEO, 'YouTube', platform)
    sent, kwargs = generator._engine.guardrail_calls[0]
    assert '#' not in sent
    assert sent == 'Rebuilding my lab on Proxmox 💻'
    assert kwargs['expected_hashtag_count'] == 0
    assert '#' not in message


def test_inline_hashtag_stripped_without_leaving_double_space(generator):
    generator._engine.response = 'A look at #Proxmox clustering and backups'
    generator.generate_notification(VIDEO, 'YouTube', 'discord')
    sent, _ = generator._engine.guardrail_calls[0]
    assert sent == 'A look at clustering and backups'


@pytest.mark.parametrize('platform', ['bluesky', 'mastodon'])
def test_hashtags_kept_on_hashtag_platforms(generator, platform):
    generator._engine.response = 'Rebuilding my lab 💻 #Homelab #Proxmox #Tech'
    generator.generate_notification(VIDEO, 'YouTube', platform)
    sent, _ = generator._engine.guardrail_calls[0]
    assert sent.count('#') == 3


def test_zero_hashtag_prompt_forbids_hashtags():
    prompt = VideoPostGenerator._build_notification_prompt(
        platform_name='YouTube', channel_name='C', title='T', description='',
        max_chars=300, use_hashtags=False, hashtag_count=0)
    assert 'DO NOT use any hashtags' in prompt


def test_hashtag_prompt_does_not_forbid_hashtags():
    prompt = VideoPostGenerator._build_notification_prompt(
        platform_name='YouTube', channel_name='C', title='T', description='',
        max_chars=240, use_hashtags=True, hashtag_count=3)
    assert 'DO NOT use any hashtags' not in prompt
