# Doppler Secret Management Setup

This guide shows how to use Doppler for secure secret management with Boon-Tube-Daemon.

## Why Use Doppler?

- 🔒 **Secure**: Secrets stored encrypted, never in `.env` files
- 🔄 **Sync**: Automatically updates secrets across environments
- 👥 **Team-friendly**: Share access without sharing credentials
- 📊 **Audit logs**: Track who accessed which secrets when
- 🚀 **Easy**: Integrates seamlessly with the daemon

## Installation

### Install Doppler CLI

**Linux/macOS**:
```bash
# Install via script
curl -Ls --tlsv1.2 --proto "=https" --retry 3 https://cli.doppler.com/install.sh | sh

# Or via package manager
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -sLf --retry 3 --tlsv1.2 --proto "=https" 'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | sudo apt-key add -
echo "deb https://packages.doppler.com/public/cli/deb/debian any-version main" | sudo tee /etc/apt/sources.list.d/doppler-cli.list
sudo apt-get update && sudo apt-get install doppler

# macOS
brew install dopplerhq/cli/doppler
```

### Verify Installation

```bash
doppler --version
```

## Setup Guide

### 1. Create Doppler Account

1. Sign up at [Doppler Dashboard](https://dashboard.doppler.com/register)
2. Create a new project called "boon-tube-daemon" (or your preferred name)
3. Create environments: `dev`, `staging`, `production`

### 2. Login via CLI

```bash
# Login to Doppler
doppler login

# Navigate to your project directory
cd /path/to/Boon-Tube-Daemon

# Setup Doppler in this directory
doppler setup
# Select your project: boon-tube-daemon
# Select your config: dev (or production)
```

This creates a `.doppler.yaml` file in your project (already in `.gitignore`).

### 3. Add Secrets to Doppler

#### Option A: Via Web Dashboard

1. Go to [Doppler Dashboard](https://dashboard.doppler.com/)
2. Select your project → environment
3. Click **Add Secret**
4. Add your secrets with these exact names:

```
YOUTUBE_API_KEY=your_youtube_api_key
YOUTUBE_USERNAME=ChiefGyk3D
YOUTUBE_ENABLE_MONITORING=true

TIKTOK_USERNAME=ChiefGyk3D
TIKTOK_ENABLE_MONITORING=true

DISCORD_WEBHOOK_URL=your_discord_webhook
DISCORD_ENABLE_POSTING=true

MATRIX_HOMESERVER=https://matrix.org
MATRIX_USER_ID=@yourusername:matrix.org
MATRIX_ACCESS_TOKEN=your_matrix_token
MATRIX_ROOM_ID=!roomid:matrix.org
MATRIX_ENABLE_POSTING=true

BLUESKY_HANDLE=yourhandle.bsky.social
BLUESKY_APP_PASSWORD=your_app_password
BLUESKY_ENABLE_POSTING=true

MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=your_mastodon_token
MASTODON_ENABLE_POSTING=true

GEMINI_API_KEY=your_gemini_api_key
GEMINI_ENABLE=true
```

#### Option B: Via CLI

```bash
# Add secrets one by one
doppler secrets set YOUTUBE_API_KEY "your_youtube_api_key"
doppler secrets set YOUTUBE_USERNAME "ChiefGyk3D"
doppler secrets set YOUTUBE_ENABLE_MONITORING "true"

# Or import from existing .env file
doppler secrets upload .env
```

### 4. Verify Secrets

```bash
# List all secrets
doppler secrets

# View a specific secret
doppler secrets get YOUTUBE_API_KEY

# Download secrets to verify (won't save to disk)
doppler secrets download --no-file --format env
```

## Running the Daemon with Doppler

### Development/Testing

```bash
# Run directly with Doppler
doppler run -- python3 main.py

# Or run tests
doppler run -- python3 test_integration.py
doppler run -- python3 test_youtube.py
```

### Production Deployment

#### Option 1: Service Token (Recommended)

1. Create a service token in Doppler Dashboard:
   - Go to your project → environment
   - Access → Service Tokens → Generate
   - Copy the token (starts with `dp.st.`)

2. Set the token in your environment:
```bash
export DOPPLER_TOKEN="dp.st.xxxxxxxxxxxxx"
```

3. Run without `doppler run`:
```bash
# Doppler automatically injects secrets when DOPPLER_TOKEN is set
python3 main.py
```

4. For systemd service, add to `/etc/systemd/system/boon-tube.service`:
```ini
[Service]
Environment="DOPPLER_TOKEN=dp.st.xxxxxxxxxxxxx"
ExecStart=/usr/bin/python3 /opt/boon-tube-daemon/main.py
```

#### Option 2: Doppler CLI in Service

```bash
# Edit the systemd service
sudo nano /etc/systemd/system/boon-tube.service
```

Change `ExecStart` to:
```ini
ExecStart=/usr/local/bin/doppler run -- /usr/bin/python3 /opt/boon-tube-daemon/main.py
```

### With Docker

```dockerfile
# Install Doppler in your Dockerfile
RUN apt-get update && apt-get install -y gnupg wget && \
    wget -q -O - https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key | apt-key add - && \
    echo "deb https://packages.doppler.com/public/cli/deb/debian any-version main" | tee /etc/apt/sources.list.d/doppler-cli.list && \
    apt-get update && apt-get install -y doppler

# Run with Doppler
CMD ["doppler", "run", "--", "python3", "main.py"]
```

Or use service token:
```bash
docker run -e DOPPLER_TOKEN="dp.st.xxxxx" boon-tube-daemon
```

## Fallback to .env

The daemon **automatically falls back** to `.env` if Doppler is not available:

1. **Doppler not installed**: Uses `.env` file
2. **Not logged in**: Uses `.env` file
3. **No DOPPLER_TOKEN**: Uses `.env` file
4. **Secret not in Doppler**: Falls back to `.env` for that secret

This means:
- ✅ Development works with `.env`
- ✅ Production can use Doppler
- ✅ No breaking changes
- ✅ Gradual migration possible

## Migration Strategy

### Gradual Migration

1. **Keep using .env** for local development
2. **Add critical secrets** to Doppler first (API keys, tokens)
3. **Test** with `doppler run` in development
4. **Deploy to production** with Doppler service token
5. **Remove secrets from .env** once confident

### Testing Migration

```bash
# Test with Doppler
doppler run -- python3 test_integration.py

# Verify secrets are loaded
doppler run -- python3 -c "import os; print('YT Key:', os.getenv('YOUTUBE_API_KEY')[:10] + '...')"

# Compare with .env
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('YT Key:', os.getenv('YOUTUBE_API_KEY')[:10] + '...')"
```

## Secret Management Best Practices

### Secret Naming Convention

Use the standard `SECTION_KEY` format:
```
YOUTUBE_API_KEY
TIKTOK_USERNAME
DISCORD_WEBHOOK_URL
MATRIX_ACCESS_TOKEN
```

### Environment Separation

Create separate Doppler configs:
- **dev**: Development/testing secrets
- **staging**: Staging environment
- **production**: Production secrets

```bash
# Switch between environments
doppler setup --config dev
doppler setup --config production
```

### Access Control

1. **Service Tokens**: For automated systems (CI/CD, servers)
2. **Personal Tokens**: For individual developers
3. **Rotate regularly**: Update tokens every 90 days
4. **Audit logs**: Review access in Doppler Dashboard

### Backup Strategy

```bash
# Export secrets for backup (store securely!)
doppler secrets download --no-file --format env > doppler-backup.env.gpg

# Encrypt backup
gpg -c doppler-backup.env.gpg

# Delete unencrypted version
shred -u doppler-backup.env.gpg
```

## Troubleshooting

### "Doppler is not initialized"

```bash
cd /path/to/Boon-Tube-Daemon
doppler setup
```

### "Authentication required"

```bash
doppler login
```

### Secrets not loading

```bash
# Verify Doppler is working
doppler secrets

# Check if token is set
echo $DOPPLER_TOKEN

# Run with debug logging
doppler run -- python3 main.py --log-level DEBUG
```

### Service token not working

1. Verify token format: `dp.st.xxx`
2. Check token hasn't expired
3. Ensure token has correct permissions
4. Test token: `DOPPLER_TOKEN=dp.st.xxx doppler secrets`

## Advanced Features

### Dynamic Secrets

Doppler supports dynamic secrets that change over time:
```bash
doppler secrets set API_ROTATION_DATE "$(date +%Y-%m-%d)"
```

### Secret References

Reference other secrets:
```bash
doppler secrets set YOUTUBE_USERNAME "ChiefGyk3D"
doppler secrets set TIKTOK_USERNAME "${YOUTUBE_USERNAME}"
```

### Webhooks

Get notified when secrets change:
1. Go to Doppler Dashboard → Integrations
2. Add webhook for your notification service
3. Receive alerts on secret updates

### CLI Autocomplete

```bash
# Bash
doppler completion bash > /etc/bash_completion.d/doppler

# Zsh
doppler completion zsh > /usr/local/share/zsh/site-functions/_doppler
```

## Cost

- **Free tier**: 5 users, unlimited secrets
- **Team tier**: $12/user/month, unlimited everything
- **Enterprise**: Custom pricing

For personal projects, **free tier is sufficient**.

## Resources

- [Doppler Documentation](https://docs.doppler.com/)
- [CLI Reference](https://docs.doppler.com/docs/cli)
- [Service Tokens Guide](https://docs.doppler.com/docs/service-tokens)
- [Best Practices](https://docs.doppler.com/docs/best-practices)

## Support

If you have issues with Doppler integration:
1. Check logs: `doppler run -- python3 main.py --log-level DEBUG`
2. Verify secrets: `doppler secrets`
3. Test fallback: `python3 main.py` (should use .env)
4. Open issue on GitHub with logs
