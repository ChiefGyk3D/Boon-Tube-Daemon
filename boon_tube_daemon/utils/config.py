# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Configuration management for Boon-Tube-Daemon.

Loads configuration from .env files and environment variables.
Supports multiple secret management backends.
"""

import logging
import os
import configparser
from pathlib import Path
from typing import Optional, Any

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Constants for secret validation
PLACEHOLDER_PREFIX = 'YOUR_'  # Prefix for placeholder values in config templates
EMPTY_SECRET = ''  # Empty string constant for fallback values

# Global config instance
_config = None

# Track if .env is loaded
_env_loaded = False


def load_config(env_path: str = ".env") -> bool:
    """
    Load configuration from .env file.
    
    Args:
        env_path: Path to .env file
        
    Returns:
        True if loaded successfully
    """
    global _env_loaded
    
    if _env_loaded:
        return True
        
    env_file = Path(env_path)
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"✓ Loaded configuration from {env_path}")
        _env_loaded = True
        return True
    else:
        logger.warning(f"⚠ Configuration file not found: {env_path}")
        return False


def get_config(section: str, key: str, default: Any = None) -> Optional[str]:
    """
    Get configuration value from Doppler or environment variables.
    
    Priority order:
    1. Doppler (if DOPPLER_TOKEN is set) - tries both simple and sectioned formats
    2. Environment variable (simple format: KEY)
    3. Environment variable (sectioned format: SECTION_KEY)
    4. Default value
    
    Supports two formats:
    1. Simple: KEY (uppercase) - e.g., CHECK_INTERVAL
    2. Sectioned: SECTION_KEY (uppercase) - e.g., SETTINGS_CHECK_INTERVAL
    
    Args:
        section: Configuration section (e.g., 'TikTok', 'YouTube', 'Settings')
        key: Configuration key (e.g., 'username', 'api_key', 'check_interval')
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    # Build key names
    simple_key = key.upper()
    sectioned_key = f"{section}_{key}".upper()
    
    # 1. Try Doppler first (if DOPPLER_TOKEN is set)
    doppler_token = os.getenv('DOPPLER_TOKEN')
    if doppler_token:
        try:
            from dopplersdk import DopplerSDK
            
            sdk = DopplerSDK(access_token=doppler_token)
            secrets_response = sdk.secrets.list(
                project=os.getenv('DOPPLER_PROJECT'),
                config=os.getenv('DOPPLER_CONFIG', 'dev')
            )
            
            if hasattr(secrets_response, 'secrets') and secrets_response.secrets:
                # Try sectioned key first (e.g., BLUESKY_HANDLE)
                if sectioned_key in secrets_response.secrets:
                    value = secrets_response.secrets[sectioned_key].get('computed',
                            secrets_response.secrets[sectioned_key].get('raw', EMPTY_SECRET))
                    if value and not value.startswith(PLACEHOLDER_PREFIX):
                        logger.debug(f"✓ Retrieved {section}.{key} from Doppler: {sectioned_key}")
                        return value
                
                # Try simple key format (e.g., CHECK_INTERVAL)
                if simple_key in secrets_response.secrets:
                    value = secrets_response.secrets[simple_key].get('computed',
                            secrets_response.secrets[simple_key].get('raw', EMPTY_SECRET))
                    if value and not value.startswith(PLACEHOLDER_PREFIX):
                        logger.debug(f"✓ Retrieved {section}.{key} from Doppler: {simple_key}")
                        return value
        except ImportError:
            logger.debug("dopplersdk not installed, skipping Doppler lookup")
        except Exception as e:
            logger.debug(f"Failed to query Doppler for config: {e}")
    
    # 2. Try simple key format from env (e.g., CHECK_INTERVAL)
    value = os.getenv(simple_key)
    if value is not None:
        return value
    
    # 3. Fall back to sectioned format from env (e.g., SETTINGS_CHECK_INTERVAL)
    value = os.getenv(sectioned_key, default)
    
    if value is None:
        logger.debug(f"Config not found: {section}.{key} (tried Doppler, {simple_key}, {sectioned_key})")
    
    return value


def get_bool_config(section: str, key: str, default: bool = False) -> bool:
    """
    Get boolean configuration value.
    
    Args:
        section: Configuration section
        key: Configuration key
        default: Default boolean value
        
    Returns:
        Boolean value
    """
    value = get_config(section, key)
    
    if value is None:
        return default
        
    # Handle various boolean representations
    if isinstance(value, bool):
        return value
        
    value_lower = str(value).lower()
    return value_lower in ('true', '1', 'yes', 'on', 'enabled')


def get_int_config(section: str, key: str, default: int = 0) -> int:
    """
    Get integer configuration value.
    
    Args:
        section: Configuration section
        key: Configuration key
        default: Default integer value
        
    Returns:
        Integer value
    """
    value = get_config(section, key)
    
    if value is None:
        return default
        
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid integer value for {section}.{key}, using default: {default}")
        return default


def get_float_config(section: str, key: str, default: float = 0.0) -> float:
    """
    Get float configuration value.
    
    Args:
        section: Configuration section
        key: Configuration key
        default: Default float value
        
    Returns:
        Float value
    """
    value = get_config(section, key)
    
    if value is None:
        return default
        
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid float value for {section}.{key}, using default: {default}")
        return default


def get_secret(section: str, key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get secret value with automatic secret manager detection.
    
    Priority order:
    1. Doppler (if DOPPLER_TOKEN is set)
    2. AWS Secrets Manager (if SECRETS_AWS_ENABLED=true)
    3. HashiCorp Vault (if SECRETS_VAULT_ENABLED=true)
    4. Environment variable (SECTION_KEY)
    5. .env file fallback
    6. Default value
    
    All secret names use the same format: SECTION_KEY (e.g., YOUTUBE_API_KEY)
    
    Args:
        section: Configuration section (e.g., 'YouTube', 'Discord')
        key: Configuration key (e.g., 'api_key', 'webhook_url')
        default: Default value if secret not found
        
    Returns:
        Secret value or default
        
    Example:
        api_key = get_secret('YouTube', 'api_key')
        # Tries: Doppler -> AWS -> Vault -> YOUTUBE_API_KEY env var -> .env -> None
    """
    env_var = f"{section}_{key}".upper()
    
    # 1. Try Doppler first (if DOPPLER_TOKEN is set)
    doppler_token = os.getenv('DOPPLER_TOKEN')
    if doppler_token:
        # First check if it's already injected as an env var (from doppler run)
        value = os.getenv(env_var)
        # Skip placeholder values
        if value and not value.startswith(PLACEHOLDER_PREFIX):
            logger.debug(f"✓ Retrieved {section}.{key} from Doppler (env var)")
            return value
        
        # If not in env, fetch from Doppler API using the SDK
        try:
            from dopplersdk import DopplerSDK
            
            sdk = DopplerSDK(access_token=doppler_token)
            # Get all secrets for this project/config
            secrets_response = sdk.secrets.list(
                project=os.getenv('DOPPLER_PROJECT'),
                config=os.getenv('DOPPLER_CONFIG', 'dev')
            )
            
            # secrets is a dict of {name: {raw: ..., computed: ...}}
            if hasattr(secrets_response, 'secrets') and secrets_response.secrets:
                if env_var in secrets_response.secrets:
                    secret_data = secrets_response.secrets[env_var]
                    # Extract the computed value (or raw if computed not available)
                    value = secret_data.get('computed', secret_data.get('raw'))
                    # Skip placeholder values
                    if value and not value.startswith(PLACEHOLDER_PREFIX):
                        logger.debug(f"✓ Retrieved {section}.{key} from Doppler (SDK)")
                        return value
        except ImportError:
            logger.debug("dopplersdk not installed, skipping Doppler SDK lookup")
        except Exception as e:
            logger.debug(f"Doppler SDK lookup failed: {e}")
    
    # 2. Try AWS Secrets Manager (if enabled)
    if get_bool_config('Secrets', 'aws_enabled', default=False):
        try:
            import boto3
            import json
            
            # Get the secret name for this section (e.g., boon-tube/youtube, boon-tube/discord)
            secret_name = get_config('Secrets', 'aws_secret_name', default='boon-tube')
            
            client = boto3.client('secretsmanager')
            response = client.get_secret_value(SecretId=f"{secret_name}/{section.lower()}")
            
            if 'SecretString' in response:
                secret_dict = json.loads(response['SecretString'])
                # Try exact key match first
                if key in secret_dict:
                    value = secret_dict[key]
                    if value and not value.startswith(PLACEHOLDER_PREFIX):
                        logger.debug(f"✓ Retrieved {section}.{key} from AWS Secrets Manager")
                        return value
                # Try uppercase key (for consistency)
                if key.upper() in secret_dict:
                    value = secret_dict[key.upper()]
                    if value and not value.startswith(PLACEHOLDER_PREFIX):
                        logger.debug(f"✓ Retrieved {section}.{key} from AWS Secrets Manager")
                        return value
                # Try the full env var name
                if env_var in secret_dict:
                    value = secret_dict[env_var]
                    if value and not value.startswith(PLACEHOLDER_PREFIX):
                        logger.debug(f"✓ Retrieved {section}.{key} from AWS Secrets Manager")
                        return value
        except ImportError:
            logger.debug("boto3 not installed, skipping AWS Secrets Manager")
        except Exception as e:
            logger.debug(f"AWS Secrets Manager lookup failed: {e}")
    
    # 3. Try HashiCorp Vault (if enabled)
    if get_bool_config('Secrets', 'vault_enabled', default=False):
        try:
            import hvac
            
            vault_addr = get_config('Secrets', 'vault_url')
            vault_token = get_config('Secrets', 'vault_token')
            vault_path = get_config('Secrets', 'vault_path', default='secret/boon-tube')
            
            if vault_addr and vault_token:
                client = hvac.Client(url=vault_addr, token=vault_token)
                # Read from path like: secret/boon-tube/youtube
                secret = client.secrets.kv.v2.read_secret_version(
                    path=f"{vault_path}/{section.lower()}"
                )
                
                data = secret['data']['data']
                # Try exact key match first
                if key in data:
                    value = data[key]
                    if value and not value.startswith(PLACEHOLDER_PREFIX):
                        logger.debug(f"✓ Retrieved {section}.{key} from HashiCorp Vault")
                        return value
                # Try uppercase key
                if key.upper() in data:
                    value = data[key.upper()]
                    if value and not value.startswith(PLACEHOLDER_PREFIX):
                        logger.debug(f"✓ Retrieved {section}.{key} from HashiCorp Vault")
                        return value
                # Try the full env var name
                if env_var in data:
                    value = data[env_var]
                    if value and not value.startswith(PLACEHOLDER_PREFIX):
                        logger.debug(f"✓ Retrieved {section}.{key} from HashiCorp Vault")
                        return value
        except ImportError:
            logger.debug("hvac not installed, skipping HashiCorp Vault")
        except Exception as e:
            logger.debug(f"Vault lookup failed: {e}")
    
    # 4. Fallback to environment variable or .env file
    value = get_config(section, key, default=default)
    # Skip placeholder values (common in template .env files)
    if value and not value.startswith(PLACEHOLDER_PREFIX):
        logger.debug(f"✓ Retrieved {section}.{key} from environment/.env")
        return value
    
    if value and value.startswith(PLACEHOLDER_PREFIX):
        logger.warning(f"⚠ Found placeholder value for {section}.{key} in .env (starts with '{PLACEHOLDER_PREFIX}')")
    
    logger.debug(f"Secret not found: {section}.{key}")
    return default


def get_youtube_accounts() -> list:
    """
    Get YouTube accounts configuration with backward compatibility.
    
    Supports two formats:
    1. Legacy single account: YOUTUBE_USERNAME and/or YOUTUBE_CHANNEL_ID
    2. Multi-account: YOUTUBE_ACCOUNTS JSON array
    
    Returns:
        List of account dicts, each with keys: username, channel_id, name, discord_role
        Example: [{"username": "@LTT", "discord_role": "123456", "name": "Linus Tech Tips"}]
    """
    import json
    
    accounts = []
    
    # Try new multi-account format first
    accounts_json = get_config('YouTube', 'accounts')
    if accounts_json:
        try:
            parsed_accounts = json.loads(accounts_json)
            if isinstance(parsed_accounts, list):
                for account in parsed_accounts:
                    if isinstance(account, dict):
                        # Validate that at least username or channel_id is present
                        if account.get('username') or account.get('channel_id'):
                            accounts.append({
                                'username': account.get('username'),
                                'channel_id': account.get('channel_id'),
                                'name': account.get('name'),  # Optional display name
                                'discord_role': account.get('discord_role')  # Optional role ID
                            })
                        else:
                            logger.warning(f"⚠ Invalid YouTube account config (missing username/channel_id)")
                    else:
                        logger.warning(f"⚠ Invalid YouTube account config (not a dict)")
                
                if accounts:
                    logger.info(f"✓ Loaded {len(accounts)} YouTube account(s) from YOUTUBE_ACCOUNTS")
                    return accounts
            else:
                logger.warning(f"⚠ YOUTUBE_ACCOUNTS is not a JSON array")
        except json.JSONDecodeError as e:
            logger.warning(f"⚠ Failed to parse YOUTUBE_ACCOUNTS JSON: {e}")
    
    # Fallback to legacy single account format
    username = get_config('YouTube', 'username')
    channel_id = get_config('YouTube', 'channel_id')
    
    if username or channel_id:
        legacy_account = {
            'username': username,
            'channel_id': channel_id,
            'name': None,  # Will be auto-detected from YouTube
            'discord_role': None,  # Use default Discord role
            'discord_webhook': None  # Use default Discord webhook
        }
        accounts.append(legacy_account)
        logger.info(f"✓ Using legacy single YouTube account configuration")
    
    return accounts


def get_bluesky_accounts() -> list:
    """
    Get Bluesky accounts configuration with backward compatibility.
    
    Supports two formats:
    1. Legacy single account: BLUESKY_HANDLE and BLUESKY_APP_PASSWORD
    2. Multi-account: BLUESKY_ACCOUNTS JSON array
    
    Returns:
        List of account dicts, each with keys: handle, app_password, name
        Example: [{"handle": "user.bsky.social", "app_password": "xxxx", "name": "Personal"}]
    """
    import json
    
    accounts = []
    
    # Try new multi-account format first
    accounts_json = get_config('Bluesky', 'accounts')
    if accounts_json:
        try:
            parsed_accounts = json.loads(accounts_json)
            if isinstance(parsed_accounts, list):
                for account in parsed_accounts:
                    if isinstance(account, dict):
                        # Validate required fields
                        if account.get('handle') and account.get('app_password'):
                            accounts.append({
                                'handle': account.get('handle'),
                                'app_password': account.get('app_password'),
                                'name': account.get('name')  # Optional display name
                            })
                        else:
                            # Log only non-sensitive field to avoid exposing app_password
                            handle = account.get('handle', 'unknown') if isinstance(account, dict) else 'unknown'
                            logger.warning(f"⚠ Invalid Bluesky account config (missing handle/app_password): handle={handle}")
                    else:
                        logger.warning(f"⚠ Invalid Bluesky account config (not a dict)")
                
                if accounts:
                    logger.info(f"✓ Loaded {len(accounts)} Bluesky account(s) from BLUESKY_ACCOUNTS")
                    return accounts
            else:
                logger.warning(f"⚠ BLUESKY_ACCOUNTS is not a JSON array")
        except json.JSONDecodeError as e:
            logger.warning(f"⚠ Failed to parse BLUESKY_ACCOUNTS JSON: {e}")
    
    # Fallback to legacy single account format
    handle = get_config('Bluesky', 'handle')
    app_password = get_secret('Bluesky', 'app_password')
    
    if handle and app_password:
        legacy_account = {
            'handle': handle,
            'app_password': app_password,
            'name': None  # Will use handle as name
        }
        accounts.append(legacy_account)
        logger.info(f"✓ Using legacy single Bluesky account configuration")
    
    return accounts


def get_mastodon_accounts() -> list:
    """
    Get Mastodon accounts configuration with backward compatibility.
    
    Supports two formats:
    1. Legacy single account: MASTODON_API_BASE_URL, MASTODON_CLIENT_ID, etc.
    2. Multi-account: MASTODON_ACCOUNTS JSON array
    
    Returns:
        List of account dicts, each with keys: api_base_url, client_id, client_secret, access_token, name
    """
    import json
    
    accounts = []
    
    # Try new multi-account format first
    accounts_json = get_config('Mastodon', 'accounts')
    if accounts_json:
        try:
            parsed_accounts = json.loads(accounts_json)
            if isinstance(parsed_accounts, list):
                for account in parsed_accounts:
                    if isinstance(account, dict):
                        # Validate required fields
                        required = ['api_base_url', 'client_id', 'client_secret', 'access_token']
                        if all(account.get(field) for field in required):
                            accounts.append({
                                'api_base_url': account.get('api_base_url'),
                                'client_id': account.get('client_id'),
                                'client_secret': account.get('client_secret'),
                                'access_token': account.get('access_token'),
                                'name': account.get('name')  # Optional display name
                            })
                        else:
                            missing = [f for f in required if not account.get(f)]
                            # Log only non-sensitive field to avoid exposing secrets
                            api_url = account.get('api_base_url', 'unknown') if isinstance(account, dict) else 'unknown'
                            logger.warning(f"⚠ Invalid Mastodon account config (missing {missing}): api_base_url={api_url}")
                    else:
                        logger.warning(f"⚠ Invalid Mastodon account config (not a dict)")
                
                if accounts:
                    logger.info(f"✓ Loaded {len(accounts)} Mastodon account(s) from MASTODON_ACCOUNTS")
                    return accounts
            else:
                logger.warning(f"⚠ MASTODON_ACCOUNTS is not a JSON array")
        except json.JSONDecodeError as e:
            logger.warning(f"⚠ Failed to parse MASTODON_ACCOUNTS JSON: {e}")
    
    # Fallback to legacy single account format
    api_base_url = get_config('Mastodon', 'api_base_url')
    client_id = get_secret('Mastodon', 'client_id')
    client_secret = get_secret('Mastodon', 'client_secret')
    access_token = get_secret('Mastodon', 'access_token')
    
    if all([api_base_url, client_id, client_secret, access_token]):
        legacy_account = {
            'api_base_url': api_base_url,
            'client_id': client_id,
            'client_secret': client_secret,
            'access_token': access_token,
            'name': None  # Will use instance URL as name
        }
        accounts.append(legacy_account)
        logger.info(f"✓ Using legacy single Mastodon account configuration")
    
    return accounts


def get_matrix_accounts() -> list:
    """
    Get Matrix accounts configuration with backward compatibility.
    
    Supports two formats:
    1. Legacy single account: MATRIX_HOMESERVER, MATRIX_ROOM_ID, MATRIX_ACCESS_TOKEN/USERNAME/PASSWORD
    2. Multi-account: MATRIX_ACCOUNTS JSON array
    
    Returns:
        List of account dicts, each with keys: homeserver, room_id, access_token/username/password, name
    """
    import json
    
    accounts = []
    
    # Try new multi-account format first
    accounts_json = get_config('Matrix', 'accounts')
    if accounts_json:
        try:
            parsed_accounts = json.loads(accounts_json)
            if isinstance(parsed_accounts, list):
                for account in parsed_accounts:
                    if isinstance(account, dict):
                        # Validate required fields
                        homeserver = account.get('homeserver')
                        room_id = account.get('room_id')
                        access_token = account.get('access_token')
                        username = account.get('username')
                        password = account.get('password')
                        
                        # Must have homeserver, room_id, and either access_token or username+password
                        if homeserver and room_id and (access_token or (username and password)):
                            accounts.append({
                                'homeserver': homeserver,
                                'room_id': room_id,
                                'access_token': access_token,
                                'username': username,
                                'password': password,
                                'name': account.get('name')  # Optional display name
                            })
                        else:
                            # Log only non-sensitive fields to avoid exposing credentials
                            hs = homeserver or 'unknown'
                            rid = room_id or 'unknown'
                            logger.warning(f"⚠ Invalid Matrix account config (missing required fields): homeserver={hs}, room_id={rid}")
                    else:
                        logger.warning(f"⚠ Invalid Matrix account config (not a dict)")
                
                if accounts:
                    logger.info(f"✓ Loaded {len(accounts)} Matrix account(s) from MATRIX_ACCOUNTS")
                    return accounts
            else:
                logger.warning(f"⚠ MATRIX_ACCOUNTS is not a JSON array")
        except json.JSONDecodeError as e:
            logger.warning(f"⚠ Failed to parse MATRIX_ACCOUNTS JSON: {e}")
    
    # Fallback to legacy single account format
    homeserver = get_config('Matrix', 'homeserver')
    room_id = get_config('Matrix', 'room_id')
    access_token = get_secret('Matrix', 'access_token')
    username = get_config('Matrix', 'username')
    password = get_secret('Matrix', 'password')
    
    # Must have homeserver, room_id, and either access_token or username+password
    if homeserver and room_id and (access_token or (username and password)):
        legacy_account = {
            'homeserver': homeserver,
            'room_id': room_id,
            'access_token': access_token,
            'username': username,
            'password': password,
            'name': None  # Will use room_id as name
        }
        accounts.append(legacy_account)
        logger.info(f"✓ Using legacy single Matrix account configuration")
    
    return accounts
