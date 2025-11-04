# 🎬 Boon-Tube-Daemon - Project Complete!

## 🎉 What We Built

A complete, production-ready daemon for monitoring TikTok and YouTube video uploads with multi-platform social notifications!

## 📁 Project Structure

```
Boon-Tube-Daemon/
├── 📄 Main Application
│   ├── main.py                 # Main daemon orchestrator
│   ├── config.py              # Configuration management
│   └── test.py                # Configuration testing tool
│
├── 📺 Media Monitoring
│   ├── Media/
│   │   ├── base.py            # Base class for media platforms
│   │   ├── youtube_videos.py # YouTube upload monitoring
│   │   ├── tiktok.py          # TikTok monitoring (unofficial API)
│   │   └── __init__.py        # Module initialization
│
├── 📢 Social Notifications
│   ├── Social/
│   │   ├── discord.py         # Discord webhooks
│   │   ├── matrix.py          # Matrix protocol
│   │   ├── bluesky.py         # Bluesky (AT Protocol)
│   │   ├── mastodon.py        # Mastodon (ActivityPub)
│   │   └── __init__.py        # Module initialization
│
├── ⚙️ Configuration
│   ├── .env.example     # Configuration template
│   ├── .env.example           # Environment variables template (optional)
│   └── .gitignore            # Git ignore rules
│
├── 🐳 Deployment
│   ├── Dockerfile            # Docker container
│   ├── docker-compose.yml    # Docker Compose orchestration
│   ├── .dockerignore         # Docker build exclusions
│   ├── boon-tube.service     # Systemd service template
│   ├── setup.sh              # Installation script
│   └── run.sh                # Quick start script
│
├── 📚 Documentation
│   ├── README.md             # Complete user guide
│   ├── QUICKSTART.md         # Quick reference
│   ├── CONTRIBUTING.md       # Contribution guide
│   ├── CHANGELOG.md          # Version history
│   └── LICENSE               # MIT License
│
└── 📦 Dependencies
    └── requirements.txt       # Python packages
```

## ✨ Key Features

### Media Platform Monitoring
- ✅ **YouTube**: Detects new video uploads using official YouTube Data API v3
- ✅ **TikTok**: Monitors for new TikTok videos (unofficial API)
- ✅ **Efficient**: Smart quota management to stay within API limits
- ✅ **Persistent**: Tracks last seen video to prevent duplicate notifications

### Social Platform Notifications
- ✅ **Discord**: Rich embeds with thumbnails via webhooks
- ✅ **Matrix**: HTML formatted messages with native protocol
- ✅ **Bluesky**: Rich text with embedded links and previews
- ✅ **Mastodon**: Posts with media attachments

### Configuration & Deployment
- ✅ **Flexible Config**: INI files or environment variables
- ✅ **Docker Ready**: Full containerization support
- ✅ **Systemd Service**: Run as a system service
- ✅ **Easy Setup**: Automated installation script
- ✅ **Testing Tools**: Verify configuration before running

### Developer Experience
- ✅ **Well Documented**: Comprehensive guides and examples
- ✅ **Type Hints**: Modern Python with type annotations
- ✅ **Error Handling**: Graceful error recovery
- ✅ **Logging**: Detailed logs for debugging
- ✅ **Contribution Guide**: Clear guidelines for contributors

## 🚀 Quick Start

### 1. Install
```bash
./setup.sh
```

### 2. Configure
```bash
cp .env.example .env
nano .env  # Add your API keys
```

### 3. Test
```bash
python test.py
```

### 4. Run
```bash
python main.py
```

## 📋 Configuration Checklist

### Required for YouTube
- [ ] YouTube API key from Google Cloud Console
- [ ] YouTube channel username or handle
- [ ] Enable YouTube Data API v3 in your project

### Required for TikTok
- [ ] TikTok username (without @)
- [ ] Run `playwright install` for browser automation

### Required for Notifications (pick at least one)
- [ ] **Discord**: Webhook URL from server settings
- [ ] **Matrix**: Homeserver URL, room ID, and access token
- [ ] **Bluesky**: Handle and app password
- [ ] **Mastodon**: Instance URL, client ID/secret, access token

## 🎯 Usage Examples

### Run Continuously
```bash
python main.py
```

### Run in Background
```bash
nohup python main.py > boon-tube.log 2>&1 &
```

### Run with Docker
```bash
docker-compose up -d
```

### Run as Systemd Service
```bash
sudo cp boon-tube.service /etc/systemd/system/
sudo systemctl enable boon-tube
sudo systemctl start boon-tube
```

## 🔧 Customization

### Custom Check Interval
```ini
[Settings]
check_interval = 300  # seconds (5 minutes)
```

### Custom Notification Template
```ini
[Settings]
notification_template = 🎬 New {platform} video!

{title}

{url}

Check it out! 🔥
```

### Environment Variables
```bash
export BOON_TUBE_YOUTUBE_API_KEY="your_key"
export BOON_TUBE_DISCORD_WEBHOOK_URL="your_webhook"
python main.py
```

## 📊 API Quota Usage

| Platform | Quota Limit | Usage per Check | Daily Checks (5min) |
|----------|-------------|-----------------|---------------------|
| YouTube | 10,000 units/day | ~3 units | ~3,333 checks |
| TikTok | None (unofficial) | N/A | Unlimited* |

*TikTok may implement rate limiting

## 🛠️ Troubleshooting

### Test Configuration
```bash
python test.py
```

### View Logs
```bash
# If systemd
journalctl -u boon-tube -f

# If nohup
tail -f boon-tube.log
```

### Common Issues
- **YouTube quota exceeded**: Increase `check_interval` to 600-900s
- **TikTok not working**: Run `playwright install chromium`
- **Import errors**: Run `pip install -r requirements.txt`

## 🔒 Security Best Practices

1. ✅ Never commit `.env` to git (already in `.gitignore`)
2. ✅ Use app passwords, not main passwords (Bluesky, etc.)
3. ✅ Rotate API keys periodically
4. ✅ Run as non-root user
5. ✅ Use environment variables in production

## 📈 Future Enhancements

Planned features for future releases:
- Instagram video monitoring
- Twitch VOD monitoring
- Telegram notifications
- Web dashboard
- Database persistence
- Multi-channel support
- Prometheus metrics
- Video metadata in notifications

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Credits

Built with:
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [TikTokApi](https://github.com/davidteather/TikTok-Api)
- [discord-webhook](https://pypi.org/project/discord-webhook/)
- [matrix-nio](https://github.com/poljar/matrix-nio)
- [atproto](https://github.com/MarshalX/atproto) (Bluesky)
- [Mastodon.py](https://github.com/halcy/Mastodon.py)

## 📞 Support

- 🐛 Bug Reports: [GitHub Issues](https://github.com/chiefgyk3d/Boon-Tube-Daemon/issues)
- 💬 Questions: [GitHub Discussions](https://github.com/chiefgyk3d/Boon-Tube-Daemon/discussions)
- 📖 Documentation: [README.md](README.md)

---

**Happy monitoring! 🎬📱 Enjoy your automated social media alerts!**

Built by [@chiefgyk3d](https://github.com/chiefgyk3d) with ❤️
