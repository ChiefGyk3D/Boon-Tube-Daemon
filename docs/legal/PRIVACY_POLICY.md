# Privacy Policy for Boon-Tube-Daemon

**Last Updated:** November 6, 2025

## Introduction

Boon-Tube-Daemon is an open-source application licensed under the Mozilla Public License 2.0 (MPL-2.0). This privacy policy explains how data is handled when you use this software.

## Developer Information

- **Developer:** ChiefGyk3D
- **Project:** Boon-Tube-Daemon
- **Repository:** https://github.com/ChiefGyk3D/Boon-Tube-Daemon
- **License:** Mozilla Public License 2.0

## No Data Collection by Developer

**ChiefGyk3D does NOT collect, store, transmit, or have access to any of your data.**

This application:
- ✅ Runs entirely on **your own infrastructure** (your computer, server, or Docker container)
- ✅ Stores all configuration and credentials **locally on your system**
- ✅ Makes API calls **directly from your system** to third-party services
- ✅ Does NOT send any data to ChiefGyk3D or any central server
- ✅ Does NOT include analytics, tracking, or telemetry
- ✅ Does NOT have a backend server controlled by the developer

## How the Application Works

### Local Operation
Boon-Tube-Daemon is a self-hosted daemon that:
1. Runs on your own hardware/infrastructure
2. Uses your own API credentials
3. Monitors content on platforms you configure (YouTube, TikTok)
4. Posts notifications to platforms you configure (Discord, Matrix, Bluesky, Mastodon)

### Data Flow
```
Your System → Third-Party APIs → Your System
     ↓
Your Configured Notification Platforms
```

**No data flows to or through ChiefGyk3D's servers** because there are no developer-controlled servers.

## Third-Party Services

This application interacts with third-party services based on your configuration:

### Content Monitoring Services
- **YouTube** (via Google YouTube Data API v3)
  - Data accessed: Public video information from channels you configure
  - Privacy Policy: https://policies.google.com/privacy
  
- **TikTok** (via unofficial TikTokApi library with Playwright)
  - Data accessed: Public video information from users you configure
  - Privacy Policy: https://www.tiktok.com/legal/privacy-policy

### Notification Services
- **Discord** (via webhook)
  - Privacy Policy: https://discord.com/privacy
  
- **Matrix** (via matrix-nio)
  - Privacy Policy: Depends on your homeserver (e.g., https://matrix.org/legal/privacy-notice)
  
- **Bluesky** (via AT Protocol)
  - Privacy Policy: https://bsky.social/about/support/privacy-policy
  
- **Mastodon** (via Mastodon.py)
  - Privacy Policy: Depends on your instance

### Optional AI Services
- **Google Gemini** (optional, for content enhancement)
  - Privacy Policy: https://policies.google.com/privacy

**You are responsible for reviewing and complying with each third-party service's privacy policy and terms of service.**

## Data Stored Locally

The following data is stored **only on your local system**:

### Configuration Data (`.env` file)
- API keys and credentials for services you use
- Platform usernames/handles you monitor
- Notification preferences and templates
- Check intervals and settings

### State Data
- Last checked video IDs (to prevent duplicate notifications)
- Timestamps of last checks

### Logs (optional)
- Application operation logs (if you enable logging)
- Error messages and debug information

**Important:** All of this data remains on your system. ChiefGyk3D has no access to it.

## Your Responsibilities

As the operator of this self-hosted application, you are responsible for:

1. **Securing your credentials:** Your API keys and passwords are stored in `.env` files on your system
2. **Complying with third-party terms:** Ensure you comply with YouTube, TikTok, Discord, etc. terms of service
3. **Respecting rate limits:** Configure appropriate check intervals to avoid API quota issues
4. **Data privacy:** Any data you post to notification platforms is subject to those platforms' policies
5. **Legal compliance:** Ensure your use complies with applicable laws and regulations

## API Usage and Rate Limits

### YouTube API
- Uses your YouTube Data API quota (10,000 units/day by default)
- Each check uses ~3 quota units
- You are responsible for staying within Google's quota limits

### TikTok
- Uses unofficial API with browser automation
- May be subject to rate limiting by TikTok
- No official TikTok Developer API is used

### Other Services
- Rate limits depend on each service's policies
- You are responsible for compliance

## Open Source Nature

This application is **open source** under the MPL-2.0 license:

- ✅ You can view all source code
- ✅ You can modify the code
- ✅ You can verify there is no data collection
- ✅ You can audit the application's behavior
- ✅ You can deploy it on your own infrastructure

**The MPL-2.0 license governs software usage and distribution, not privacy/data practices, because no data is collected by the developer.**

## Security Best Practices

To protect your data:

1. **Never commit `.env` files to version control** (already in `.gitignore`)
2. **Use strong, unique API credentials** for each service
3. **Regularly rotate API keys and passwords**
4. **Run the application on secure infrastructure**
5. **Keep the software updated** to receive security patches
6. **Use app-specific passwords** where available (e.g., Bluesky)
7. **Review file permissions** on configuration files

## Children's Privacy

This application is not directed at children under 13. As a self-hosted tool, no data is collected by the developer. However, if you use this application, ensure you comply with applicable children's privacy laws (e.g., COPPA, GDPR) when monitoring or posting content.

## International Users

This application can be used worldwide. As a self-hosted solution:
- Data is stored on **your infrastructure** in **your jurisdiction**
- No international data transfers to ChiefGyk3D occur
- You are responsible for compliance with local data protection laws (GDPR, CCPA, etc.)

## Changes to This Privacy Policy

This privacy policy may be updated to reflect:
- Changes in applicable laws
- Updates to third-party services
- New features or functionality

Changes will be documented in the repository's commit history and `CHANGELOG.md`.

## Disclaimer of Warranties

This application is provided "AS IS" without warranty of any kind, as specified in the MPL-2.0 license. The developer makes no guarantees about:
- Availability or reliability of third-party APIs
- Accuracy of monitored content
- Delivery of notifications
- Security of your credentials

## Contact Information

This is an open-source project. For questions or concerns:

- **GitHub Issues:** https://github.com/ChiefGyk3D/Boon-Tube-Daemon/issues
- **Repository:** https://github.com/ChiefGyk3D/Boon-Tube-Daemon

**Please do not send private credentials or sensitive information via GitHub issues.**

## Summary

**Key Points:**
- ✅ No data is collected, stored, or transmitted to ChiefGyk3D
- ✅ Application runs entirely on your infrastructure
- ✅ All credentials and data stay on your system
- ✅ Open-source code can be audited
- ✅ You are responsible for third-party service compliance
- ✅ MPL-2.0 license governs software usage, not data practices

**This is a self-hosted, privacy-respecting tool. Your data is yours.**

---

*This privacy policy applies to Boon-Tube-Daemon software distributed under the MPL-2.0 license. Third-party services have their own privacy policies.*
