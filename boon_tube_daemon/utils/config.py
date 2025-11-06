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
    Get configuration value from environment variables.
    
    Environment variable format: SECTION_KEY (uppercase)
    Example: TikTok.username -> TIKTOK_USERNAME
    
    Args:
        section: Configuration section (e.g., 'TikTok', 'YouTube')
        key: Configuration key (e.g., 'username', 'api_key')
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    # Convert to environment variable format
    env_var = f"{section}_{key}".upper()
    value = os.getenv(env_var, default)
    
    if value is None:
        logger.debug(f"Config not found: {section}.{key} ({env_var})")
    
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
        logger.warning(f"Invalid integer value for {section}.{key}: {value}, using default: {default}")
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
    
    # 1. Try Doppler first (if DOPPLER_TOKEN is set, Doppler injects all secrets as env vars)
    if os.getenv('DOPPLER_TOKEN'):
        value = os.getenv(env_var)
        if value:
            logger.debug(f"✓ Retrieved {section}.{key} from Doppler")
            return value
    
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
                    logger.debug(f"✓ Retrieved {section}.{key} from AWS Secrets Manager")
                    return secret_dict[key]
                # Try uppercase key (for consistency)
                if key.upper() in secret_dict:
                    logger.debug(f"✓ Retrieved {section}.{key} from AWS Secrets Manager")
                    return secret_dict[key.upper()]
                # Try the full env var name
                if env_var in secret_dict:
                    logger.debug(f"✓ Retrieved {section}.{key} from AWS Secrets Manager")
                    return secret_dict[env_var]
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
                    logger.debug(f"✓ Retrieved {section}.{key} from HashiCorp Vault")
                    return data[key]
                # Try uppercase key
                if key.upper() in data:
                    logger.debug(f"✓ Retrieved {section}.{key} from HashiCorp Vault")
                    return data[key.upper()]
                # Try the full env var name
                if env_var in data:
                    logger.debug(f"✓ Retrieved {section}.{key} from HashiCorp Vault")
                    return data[env_var]
        except ImportError:
            logger.debug("hvac not installed, skipping HashiCorp Vault")
        except Exception as e:
            logger.debug(f"Vault lookup failed: {e}")
    
    # 4. Fallback to environment variable or .env file
    value = get_config(section, key, default=default)
    if value:
        logger.debug(f"✓ Retrieved {section}.{key} from environment/.env")
        return value
    
    logger.debug(f"Secret not found: {section}.{key}")
    return default
