# Multi-Account YouTube Monitoring - Migration Guide

This guide explains how to upgrade from single-account to multi-account YouTube monitoring.

## Overview

The multi-account feature allows you to monitor multiple YouTube channels simultaneously, each with its own optional Discord configuration (role, webhook, or both).

**Key Features:**
- Monitor unlimited YouTube channels
- **Assign different Discord roles per channel** (mention different groups)
- **Post to different Discord channels/servers per YouTube channel** (via webhooks)
- **Mix and match**: Some channels share webhooks, others use dedicated ones
- Backward compatible - existing configs work without changes
- Drop-in upgrade - no breaking changes

## Real-World Use Cases

### Use Case 1: Multi-Server Bot
You run a bot that serves multiple Discord servers. Each server wants notifications for different YouTube creators:
- Server A wants announcements for Creator 1 in their #videos channel
- Server B wants announcements for Creator 2 in their #announcements channel
- Server C wants both creators but in separate channels

**Solution:** Use per-channel `discord_webhook` to route each creator to the right server/channel.

### Use Case 2: Role-Based Notifications in One Server
Your Discord server monitors multiple creators, and members can opt-in to specific creators:
- @LinusTechTips role for LTT fans
- @MKBHD role for Marques fans
- @VeritasiumFans role for science enthusiasts

**Solution:** Use per-channel `discord_role` to mention the right group for each creator.

### Use Case 3: Mixed Configuration
You have a main server (#youtube-uploads) for all creators, but one popular creator gets their own dedicated channel:
- 5 creators → Post to #youtube-uploads with @AllVideos role
- VIP creator → Post to #vip-creator with @VIPFans role

**Solution:** Set default webhook for most channels, override with `discord_webhook` for the VIP channel.

## Backward Compatibility

### ✅ Existing Configurations Continue Working

If you have an existing setup with:
```bash
YOUTUBE_USERNAME=@YourChannel
# or
YOUTUBE_CHANNEL_ID=UCxxxxxxxxx
```

**Nothing breaks!** Your daemon will continue working exactly as before. The system automatically converts your single-account config to the new format internally.

## Migration Paths

### Option 1: Keep Single Account (No Changes Required)

If you only monitor one channel, you don't need to change anything. Your existing config works perfectly:

```bash
YOUTUBE_ENABLE_MONITORING=true
YOUTUBE_USERNAME=@YourChannel
YOUTUBE_API_KEY=your_api_key
```

### Option 2: Upgrade to Multi-Account

To monitor multiple YouTube channels, add the `YOUTUBE_ACCOUNTS` variable:

#### Step 1: Create JSON Array

Format:
```bash
YOUTUBE_ACCOUNTS=[{"username":"@Channel1"},{"username":"@Channel2"}]
```

Each account object supports:
- `username`: YouTube @handle or username (required if no channel_id)
- `channel_id`: YouTube channel ID (required if no username, faster lookup)
- `name`: Optional display name for logs (auto-detected if omitted)
- `discord_role`: Optional Discord role ID to mention for this channel

#### Step 2: Update .env File

**Before (single account):**
```bash
YOUTUBE_ENABLE_MONITORING=true
YOUTUBE_USERNAME=@LinusTechTips
YOUTUBE_CHANNEL_ID=UCXuqSBlHAE6Xw-yeJA0Tunw
YOUTUBE_API_KEY=your_api_key
```

**After (multi-account):**
```bash
YOUTUBE_ENABLE_MONITORING=true

# Legacy vars (now optional, kept for backward compat)
#YOUTUBE_USERNAME=@LinusTechTips
#YOUTUBE_CHANNEL_ID=UCXuqSBlHAE6Xw-yeJA0Tunw

# New multi-account config
YOUTUBE_ACCOUNTS=[{"username":"@LinusTechTips","discord_role":"111111111"},{"username":"@TechLinked","discord_role":"222222222"},{"channel_id":"UCXuqSBlHAE6Xw-yeJA0Tunw","name":"LTT Clips","discord_role":"333333333"}]

YOUTUBE_API_KEY=your_api_key
```

#### Step 3: Restart Daemon

```bash
sudo systemctl restart boon-tube-daemon
```

#### Step 4: Verify Logs

Check that all channels are detected:
```bash
sudo journalctl -u boon-tube-daemon -f
```

You should see:
```
✓ YouTube: Monitoring Linus Tech Tips (ID: UCXuqSBlHAE6...)
✓ YouTube: Monitoring TechLinked (ID: UCddiU...)
✓ YouTube: Monitoring LTT Clips (ID: UCXuqSBlH...)
✓ YouTube Videos authenticated for 3 account(s)
```

## Configuration Examples

### Example 1: Two Channels, Same Discord Role

```bash
YOUTUBE_ACCOUNTS=[{"username":"@MainChannel"},{"username":"@SecondChannel"}]
DISCORD_ROLE=123456789012345678
```

Both channels will use the default Discord role.

### Example 2: Two Channels, Different Discord Roles

```bash
YOUTUBE_ACCOUNTS=[{"username":"@TechNews","discord_role":"111111111"},{"username":"@Gaming","discord_role":"222222222"}]
```

Each channel mentions its own Discord role.

### Example 3: Mix of Usernames and Channel IDs

```bash
YOUTUBE_ACCOUNTS=[{"username":"@FastLookup"},{"channel_id":"UCxxxxxxxxxxxxx","name":"Slow Lookup Channel"}]
```

Use `channel_id` when available (faster, uses less API quota).

### Example 4: Minimal Config (No Roles)

```bash
YOUTUBE_ACCOUNTS=[{"username":"@Channel1"},{"username":"@Channel2"},{"username":"@Channel3"}]
```

Simple monitoring without Discord role mentions.

### Example 5: Advanced (Multiple Channels, Different Roles, Custom Names)

```bash
YOUTUBE_ACCOUNTS=[{"channel_id":"UCXuqSBlHAE6Xw-yeJA0Tunw","name":"LTT Main","discord_role":"111111111"},{"channel_id":"UCddiUEpeqJcYeBxX1IVBKvQ","name":"LTT ShortCircuit","discord_role":"222222222"},{"channel_id":"UC0vBXGSyV14uvJ4hECDOl0Q","name":"LTT TechLinked","discord_role":"333333333"}]
```

### Example 6: Different Discord Servers/Channels per YouTube Channel

**Use Case:** Post tech videos to #tech-news channel, gaming videos to #gaming-announcements channel

```bash
# Tech channel posts to #tech-news webhook
# Gaming channel posts to #gaming-announcements webhook
YOUTUBE_ACCOUNTS=[{"username":"@TechChannel","discord_webhook":"https://discord.com/api/webhooks/111111/xxxTECHxxx","discord_role":"123456"},{"username":"@GamingChannel","discord_webhook":"https://discord.com/api/webhooks/222222/yyyGAMEyyy","discord_role":"789012"}]
```

Each YouTube channel posts to a completely different Discord channel or even different server!

### Example 7: Mix Everything - Different Servers, Roles, and Channels

**Use Case:** Multi-server bot posting different creators to different communities

```bash
YOUTUBE_ACCOUNTS=[{"username":"@Creator1","discord_webhook":"https://discord.com/api/webhooks/111/aaa","discord_role":"100"},{"username":"@Creator2","discord_webhook":"https://discord.com/api/webhooks/222/bbb","discord_role":"200"},{"username":"@Creator3","discord_role":"300"}]
```

- Creator1 → Posts to Server A's #creator1-videos with @Creator1Fans role
- Creator2 → Posts to Server B's #announcements with @Subscribers role  
- Creator3 → Posts to default webhook with @Creator3 role

## Discord Webhook & Role Configuration

### Finding Discord Role IDs

1. Enable Developer Mode in Discord:
   - User Settings → Advanced → Developer Mode (ON)

2. Right-click the role in Server Settings → Roles
3. Click "Copy ID"

### Priority Order for Webhooks

When posting a new video, Discord webhooks are selected in this priority order:

1. **Channel-specific webhook** (from `YOUTUBE_ACCOUNTS[].discord_webhook`)
2. **Platform-specific webhook** (from `DISCORD_WEBHOOK_YOUTUBE`)
3. **Default webhook** (from `DISCORD_WEBHOOK_URL`)

### Priority Order for Role Mentions

When a new video is posted, Discord role mentions follow this priority:

1. **Channel-specific role** (from `YOUTUBE_ACCOUNTS[].discord_role`)
2. **Platform-specific role** (from `DISCORD_ROLE_YOUTUBE`)
3. **Default role** (from `DISCORD_ROLE`)

### Complete Example - All Priority Levels

```bash
# Default webhook and role (used by all platforms unless overridden)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/000/default
DISCORD_ROLE=999999999

# YouTube-specific webhook and role (overrides defaults for all YouTube channels)
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/111/youtube
DISCORD_ROLE_YOUTUBE=888888888

# Per-channel webhooks and roles (override all defaults and platform-specific)
YOUTUBE_ACCOUNTS=[{"username":"@SpecialChannel","discord_webhook":"https://discord.com/api/webhooks/222/special","discord_role":"777777777"},{"username":"@RegularChannel"}]
```

**Result:**
- **Special Channel** videos → Webhook `222/special` with role `777777777` (channel-specific overrides)
- **Regular Channel** videos → Webhook `111/youtube` with role `888888888` (YouTube-specific)
- **TikTok/other platforms** → Webhook `000/default` with role `999999999` (defaults)

## API Quota Considerations

### Single Account vs Multi-Account

**API costs per check:**
- Get channel uploads playlist: 1 unit
- Get recent videos: 1 unit
- Get video details: 1 unit
- **Total per channel per check: 3 units**

**Daily quota: 10,000 units**

### Quota Planning

With default 15-minute interval (96 checks/day):

| Channels | Units/Check | Daily Units | Remaining Quota |
|----------|-------------|-------------|-----------------|
| 1        | 3           | 288         | 9,712 (97%)     |
| 2        | 6           | 576         | 9,424 (94%)     |
| 3        | 9           | 864         | 9,136 (91%)     |
| 5        | 15          | 1,440       | 8,560 (86%)     |
| 10       | 30          | 2,880       | 7,120 (71%)     |

**Recommendation:** With the default 15-minute interval, you can safely monitor up to 10 channels while leaving plenty of quota for other API operations.

### Adjusting Check Interval

If monitoring many channels, increase `CHECK_INTERVAL`:

```bash
# 30-minute intervals (48 checks/day, 50% quota usage for 10 channels)
CHECK_INTERVAL=1800

# 1-hour intervals (24 checks/day, 25% quota usage for 10 channels)
CHECK_INTERVAL=3600
```

## Testing Your Configuration

### Test 1: Validate Configuration Parsing

```bash
python3 -c "from boon_tube_daemon.utils.config import load_config, get_youtube_accounts; load_config(); accounts = get_youtube_accounts(); print(f'✓ Loaded {len(accounts)} account(s)'); [print(f'  - {a[\"name\"] or a.get(\"username\") or a.get(\"channel_id\")}') for a in accounts]"
```

Expected output:
```
✓ Loaded 3 account(s)
  - @LinusTechTips
  - @TechLinked
  - LTT Clips
```

### Test 2: Dry Run (Check Authentication)

```bash
# Temporarily add this to main.py authenticate():
logger.info(f"Loaded {len(self.accounts)} YouTube account(s)")
for account in self.accounts:
    logger.info(f"  - {account['name']}: {account.get('discord_role', 'No role')}")
```

### Test 3: Monitor Live

```bash
sudo journalctl -u boon-tube-daemon -f --since "5 minutes ago"
```

Watch for:
```
✓ YouTube: Monitoring Channel Name (ID: UCxxx...)
🎬 YouTube (Channel Name): New video: Video Title...
📤 Posting to Discord...
✓ Posted to Discord
```

## Troubleshooting

### Issue: "No YouTube accounts configured"

**Cause:** Both legacy and new config vars are empty.

**Fix:** Set either:
- Legacy: `YOUTUBE_USERNAME` or `YOUTUBE_CHANNEL_ID`
- New: `YOUTUBE_ACCOUNTS`

### Issue: "Failed to parse YOUTUBE_ACCOUNTS JSON"

**Cause:** Invalid JSON syntax.

**Fix:** Validate JSON format:
- Use double quotes, not single quotes
- Escape quotes inside strings: `\"`
- No trailing commas
- Brackets match: `[` and `]`

**Valid:**
```bash
YOUTUBE_ACCOUNTS=[{"username":"@Test"}]
```

**Invalid:**
```bash
YOUTUBE_ACCOUNTS=[{'username':'@Test'}]  # Single quotes
YOUTUBE_ACCOUNTS=[{"username":"@Test"},]  # Trailing comma
```

### Issue: "Could not find YouTube channel for username"

**Cause:** Username not found or typo.

**Fix:**
1. Verify username on YouTube
2. Try with `@` prefix: `@username`
3. Or use `channel_id` instead (more reliable)

### Issue: Discord role not mentioned

**Cause:** Role ID is incorrect or bot lacks permissions.

**Fix:**
1. Verify role ID (right-click role → Copy ID)
2. Ensure role is mentionable in Discord server settings
3. Check bot has permission to mention roles

### Issue: Quota exceeded errors

**Cause:** Too many channels or too frequent checks.

**Fix:**
1. Increase `CHECK_INTERVAL`:
   ```bash
   CHECK_INTERVAL=1800  # 30 minutes
   ```
2. Reduce number of monitored channels
3. Use `channel_id` instead of `username` (saves 1 API unit per check)

---

## Multi-Account Social Platform Support

In addition to multi-account YouTube monitoring, you can also configure multiple accounts for Bluesky, Mastodon, and Matrix platforms.

### Bluesky Multi-Account

**Use Cases:**
- Post to both personal and project accounts
- Cross-post to multiple Bluesky accounts
- Separate accounts for different content types

**Configuration Example:**
```bash
BLUESKY_ENABLE_POSTING=true
BLUESKY_ACCOUNTS='[
  {
    "handle": "personal.bsky.social",
    "app_password": "xxxx-xxxx-xxxx-xxxx",
    "name": "Personal"
  },
  {
    "handle": "project.bsky.social",
    "app_password": "yyyy-yyyy-yyyy-yyyy",
    "name": "Project Updates"
  }
]'
```

**Backward Compatible:** Existing single-account configs continue working:
```bash
BLUESKY_ENABLE_POSTING=true
BLUESKY_HANDLE=yourhandle.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

### Mastodon Multi-Instance

**Use Cases:**
- Cross-post to multiple Mastodon instances (mastodon.social, fosstodon.org, etc.)
- Post to both personal and organizational accounts
- Reach different communities across the fediverse

**Configuration Example:**
```bash
MASTODON_ENABLE_POSTING=true
MASTODON_ACCOUNTS='[
  {
    "api_base_url": "https://mastodon.social",
    "client_id": "your_client_id_1",
    "client_secret": "your_client_secret_1",
    "access_token": "your_access_token_1",
    "name": "Mastodon Social"
  },
  {
    "api_base_url": "https://fosstodon.org",
    "client_id": "your_client_id_2",
    "client_secret": "your_client_secret_2",
    "access_token": "your_access_token_2",
    "name": "Fosstodon"
  }
]'
```

**Backward Compatible:** Existing single-account configs continue working:
```bash
MASTODON_ENABLE_POSTING=true
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_CLIENT_ID=your_client_id
MASTODON_CLIENT_SECRET=your_client_secret
MASTODON_ACCESS_TOKEN=your_access_token
```

### Matrix Multi-Room/Multi-Homeserver

**Use Cases:**
- Post to multiple rooms on the same homeserver
- Post to rooms on different homeservers
- Separate accounts for different projects/communities

**Configuration Example (Access Token Method):**
```bash
MATRIX_ENABLE_POSTING=true
MATRIX_ACCOUNTS='[
  {
    "homeserver": "https://matrix.org",
    "room_id": "!roomid1:matrix.org",
    "access_token": "your_token_1",
    "name": "Main Room"
  },
  {
    "homeserver": "https://chat.mydomain.com",
    "room_id": "!roomid2:chat.mydomain.com",
    "access_token": "your_token_2",
    "name": "Self-Hosted Server"
  }
]'
```

**Configuration Example (Username/Password Method with Auto-Rotation):**
```bash
MATRIX_ENABLE_POSTING=true
MATRIX_ACCOUNTS='[
  {
    "homeserver": "https://matrix.org",
    "room_id": "!roomid1:matrix.org",
    "username": "@botuser:matrix.org",
    "password": "bot_password",
    "name": "Main Bot"
  }
]'
```

**Note:** If both `access_token` and `username`/`password` are provided for an account, username/password takes precedence (preferred for auto-rotation).

**Backward Compatible:** Existing single-account configs continue working:
```bash
MATRIX_ENABLE_POSTING=true
MATRIX_HOMESERVER=https://matrix.org
MATRIX_ROOM_ID=!yourroom:matrix.org
MATRIX_ACCESS_TOKEN=your_token
# OR
MATRIX_USERNAME=@botuser:matrix.org
MATRIX_PASSWORD=bot_password
```

### Social Platform Logging

With multi-account social platforms, logs show which accounts receive posts:

```
✓ Bluesky: Authenticated Personal
✓ Bluesky: Authenticated Project Updates
✓ Bluesky authenticated for 2 account(s)

✓ Mastodon: Authenticated Mastodon Social
✓ Mastodon: Authenticated Fosstodon
✓ Mastodon authenticated for 2 account(s)

✓ Matrix: Authenticated Main Room
✓ Matrix: Authenticated Self-Hosted Server
✓ Matrix authenticated for 2 account(s)

[New video detected]
✓ Bluesky: Posted to Personal
✓ Bluesky: Posted to Project Updates
✓ Mastodon: Posted to Mastodon Social
✓ Mastodon: Posted to Fosstodon
✓ Matrix: Posted to Main Room
✓ Matrix: Posted to Self-Hosted Server
```

### Error Handling

If one account fails, others continue:

```
✓ Bluesky: Authenticated Personal
✗ Bluesky authentication failed for Project Updates: Invalid credentials
✓ Bluesky authenticated for 1 account(s)

[New video detected]
✓ Bluesky: Posted to Personal
✗ Bluesky post failed for Project Updates: Not authenticated
```

The daemon continues running even if some accounts fail authentication or posting.

---

## Rollback

If you need to revert to single-account:

1. **Remove or comment out `YOUTUBE_ACCOUNTS`:**
   ```bash
   #YOUTUBE_ACCOUNTS=[...]
   ```

2. **Ensure legacy vars are set:**
   ```bash
   YOUTUBE_USERNAME=@YourChannel
   YOUTUBE_API_KEY=your_api_key
   ```

3. **Restart daemon:**
   ```bash
   sudo systemctl restart boon-tube-daemon
   ```

The system automatically falls back to legacy single-account mode.

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u boon-tube-daemon -f`
2. Validate JSON: https://jsonlint.com/
3. Open issue: https://github.com/ChiefGyk3D/Boon-Tube-Daemon/issues

## Summary

- **Backward compatible:** Existing configs work without changes
- **Drop-in upgrade:** Add `YOUTUBE_ACCOUNTS` to enable multi-account
- **Per-channel roles:** Assign different Discord roles per channel
- **API quota friendly:** ~3 units per channel per check
- **Easy rollback:** Remove `YOUTUBE_ACCOUNTS` to revert
