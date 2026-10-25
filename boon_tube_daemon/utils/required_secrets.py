# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Required secrets: one placeholder rule, and a fail-closed check per feature.

hypeman-social (pinned 0.3.4) has two placeholder checks, both case-sensitive
and both only for a leading ``YOUR_``: ``get_secret`` applies it to secrets,
``get_config`` applies it only to Doppler values (an env value passes
through), and the secret-manager tokens are read with ``os.getenv`` and not
checked at all. So ``your_vault_token``, ``dp.st.your_token_here`` and a
webhook URL containing ``YOUR_ID`` all counted as real values.

This module is the single rule for this daemon. It scrubs placeholder values
out of the environment before the library reads them, then answers "which
variables is this feature missing?" so the daemon can refuse to enable the
feature and name the variable. Messages carry variable names only, never
values.
"""

import logging
import os
import re
from typing import Any

from hypeman_social.config import get_bool_config, get_config
from hypeman_social.social.base import platform_secret

logger = logging.getLogger(__name__)

# Case-insensitive. A value is a placeholder when, after trimming, it starts
# with one of these, is exactly one of _EXACT, is wrapped in <...>, or has a
# URL/host segment starting with your_ (https://host/webhooks/YOUR_ID/...).
_PREFIXES = ("your_", "changeme", "xxx", "dp.st.your")
_EXACT = frozenset({"example", "placeholder"})
_ANGLE = re.compile(r"^<.*>$")
_SEGMENT = re.compile(r"(?:^|[/:@=?&.])your_")

# Every variable that carries a credential or a template identifier, plus the
# secret-manager settings the library reads straight from the environment.
MANAGED_VARS = (
    "YOUTUBE_API_KEY", "YOUTUBE_USERNAME", "YOUTUBE_CHANNEL_ID",
    "TIKTOK_USERNAME", "TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET",
    "TIKTOK_ACCESS_TOKEN", "TIKTOK_MS_TOKEN",
    "LLM_GEMINI_API_KEY", "GEMINI_API_KEY",
    "DISCORD_WEBHOOK_URL", "DISCORD_WEBHOOK_YOUTUBE", "DISCORD_WEBHOOK_TIKTOK",
    "MATRIX_HOMESERVER", "MATRIX_ROOM_ID", "MATRIX_ACCESS_TOKEN",
    "MATRIX_USERNAME", "MATRIX_PASSWORD",
    "BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD",
    "MASTODON_API_BASE_URL", "MASTODON_CLIENT_ID", "MASTODON_CLIENT_SECRET",
    "MASTODON_ACCESS_TOKEN",
    "DOPPLER_TOKEN", "SECRETS_VAULT_TOKEN",
)


def is_placeholder(value: Any) -> bool:
    """True if the value is an unedited template placeholder (not merely empty)."""
    if not isinstance(value, str):
        return False
    text = value.strip().lower()
    if not text:
        return False
    return (
        text.startswith(_PREFIXES)
        or text in _EXACT
        or bool(_ANGLE.match(text))
        or bool(_SEGMENT.search(text))
    )


def is_usable(value: Any) -> bool:
    """True if the value is non-empty and not a placeholder."""
    return isinstance(value, str) and bool(value.strip()) and not is_placeholder(value)


def scrub_placeholder_env(names: tuple = MANAGED_VARS) -> list[str]:
    """
    Remove placeholder values from the environment so the library sees them
    as unset. Returns the variable names removed. Names are logged, values
    never are. Empty values are left alone: the library already treats them
    as unset.
    """
    scrubbed = []
    for name in names:
        if is_placeholder(os.environ.get(name)):
            del os.environ[name]
            scrubbed.append(name)
            logger.warning(f"⚠ {name} is still a template placeholder; treating it as unset")
    return scrubbed


def _secret(platform: str, key: str) -> str | None:
    value = platform_secret(platform, key)
    return value if is_usable(value) else None


def _config(section: str, key: str) -> str | None:
    value = get_config(section, key)
    return value if is_usable(value) else None


def missing_for(feature: str) -> list[str]:
    """
    Variables a feature still needs, by name. Empty list means usable.

    Features: youtube, tiktok, llm, discord, matrix, bluesky, mastodon.
    """
    missing: list[str] = []

    if feature == "youtube":
        if not _secret("YouTube", "api_key"):
            missing.append("YOUTUBE_API_KEY")
        if not (_config("YouTube", "username") or _config("YouTube", "channel_id")):
            missing.append("YOUTUBE_USERNAME or YOUTUBE_CHANNEL_ID")

    elif feature == "tiktok":
        if not _config("TikTok", "username"):
            missing.append("TIKTOK_USERNAME")

    elif feature == "llm":
        if get_bool_config("LLM", "enable", default=False):
            providers = {
                (get_config("LLM", "provider", default="gemini") or "").strip().lower(),
                (get_config("LLM", "fallback_provider", default="") or "").strip().lower(),
            }
            if "gemini" in providers and not (
                _secret("LLM", "gemini_api_key") or (os.getenv("GEMINI_API_KEY") or "").strip()
            ):
                missing.append("LLM_GEMINI_API_KEY (or GEMINI_API_KEY)")

    elif feature == "discord":
        urls = [_secret("Discord", k) for k in ("webhook_url", "webhook_youtube", "webhook_tiktok")]
        if not any(urls):
            missing.append("DISCORD_WEBHOOK_URL")

    elif feature == "matrix":
        if not _secret("Matrix", "homeserver"):
            missing.append("MATRIX_HOMESERVER")
        if not _secret("Matrix", "room_id"):
            missing.append("MATRIX_ROOM_ID")
        has_login = _secret("Matrix", "username") and _secret("Matrix", "password")
        if not (has_login or _secret("Matrix", "access_token")):
            missing.append("MATRIX_ACCESS_TOKEN or MATRIX_USERNAME and MATRIX_PASSWORD")

    elif feature == "bluesky":
        if not _config("Bluesky", "handle"):
            missing.append("BLUESKY_HANDLE")
        if not _secret("Bluesky", "app_password"):
            missing.append("BLUESKY_APP_PASSWORD")

    elif feature == "mastodon":
        if not _secret("Mastodon", "access_token"):
            missing.append("MASTODON_ACCESS_TOKEN")
        if not _config("Mastodon", "api_base_url"):
            missing.append("MASTODON_API_BASE_URL")

    else:
        raise ValueError(f"unknown feature: {feature}")

    return missing
