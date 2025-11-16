# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Mastodon social platform implementation with threading support.
"""

import logging
from typing import Optional
from mastodon import Mastodon
from boon_tube_daemon.utils.config import get_config, get_bool_config, get_secret, get_mastodon_accounts

logger = logging.getLogger(__name__)


class SocialPlatform:
    """Base class for social platforms."""
    
    def __init__(self, name):
        self.name = name
        self.enabled = False
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None) -> Optional[str]:
        """
        Post message to platform.
        
        Args:
            message: The message to post
            reply_to_id: Optional post ID to reply to (for threading)
            platform_name: Optional streaming platform name (for role mentions in Discord/Matrix)
            
        Returns:
            Post ID if successful, None otherwise
        """
        raise NotImplementedError
    
    def authenticate(self):
        """Authenticate with the platform."""
        raise NotImplementedError


class MastodonPlatform(SocialPlatform):
    """Mastodon social platform with multi-account support."""
    
    def __init__(self):
        super().__init__("Mastodon")
        self.accounts = []  # List of {'client': Mastodon, 'api_base_url': str, 'name': str}
        
    def authenticate(self):
        if not get_bool_config('Mastodon', 'enable_posting', default=False):
            return False
        
        # Load account configurations (supports both legacy single and new multi-account)
        account_configs = get_mastodon_accounts()
        
        if not account_configs:
            logger.warning("✗ No Mastodon accounts configured")
            return False
        
        # Authenticate all accounts
        for account_config in account_configs:
            client_id = account_config.get('client_id')
            client_secret = account_config.get('client_secret')
            access_token = account_config.get('access_token')
            api_base_url = account_config.get('api_base_url')
            name = account_config.get('name') or api_base_url
            
            if not all([client_id, client_secret, access_token, api_base_url]):
                missing = []
                if not client_id: missing.append('client_id')
                if not client_secret: missing.append('client_secret')
                if not access_token: missing.append('access_token')
                if not api_base_url: missing.append('api_base_url')
                logger.warning(f"✗ Mastodon account {name} missing credentials: {', '.join(missing)}")
                continue
            
            try:
                client = Mastodon(
                    client_id=client_id,
                    client_secret=client_secret,
                    access_token=access_token,
                    api_base_url=api_base_url
                )
                
                self.accounts.append({
                    'client': client,
                    'api_base_url': api_base_url,
                    'name': name
                })
                logger.info(f"✓ Mastodon: Authenticated {name}")
            except Exception as e:
                logger.warning(f"✗ Mastodon authentication failed for {name}: {type(e).__name__}")
                continue
        
        if not self.accounts:
            logger.warning("✗ No Mastodon accounts could be authenticated")
            return False
        
        self.enabled = True
        logger.info(f"✓ Mastodon authenticated for {len(self.accounts)} account(s)")
        return True
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None) -> Optional[str]:
        if not self.enabled or not self.accounts:
            return None
        
        post_ids = []
        
        # Post to all configured Mastodon accounts
        for account in self.accounts:
            client = account['client']
            account_name = account['name']
            
            try:
                # Check if we should attach a thumbnail image
                media_ids = []
                if stream_data:
                    thumbnail_url = stream_data.get('thumbnail_url')
                    if thumbnail_url:
                        try:
                            import requests
                            import tempfile
                            import os
                            
                            # Download thumbnail
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                            }
                            img_response = requests.get(thumbnail_url, headers=headers, timeout=10)
                            
                            if img_response.status_code == 200:
                                # Determine file extension from content type or URL
                                content_type = img_response.headers.get('content-type', '')
                                if 'jpeg' in content_type or 'jpg' in content_type or thumbnail_url.endswith('.jpg'):
                                    ext = '.jpg'
                                elif 'png' in content_type or thumbnail_url.endswith('.png'):
                                    ext = '.png'
                                elif 'webp' in content_type or thumbnail_url.endswith('.webp'):
                                    ext = '.webp'
                                else:
                                    ext = '.jpg'  # Default fallback
                                
                                # Save to temporary file
                                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                                    tmp_file.write(img_response.content)
                                    tmp_path = tmp_file.name
                                
                                try:
                                    # Upload to Mastodon
                                    # Build description with stream info
                                    viewer_count = stream_data.get('viewer_count', 0)
                                    game_name = stream_data.get('game_name', '')
                                    description = f"🔴 LIVE"
                                    if viewer_count:
                                        description += f" • {viewer_count:,} viewers"
                                    if game_name:
                                        description += f" • {game_name}"
                                    
                                    media = client.media_post(tmp_path, description=description)
                                    media_ids.append(media['id'])
                                    logger.info(f"✓ Uploaded thumbnail to Mastodon account {account_name} (media ID: {media['id']})")
                                finally:
                                    # Clean up temp file
                                    os.unlink(tmp_path)
                        except Exception as img_error:
                            logger.warning(f"⚠ Could not upload thumbnail to Mastodon account {account_name}: {type(img_error).__name__}")
                
                # Post as a reply if reply_to_id is provided (threading)
                status = client.status_post(
                    message, 
                    in_reply_to_id=reply_to_id,
                    media_ids=media_ids if media_ids else None
                )
                post_id = str(status['id'])
                post_ids.append(post_id)
                logger.info(f"✓ Mastodon: Posted to {account_name}")
                
            except Exception as e:
                logger.error(f"✗ Mastodon post failed for {account_name}: {type(e).__name__}")
                continue
        
        # Return first post ID for compatibility, or None if all failed
        return post_ids[0] if post_ids else None
