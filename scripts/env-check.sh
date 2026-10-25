#!/bin/bash
# Usage: env-check.sh /path/to/.env
#
# Exit 1 and name every variable in the file whose value is still a template
# placeholder. Same rule as boon_tube_daemon/utils/required_secrets.py
# (case-insensitive): starts with your_, changeme, xxx or dp.st.your; is
# exactly "example" or "placeholder"; is wrapped in <...>; or has a URL
# segment starting with your_. Values are never printed. Empty values pass
# (a secrets manager may supply them); the daemon itself refuses to enable a
# feature whose required secret is empty.

set -euo pipefail

ENV_FILE="${1:?usage: env-check.sh /path/to/.env}"

# Keep in sync with MANAGED_VARS in required_secrets.py.
MANAGED=(
    YOUTUBE_API_KEY YOUTUBE_USERNAME YOUTUBE_CHANNEL_ID
    TIKTOK_USERNAME TIKTOK_CLIENT_KEY TIKTOK_CLIENT_SECRET TIKTOK_ACCESS_TOKEN TIKTOK_MS_TOKEN
    LLM_GEMINI_API_KEY GEMINI_API_KEY
    DISCORD_WEBHOOK_URL DISCORD_WEBHOOK_YOUTUBE DISCORD_WEBHOOK_TIKTOK
    MATRIX_HOMESERVER MATRIX_ROOM_ID MATRIX_ACCESS_TOKEN MATRIX_USERNAME MATRIX_PASSWORD
    BLUESKY_HANDLE BLUESKY_APP_PASSWORD
    MASTODON_API_BASE_URL MASTODON_CLIENT_ID MASTODON_CLIENT_SECRET MASTODON_ACCESS_TOKEN
    DOPPLER_TOKEN SECRETS_VAULT_TOKEN
)

is_placeholder() {
    local v
    v="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
    v="${v#"${v%%[![:space:]]*}"}"
    v="${v%"${v##*[![:space:]]}"}"
    [[ -z "$v" ]] && return 1
    case "$v" in
        your_*|changeme*|xxx*|dp.st.your*|example|placeholder) return 0 ;;
        '<'*'>') return 0 ;;
    esac
    [[ "$v" =~ (^|[/:@=?\&.])your_ ]]
}

bad=()
for name in "${MANAGED[@]}"; do
    line="$(grep -E "^${name}=" "$ENV_FILE" | tail -n 1 || true)"
    [[ -z "$line" ]] && continue
    value="${line#*=}"
    value="${value%\"}"; value="${value#\"}"
    value="${value%\'}"; value="${value#\'}"
    if is_placeholder "$value"; then
        bad+=("$name")
    fi
done

if [[ ${#bad[@]} -gt 0 ]]; then
    echo "ERROR: these .env variables are still template placeholders:" >&2
    for name in "${bad[@]}"; do
        echo "  - $name" >&2
    done
    echo "Set a real value, or leave the line empty if a secrets manager supplies it." >&2
    exit 1
fi
