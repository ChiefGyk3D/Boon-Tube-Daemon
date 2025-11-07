# Social Platforms Setup Guide

This guide will help you configure Bluesky, Mastodon, Discord, and Matrix for your Boon-Tube-Daemon.

## 🚀 Quick Overview

All platforms use the same setup pattern:
1. Get credentials from the platform
2. Add to Doppler (sensitive) or .env (local dev)
3. Enable posting in .env
4. Test!

---

## 🦋 Bluesky Setup

### What You Need
- Bluesky account handle (e.g., `yourname.bsky.social`)
- App password (NOT your main password)

### Step 1: Create App Password
1. Go to https://bsky.app/settings/app-passwords
2. Click "Add App Password"
3. Name it "Boon-Tube-Daemon"
4. Copy the generated password (you can't see it again!)

### Step 2: Add to Doppler or .env

**Option A: Doppler (Recommended for production)**
```bash
doppler secrets set BLUESKY_APP_PASSWORD="your-app-password-here"
```

**Option B: .env (Local development)**
```bash
# In .env
BLUESKY_APP_PASSWORD=your-app-password-here
```

### Step 3: Configure Handle in .env
```bash
# In .env (this is not sensitive)
BLUESKY_HANDLE=yourname.bsky.social
BLUESKY_ENABLE_POSTING=true
```

### Step 4: Test
```bash
doppler run -- python3 test_social.py --platform bluesky
```

---

## 🐘 Mastodon Setup

### What You Need
- Mastodon instance URL (e.g., `https://mastodon.social`)
- Client ID, Client Secret, and Access Token

### Step 1: Create Mastodon Application
1. Log into your Mastodon instance
2. Go to Settings → Development → New Application
3. Name: "Boon-Tube-Daemon"
4. Scopes: `read` and `write`
5. Click "Submit"
6. Copy: Client Key, Client Secret, and Your Access Token

### Step 2: Add to Doppler or .env

**Option A: Doppler (Recommended)**
```bash
doppler secrets set MASTODON_CLIENT_ID="your-client-id"
doppler secrets set MASTODON_CLIENT_SECRET="your-client-secret"
doppler secrets set MASTODON_ACCESS_TOKEN="your-access-token"
```

**Option B: .env (Local development)**
```bash
# In .env
MASTODON_CLIENT_ID=your-client-id
MASTODON_CLIENT_SECRET=your-client-secret
MASTODON_ACCESS_TOKEN=your-access-token
```

### Step 3: Configure Instance in .env
```bash
# In .env (this is not sensitive)
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_ENABLE_POSTING=true
```

### Step 4: Test
```bash
doppler run -- python3 test_social.py --platform mastodon
```

---

## 💬 Discord Setup

### What You Need
- Discord webhook URL(s)
- Optional: Role ID for mentions

### Step 1: Create Webhook
1. Open your Discord server
2. Go to Server Settings → Integrations → Webhooks
3. Click "New Webhook"
4. Name it "Boon-Tube" (or similar)
5. Choose the channel for notifications
6. Click "Copy Webhook URL"

### Step 2: Add to Doppler or .env

**Option A: Doppler (Recommended)**
```bash
doppler secrets set DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

**Option B: .env (Local development)**
```bash
# In .env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Step 3: Optional - Per-Platform Webhooks
You can have different webhooks for different content sources (e.g., separate channels for YouTube vs TikTok):

```bash
# Doppler
doppler secrets set DISCORD_WEBHOOK_YOUTUBE="https://discord.com/api/webhooks/..."
doppler secrets set DISCORD_WEBHOOK_TIKTOK="https://discord.com/api/webhooks/..."

# Or in .env
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_TIKTOK=https://discord.com/api/webhooks/...
```

**Example Use Case:**
- `#youtube-uploads` channel → `DISCORD_WEBHOOK_YOUTUBE`
- `#tiktok-uploads` channel → `DISCORD_WEBHOOK_TIKTOK`
- Default webhook for everything else → `DISCORD_WEBHOOK_URL`

### Step 4: Optional - Role Mentions (Separate Roles Per Platform!)
This is perfect for creators who want different alert roles for YouTube vs TikTok content.

**Step 4.1: Get Role IDs**

1. Enable Developer Mode: User Settings → App Settings → Advanced → Developer Mode
2. Right-click role → Copy ID
3. Or type `\@RoleName` in chat to see the ID

**Step 4.2: Configure Roles**

```bash
# Option 1: Default role for all platforms
doppler secrets set DISCORD_ROLE="1234567890"
# Or in .env:
DISCORD_ROLE=1234567890

# Option 2: Separate roles for each platform (RECOMMENDED for multi-platform creators!)
doppler secrets set DISCORD_ROLE_YOUTUBE="1111111111"
doppler secrets set DISCORD_ROLE_TIKTOK="2222222222"
# Or in .env:
DISCORD_ROLE_YOUTUBE=1111111111
DISCORD_ROLE_TIKTOK=2222222222
```

**Real-World Example:**
```bash
# Your server has:
# @YouTube-Squad (ID: 123456789) - fans who want YouTube notifications
# @TikTok-Crew (ID: 987654321) - fans who want TikTok notifications
# @All-Content (ID: 555555555) - fans who want everything

# Setup:
DISCORD_ROLE=555555555                 # Default for any future platforms
DISCORD_ROLE_YOUTUBE=123456789         # YouTube videos mention @YouTube-Squad
DISCORD_ROLE_TIKTOK=987654321          # TikTok videos mention @TikTok-Crew
```

When a YouTube video is posted: "🔴 @YouTube-Squad New video is live!"  
When a TikTok video is posted: "📱 @TikTok-Crew New TikTok just dropped!"

### Step 5: Enable in .env
```bash
# In .env
DISCORD_ENABLE_POSTING=true
```

### Step 6: Test
```bash
doppler run -- python3 test_social.py --platform discord
```

---

## 🔐 Matrix Setup

### What You Need
- Matrix homeserver URL (e.g., `https://matrix.org`)
- Room ID (e.g., `!abc123:matrix.org`)
- Username and password (preferred) OR access token

### Step 1: Get Room ID
1. In Element (or your Matrix client), open the room
2. Go to Room Settings → Advanced
3. Copy the "Internal room ID"

### Step 2: Authentication Options

**Option A: Username/Password (Recommended - auto-rotating)**
```bash
# Doppler
doppler secrets set MATRIX_USERNAME="@yourbot:matrix.org"
doppler secrets set MATRIX_PASSWORD="your-password"

# Or in .env
MATRIX_USERNAME=@yourbot:matrix.org
MATRIX_PASSWORD=your-password
```

**Option B: Access Token (Manual management)**
```bash
# Doppler
doppler secrets set MATRIX_ACCESS_TOKEN="your-access-token"

# Or in .env
MATRIX_ACCESS_TOKEN=your-access-token
```

### Step 3: Configure Homeserver and Room in .env
```bash
# In .env (not sensitive)
MATRIX_HOMESERVER=https://matrix.org
MATRIX_ROOM_ID=!abc123:matrix.org
MATRIX_ENABLE_POSTING=true
```

### Step 4: Test
```bash
doppler run -- python3 test_social.py --platform matrix
```

---

## 🧪 Testing All Platforms

### Test Individual Platforms
```bash
doppler run -- python3 test_social.py --platform bluesky
doppler run -- python3 test_social.py --platform mastodon
doppler run -- python3 test_social.py --platform discord
doppler run -- python3 test_social.py --platform matrix
```

### Test All Platforms at Once
```bash
doppler run -- python3 test_social.py --all
```

### Test with Custom Message
```bash
doppler run -- python3 test_social.py --platform discord --message "Testing from Boon-Tube! 🎉"
```

---

## 📋 Quick Reference: .env Variables

### Bluesky
```bash
BLUESKY_HANDLE=yourname.bsky.social
BLUESKY_APP_PASSWORD=xxx  # In Doppler
BLUESKY_ENABLE_POSTING=true
```

### Mastodon
```bash
MASTODON_API_BASE_URL=https://mastodon.social
MASTODON_CLIENT_ID=xxx  # In Doppler
MASTODON_CLIENT_SECRET=xxx  # In Doppler
MASTODON_ACCESS_TOKEN=xxx  # In Doppler
MASTODON_ENABLE_POSTING=true
```

### Discord
```bash
# Basic setup
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...  # In Doppler (default)
DISCORD_ENABLE_POSTING=true

# Optional: Per-platform webhooks
DISCORD_WEBHOOK_YOUTUBE=https://discord.com/api/webhooks/...  # In Doppler
DISCORD_WEBHOOK_TIKTOK=https://discord.com/api/webhooks/...   # In Doppler

# Optional: Role mentions (separate roles for YouTube/TikTok!)
DISCORD_ROLE=1234567890           # Default role (in Doppler)
DISCORD_ROLE_YOUTUBE=1111111111   # YouTube-specific role (in Doppler)
DISCORD_ROLE_TIKTOK=2222222222    # TikTok-specific role (in Doppler)
```

### Matrix
```bash
MATRIX_HOMESERVER=https://matrix.org
MATRIX_ROOM_ID=!abc123:matrix.org
MATRIX_USERNAME=@yourbot:matrix.org  # In Doppler
MATRIX_PASSWORD=xxx  # In Doppler
# OR
MATRIX_ACCESS_TOKEN=xxx  # In Doppler
MATRIX_ENABLE_POSTING=true
```

---

## 🔒 Security Best Practices

1. **Sensitive in Doppler, Config in .env**
   - Passwords, tokens, webhooks → Doppler
   - URLs, handles, room IDs → .env

2. **Use App Passwords**
   - Bluesky: Always use app password, never main password
   - Matrix: Consider using a dedicated bot account

3. **Webhook Security**
   - Discord: Anyone with the webhook URL can post - keep it secret!
   - Consider using per-platform webhooks to isolate access

4. **Access Token Rotation**
   - Matrix: Username/password allows automatic token rotation
   - Mastodon: Manually rotate access tokens periodically

---

## 🐛 Troubleshooting

### "Authentication failed"
- Double-check credentials in Doppler: `doppler secrets`
- Verify ENABLE_POSTING=true in .env
- Check logs for specific error messages

### "No webhook URL configured"
- Make sure DISCORD_WEBHOOK_URL is in Doppler or .env
- Verify you're in the correct Doppler project: `doppler configure get project`

### "Room not found" (Matrix)
- Verify Room ID format: `!abc123:matrix.org`
- Ensure bot has permission to post in the room
- Check homeserver URL is correct (include https://)

### "Invalid credentials" (Bluesky)
- Use app password, not main password
- Check handle format: `name.bsky.social` (no @)

### Doppler not loading secrets
```bash
# Check project
doppler configure get project

# List secrets
doppler secrets --only-names

# Test loading
doppler run -- env | grep -E "DISCORD|MATRIX|BLUESKY|MASTODON"
```

---

## 🎯 Next Steps

After setting up social platforms:
1. Test each platform individually
2. Configure YouTube/TikTok monitoring (see main README.md)
3. Optional: Enable LLM post generation (see LLM_SETUP.md)
4. Run the daemon: `doppler run -- python3 -m boon_tube_daemon`

---

## 📚 Additional Resources

- [Bluesky API Docs](https://docs.bsky.app/)
- [Mastodon API Docs](https://docs.joinmastodon.org/api/)
- [Discord Webhooks Guide](https://discord.com/developers/docs/resources/webhook)
- [Matrix API Docs](https://matrix.org/docs/api/)
