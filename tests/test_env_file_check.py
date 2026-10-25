# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The installer's .env check uses the same placeholder rule as the daemon."""

import subprocess
from pathlib import Path

import pytest

from boon_tube_daemon.utils.required_secrets import MANAGED_VARS, is_placeholder

SCRIPT = Path(__file__).parent.parent / "scripts" / "env-check.sh"

LINES = {
    "YOUTUBE_API_KEY": "YOUR_YOUTUBE_API_KEY",
    "SECRETS_VAULT_TOKEN": "your_vault_token",
    "DOPPLER_TOKEN": "dp.st.your_token_here",
    "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN",
    "BLUESKY_HANDLE": '"YOUR_HANDLE.bsky.social"',
    "MATRIX_PASSWORD": "<password>",
    "MASTODON_CLIENT_SECRET": "changeme",
}


def run(tmp_path, body):
    env = tmp_path / ".env"
    env.write_text(body)
    return subprocess.run(
        ["bash", str(SCRIPT), str(env)], capture_output=True, text=True, check=False
    )


def test_script_exists():
    assert SCRIPT.is_file()


@pytest.mark.parametrize("name", sorted(LINES))
def test_placeholder_line_fails_and_names_variable_only(tmp_path, name):
    result = run(tmp_path, f"{name}={LINES[name]}\n")
    assert result.returncode == 1
    assert name in result.stdout + result.stderr
    assert LINES[name].strip('"') not in result.stdout + result.stderr


def test_empty_and_real_values_pass(tmp_path):
    body = "YOUTUBE_API_KEY=\nDOPPLER_TOKEN=\nDISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123/abcDEF\n"
    body += "BLUESKY_HANDLE=alice.bsky.social\n# SECRETS_VAULT_TOKEN=your_vault_token\n"
    result = run(tmp_path, body)
    assert result.returncode == 0, result.stdout + result.stderr


def test_script_and_python_rule_agree(tmp_path):
    """Guard: every sample the shell rejects the Python rule rejects, and vice versa."""
    assert LINES and set(LINES) <= set(MANAGED_VARS)
    for name, value in LINES.items():
        assert is_placeholder(value.strip('"'))
        assert run(tmp_path, f"{name}={value}\n").returncode == 1
    for real in ("AIzaSyD-9tSrke72PouQMnMX", "yours_truly_token", "dp.st.prd.abc123"):
        assert not is_placeholder(real)
        assert run(tmp_path, f"YOUTUBE_API_KEY={real}\n").returncode == 0
