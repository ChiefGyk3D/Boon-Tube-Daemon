# Boon-Tube-Daemon Quick Reference

## 🚀 Quick Start Commands

```bash
# Install dependencies
./setup.sh

# Configure
cp .env.example .env
nano .env

# Test configuration
python test.py

# Run daemon
python main.py

# Run in background
nohup python main.py > boon-tube.log 2>&1 &
```

## 📝 Configuration Quick Reference

### Essential Settings

```bash
# YouTube
YOUTUBE_ENABLE=true
YOUTUBE_USERNAME=@YourChannel
YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY

# TikTok
TIKTOK_ENABLE=true
TIKTOK_USERNAME=your_username

# Discord
DISCORD_ENABLE=true
DISCORD_WEBHOOK_URL=YOUR_WEBHOOK_URL
```

## 🔑 Getting API Keys

### YouTube API Key
1. https://console.cloud.google.com/
2. Create/select project
3. Enable YouTube Data API v3
4. Credentials → Create → API Key

### Discord Webhook
1. Server Settings → Integrations → Webhooks
2. New Webhook → Copy URL

### Bluesky App Password
1. Settings → App Passwords
2. Create new password (NOT main password!)

### Mastodon Tokens
1. Settings → Development → New Application
2. Set scopes: `write:statuses`
3. Copy credentials

## ⚙️ Common Tasks

### Check if running
```bash
ps aux | grep main.py
```

### View logs (if using systemd)
```bash
journalctl -u boon-tube -f
```

### View logs (if using nohup)
```bash
tail -f boon-tube.log
```

### Stop daemon
```bash
# If foreground (Ctrl+C)
pkill -f "python main.py"

# If systemd
sudo systemctl stop boon-tube
```

### Restart daemon
```bash
# If systemd
sudo systemctl restart boon-tube

# If running manually, stop and start again
```

## 🐛 Troubleshooting

### YouTube quota exceeded
- Increase `check_interval` to 600+ seconds
- Wait until midnight Pacific Time (quota resets)

### TikTok not working
```bash
playwright install chromium
pip install --upgrade TikTokApi
```

### Import errors
```bash
pip install -r requirements.txt
```

### Config not found
```bash
cp .env.example .env
```

## 📊 File Locations

| File | Purpose |
|------|---------|
| `.env` | Your configuration (not in git) |
| `main.py` | Main daemon script |
| `test.py` | Test configuration |
| `requirements.txt` | Python dependencies |
| `setup.sh` | Installation script |
| `run.sh` | Quick start script |

## 🔒 Security Notes

- Never commit `.env` to git (it's in `.gitignore`)
- Use app passwords, not main passwords
- Rotate API keys periodically
- Use read-only webhooks when possible
- Run as non-root user

## ⏱️ Recommended Check Intervals

| Frequency | Seconds | Use Case |
|-----------|---------|----------|
| 5 min | 300 | Default (balanced) |
| 10 min | 600 | Reduced API usage |
| 15 min | 900 | Minimal API usage |
| 30 min | 1800 | Very low traffic channels |
| 1 hour | 3600 | Infrequent uploaders |

## 📞 Support

- Issues: https://github.com/chiefgyk3d/Boon-Tube-Daemon/issues
- Docs: README.md
- Test: `python test.py`

## 🎯 Quick Debugging Checklist

- [ ] Config file exists (`.env`)
- [ ] API keys are valid and not expired
- [ ] Usernames are correct
- [ ] Platforms are enabled in config
- [ ] Dependencies installed (`pip list`)
- [ ] Playwright browsers installed (for TikTok)
- [ ] Network connectivity OK
- [ ] No rate limits hit (check logs)
- [ ] Test script passes (`python test.py`)
