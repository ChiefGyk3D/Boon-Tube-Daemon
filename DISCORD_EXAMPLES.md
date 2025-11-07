# Discord Setup Examples for Multi-Platform Creators

This guide shows real-world examples of Discord webhook and role configurations for creators who post on both YouTube and TikTok.

## 📋 Scenario 1: Single Channel, Separate Roles

**Goal:** All notifications in one channel, but different roles for YouTube vs TikTok

**Server Setup:**
- Channel: `#content-alerts`
- Roles: `@YouTube Fans` and `@TikTok Squad`

**Configuration:**
```bash
# In Doppler (or .env)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456/abcdef
DISCORD_ROLE_YOUTUBE=111111111
DISCORD_ROLE_TIKTOK=222222222
```

**Result:**
- YouTube upload → Posts to #content-alerts, mentions @YouTube Fans
- TikTok upload → Posts to #content-alerts, mentions @TikTok Squad

**Use Case:** Your community is small and you want all content in one place, but let people choose which platforms they want alerts for.

---

## 📋 Scenario 2: Separate Channels Per Platform

**Goal:** Different channels for different content types

**Server Setup:**
- Channels: `#youtube-uploads` and `#tiktok-uploads`
- Roles: `@YT Notifs` and `@TT Notifs`

**Configuration:**
```bash
# In Doppler (or .env)
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/111111/youtube-webhook
DISCORD_WEBHOOK_TIKTOK=https://discord.com/api/webhooks/222222/tiktok-webhook
DISCORD_ROLE_YOUTUBE=333333333
DISCORD_ROLE_TIKTOK=444444444
```

**Result:**
- YouTube upload → Posts to #youtube-uploads, mentions @YT Notifs
- TikTok upload → Posts to #tiktok-uploads, mentions @TT Notifs

**Use Case:** Your community prefers organized channels, or you have mods who manage each platform separately.

---

## 📋 Scenario 3: Single Role for Everything

**Goal:** Simple setup, everyone gets all notifications

**Server Setup:**
- Channel: `#uploads`
- Role: `@Content Alerts`

**Configuration:**
```bash
# In Doppler (or .env)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456/abcdef
DISCORD_ROLE=555555555
```

**Result:**
- YouTube upload → Posts to #uploads, mentions @Content Alerts
- TikTok upload → Posts to #uploads, mentions @Content Alerts

**Use Case:** You're just starting out, or your audience wants to be notified about everything.

---

## 📋 Scenario 4: Advanced - Multiple Channels + Fallback Role

**Goal:** Separate channels, but with a default role for any future platforms

**Server Setup:**
- Channels: `#youtube`, `#tiktok`, `#general-content`
- Roles: `@YT`, `@TT`, `@All Content`

**Configuration:**
```bash
# In Doppler (or .env)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456/general-webhook
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/111111/yt-webhook
DISCORD_WEBHOOK_TIKTOK=https://discord.com/api/webhooks/222222/tt-webhook
DISCORD_ROLE=999999999  # Default for future platforms
DISCORD_ROLE_YOUTUBE=333333333
DISCORD_ROLE_TIKTOK=444444444
```

**Result:**
- YouTube upload → Posts to #youtube, mentions @YT
- TikTok upload → Posts to #tiktok, mentions @TT
- Future platform (Twitch, Kick) → Posts to #general-content, mentions @All Content

**Use Case:** You're planning to expand to more platforms and want a scalable setup.

---

## 📋 Scenario 5: No Role Mentions (Just Webhooks)

**Goal:** Clean notifications without pinging anyone

**Server Setup:**
- Channels: `#youtube`, `#tiktok`
- Roles: None needed

**Configuration:**
```bash
# In Doppler (or .env)
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/111111/yt-webhook
DISCORD_WEBHOOK_TIKTOK=https://discord.com/api/webhooks/222222/tt-webhook
# No role configuration!
```

**Result:**
- YouTube upload → Posts to #youtube (no mentions)
- TikTok upload → Posts to #tiktok (no mentions)

**Use Case:** Your community prefers not to be pinged, they just check the channels when they want.

---

## 🎯 How to Choose?

| Scenario | Best For | Complexity | Flexibility |
|----------|----------|------------|-------------|
| 1. Single Channel, Separate Roles | Small communities | ⭐ Easy | ⭐⭐ Moderate |
| 2. Separate Channels | Organized servers | ⭐⭐ Moderate | ⭐⭐⭐ High |
| 3. Single Role | Getting started | ⭐ Very Easy | ⭐ Low |
| 4. Advanced Multi-Setup | Growing creators | ⭐⭐⭐ Complex | ⭐⭐⭐⭐ Very High |
| 5. No Mentions | Low-noise servers | ⭐ Very Easy | ⭐⭐ Moderate |

---

## 🛠️ Step-by-Step: Setting Up Scenario 2 (Separate Channels)

This is the most popular setup for multi-platform creators.

### Step 1: Create Discord Webhooks

1. **Create #youtube-uploads channel**
   - Server Settings → Integrations → Webhooks → New Webhook
   - Name: "Boon-Tube YouTube"
   - Channel: #youtube-uploads
   - Copy Webhook URL

2. **Create #tiktok-uploads channel**
   - Server Settings → Integrations → Webhooks → New Webhook
   - Name: "Boon-Tube TikTok"
   - Channel: #tiktok-uploads
   - Copy Webhook URL

### Step 2: Create Roles

1. **Create @YouTube Fans role**
   - Server Settings → Roles → Create Role
   - Name: "YouTube Fans"
   - Color: Red (YouTube theme)
   - Allow anyone to @mention this role: ✓

2. **Create @TikTok Squad role**
   - Server Settings → Roles → Create Role
   - Name: "TikTok Squad"
   - Color: Light Blue (TikTok theme)
   - Allow anyone to @mention this role: ✓

### Step 3: Get Role IDs

1. Enable Developer Mode: User Settings → App Settings → Advanced → Developer Mode
2. Right-click "YouTube Fans" role → Copy ID
3. Right-click "TikTok Squad" role → Copy ID

### Step 4: Add to Doppler

```bash
doppler secrets set DISCORD_WEBHOOK_YOUTUBE="https://discord.com/api/webhooks/111.../yt..."
doppler secrets set DISCORD_WEBHOOK_TIKTOK="https://discord.com/api/webhooks/222.../tt..."
doppler secrets set DISCORD_ROLE_YOUTUBE="333333333"
doppler secrets set DISCORD_ROLE_TIKTOK="444444444"
```

### Step 5: Enable in .env

```bash
DISCORD_ENABLE_POSTING=true
```

### Step 6: Test

```bash
doppler run -- python3 test_social.py --platform discord --message "🎬 Testing YouTube webhook!"
# Check #youtube-uploads channel

# Manually switch to test TikTok (edit test script or post real TikTok)
```

---

## 💡 Pro Tips

1. **Role Colors:** Use platform colors to make roles easy to identify
   - YouTube: Red (#FF0000)
   - TikTok: Cyan (#00F2EA)

2. **Role Permissions:** You don't need to give these roles any special permissions - they're just for mentions

3. **Test First:** Use a test server or test channels before going live

4. **Webhook Names:** Name webhooks clearly so you can identify them later (e.g., "Boon-Tube YouTube" not just "Webhook")

5. **Channel Names:** Use clear names like `#youtube-uploads` instead of just `#uploads`

6. **Fallback:** Always configure `DISCORD_WEBHOOK_URL` as a fallback even if you have per-platform webhooks

---

## 🐛 Troubleshooting

**"Role mention didn't work"**
- Verify role ID is correct (right-click → Copy ID)
- Check "Allow anyone to @mention this role" is enabled
- Make sure the role exists in the same server as the webhook

**"Wrong channel"**
- Double-check which channel the webhook was created for
- Verify you're using the correct webhook URL for the platform

**"No notification"**
- Check `DISCORD_ENABLE_POSTING=true` in .env
- Verify webhook URLs are in Doppler: `doppler secrets --only-names`
- Run test script: `doppler run -- python3 test_social.py --platform discord`

---

## 📚 See Also

- [SOCIAL_PLATFORMS_SETUP.md](SOCIAL_PLATFORMS_SETUP.md) - Complete social platform guide
- [Discord Webhook Documentation](https://discord.com/developers/docs/resources/webhook)
- [test_social.py](test_social.py) - Test script for all platforms
