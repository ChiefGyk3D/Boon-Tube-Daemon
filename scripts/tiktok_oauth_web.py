#!/usr/bin/env python3
"""
TikTok OAuth Helper Script (Web Login Kit Flow)

This script follows the official TikTok Login Kit for Web documentation.
https://developers.tiktok.com/doc/login-kit-web/

Key requirements for Web platform:
- Redirect URI MUST be HTTPS (use ngrok for local development)
- Uses https://www.tiktok.com/v2/auth/authorize/ endpoint
- Does NOT use PKCE (not mentioned in Web docs)

Usage:
    1. Start ngrok: ngrok http 8080
    2. Get the HTTPS URL from ngrok
    3. Register it in TikTok Developer Portal > Your App > Login Kit > Web > Redirect URI
    4. Run: python3 scripts/tiktok_oauth_web.py
    5. Authorize in browser
    6. Store tokens using commands printed
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

# Import Doppler for secrets
try:
    from doppler_sdk import DopplerSDK
    doppler = DopplerSDK()
    doppler_secrets = doppler.secrets.get()
except Exception as e:
    print(f"WARNING: Could not load Doppler SDK: {e}")
    print("Falling back to environment variables")
    doppler_secrets = {}

# Load .env as fallback
from dotenv import load_dotenv
load_dotenv()

# TikTok OAuth endpoints (Web Login Kit v2)
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

# OAuth parameters (try Doppler first, then environment)
CLIENT_KEY = doppler_secrets.get("TIKTOK_CLIENT_KEY") or os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = doppler_secrets.get("TIKTOK_CLIENT_SECRET") or os.getenv("TIKTOK_CLIENT_SECRET")
SCOPE = "user.info.basic"  # Testing Login Kit only (no Display API)

# Global variables for callback handling
auth_code = None
auth_error = None
debug_mode = False


def get_redirect_uri():
    """
    Get the HTTPS redirect URI for OAuth callbacks.
    
    For TikTok Web Login Kit, the redirect URI MUST:
    - Be absolute and begin with HTTPS
    - Be registered in the TikTok Developer Portal under Web platform
    - Not include query parameters or fragments
    
    Priority:
    1. TIKTOK_REDIRECT_URI environment variable (if set)
    2. Auto-detect ngrok tunnel
    3. Error if no HTTPS URL available
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
    print("  - Select 'Web' platform")
    print("  - Add your HTTPS URL to 'Redirect URI'")
    sys.exit(1)


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callbacks"""
    
    def do_GET(self):
        """Handle GET requests to the callback endpoint"""
        global auth_code, auth_error, debug_mode
        
        if debug_mode:
            print(f"\n[DEBUG] Received callback request:")
            print(f"  Path: {self.path}")
            print(f"  Headers: {dict(self.headers)}")
        
        # Parse the callback URL
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        
        # Check for authorization code
        if "code" in params:
            auth_code = params["code"][0]
            
            # Send success response to browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            success_html = """
            <html>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: green;">✓ Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())
            
        elif "error" in params:
            auth_error = params.get("error_description", [params["error"][0]])[0]
            
            # Send error response to browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            error_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: red;">✗ Authorization Failed</h1>
                <p><strong>Error:</strong> {auth_error}</p>
                <p>Please check the terminal for more information.</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())
        
        else:
            # Unknown callback
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Bad Request</h1><p>Missing code or error parameter</p>")
    
    def log_message(self, format, *args):
        """Suppress default logging unless in debug mode"""
        if debug_mode:
            super().log_message(format, *args)


def get_tokens(code, redirect_uri):
    """
    Exchange authorization code for access and refresh tokens.
    
    Per Web Login Kit docs, uses POST to /v2/oauth/token/
    """
    print("\nExchanging authorization code for tokens...")
    
    # Prepare token request (application/x-www-form-urlencoded format)
    data = {
        "client_key": CLIENT_KEY,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache"
    }
    
    try:
        response = requests.post(TOKEN_URL, data=data, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if debug_mode:
            print(f"\n[DEBUG] Token response:")
            print(json.dumps(result, indent=2))
        
        # Check for successful response
        if result.get("message") == "success" and "data" in result:
            token_data = result["data"]
            return {
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "open_id": token_data.get("open_id"),
                "expires_in": token_data.get("expires_in"),
                "scope": token_data.get("scope")
            }
        else:
            print(f"ERROR: Token request failed")
            print(f"Response: {json.dumps(result, indent=2)}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to get tokens: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def main(no_open=False, debug=False):
    """Main OAuth flow"""
    global debug_mode
    debug_mode = debug
    
    # Validate credentials
    if not CLIENT_KEY or not CLIENT_SECRET:
        print("ERROR: Missing TikTok credentials")
        print("Please set TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET in Doppler")
        print("\nTo check Doppler secrets:")
        print("  doppler secrets --only-names")
        sys.exit(1)
    
    # Get redirect URI (validates HTTPS requirement)
    redirect_uri = get_redirect_uri()
    
    # Generate CSRF state token (random for security)
    state = secrets.token_urlsafe(32)
    
    # Build authorization URL (Web Login Kit format)
    auth_params = {
        "client_key": CLIENT_KEY,
        "scope": SCOPE,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state
    }
    
    auth_url = f"{AUTH_URL}?{urlencode(auth_params)}"
    
    print("\n" + "="*70)
    print("TikTok OAuth - Web Login Kit Flow")
    print("="*70)
    print(f"\nRedirect URI: {redirect_uri}")
    print(f"Scopes: {SCOPE}")
    print("\nSTEP 1: User Authorization")
    print(f"\nOpening TikTok authorization page...")
    print(f"\nIf browser doesn't open, visit this URL:")
    print(f"\n{auth_url}\n")
    
    if not no_open:
        webbrowser.open(auth_url)
    
    # Start HTTP server to receive callback
    server_port = 8080
    server = HTTPServer(("", server_port), CallbackHandler)
    
    print(f"\nSTEP 2: Waiting for callback on http://localhost:{server_port}/callback")
    print("(via ngrok HTTPS tunnel)")
    print("\nAuthorize the app in your browser, then return here...")
    
    # Wait for callback
    global auth_code, auth_error
    while auth_code is None and auth_error is None:
        server.handle_request()
    
    # Check if we got an error
    if auth_error:
        print(f"\n✗ Authorization failed: {auth_error}")
        server.server_close()
        sys.exit(1)
    
    print(f"\n✓ Received authorization code")
    server.server_close()
    
    # Exchange code for tokens
    tokens = get_tokens(auth_code, redirect_uri)
    
    if not tokens:
        print("\n✗ Failed to get access tokens")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("✓ SUCCESS! TikTok OAuth Complete")
    print("="*70)
    print(f"\nAccess Token: {tokens['access_token']}")
    print(f"Refresh Token: {tokens['refresh_token']}")
    print(f"Open ID: {tokens['open_id']}")
    print(f"Expires In: {tokens['expires_in']} seconds")
    print(f"Scope: {tokens['scope']}")
    
    print("\n" + "="*70)
    print("NEXT STEPS: Store these tokens in Doppler")
    print("="*70)
    print("\nRun these commands:\n")
    print(f"doppler secrets set TIKTOK_ACCESS_TOKEN='{tokens['access_token']}'")
    print(f"doppler secrets set TIKTOK_REFRESH_TOKEN='{tokens['refresh_token']}'")
    print(f"doppler secrets set TIKTOK_OPEN_ID='{tokens['open_id']}'")
    print("\n" + "="*70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TikTok OAuth helper (Web Login Kit flow)"
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't automatically open browser"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    args = parser.parse_args()
    main(no_open=args.no_open, debug=args.debug)
