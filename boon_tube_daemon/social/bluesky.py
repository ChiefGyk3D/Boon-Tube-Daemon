# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Bluesky social platform implementation with threading and rich embed support.
"""

import logging
import re
from typing import Optional
from urllib.parse import urlparse
from atproto import Client, models, client_utils
from boon_tube_daemon.utils.config import get_config, get_bool_config, get_secret, get_bluesky_accounts

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
        # Check exact match or subdomain (e.g., www.kick.com matches kick.com)
        return hostname == domain or hostname.endswith('.' + domain)
    except Exception:
        return False


class BlueskyPlatform:
    """Bluesky social platform with multi-account support."""
    
    def __init__(self):
        self.name = "Bluesky"
        self.enabled = False
        self.accounts = []  # List of {'client': Client, 'handle': str, 'name': str}
        
    def authenticate(self):
        if not get_bool_config('Bluesky', 'enable_posting', default=False):
            return False
        
        # Load account configurations (supports both legacy single and new multi-account)
        account_configs = get_bluesky_accounts()
        
        if not account_configs:
            logger.warning("✗ No Bluesky accounts configured")
            return False
        
        # Authenticate all accounts
        for account_config in account_configs:
            handle = account_config.get('handle')
            app_password = account_config.get('app_password')
            name = account_config.get('name') or handle
            
            if not all([handle, app_password]):
                logger.warning(f"✗ Bluesky account missing credentials: {name}")
                continue
            
            try:
                client = Client()
                client.login(handle, app_password)
                
                self.accounts.append({
                    'client': client,
                    'handle': handle,
                    'name': name
                })
                logger.info(f"✓ Bluesky: Authenticated {name}")
            except Exception as e:
                logger.warning(f"✗ Bluesky authentication failed for {name}: {type(e).__name__}")
                continue
        
        if not self.accounts:
            logger.warning("✗ No Bluesky accounts could be authenticated")
            return False
        
        self.enabled = True
        logger.info(f"✓ Bluesky authenticated for {len(self.accounts)} account(s)")
        return True
    
    def post(self, message: str, reply_to_id: Optional[str] = None, platform_name: Optional[str] = None, stream_data: Optional[dict] = None) -> Optional[str]:
        if not self.enabled or not self.accounts:
            return None
        
        post_uris = []
        
        # Post to all configured Bluesky accounts
        for account in self.accounts:
            client = account['client']
            account_name = account['name']
            
            try:
                # Use TextBuilder to create rich text with explicit links and hashtags
                text_builder = client_utils.TextBuilder()
                
                # Combined pattern for URLs and hashtags
                # URL pattern: http:// and https:// URLs
                # Hashtag pattern: # followed by alphanumeric characters (including Unicode)
                url_pattern = r'https?://[^\s]+'
                hashtag_pattern = r'#\w+'
                combined_pattern = f'({url_pattern}|{hashtag_pattern})'
                
                last_pos = 0
                first_url = None  # Track first URL for embed card
                
                for match in re.finditer(combined_pattern, message):
                    # Add text before URL/hashtag
                    if match.start() > last_pos:
                        text_builder.text(message[last_pos:match.start()])
                    
                    matched_text = match.group()
                    
                    # Check if it's a URL or hashtag
                    if matched_text.startswith('http://') or matched_text.startswith('https://'):
                        # Add URL as clickable link
                        text_builder.link(matched_text, matched_text)
                        
                        # Capture first URL for embed card
                        if first_url is None:
                            first_url = matched_text
                    elif matched_text.startswith('#'):
                        # Add hashtag as clickable tag
                        # First param is display text WITH #, second param is tag value WITHOUT #
                        text_builder.tag(matched_text, matched_text[1:])
                    
                    last_pos = match.end()
                
                # Add any remaining text after last URL/hashtag
                if last_pos < len(message):
                    text_builder.text(message[last_pos:])
            
                # Create embed card for the first URL if found
                embed = None
                if first_url:
                    try:
                        # Special handling for Kick with stream_data - use provided metadata
                        if _is_url_for_domain(first_url, 'kick.com') and stream_data:
                            logger.info(f"ℹ Using stream metadata for Kick embed (CloudFlare bypass)")
                            
                            title = stream_data.get('title', 'Live on Kick')
                            thumbnail_url = stream_data.get('thumbnail_url')
                            
                            # Upload thumbnail to Bluesky if available
                            thumb_blob = None
                            if thumbnail_url:
                                try:
                                    import requests
                                    headers = {
                                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                                    }
                                    img_response = requests.get(thumbnail_url, headers=headers, timeout=10)
                                    if img_response.status_code == 200:
                                        upload_response = client.upload_blob(img_response.content)
                                        thumb_blob = upload_response.blob if hasattr(upload_response, 'blob') else None
                                except Exception as img_error:
                                    logger.warning(f"⚠ Could not upload Kick thumbnail: {img_error}")
                            
                            # Create external embed with stream metadata (no viewer count to avoid showing 0 at start)
                            game_name = stream_data.get('game_name', '')
                            description = f"🔴 LIVE"
                            if game_name:
                                description += f" • {game_name}"
                            
                            embed = models.AppBskyEmbedExternal.Main(
                                external=models.AppBskyEmbedExternal.External(
                                    uri=first_url,
                                    title=title[:300] if title else 'Live on Kick',
                                    description=description[:1000],
                                    thumb=thumb_blob if thumb_blob else None
                                )
                            )
                        elif _is_url_for_domain(first_url, 'kick.com'):
                            # Kick.com without stream_data - blocks automated requests with CloudFlare security policies
                            # Links will still be clickable, just without embed cards
                            logger.info(f"ℹ Kick.com blocks automated requests, posting with clickable link only")
                            embed = None
                        elif stream_data and (_is_url_for_domain(first_url, 'twitch.tv') or _is_url_for_domain(first_url, 'youtube.com') or _is_url_for_domain(first_url, 'youtu.be')):
                            # Use stream_data for Twitch/YouTube if available (more reliable than scraping)
                            logger.info(f"ℹ Using stream metadata for embed")
                            
                            title = stream_data.get('title', 'Video')
                            thumbnail_url = stream_data.get('thumbnail_url')
                            
                            # Upload thumbnail to Bluesky if available
                            thumb_blob = None
                            if thumbnail_url:
                                try:
                                    import requests
                                    headers = {
                                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                                    }
                                    img_response = requests.get(thumbnail_url, headers=headers, timeout=10)
                                    if img_response.status_code == 200:
                                        upload_response = client.upload_blob(img_response.content)
                                        thumb_blob = upload_response.blob if hasattr(upload_response, 'blob') else None
                                except Exception as img_error:
                                    logger.warning(f"⚠ Could not upload thumbnail: {img_error}")
                            
                            # Check if it's actually a livestream or a video
                            is_live = stream_data.get('is_live', False) or stream_data.get('viewer_count') is not None
                            
                            # Create description based on content type
                            if is_live:
                                game_name = stream_data.get('game_name', '')
                                description = f"🔴 LIVE"
                                if game_name:
                                    description += f" • {game_name}"
                            else:
                                # For videos, use the description or a simple label
                                description = stream_data.get('description', 'New video')[:200] if stream_data.get('description') else 'New video'
                            
                            embed = models.AppBskyEmbedExternal.Main(
                                external=models.AppBskyEmbedExternal.External(
                                    uri=first_url,
                                    title=title[:300] if title else 'Video',
                                    description=description[:1000],
                                    thumb=thumb_blob if thumb_blob else None
                                )
                            )
                        else:
                            # For non-Kick URLs, scrape Open Graph metadata
                            import requests
                            from bs4 import BeautifulSoup
                            
                            # Fetch the page with a realistic browser User-Agent
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                'Accept-Language': 'en-US,en;q=0.5',
                            }
                            
                            response = requests.get(first_url, headers=headers, timeout=10)
                            response.raise_for_status()  # Raise exception for 4xx/5xx status codes
                            
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Try Open Graph metadata first
                            og_title = soup.find('meta', property='og:title')
                            og_description = soup.find('meta', property='og:description')
                            og_image = soup.find('meta', property='og:image')
                            
                            # Fallback to Twitter Card metadata if OG tags not found
                            if not og_title:
                                og_title = soup.find('meta', attrs={'name': 'twitter:title'})
                            if not og_description:
                                og_description = soup.find('meta', attrs={'name': 'twitter:description'})
                            if not og_image:
                                og_image = soup.find('meta', attrs={'name': 'twitter:image'})
                            
                            title = og_title['content'] if og_title and og_title.get('content') else first_url
                            description = og_description['content'] if og_description and og_description.get('content') else ''
                            image_url = og_image['content'] if og_image and og_image.get('content') else None
                            
                            # Upload image to Bluesky if available
                            thumb_blob = None
                            if image_url:
                                try:
                                    # Handle relative URLs
                                    if image_url.startswith('//'):
                                        image_url = 'https:' + image_url
                                    elif image_url.startswith('/'):
                                        parsed = urlparse(first_url)
                                        image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"
                                    
                                    img_response = requests.get(image_url, headers=headers, timeout=10)
                                    if img_response.status_code == 200:
                                        # Upload image as blob and extract the blob reference
                                        upload_response = client.upload_blob(img_response.content)
                                        # The upload_blob returns a Response object with a blob attribute
                                        thumb_blob = upload_response.blob if hasattr(upload_response, 'blob') else None
                                except Exception as img_error:
                                    logger.warning(f"⚠ Could not upload thumbnail: {img_error}")
                            
                            # Create external embed with metadata
                            embed = models.AppBskyEmbedExternal.Main(
                                external=models.AppBskyEmbedExternal.External(
                                    uri=first_url,
                                    title=title[:300] if title else first_url,  # Limit title length
                                    description=description[:1000] if description else '',  # Limit description length
                                    thumb=thumb_blob if thumb_blob else None
                                )
                            )
                    except Exception as embed_error:
                        logger.warning(f"⚠ Could not create embed card: {embed_error}")
                        embed = None
                
                if reply_to_id:
                    # Threading on Bluesky requires parent and root references
                    try:
                        # Get the parent post details
                        parent_response = client.app.bsky.feed.get_posts({'uris': [reply_to_id]})
                        
                        if not parent_response or not hasattr(parent_response, 'posts') or not parent_response.posts:
                            logger.warning(f"⚠ Could not fetch parent post, posting without thread to {account_name}")
                            response = client.send_post(text_builder, embed=embed)
                            post_uri = response.uri if hasattr(response, 'uri') else None
                            if post_uri:
                                post_uris.append(post_uri)
                                logger.info(f"✓ Bluesky: Posted to {account_name}")
                            continue
                        
                        parent_post = parent_response.posts[0]
                        
                        # Determine root: if parent has a reply, use its root, otherwise parent is root
                        if hasattr(parent_post.record, 'reply') and parent_post.record.reply:
                            root_ref = parent_post.record.reply.root
                        else:
                            # Parent is the root - create strong ref
                            root_ref = models.create_strong_ref(parent_post)
                        
                        # Create parent reference
                        parent_ref = models.create_strong_ref(parent_post)
                        
                        # Create reply reference
                        reply_ref = models.AppBskyFeedPost.ReplyRef(
                            parent=parent_ref,
                            root=root_ref
                        )
                        
                        # Send threaded post with rich text and embed
                        response = client.send_post(text_builder, reply_to=reply_ref, embed=embed)
                        post_uri = response.uri if hasattr(response, 'uri') else None
                        if post_uri:
                            post_uris.append(post_uri)
                            logger.info(f"✓ Bluesky: Posted threaded reply to {account_name}")
                        
                    except Exception as thread_error:
                        logger.warning(f"⚠ Bluesky threading failed for {account_name}, posting without thread: {type(thread_error).__name__}")
                        # Fall back to non-threaded post
                        try:
                            response = client.send_post(text_builder, embed=embed)
                            post_uri = response.uri if hasattr(response, 'uri') else None
                            if post_uri:
                                post_uris.append(post_uri)
                                logger.info(f"✓ Bluesky: Posted to {account_name}")
                        except Exception as fallback_error:
                            logger.error(f"✗ Bluesky post failed for {account_name}: {type(fallback_error).__name__}")
                else:
                    # Simple post without threading, with rich text and embed card
                    response = client.send_post(text_builder, embed=embed)
                    post_uri = response.uri if hasattr(response, 'uri') else None
                    if post_uri:
                        post_uris.append(post_uri)
                        logger.info(f"✓ Bluesky: Posted to {account_name}")
                    
            except Exception as e:
                logger.error(f"✗ Bluesky post failed for {account_name}: {type(e).__name__}")
                continue
        
        # Return first post URI for compatibility, or None if all failed
        return post_uris[0] if post_uris else None
