# Boon-Tube-Daemon threat model

`boon-tube-daemon.threat-dragon.json` is an OWASP Threat Dragon v2 STRIDE model
of the upload monitor: YouTube and TikTok in, an optional LLM step, Discord,
Matrix, Bluesky and Mastodon out, plus the container and CI release path.

Open it in the Threat Dragon desktop or web app with File > Open.

Everything in it was read from this repository. Posting, config and LLM
provider code live in the external `hypeman-social` package; that package was
not reviewed, so threats that depend on it say so. This is not a full audit.

## Trust boundaries

- Third-party platforms (internet): YouTube, TikTok, the four social networks, Gemini.
- Operator host or container: the daemon, config, secrets and the state file.
- Operator-run LLM host: the Ollama server.
- Source repo and CI/release: GitHub, GYST workflows, the GHCR image.

## Open High and Critical threats

None.

## Open Medium threats worth a look

- OAuth helper (`scripts/tiktok_oauth_web.py`) never compares the `state`
  value and listens on all interfaces.
- Prompt injection: video title and description go into prompts unescaped
  (source is the channel owner's own metadata).
- Model output is posted publicly; content checks depend on `hypeman-social`.
- Core posting code and credentials sit in `hypeman-social`.
- Headless Chromium renders remote TikTok pages (not installed in the image by default).
- Secrets in `.env` / the container environment.

## UNVERIFIED items

- Timeouts and bind address of the health server (inside `hypeman-social`).
- `apply_guardrails` content rules (inside `hypeman-social`).
- Ollama host scheme, auth and network exposure (operator deployment).
- Whether `googleapiclient` errors put the API key in debug log text.
- Character validation of TikTok item ids before URL construction.
