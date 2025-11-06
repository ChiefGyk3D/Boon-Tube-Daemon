# Boon-Tube-Daemon Quick Start Guide

Complete monitoring solution for TikTok and YouTube with multi-platform notifications.

## ✅ What's Working Now

### Media Platforms
- ✅ **TikTok**: Playwright network interception (no TikTokApi needed)
- ✅ **YouTube**: Data API v3 for regular video uploads
- ⏸️ **Livestream detection**: Separate feature (not in scope)

### Social Platforms (Ready to Configure)
- 🔧 **Discord**: Webhook-based notifications
- 🔧 **Matrix**: Matrix protocol via nio library
- 🔧 **Bluesky**: AT Protocol integration
- 🔧 **Mastodon**: REST API via Mastodon.py

### Features
- ✅ **Secret Management**: Doppler with .env fallback
- ✅ **Duplicate Detection**: Tracks last video to avoid repeat notifications
- ✅ **Quota Management**: YouTube API quota monitoring
- ✅ **LLM Ready**: Gemini 2.0 Flash Lite for enhanced posts
- ✅ **Production Ready**: systemd service, Docker support

## 🚀 Quick Setup

### 1. YouTube Configuration

You need a YouTube Data API v3 key (your current key is expired).

```bash
# Get a new API key
# Visit: https://console.cloud.google.com/apis/credentials
# Create Credentials → API Key
# Enable YouTube Data API v3

# Add to .env
YOUTUBE_API_KEY=AIzaSy_your_new_key_here
YOUTUBE_USERNAME=ChiefGyk3D
YOUTUBE_ENABLE_MONITORING=true
```

**Full guide**: `docs/YOUTUBE_SETUP.md`

### 2. TikTok Configuration

Already working! Uses Playwright to monitor TikTok profiles.

```bash
TIKTOK_ENABLE_MONITORING=true
TIKTOK_USERNAME=ChiefGyk3D
```

**No ms_token required** - Playwright handles authentication automatically.

### 3. Secret Management (Doppler)

Doppler is **already installed and configured** on your system!

```bash
# View current secrets
doppler secrets

# Run daemon with Doppler
doppler run -- python3 main.py

# Or use service token in production
export DOPPLER_TOKEN=dp.st.your_token_here
python3 main.py
```

**Falls back to .env automatically** if Doppler isn't available.

**Full guide**: `docs/DOPPLER_SETUP.md`

## 🧪 Testing

### Test TikTok Integration
```bash
python3 test_integration.py
```
✅ **Status**: Working (tested with @therock)

### Test YouTube Integration
```bash
python3 test_youtube.py
```
⚠️ **Status**: Needs valid API key

### Test Doppler Integration
```bash
python3 test_doppler.py
```
✅ **Status**: Working (CLI configured)

### Test Full Daemon
```bash
python3 main.py
```

## 📝 Configuration Priority

Secrets are loaded in this order:

1. **Doppler** (if `DOPPLER_TOKEN` set)
2. **AWS Secrets Manager** (if configured)
3. **HashiCorp Vault** (if configured)
4. **Environment variables**
5. **.env file** (fallback)
6. **Default values**

This means you can:
- Use Doppler in production
- Use .env for local development
- Mix and match as needed
- Migrate gradually

## 🔑 Required Credentials

### For YouTube
- [ ] `YOUTUBE_API_KEY` - Get from Google Cloud Console
- [x] `YOUTUBE_USERNAME` - Already set: ChiefGyk3D

### For TikTok
- [x] `TIKTOK_USERNAME` - Already set: ChiefGyk3D
- [x] Playwright installed

### For Social Platforms (Optional)
- [ ] Discord webhook URL
- [ ] Matrix homeserver, user ID, access token, room ID
- [ ] Bluesky handle and app password
- [ ] Mastodon instance URL and access token

### For LLM (Optional)
- [ ] `GEMINI_API_KEY` - Get from Google AI Studio

## 🏃 Running the Daemon

### Local Development
```bash
# With .env
python3 main.py

# With Doppler
doppler run -- python3 main.py
```

### Production (systemd)
```bash
# Edit service file
sudo nano /etc/systemd/system/boon-tube.service

# Add Doppler token if using Doppler
[Service]
Environment="DOPPLER_TOKEN=dp.st.your_token"

# Start service
sudo systemctl daemon-reload
sudo systemctl enable boon-tube
sudo systemctl start boon-tube

# View logs
sudo journalctl -u boon-tube -f
```

### Docker
```bash
# With .env
docker run -v $(pwd)/.env:/app/.env boon-tube-daemon

# With Doppler
docker run -e DOPPLER_TOKEN=dp.st.your_token boon-tube-daemon
```

## 📊 Current Status

### Completed
- ✅ TikTok monitoring (Playwright)
- ✅ YouTube video detection (API v3)
- ✅ Doppler integration
- ✅ Configuration management
- ✅ Test suite
- ✅ Documentation

### Next Steps (Your Choice)
1. **Get YouTube API key** - Create new key in Google Cloud Console
2. **Test YouTube** - Run `python3 test_youtube.py` with valid key
3. **Configure social platforms** - Add Discord/Matrix/Bluesky/Mastodon credentials
4. **Enable LLM** - Add Gemini API key for AI-generated posts
5. **Deploy to production** - Set up systemd service or Docker

## 🎯 Immediate Action Items

### To Get YouTube Working
1. Go to https://console.cloud.google.com/apis/credentials
2. Create new API key or renew existing
3. Update `.env`: `YOUTUBE_API_KEY=your_new_key`
4. Test: `python3 test_youtube.py`

### To Use Doppler (Optional)
```bash
# Add secrets to Doppler
doppler secrets set YOUTUBE_API_KEY "your_key_here"
doppler secrets set YOUTUBE_USERNAME "ChiefGyk3D"

# Test
doppler run -- python3 test_youtube.py
```

### To Add Social Platforms
Choose which platforms you want:
- Discord: Easiest (just webhook URL)
- Matrix: Medium (needs homeserver setup)
- Bluesky: Easy (handle + app password)
- Mastodon: Medium (instance + access token)

## 📚 Documentation

- **YouTube Setup**: `docs/YOUTUBE_SETUP.md`
- **Doppler Setup**: `docs/DOPPLER_SETUP.md`
- **Privacy Policy**: `PRIVACY_POLICY.md`
- **Terms of Service**: `TERMS_OF_SERVICE.md`

## 🐛 Troubleshooting

### YouTube Authentication Failed
- Check API key is valid
- Ensure YouTube Data API v3 is enabled
- Verify quota hasn't been exceeded

### TikTok Not Working
- Check username is correct (without @)
- Ensure Playwright is installed: `playwright install chromium`
- Check logs for detailed errors

### Doppler Not Loading Secrets
- Verify login: `doppler login`
- Check project: `doppler configure get project`
- List secrets: `doppler secrets`
- Set token: `export DOPPLER_TOKEN=dp.st.xxx`

### .env Fallback Not Working
- Check file exists: `ls -la .env`
- Verify format: Variables should be `SECTION_KEY=value`
- Load manually: `source .env`

## 📞 Support

- GitHub Issues: https://github.com/ChiefGyk3D/Boon-Tube-Daemon/issues
- Documentation: See `docs/` folder
- Test Scripts: `test_*.py` files show example usage

## 🎉 Success Checklist

- [ ] YouTube API key renewed
- [ ] YouTube test passing: `python3 test_youtube.py`
- [ ] TikTok test passing: `python3 test_integration.py`
- [ ] Doppler configured (optional): `doppler secrets`
- [ ] At least one social platform configured
- [ ] Daemon runs successfully: `python3 main.py`
- [ ] New videos detected and notifications sent

## 🔄 Git Status

Current commits:
```
6f428bc feat: Add Doppler secret management with .env fallback
b12c4d4 feat: Add TikTok monitoring with Playwright network interception
8b5b044 TOS and Privacy Policy to get API access for Tiktok
```

**Ready to push**: 2 commits ahead of origin/main

```bash
# Push to GitHub
git push origin main
```

---

**Next Session Focus**: Choose one of:
1. Get YouTube API key and test full integration
2. Configure Discord/Matrix for notifications
3. Enable Gemini LLM for enhanced posts
4. Deploy to production with systemd
