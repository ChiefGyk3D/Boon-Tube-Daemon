# Changelog

All notable changes to Boon-Tube-Daemon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-03

### Added
- Initial release of Boon-Tube-Daemon
- YouTube video upload monitoring via YouTube Data API v3
- TikTok video monitoring via unofficial TikTokApi
- Discord notification support via webhooks
- Matrix notification support via matrix-nio
- Bluesky notification support via AT Protocol
- Mastodon notification support via Mastodon.py
- Configurable check intervals
- Custom notification templates
- Environment variable configuration support
- Comprehensive documentation (README, QUICKSTART, CONTRIBUTING)
- Docker and docker-compose support
- Systemd service template
- Setup and test scripts
- Graceful error handling and quota management
- Logging with timestamps

### Features
- **Media Platforms**:
  - YouTube video upload detection
  - TikTok video upload detection
  - Efficient API quota usage
  - Automatic state tracking (prevents duplicate notifications)
  
- **Social Platforms**:
  - Discord with role mentions and rich embeds
  - Matrix with HTML formatting
  - Bluesky with rich text and link cards
  - Mastodon with media attachments
  
- **Configuration**:
  - INI file configuration
  - Environment variable overrides
  - Example configuration templates
  - Secret management support
  
- **Deployment**:
  - Python script (direct execution)
  - Systemd service
  - Docker container
  - Docker Compose orchestration
  
- **Developer Experience**:
  - Test script for configuration validation
  - Setup script for easy installation
  - Quick start guide
  - Contribution guidelines
  - MIT License

### Known Limitations
- TikTok monitoring uses unofficial API (may break with updates)
- YouTube API has daily quota limits (10,000 units/day)
- Matrix does not support editing messages (no live updates)
- First TikTok run requires downloading browser binaries (~150MB)

## [Unreleased]

### Planned Features
- Instagram video monitoring
- Twitch VOD monitoring
- Telegram notification support
- Slack notification support
- Database persistence for state tracking
- Web dashboard for monitoring
- Multi-channel/multi-user support
- Webhook notification support (generic)
- RSS feed generation
- Healthcheck endpoints
- Prometheus metrics
- Rate limit backoff strategies
- Video metadata in notifications (duration, views, etc.)
- Thumbnail customization
- Notification filtering (by keywords, hashtags)

---

## Version History

- **1.0.0** (2025-11-03) - Initial release

## Migration Guide

N/A - First release

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/chiefgyk3d/Boon-Tube-Daemon/issues
- GitHub Discussions: https://github.com/chiefgyk3d/Boon-Tube-Daemon/discussions
