#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Helper script to get ms_token from TikTok cookies.

This script will launch a browser for you to log into TikTok,
then extract the ms_token cookie automatically.
"""

import asyncio
from playwright.async_api import async_playwright
import sys

async def get_ms_token():
    """Launch browser and get ms_token from TikTok."""
    print("\n" + "="*60)
    print("TikTok ms_token Extractor")
    print("="*60)
    print("\nThis will open a browser window.")
    print("Please:")
    print("  1. Log into TikTok (or just visit a profile)")
    print("  2. Wait for the page to fully load")
    print("  3. Press Enter in this terminal when ready")
    print("\nThe script will then extract the ms_token cookie.\n")
    
    async with async_playwright() as p:
        # Launch browser (not headless so user can interact)
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Go to TikTok
        print("Opening TikTok.com...")
        await page.goto('https://www.tiktok.com')
        
        # Wait for user to log in
        input("\n👉 Press Enter after you've visited TikTok (and optionally logged in)...")
        
        # Get cookies
        print("\nExtracting cookies...")
        cookies = await context.cookies()
        
        # Find ms_token
        ms_token = None
        for cookie in cookies:
            if cookie['name'] == 'ms_token':
                ms_token = cookie['value']
                break
        
        await browser.close()
        
        if ms_token:
            print("\n" + "="*60)
            print("✓ Successfully extracted ms_token!")
            print("="*60)
            print(f"\nms_token: {ms_token}\n")
            print("To use this token:")
            print(f"  export ms_token='{ms_token}'")
            print("  python3 test_tiktok.py")
            print("\n" + "="*60)
            print("Add to your .env file:")
            print("="*60)
            print(f"TIKTOK_MS_TOKEN={ms_token}")
            print("\nThen configure TikTok monitoring:")
            print("TIKTOK_ENABLE=true")
            print("TIKTOK_USERNAME=username_to_monitor")
            print("="*60 + "\n")
            
            # Save to file
            try:
                with open('.ms_token', 'w') as f:
                    f.write(ms_token)
                print("✓ Token saved to .ms_token file")
                print("  (This file is gitignored)")
                print("\nTo load it:")
                print("  export ms_token=$(cat .ms_token)")
                print("  python3 test_tiktok.py\n")
            except Exception as e:
                print(f"Could not save to file: {e}")
            
            return ms_token
        else:
            print("\n" + "="*60)
            print("✗ ms_token not found")
            print("="*60)
            print("\nPossible reasons:")
            print("  1. You didn't visit TikTok.com")
            print("  2. TikTok didn't set the ms_token cookie")
            print("  3. You need to visit a user profile first")
            print("\nTry again and make sure to:")
            print("  - Visit TikTok.com")
            print("  - Click on a user profile")
            print("  - Wait for page to fully load")
            print("\n")
            return None

async def main():
    try:
        ms_token = await get_ms_token()
        if ms_token:
            print("Ready to test TikTok API!")
            return 0
        else:
            print("Failed to get ms_token. Try again or get it manually.")
            return 1
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
