# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# This Source Code Form is subject to the terms of the Mozilla Public"""

# License, v. 2.0. If a copy of the MPL was not distributed with thisConfiguration management for Boon-Tube-Daemon.

# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Configuration management for Boon-Tube-Daemon.

Loads configuration from .env files and environment variables.
Supports multiple secret management backends.
"""



Loads configuration from .env file and environment variables.import logging

Supports multiple secret management backends.import os

"""import configparser

from pathlib import Path

import loggingfrom typing import Optional, Any

import os

from pathlib import Pathlogger = logging.getLogger(__name__)

from typing import Optional, Any

from dotenv import load_dotenv# Global config instance

_config = None

logger = logging.getLogger(__name__)



# Track if .env is loaded
def load_config(config_path: str = ".env") -> configparser.ConfigParser:

_env_loaded = False    """

    Load configuration from INI file.

    

def load_config(env_path: str = ".env") -> bool:    Args:

    """
        config_path: Path to .env file

    Load configuration from .env file.        

        Returns:

    Args:        ConfigParser instance with loaded configuration

        env_path: Path to .env file    """

            global _config

    Returns:    

        True if .env file was loaded successfully    if _config is not None:

    """        return _config

    global _env_loaded    

        config = configparser.ConfigParser()

    if _env_loaded:    

        return True    # Try to load config file

        config_file = Path(config_path)

    # Try to load .env file    if config_file.exists():

    env_file = Path(env_path)        config.read(config_file)

    if env_file.exists():        logger.info(f"✓ Loaded configuration from {config_path}")

        load_dotenv(env_file, override=False)    else:

        logger.info(f"✓ Loaded configuration from {env_path}")        logger.warning(f"⚠ Configuration file not found: {config_path}")

        _env_loaded = True        logger.info("  Creating default configuration...")

        return True    

    else:    _config = config

        logger.warning(f"⚠ Configuration file not found: {env_path}")    return config

        logger.info("  Using environment variables only")

        _env_loaded = True

        return Falsedef get_config(section: str, key: str, default: Any = None) -> Any:

    """

    Get configuration value from .env file or environment variable.

def get_config(section: str, key: str, default: Any = None) -> Any:    

    """    Environment variable format: BOON_TUBE_<SECTION>_<KEY>

    Get configuration value from environment variable.    Example: BOON_TUBE_YOUTUBE_USERNAME

        

    Environment variable format: <SECTION>_<KEY>    Args:

    Example: YOUTUBE_USERNAME, DISCORD_WEBHOOK_URL        section: Configuration section

            key: Configuration key

    For backwards compatibility also supports: BOON_TUBE_<SECTION>_<KEY>        default: Default value if not found

            

    Args:    Returns:

        section: Configuration section (e.g., 'YouTube', 'Discord')        Configuration value or default

        key: Configuration key (e.g., 'username', 'api_key')    """

        default: Default value if not found    if _config is None:

                load_config()

    Returns:    

        Configuration value or default    # Try environment variable first (highest priority)

    """    env_key = f"BOON_TUBE_{section.upper()}_{key.upper()}"

    if not _env_loaded:    env_value = os.getenv(env_key)

        load_config()    if env_value is not None:

            logger.debug(f"Config from env: {env_key}")

    # Try new format first: SECTION_KEY        return env_value

    env_key = f"{section.upper()}_{key.upper()}"    

    env_value = os.getenv(env_key)    # Try config file

    if env_value is not None:    try:

        logger.debug(f"Config from env: {env_key}")        if _config.has_option(section, key):

        return env_value            value = _config.get(section, key)

                logger.debug(f"Config from file: [{section}] {key}")

    # Try legacy format: BOON_TUBE_SECTION_KEY            return value

    legacy_key = f"BOON_TUBE_{section.upper()}_{key.upper()}"    except (configparser.NoSectionError, configparser.NoOptionError):

    env_value = os.getenv(legacy_key)        pass

    if env_value is not None:    

        logger.debug(f"Config from env (legacy): {legacy_key}")    # Return default

        return env_value    if default is not None:

            logger.debug(f"Config using default: [{section}] {key} = {default}")

    # Try short format for common keys    return default

    if key.upper() in ['ENABLE', 'ENABLE_MONITORING', 'ENABLE_POSTING']:

        short_key = f"{section.upper()}_ENABLE"

        env_value = os.getenv(short_key)def get_bool_config(section: str, key: str, default: bool = False) -> bool:

        if env_value is not None:    """

            logger.debug(f"Config from env (short): {short_key}")    Get boolean configuration value.

            return env_value    

        Args:

    # Return default        section: Configuration section

    if default is not None:        key: Configuration key

        logger.debug(f"Config using default: {section}_{key} = {default}")        default: Default value if not found

    return default        

    Returns:

        Boolean configuration value

def get_bool_config(section: str, key: str, default: bool = False) -> bool:    """

    """    value = get_config(section, key, default)

    Get boolean configuration value.    

        if isinstance(value, bool):

    Args:        return value

        section: Configuration section    

        key: Configuration key    if isinstance(value, str):

        default: Default value if not found        return value.lower() in ('true', 'yes', '1', 'on', 'enabled')

            

    Returns:    return bool(value)

        Boolean configuration value

    """

    value = get_config(section, key, default)def get_int_config(section: str, key: str, default: int = 0) -> int:

        """

    if isinstance(value, bool):    Get integer configuration value.

        return value    

        Args:

    if isinstance(value, str):        section: Configuration section

        return value.lower() in ('true', 'yes', '1', 'on', 'enabled')        key: Configuration key  

            default: Default value if not found

    return bool(value)        

    Returns:

        Integer configuration value

def get_int_config(section: str, key: str, default: int = 0) -> int:    """

    """    value = get_config(section, key, default)

    Get integer configuration value.    

        try:

    Args:        return int(value)

        section: Configuration section    except (ValueError, TypeError):

        key: Configuration key          logger.warning(f"Invalid integer value for [{section}] {key}: {value}, using default: {default}")

        default: Default value if not found        return default

        

    Returns:

        Integer configuration valuedef get_secret(section: str, key: str, 

    """               secret_name_env: Optional[str] = None,

    value = get_config(section, key, default)               secret_path_env: Optional[str] = None,

                   doppler_secret_env: Optional[str] = None) -> Optional[str]:

    try:    """

        return int(value)    Get secret value from various sources (in priority order):

    except (ValueError, TypeError):    1. Environment variable (BOON_TUBE_<SECTION>_<KEY>)

        logger.warning(f"Invalid integer value for {section}_{key}: {value}, using default: {default}")    2. Config file

        return default    3. AWS Secrets Manager (if configured)

    4. HashiCorp Vault (if configured)

    5. Doppler (if configured)

def get_secret(section: str, key: str,     

               secret_name_env: Optional[str] = None,    Args:

               secret_path_env: Optional[str] = None,        section: Configuration section

               doppler_secret_env: Optional[str] = None) -> Optional[str]:        key: Configuration key

    """        secret_name_env: Environment variable name for AWS secret name

    Get secret value from various sources (in priority order):        secret_path_env: Environment variable name for Vault secret path

    1. Direct environment variable (<SECTION>_<KEY>)        doppler_secret_env: Environment variable name for Doppler secret name

    2. Legacy environment variable (BOON_TUBE_<SECTION>_<KEY>)        

    3. AWS Secrets Manager (if configured)    Returns:

    4. HashiCorp Vault (if configured)        Secret value or None if not found

    5. Doppler (if configured)    """

        # Try environment variable and config file first

    Args:    value = get_config(section, key, None)

        section: Configuration section    if value:

        key: Configuration key        return value

        secret_name_env: Environment variable name for AWS secret name    

        secret_path_env: Environment variable name for Vault secret path    # TODO: Add support for external secret managers

        doppler_secret_env: Environment variable name for Doppler secret name    # For now, secrets must be in environment variables or .env file

            

    Returns:    return None

        Secret value or None if not found

    """

    # Try direct environment variable firstdef get_all_platform_configs() -> dict:

    value = get_config(section, key, None)    """

    if value:    Get all platform configurations.

        return value    

        Returns:

    # TODO: Add support for external secret managers        Dictionary of platform configurations

    # For now, secrets must be in environment variables or .env file    """

        if _config is None:

    return None        load_config()

    

    platforms = {}

def get_all_config() -> dict:    

    """    # Get all sections

    Get all configuration from environment.    for section in _config.sections():

            if section in ['Settings', 'General']:

    Returns:            continue

        Dictionary of all environment variables        

    """        platforms[section] = {}

    if not _env_loaded:        for key, value in _config.items(section):

        load_config()            platforms[section][key] = value

        

    return dict(os.environ)    return platforms





def reload_config():def reload_config():

    """Reload configuration from .env file."""    """Reload configuration from file."""

    global _env_loaded    global _config

    _env_loaded = False    _config = None

    load_config()    load_config()



# Special handling for Settings section
def get_check_interval() -> int:
    """Get check interval from CHECK_INTERVAL or Settings section."""
    # Try direct CHECK_INTERVAL first
    value = os.getenv('CHECK_INTERVAL')
    if value:
        try:
            return int(value)
        except ValueError:
            pass
    
    # Fall back to Settings_check_interval
    return get_int_config('Settings', 'check_interval', 300)


def get_notification_template() -> str:
    """Get notification template."""
    return get_config('Settings', 'notification_template', 
                     "🎬 New {platform} video!\n\n{title}\n\n{url}")


def get_hashtags() -> str:
    """Get hashtags configuration."""
    return get_config('Settings', 'hashtags', '')
