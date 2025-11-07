#!/usr/bin/env python3
"""
TikTok OAuth Helper Script (Web Login Kit Flow)

This script helps you obtain TikTok access tokens for the Boon Tube Daemon.
It starts a local HTTP server to receive the OAuth callback and exchanges
the authorization code for an access token.

Follows the official TikTok Login Kit for Web documentation:
https://developers.tiktok.com/doc/login-kit-web/

Usage:
    1. Make sure TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET are in Doppler
    2. Run: python3 scripts/tiktok_oauth.py
    3. Browser will open to TikTok login
    4. After authorizing, tokens will be displayed
    5. Store them in Doppler using the commands printed
"""

import os
import sys
import json
import webbrowser
import secrets
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# TikTok OAuth endpoints (Web Login Kit v2)
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

# OAuth parameters
CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
SCOPE = "user.info.basic,video.list"
STATE = "random_state_string_12345"  # In production, generate this randomly

def get_redirect_uri():
    """
    Get the redirect URI for OAuth callbacks.
    
    For TikTok Web Login Kit, the redirect URI MUST:
    - Be absolute and begin with HTTPS
    - Be registered in the TikTok Developer Portal under Web platform
    - Not include query parameters or fragments
    
    Priority:
    1. TIKTOK_REDIRECT_URI environment variable (if set)
    2. Auto-detect ngrok tunnel (REQUIRED for Web platform)
    3. Error if no HTTPS URL available
    
    Returns:
        str: The redirect URI to use for OAuth
    """
    # Check environment variable first
    env_redirect = os.getenv("TIKTOK_REDIRECT_URI")
    if env_redirect:
        if not env_redirect.startswith("https://"):
            print(f"ERROR: TikTok Web Login Kit requires HTTPS redirect URI")
            print(f"Your URI: {env_redirect}")
            print(f"Please set TIKTOK_REDIRECT_URI to an HTTPS URL or start ngrok")
            sys.exit(1)
        print(f"Using redirect URI from environment: {env_redirect}")
        return env_redirect
    
    # Try to detect ngrok tunnel
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        tunnels = response.json().get("tunnels", [])
        for tunnel in tunnels:
            if tunnel.get("proto") == "https":
                ngrok_url = tunnel["public_url"]
                redirect_uri = f"{ngrok_url}/callback"
                print(f"Auto-detected ngrok tunnel: {redirect_uri}")
                return redirect_uri
    except Exception:
        pass  # ngrok not running
    
    # No HTTPS URL available - error for Web platform
    print("ERROR: TikTok Web Login Kit requires HTTPS redirect URI")
    print("")
    print("Solutions:")
    print("1. Start ngrok: ngrok http 8080")
    print("2. Set TIKTOK_REDIRECT_URI in .env to your ngrok HTTPS URL")
    print("")
    print("Then register the HTTPS URL in TikTok Developer Portal:")
    print("  - Go to: https://developers.tiktok.com/apps/")
    print("  - Select your app")
    print("  - Click 'Login Kit' product")
    print("  - Add your HTTPS URL to 'Redirect URI' (Web platform)")
    sys.exit(1)
