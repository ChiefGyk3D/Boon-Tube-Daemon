# YouTube API Setup Guide

This guide walks you through setting up the YouTube Data API v3 for Boon-Tube-Daemon.

## Quick Start

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Name it something like "Boon-Tube-Daemon" or "YouTube Monitor"

### 2. Enable YouTube Data API v3

1. In the Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "YouTube Data API v3"
3. Click on it and press **Enable**

### 3. Create API Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **API Key**
3. Your API key will be generated (it looks like: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)
4. **Optional but recommended**: Click **Restrict Key** to add restrictions:
   - Under "API restrictions", select "Restrict key"
   - Choose "YouTube Data API v3"
   - This prevents unauthorized use if your key is exposed

### 4. Add API Key to .env

Edit your `.env` file and add:

```bash
YOUTUBE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 5. Configure Your Channel

Add your YouTube channel username or handle:

```bash
YOUTUBE_USERNAME=@YourChannelHandle
# OR
YOUTUBE_USERNAME=YourChannelName
```

**Optional**: If you know your channel ID, you can add it for faster lookups:

```bash
YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxxxxxx
```

To find your channel ID:
1. Go to [YouTube Studio](https://studio.youtube.com/)
2. Go to **Settings** → **Channel** → **Advanced settings**
3. Your channel ID is listed at the top

## API Quota Information

### Daily Limits

- **Daily quota**: 10,000 units per day
- **Cost per video check**: 3 units
  - 1 unit: Get channel uploads playlist
  - 1 unit: Get latest video from playlist
  - 1 unit: Get video details (title, description, stats)
- **Maximum checks per day**: ~3,333

### Recommended Check Intervals

- **Frequent**: 5 minutes = 288 checks/day = 864 units/day
- **Moderate**: 10 minutes = 144 checks/day = 432 units/day
- **Conservative**: 15 minutes = 96 checks/day = 288 units/day

The daemon defaults to 5-minute intervals, which is well within quota limits.

### Quota Exceeded Handling

If quota is exceeded, the daemon will:
1. Log the quota exceeded error
2. Pause YouTube checks for 1 hour
3. Automatically resume after cooldown
4. Continue monitoring other platforms (TikTok, etc.)

## Testing Your Setup

### Test YouTube Integration

```bash
python3 test_youtube.py
```

This will:
- ✓ Test API authentication
- ✓ Retrieve your latest video
- ✓ Show video details (title, views, likes, etc.)
- ✓ Test new video detection
- ✓ Display quota information

### Test Full Daemon

```bash
python3 test_integration.py
```

This tests both YouTube and TikTok integration together.

## Troubleshooting

### Authentication Failed

**Error**: "YouTube API key not found" or "authentication failed"

**Solutions**:
- Verify `YOUTUBE_API_KEY` is set in `.env`
- Check that the API key is valid (no extra spaces)
- Ensure YouTube Data API v3 is enabled in Google Cloud Console
- Try creating a new API key

### Channel Not Found

**Error**: "Could not find YouTube channel for username"

**Solutions**:
- Try with `@` prefix: `YOUTUBE_USERNAME=@YourChannel`
- Try without `@`: `YOUTUBE_USERNAME=YourChannel`
- Use channel ID instead: `YOUTUBE_CHANNEL_ID=UCxxxxxxxxx`
- Verify the channel exists and is public

### Quota Exceeded

**Error**: "YouTube API quota exceeded"

**Solutions**:
- Wait 1 hour for automatic cooldown
- Check your quota usage in [Google Cloud Console](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)
- Increase check interval in daemon settings
- Request quota increase from Google (if needed for high-frequency monitoring)

### No Videos Found

**Error**: "No uploads found for YouTube channel"

**Solutions**:
- Verify the channel has uploaded videos
- Check that videos are public (not private/unlisted)
- Make sure it's the correct channel
- Try accessing the channel directly: `https://youtube.com/@YourChannel`

## API Key Security

### Best Practices

1. **Never commit API keys to git**
   - The `.env` file is in `.gitignore`
   - Use `.env.example` for templates

2. **Restrict API keys** in Google Cloud Console:
   - Application restrictions: Set to "None" or specific IP
   - API restrictions: Limit to "YouTube Data API v3"

3. **Use secret managers** for production:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Doppler

4. **Rotate keys** periodically:
   - Create new key
   - Update `.env`
   - Delete old key

5. **Monitor usage**:
   - Check [API Dashboard](https://console.cloud.google.com/apis/dashboard)
   - Set up billing alerts
   - Watch for unusual quota usage

## Advanced Configuration

### Using Secret Managers

Instead of storing the API key in `.env`, you can use secret managers:

**AWS Secrets Manager**:
```bash
SECRETS_AWS_YOUTUBE_SECRET_NAME=boon-tube/youtube-api-key
```

**HashiCorp Vault**:
```bash
SECRETS_VAULT_YOUTUBE_SECRET_PATH=secret/boon-tube/youtube
```

**Doppler**:
```bash
SECRETS_DOPPLER_YOUTUBE_SECRET_NAME=YOUTUBE_API_KEY
```

### Multiple Channels

To monitor multiple YouTube channels, you can:
1. Create multiple instances of the daemon
2. Use different config files
3. Or modify the code to support multiple channels (future feature)

## Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [API Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
- [Google Cloud Console](https://console.cloud.google.com/)
- [YouTube Studio](https://studio.youtube.com/)

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs for detailed error messages
3. Test with `test_youtube.py` for diagnostic information
4. Check GitHub issues for similar problems
