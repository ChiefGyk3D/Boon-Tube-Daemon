# Multi-Account YouTube Monitoring - Migration Guide

This guide explains how to upgrade from single-account to multi-account YouTube monitoring.

## Overview

The multi-account feature allows you to monitor multiple YouTube channels simultaneously, each with its own optional Discord role for notifications.

**Key Features:**
- Monitor unlimited YouTube channels
- Assign different Discord roles per channel
- Backward compatible - existing configs work without changes
- Drop-in upgrade - no breaking changes

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

## Discord Role Configuration

### Finding Discord Role IDs

1. Enable Developer Mode in Discord:
   - User Settings → Advanced → Developer Mode (ON)

2. Right-click the role in Server Settings → Roles
3. Click "Copy ID"

### Priority Order for Role Mentions

When a new video is posted, Discord role mentions follow this priority:

1. **Channel-specific role** (from `YOUTUBE_ACCOUNTS[].discord_role`)
2. **Platform-specific role** (from `DISCORD_ROLE_YOUTUBE`)
3. **Default role** (from `DISCORD_ROLE`)

Example:
```bash
# Default role for all platforms
DISCORD_ROLE=999999999

# YouTube-specific role (overrides default for YouTube)
DISCORD_ROLE_YOUTUBE=888888888

# Per-channel roles (override both default and platform-specific)
YOUTUBE_ACCOUNTS=[{"username":"@MainChannel","discord_role":"777777777"}]
```

Result:
- Main Channel videos mention role `777777777`
- Other YouTube channels mention role `888888888`
- Non-YouTube platforms mention role `999999999`

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
