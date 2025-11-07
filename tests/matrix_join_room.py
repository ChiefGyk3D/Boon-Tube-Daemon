#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Matrix bot room join helper.
Attempts to join the configured Matrix room.
"""

import sys
import logging
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from boon_tube_daemon.utils.config import load_config, get_config, get_secret

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("\n" + "="*70)
    print("🟪 Matrix Bot Room Join Helper")
    print("="*70)
    
    # Load configuration
    print("\n📋 Loading configuration...")
    load_config()
    print("✓ Configuration loaded")
    
    # Get Matrix config
    homeserver = get_config('Matrix', 'homeserver')
    room_id = get_config('Matrix', 'room_id')
    username = get_config('Matrix', 'username')
    password = get_secret('Matrix', 'password')
    access_token = get_secret('Matrix', 'access_token')
    
    print(f"\n🔍 Configuration:")
    print(f"  Homeserver: {homeserver}")
    print(f"  Room ID: {room_id}")
    print(f"  Username: {username}")
    
    if not all([homeserver, room_id]):
        print("\n✗ Missing required configuration (homeserver or room_id)")
        return False
    
    # Ensure homeserver has proper format
    if not homeserver.startswith('http'):
        homeserver = f"https://{homeserver}"
    
    # Get access token (prefer username/password for fresh token)
    token = None
    if username and password:
        print("\n🔐 Logging in with username/password...")
        username_local = username
        if username_local.startswith('@'):
            username_local = username_local[1:].split(':')[0]
        
        login_url = f"{homeserver}/_matrix/client/r0/login"
        login_data = {
            "type": "m.login.password",
            "user": username_local,
            "password": password
        }
        
        try:
            response = requests.post(login_url, json=login_data, timeout=30)
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                print(f"✓ Logged in successfully")
            else:
                print(f"✗ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"✗ Login error: {e}")
            return False
    elif access_token:
        print("\n🔐 Using existing access token...")
        token = access_token
    
    if not token:
        print("\n✗ No access token available")
        return False
    
    # Try to join the room
    print(f"\n🚪 Attempting to join room: {room_id}")
    join_url = f"{homeserver}/_matrix/client/r0/join/{requests.utils.quote(room_id, safe='')}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(join_url, headers=headers, json={}, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Successfully joined room!")
            data = response.json()
            print(f"   Room ID: {data.get('room_id', room_id)}")
            return True
        elif response.status_code == 403:
            error_data = response.json()
            if 'already in the room' in error_data.get('error', '').lower():
                print(f"✓ Already in the room!")
                return True
            else:
                print(f"✗ Forbidden (403): {error_data.get('error', 'No error message')}")
                print(f"   You may need to invite the bot (@{username}) to the room first")
                return False
        else:
            print(f"✗ Failed to join room: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error joining room: {e}")
        logger.exception("Error joining room")
        return False


if __name__ == "__main__":
    success = main()
    print()
    if success:
        print("✅ Bot is now in the room and ready to post!")
    else:
        print("❌ Bot could not join the room. Please:")
        print("   1. Invite the bot user to the room in Element/Matrix client")
        print("   2. Run this script again to accept the invitation")
    print()
    sys.exit(0 if success else 1)
