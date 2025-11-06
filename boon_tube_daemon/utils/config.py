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


def get_secret(section: str, key: str, 
               secret_name_env: Optional[str] = None,
               secret_path_env: Optional[str] = None,
               doppler_secret_env: Optional[str] = None) -> Optional[str]:
    """
    Get secret value with support for multiple secret backends.
    
    Priority order:
    1. Direct environment variable (SECTION_KEY)
    2. AWS Secrets Manager (if secret_name_env provided)
    3. HashiCorp Vault (if secret_path_env provided)
    4. Doppler (if doppler_secret_env provided)
    
    Args:
        section: Configuration section
        key: Configuration key
        secret_name_env: Environment variable containing AWS secret name
        secret_path_env: Environment variable containing Vault secret path
        doppler_secret_env: Environment variable containing Doppler secret name
        
    Returns:
        Secret value or None
    """
    # Try direct environment variable first
    value = get_config(section, key)
    if value:
        return value
    
    # Try AWS Secrets Manager
    if secret_name_env:
        secret_name = os.getenv(secret_name_env)
        if secret_name:
            try:
                import boto3
                import json
                
                client = boto3.client('secretsmanager')
                response = client.get_secret_value(SecretId=secret_name)
                
                if 'SecretString' in response:
                    secret_dict = json.loads(response['SecretString'])
                    if key in secret_dict:
                        logger.debug(f"Retrieved {section}.{key} from AWS Secrets Manager")
                        return secret_dict[key]
            except Exception as e:
                logger.debug(f"AWS Secrets Manager lookup failed: {e}")
    
    # Try HashiCorp Vault
    if secret_path_env:
        secret_path = os.getenv(secret_path_env)
        if secret_path:
            try:
                import hvac
                
                vault_addr = os.getenv('VAULT_ADDR')
                vault_token = os.getenv('VAULT_TOKEN')
                
                if vault_addr and vault_token:
                    client = hvac.Client(url=vault_addr, token=vault_token)
                    secret = client.secrets.kv.v2.read_secret_version(path=secret_path)
                    
                    if key in secret['data']['data']:
                        logger.debug(f"Retrieved {section}.{key} from HashiCorp Vault")
                        return secret['data']['data'][key]
            except Exception as e:
                logger.debug(f"Vault lookup failed: {e}")
    
    # Try Doppler
    if doppler_secret_env:
        doppler_secret = os.getenv(doppler_secret_env)
        if doppler_secret:
            # Doppler injects secrets as environment variables
            value = os.getenv(doppler_secret)
            if value:
                logger.debug(f"Retrieved {section}.{key} from Doppler")
                return value
    
    logger.debug(f"Secret not found: {section}.{key}")
    return None
