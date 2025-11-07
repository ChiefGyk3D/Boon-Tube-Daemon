# TikTok API Setup Guide

## ⚠️ IMPORTANT: TikTok Integration Currently Not Working

**Status:** ⏳ Planned but non-functional

TikTok support is **not currently working** and should not be attempted. This documentation is preserved for reference and potential future use if TikTok improves their developer experience.

### Why It Doesn't Work

TikTok integration faces multiple insurmountable barriers:

1. **Official API Issues:**
   - OAuth 2.0 returns persistent "server_error" in sandbox mode
   - App approval requires business verification and is extremely restrictive
   - Sandbox environment is unreliable and non-functional
   - Developer portal frequently changes requirements

2. **Unofficial Methods:**
   - Bot detection blocks all automated access
   - Web scraping consistently returns empty responses
   - Cookie-based authentication (`ms_token`) fails
   - Profile pages don't load in automated browsers

3. **Platform Approach:**
   - TikTok actively prevents automated access
   - No reliable third-party APIs exist
   - Developer experience is deliberately hostile to automation

### Recommendation

**Use the 5 working platforms instead:**
- ✅ YouTube (video monitoring)
- ✅ Discord (notifications)
- ✅ Matrix (notifications)
- ✅ Bluesky (notifications)
- ✅ Mastodon (notifications)

See [PLATFORM_STATUS.md](../../PLATFORM_STATUS.md) for details on working platforms.

---

## Historical Documentation (For Reference Only)

The following documentation describes the attempted TikTok integration. **Do not follow these steps** as they will not work due to platform limitations.

### Prerequisites (Non-Functional)

1. **TikTok Developer Account**: Sign up at https://developers.tiktok.com/
2. **Create an App**:
   - Go to TikTok Developer Portal
   - Create a new app
   - Enable these products:
     - **Login Kit** (for OAuth authentication)
     - **Video API** (to fetch user videos)
   - Set redirect URI to: `http://localhost:8080/callback`

3. **Get Credentials**:
   - Client Key (like an API key)
   - Client Secret (keep this secure!)

## Step 1: Add Credentials to Doppler

Store your TikTok API credentials securely in Doppler:

```bash
# Add Client Key
doppler secrets set TIKTOK_CLIENT_KEY="your_client_key_here"

# Add Client Secret
doppler secrets set TIKTOK_CLIENT_SECRET="your_client_secret_here"
```

Or use the Doppler web dashboard:
1. Go to https://dashboard.doppler.com/
2. Project: `boon-tube-daemon`
3. Config: `dev`
4. Click "Add Secret"
5. Add both `TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET`

## Step 2: Run OAuth Flow (One-Time Setup)

The TikTok API requires OAuth authorization. Run this script to authorize:

```bash
cd /home/chiefgyk3d/src/Boon-Tube-Daemon
python3 scripts/tiktok_oauth.py
```

This will:
1. Open a browser for you to login to TikTok
2. Ask you to authorize the app
3. Receive an authorization code
4. Exchange it for access and refresh tokens
5. Display commands to store tokens in Doppler

## Step 3: Store Tokens in Doppler

After running the OAuth script, it will give you commands like:

```bash
doppler secrets set TIKTOK_ACCESS_TOKEN="your_access_token"
doppler secrets set TIKTOK_REFRESH_TOKEN="your_refresh_token"
```

Run these commands to store the tokens.

## Step 4: Configure Username

Make sure your TikTok username is set in `.env`:

```env
TIKTOK_ENABLE_MONITORING=true
TIKTOK_USERNAME=chiefgyk3d
```

## Step 5: Test

Test the TikTok API integration:

```bash
python3 << 'EOF'
from dotenv import load_dotenv
load_dotenv()

from boon_tube_daemon.media.tiktok_api import TikTokAPIPlatform

tiktok = TikTokAPIPlatform()
if tiktok.authenticate():
    success, video = tiktok.get_latest_video()
    if success and video:
        print(f"✓ Found: {video['title']}")
        print(f"  URL: {video['url']}")
        print(f"  Views: {video['stats']['plays']:,}")
    else:
        print("✗ No video found")
else:
    print("✗ Authentication failed")
EOF
```

## Configuration Summary

### In Doppler (Secrets):
- `TIKTOK_CLIENT_KEY` - Your app's client key
- `TIKTOK_CLIENT_SECRET` - Your app's client secret
- `TIKTOK_ACCESS_TOKEN` - OAuth access token (from OAuth flow)
- `TIKTOK_REFRESH_TOKEN` - OAuth refresh token (for renewing access)

### In .env (Config):
- `TIKTOK_ENABLE_MONITORING=true`
- `TIKTOK_USERNAME=chiefgyk3d`

## Token Refresh

Access tokens expire. The daemon will need logic to:
1. Check if access token is expired
2. Use refresh token to get a new access token
3. Store the new access token

This is handled automatically by the `tiktok_api.py` module (TODO: implement refresh logic).

## Troubleshooting

### "No TikTok API credentials configured"
- Make sure `TIKTOK_CLIENT_KEY` and `TIKTOK_CLIENT_SECRET` are in Doppler
- Run `doppler secrets` to verify

### "No TikTok access token available"
- Run the OAuth flow: `python3 scripts/tiktok_oauth.py`
- Store the resulting tokens in Doppler

### "Authorization Failed"
- Check that redirect URI in TikTok Developer Portal matches: `http://localhost:8080/callback`
- Make sure Login Kit product is enabled for your app

### "Video list API returns error"
- Make sure Video API product is enabled for your app
- Check that scopes include `video.list` and `user.info.basic`
- Verify access token is not expired

## API Rate Limits

TikTok API has rate limits:
- **User Info**: 100 requests/day per user
- **Video List**: 100 requests/day per user

The daemon should cache results and only check periodically (e.g., every 15 minutes).

## Fallback to Playwright

If TikTok API is not configured, the system will fall back to Playwright browser automation (which has bot detection issues). The official API is strongly recommended.

## References

- TikTok Developer Portal: https://developers.tiktok.com/
- Login Kit Documentation: https://developers.tiktok.com/doc/login-kit-web
- Video API Documentation: https://developers.tiktok.com/doc/display-api-get-user-info
- OAuth 2.0 Flow: https://developers.tiktok.com/doc/oauth-user-access-token-management
