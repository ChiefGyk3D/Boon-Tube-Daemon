# Boon-Tube-Daemon 🎬

**Automated monitoring daemon for TikTok and YouTube video uploads with multi-platform social notifications and AI enhancement.**

Monitor your favorite creators for new TikTok and YouTube videos and automatically post notifications to Discord, Matrix, Bluesky, and/or Mastodon. Now with optional **Gemini AI integration** for intelligent content analysis and enhanced notifications!

## WORK IN PROGRESS

## ✨ Key Features

- 📺 **YouTube Monitoring**: Detect new video uploads using YouTube Data API v3
- 🎵 **TikTok Monitoring**: Track new TikTok videos (unofficial API)
- 🤖 **AI Enhancement** (Optional): Gemini Flash 2.0 Lite for:
  - Intelligent content summaries
  - Auto-generated hashtags
  - Enhanced notification text
  - Content quality filtering
- 📢 **Multi-Platform Notifications**: Discord, Matrix, Bluesky, Mastodon
- ⚙️ **Highly Configurable**: Custom intervals, templates, filters
- 🐳 **Docker Ready**: Full containerization support
- 🔄 **Production Ready**: Systemd service, error handling, logging

## Quick Start

```bash
# Install
./setup.sh

# Configure
cp .env.example .env
nano .env  # Add your API keys

# Test
python test.py

# Run
python main.py
```

## Project Structure

```
Boon-Tube-Daemon/
├── boon_tube_daemon/      # Main application package
│   ├── media/            # YouTube & TikTok monitors
│   ├── social/           # Discord, Matrix, Bluesky, Mastodon
│   ├── llm/              # Gemini AI integration
│   └── utils/            # Configuration & secrets
├── docker/               # Docker files
├── docs/                 # Documentation
├── main.py              # Entry point
└── .env.example         # Configuration template
```

## Documentation

- 📖 [Full Documentation](README.md)
- ⚡ [Quick Reference](docs/QUICKSTART.md)
- 🤝 [Contributing Guide](docs/CONTRIBUTING.md)
- 📋 [Changelog](docs/CHANGELOG.md)

## Requirements

- Python 3.8+
- YouTube Data API key (for YouTube)
- Playwright (for TikTok)
- At least one social platform configured
- (Optional) Gemini API key for AI features

## Legal

### License
Mozilla Public License 2.0 - See [LICENSE](LICENSE)

This project is licensed under the MPL-2.0, which allows you to use, modify, and distribute this software while requiring that modifications to MPL-licensed files remain open source.

### Privacy & Terms
- 📜 [Privacy Policy](PRIVACY_POLICY.md) - No data collection, self-hosted
- 📋 [Terms of Service](TERMS_OF_SERVICE.md) - Open source, use at your own risk

**Important:** You are responsible for complying with third-party service terms (YouTube, TikTok, Discord, etc.) when using this software.

---

Built with ❤️ by [@chiefgyk3d](https://github.com/chiefgyk3d)
