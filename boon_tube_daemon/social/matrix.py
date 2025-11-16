# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Matrix platform implementation with rich message support.

NOTE: Matrix does NOT support editing messages like Discord.
Messages are posted once and cannot be updated with live viewer counts.
"""

import logging
import re
from typing import Optional
from urllib.parse import quote, urlparse
import requests
from boon_tube_daemon.utils.config import get_bool_config, get_secret, get_matrix_accounts

logger = logging.getLogger(__name__)


def _is_url_for_domain(url: str, domain: str) -> bool:
    """
    Safely check if a URL is for a specific domain.
    
    Args:
        url: The URL to check
        domain: The domain to match (e.g., 'kick.com', 'twitch.tv')
    
    Returns:
        True if the URL's hostname matches or is a subdomain of the domain
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Normalize to lowercase for comparison
        hostname = hostname.lower()
        domain = domain.lower()
        
        # Check exact match
        if hostname == domain:
            return True
        
        # Check if it's a proper subdomain (must end with .domain, not just contain domain)
        # This prevents eviltwitch.tv from matching twitch.tv
        if hostname.endswith('.' + domain):
            # Ensure there's no additional dot after the subdomain
            # e.g., www.twitch.tv is valid, but not twitch.tv.evil.com
            return True
        
        return False
    except Exception:
        return False


class MatrixPlatform:
    """
    Matrix platform with multi-account support and rich message formatting.
    
    NOTE: Matrix does NOT support editing messages like Discord.
    Messages are posted once and cannot be updated with live viewer counts.
    """
    
    def __init__(self):
        self.name = "Matrix"
        self.enabled = False
        self.accounts = []  # List of {'homeserver': str, 'room_id': str, 'access_token': str, 'name': str}
        
    def authenticate(self):
        if not get_bool_config('Matrix', 'enable_posting', default=False):
            return False
        
        # Load account configurations (supports both legacy single and new multi-account)
        account_configs = get_matrix_accounts()
        
        if not account_configs:
            logger.warning("✗ No Matrix accounts configured")
            return False
        
        # Authenticate all accounts
        for account_config in account_configs:
            homeserver = account_config.get('homeserver')
            room_id = account_config.get('room_id')
            access_token = account_config.get('access_token')
            username = account_config.get('username')
            password = account_config.get('password')
            name = account_config.get('name') or room_id
            
            if not homeserver or not room_id:
                logger.warning(f"✗ Matrix account {name} missing required fields (homeserver, room_id)")
                continue
            
            # Ensure homeserver has proper format
            if not homeserver.startswith('http'):
                homeserver = f"https://{homeserver}"
            
            # Priority: Username/Password > Access Token
            # If both are set, username/password takes precedence for automatic token rotation
            if username and password:
                # Login to get fresh access token
                logger.info(f"Matrix {name}: Using username/password authentication (auto-rotation enabled)")
                access_token = self._login_and_get_token(homeserver, username, password, name)
                if not access_token:
                    logger.error(f"✗ Matrix login failed for {name} - check username/password")
                    continue
                logger.info(f"✓ Matrix {name}: Logged in and obtained access token")
            elif access_token:
                # Use static access token
                logger.info(f"Matrix {name}: Using static access token authentication")
            else:
                logger.error(f"✗ Matrix account {name} authentication failed - need either access_token OR username+password")
                continue
            
            self.accounts.append({
                'homeserver': homeserver,
                'room_id': room_id,
                'access_token': access_token,
                'name': name
            })
            logger.info(f"✓ Matrix: Authenticated {name}")
        
        if not self.accounts:
            logger.warning("✗ No Matrix accounts could be authenticated")
            return False
        
        self.enabled = True
        logger.info(f"✓ Matrix authenticated for {len(self.accounts)} account(s)")
        return True
    
    def _login_and_get_token(self, homeserver: str, username: str, password: str, account_name: str) -> Optional[str]:
        """Login with username/password to get access token."""
        try:
            # Extract just the username part from full MXID (@username:domain)
            # Matrix login expects just "username", not "@username:domain"
            username_local = username
            if username_local.startswith('@'):
                # Remove @ prefix and :domain suffix
                username_local = username_local[1:].split(':')[0]
            
            login_url = f"{homeserver}/_matrix/client/r0/login"
            login_data = {
                "type": "m.login.password",
                "identifier": {
                    "type": "m.id.user",
                    "user": username_local
                },
                "password": password
            }
            
            response = requests.post(login_url, json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access_token')
                if access_token:
                    logger.info(f"✓ Obtained Matrix access token for {account_name} (expires: {data.get('expires_in_ms', 'never')})")
                    return access_token
                else:
                    logger.error(f"✗ Matrix login succeeded for {account_name} but no access_token in response")
            else:
                logger.error(f"✗ Matrix login failed for {account_name}: {response.status_code}")
            
            return None
        except Exception as e:
            logger.error(f"✗ Matrix login error for {account_name}: {e}")
            return None
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None) -> Optional[str]:
        if not self.enabled or not self.accounts:
            return None
        
        event_ids = []
        
        # Post to all configured Matrix accounts
        for account in self.accounts:
            homeserver = account['homeserver']
            room_id = account['room_id']
            access_token = account['access_token']
            account_name = account['name']
            
            try:
                # Extract URL from message for rich formatting
                url_pattern = r'https?://[^\s]+'
                url_match = re.search(url_pattern, message)
                first_url = url_match.group() if url_match else None
                
                # Create rich HTML message with link preview
                html_body = message
                plain_body = message
                
                if first_url:
                    # Make URL clickable in HTML
                    html_body = re.sub(url_pattern, f'<a href="{first_url}">{first_url}</a>', message)
                    
                    # Add platform-specific styling
                    if _is_url_for_domain(first_url, 'twitch.tv'):
                        html_body = f'<p><strong>🟣 Live on Twitch!</strong></p><p>{html_body}</p>'
                    elif _is_url_for_domain(first_url, 'youtube.com') or _is_url_for_domain(first_url, 'youtu.be'):
                        html_body = f'<p><strong>🔴 Live on YouTube!</strong></p><p>{html_body}</p>'
                    elif _is_url_for_domain(first_url, 'kick.com'):
                        html_body = f'<p><strong>🟢 Live on Kick!</strong></p><p>{html_body}</p>'
                
                # Build Matrix message event
                event_data = {
                    "msgtype": "m.text",
                    "body": plain_body,
                    "format": "org.matrix.custom.html",
                    "formatted_body": html_body
                }
                
                # Add reply reference if provided
                if reply_to_id:
                    event_data["m.relates_to"] = {
                        "m.in_reply_to": {
                            "event_id": reply_to_id
                        }
                    }
                
                # Send message via Matrix Client-Server API
                url = f"{homeserver}/_matrix/client/r0/rooms/{quote(room_id)}/send/m.room.message"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(url, json=event_data, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    event_id = data.get('event_id')
                    event_ids.append(event_id)
                    logger.info(f"✓ Matrix: Posted to {account_name}")
                else:
                    logger.warning(f"⚠ Matrix post failed for {account_name} with status {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"✗ Matrix post failed for {account_name}: {e}")
                continue
        
        # Return first event ID for compatibility, or None if all failed
        return event_ids[0] if event_ids else None
