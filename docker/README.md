# Docker Usage for Boon-Tube-Daemon

## 📦 Pull from GitHub Container Registry (Recommended)

Pre-built images are available on GitHub Container Registry:

```bash
# Pull the latest image
docker pull ghcr.io/chiefgyk3d/boon-tube-daemon:latest

# Run directly from GHCR
docker run -d --env-file .env ghcr.io/chiefgyk3d/boon-tube-daemon:latest
```

**Available tags:**
- `latest` - Latest stable build from main branch
- `v1.2.3` - Specific version tags
- `main-<sha>` - Specific commit from main branch

## Build Variants

### 🚀 Optimized Build (Default - Recommended)
**Size:** ~652MB | **TikTok:** ❌ | **CVE Fixes:** ✅

The optimized build excludes TikTok/Playwright dependencies for a smaller, more secure image:
- ✅ YouTube monitoring
- ✅ All social platforms (Discord, Matrix, Bluesky, Mastodon)
- ✅ Gemini LLM integration
- ✅ CVE-2025-7709 fix (SQLite 3.50.4)
- ✅ CVE-2025-8869 fix (pip 25.3+)
- ❌ TikTok monitoring (Playwright not included)

### 📦 Full Build (With TikTok)
**Size:** ~2GB | **TikTok:** ⚠️ Planned | **CVE Fixes:** ✅

TikTok support is planned but not yet functional. Use optimized build until TikTok is ready.

## Quick Start (Build Locally)

### Build the Image

```bash
# Optimized build (default)
docker build -t boon-tube-daemon:latest -f docker/Dockerfile .
```

### Run with docker-compose (Recommended)

```bash
# Start the daemon
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the daemon
docker-compose down
```

### Run with docker run

```bash
# Run in foreground
docker run --rm --env-file .env boon-tube-daemon:latest

# Run in background
docker run -d \
  --name boon-tube-daemon \
  --restart unless-stopped \
  --env-file .env \
  boon-tube-daemon:latest

# View logs
docker logs -f boon-tube-daemon

# Stop
docker stop boon-tube-daemon
docker rm boon-tube-daemon
```

## Configuration

### Environment Variables

The container reads configuration from the `.env` file. Make sure to configure:

**Required:**
- `YOUTUBE_API_KEY` - YouTube Data API v3 key (in Doppler or .env)
- `GEMINI_API_KEY` - Google Gemini API key (in Doppler or .env)
- `YOUTUBE_CHANNEL_ID` - Your YouTube channel ID
- `CHECK_INTERVAL` - Check interval in seconds (default: 900 = 15 minutes)

**Optional Social Platforms (at least one recommended):**
- Discord: `DISCORD_WEBHOOK_URL`, `DISCORD_ROLE_YOUTUBE`
- Matrix: `MATRIX_USERNAME`, `MATRIX_PASSWORD`, `MATRIX_ROOM_ID`
- Bluesky: `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD`
- Mastodon: `MASTODON_ACCESS_TOKEN`, `MASTODON_INSTANCE_URL`

### Volumes

The `docker-compose.yml` mounts a `./config` directory for persistent state:

```yaml
volumes:
  - ./config:/app/config
```

This allows the daemon to remember the last video ID across container restarts.

## Image Details

- **Base Image:** python:3.14-slim
- **Size:** ~652MB (optimized) / ~2GB (with TikTok)
- **Python Version:** 3.14 (in virtual environment)
- **Multi-arch:** amd64, arm64
- **Health Check:** Runs every 5 minutes

### Security Fixes

#### CVE-2025-7709: SQLite Integer Overflow
**Severity:** High | **Fixed in:** SQLite 3.50.3+

Debian trixie ships SQLite 3.46.1-7 which is vulnerable to an integer overflow in the FTS5 extension. We compile SQLite 3.50.4 from source to ensure security.

#### CVE-2025-8869: pip Symbolic Link Extraction
**Severity:** Medium | **Fixed in:** pip 25.3+

pip versions before 25.3 are vulnerable to a symbolic link extraction vulnerability. We upgrade pip to the latest version (25.3+) during build.

## Health Check

The container includes a health check that verifies the package can be imported:

```bash
docker inspect --format='{{.State.Health.Status}}' boon-tube-daemon
```

## Troubleshooting

### Check logs

```bash
# docker-compose
docker-compose logs -f

# docker run
docker logs -f boon-tube-daemon
```

### Test configuration

```bash
# Run interactively to see startup
docker run --rm -it --env-file .env boon-tube-daemon:latest
```

### Verify .env file is loaded

```bash
docker run --rm --env-file .env boon-tube-daemon:latest env | grep YOUTUBE
```

### Common Issues

**Bluesky 401 Unauthorized:**
- Update `BLUESKY_HANDLE` and `BLUESKY_APP_PASSWORD` in .env
- Generate app password at: https://bsky.app/settings/app-passwords

**YouTube API errors:**
- Verify `YOUTUBE_API_KEY` in Doppler or .env
- Check API is enabled in Google Cloud Console

**Matrix authentication:**
- Ensure `MATRIX_USERNAME` includes homeserver (e.g., `@user:matrix.org`)
- Room ID should not include server suffix (e.g., `!ABC123` not `!ABC123:matrix.org`)

## Production Deployment

### Using docker-compose (Recommended)

```bash
# Start in detached mode
docker-compose up -d

# Enable auto-restart on boot
docker-compose up -d --force-recreate
```

### Using systemd with Docker

Create `/etc/systemd/system/boon-tube-daemon.service`:

```ini
[Unit]
Description=Boon-Tube-Daemon Docker Container
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/Boon-Tube-Daemon
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable boon-tube-daemon
sudo systemctl start boon-tube-daemon
```

## GitHub Container Registry

The image is automatically built and published to:
- `ghcr.io/chiefgyk3d/boon-tube-daemon:latest`
- `ghcr.io/chiefgyk3d/boon-tube-daemon:v1.0.0` (tagged releases)

Pull and run:

```bash
docker pull ghcr.io/chiefgyk3d/boon-tube-daemon:latest
docker run --rm --env-file .env ghcr.io/chiefgyk3d/boon-tube-daemon:latest
```

## Building for Multiple Architectures

```bash
# Enable buildx
docker buildx create --use

# Build for amd64 and arm64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t boon-tube-daemon:latest \
  -f docker/Dockerfile \
  --push \
  .
```

## Environment Variable Reference

See `.env.example` for a complete list of configuration options.

Key settings:
- `CHECK_INTERVAL=900` - Check every 15 minutes (optimized for video uploads)
- `LLM_ENABLED=true` - Enable AI-generated posts
- `LLM_MODEL=gemini-2.5-flash-lite` - Gemini model (1,000 req/day free)
- `*_POST_STYLE` - Platform posting styles (professional/conversational/detailed/concise)
