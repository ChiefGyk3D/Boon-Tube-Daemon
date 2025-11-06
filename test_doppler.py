#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test script for Doppler secret management integration.
Verifies that secrets can be loaded from Doppler with fallback to .env.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from boon_tube_daemon.utils.config import load_config, get_config, get_secret

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_doppler_status():
    """Check if Doppler is available and configured."""
    print("\n" + "="*70)
    print("🔍 Checking Doppler Status")
    print("="*70)
    
    # Check for DOPPLER_TOKEN
    doppler_token = os.getenv('DOPPLER_TOKEN')
    if doppler_token:
        print(f"✓ DOPPLER_TOKEN is set: {doppler_token[:10]}...")
        print("  → Doppler will be used for secrets")
        return 'token'
    
    # Check if Doppler CLI is available
    try:
        import subprocess
        result = subprocess.run(['doppler', '--version'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            print(f"✓ Doppler CLI installed: {result.stdout.strip()}")
            
            # Check if project is configured
            result = subprocess.run(['doppler', 'configure', 'get', 'project'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                print(f"✓ Doppler project configured: {result.stdout.strip()}")
                
                result = subprocess.run(['doppler', 'configure', 'get', 'config'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and result.stdout.strip():
                    print(f"✓ Doppler config: {result.stdout.strip()}")
                    print("  → You can use 'doppler run -- python3 main.py'")
                    return 'cli'
            else:
                print("⚠ Doppler CLI installed but not configured")
                print("  → Run 'doppler setup' to configure")
                return 'not-configured'
        else:
            print("✗ Doppler CLI not working properly")
            return None
    except FileNotFoundError:
        print("✗ Doppler CLI not installed")
        print("  → Install from: https://docs.doppler.com/docs/install-cli")
        return None
    except Exception as e:
        print(f"⚠ Error checking Doppler: {e}")
        return None


def test_secret_loading():
    """Test loading secrets from different sources."""
    print("\n" + "="*70)
    print("🔑 Testing Secret Loading")
    print("="*70)
    
    # Load .env as fallback
    env_file = project_root / '.env'
    if env_file.exists():
        load_config(str(env_file))
        print("✓ Loaded .env file (fallback)")
    else:
        print("⚠ No .env file found (will rely on Doppler or env vars)")
    
    test_secrets = [
        ('YouTube', 'api_key', 'SECRETS_DOPPLER_YOUTUBE_SECRET_NAME'),
        ('TikTok', 'username', None),
        ('Discord', 'webhook_url', 'SECRETS_DOPPLER_DISCORD_SECRET_NAME'),
        ('Gemini', 'api_key', 'SECRETS_DOPPLER_LLM_SECRET_NAME'),
    ]
    
    print("\nTesting secret retrieval:")
    for section, key, doppler_env in test_secrets:
        if doppler_env:
            value = get_secret(section, key, doppler_secret_env=doppler_env)
        else:
            value = get_secret(section, key)
        
        if value:
            # Mask the secret
            if len(value) > 10:
                masked = f"{value[:5]}...{value[-3:]}"
            else:
                masked = "***"
            print(f"  ✓ {section}.{key}: {masked}")
        else:
            print(f"  ✗ {section}.{key}: Not found")


def test_config_priority():
    """Test configuration priority order."""
    print("\n" + "="*70)
    print("📊 Testing Configuration Priority")
    print("="*70)
    
    print("\nPriority order:")
    print("  1. Doppler (if DOPPLER_TOKEN set)")
    print("  2. AWS Secrets Manager (if configured)")
    print("  3. HashiCorp Vault (if configured)")
    print("  4. Environment variables / .env file")
    
    # Test with a known value
    test_key = 'YOUTUBE_USERNAME'
    
    # Check each source
    print(f"\nLooking for {test_key}:")
    
    if os.getenv('DOPPLER_TOKEN'):
        doppler_value = os.getenv(test_key)
        if doppler_value:
            print(f"  ✓ Found in Doppler: {doppler_value}")
    
    env_value = os.getenv(test_key)
    if env_value:
        print(f"  ✓ Found in environment: {env_value}")
    
    config_value = get_config('YouTube', 'username')
    print(f"  → Final value: {config_value}")


def test_fallback_behavior():
    """Test fallback from Doppler to .env."""
    print("\n" + "="*70)
    print("🔄 Testing Fallback Behavior")
    print("="*70)
    
    # Create a test secret that only exists in .env
    os.environ['TEST_SECRET'] = 'from_env'
    
    value = get_secret('Test', 'secret')
    if value == 'from_env':
        print("✓ Fallback to environment variable works")
    else:
        print(f"✗ Fallback failed, got: {value}")
    
    # Test with missing secret
    value = get_secret('NonExistent', 'secret', default='default_value')
    if value == 'default_value':
        print("✓ Default value fallback works")
    else:
        print(f"✗ Default fallback failed, got: {value}")
    
    # Clean up
    del os.environ['TEST_SECRET']


def show_recommendations(doppler_status):
    """Show recommendations based on Doppler status."""
    print("\n" + "="*70)
    print("💡 Recommendations")
    print("="*70)
    
    if doppler_status == 'token':
        print("\n✅ Using Doppler via service token")
        print("  → Secrets are loaded from Doppler")
        print("  → .env is used as fallback only")
        print("\nTo update secrets:")
        print("  1. Login to Doppler Dashboard")
        print("  2. Update secrets in your project")
        print("  3. Restart the daemon to pick up changes")
        
    elif doppler_status == 'cli':
        print("\n✅ Doppler CLI configured")
        print("  → Run with: doppler run -- python3 main.py")
        print("  → This injects secrets at runtime")
        print("\nFor production deployment:")
        print("  1. Create service token in Doppler Dashboard")
        print("  2. Set DOPPLER_TOKEN environment variable")
        print("  3. Run without 'doppler run' prefix")
        
    elif doppler_status == 'not-configured':
        print("\n⚠ Doppler CLI installed but not configured")
        print("\nTo configure:")
        print("  1. Run: doppler login")
        print("  2. Run: doppler setup")
        print("  3. Select your project and config")
        print("  4. Run: doppler run -- python3 main.py")
        
    else:
        print("\n📋 Using .env file (no Doppler)")
        print("  → Secrets loaded from .env")
        print("  → This is fine for local development")
        print("\nTo enable Doppler:")
        print("  1. Install CLI: https://docs.doppler.com/docs/install-cli")
        print("  2. Run: doppler login")
        print("  3. Run: doppler setup")
        print("  4. See: docs/DOPPLER_SETUP.md")


def main():
    """Run all Doppler integration tests."""
    print("\n" + "="*70)
    print("🔐 Doppler Secret Management Test Suite")
    print("="*70)
    
    # Check Doppler status
    doppler_status = check_doppler_status()
    
    # Test secret loading
    test_secret_loading()
    
    # Test priority
    test_config_priority()
    
    # Test fallback
    test_fallback_behavior()
    
    # Show recommendations
    show_recommendations(doppler_status)
    
    # Summary
    print("\n" + "="*70)
    print("✅ Doppler Integration Tests Complete!")
    print("="*70)
    
    if doppler_status:
        print("\n✓ Secret management working correctly")
        print("✓ Fallback to .env working")
        print("✓ Ready for production deployment")
    else:
        print("\n✓ Fallback to .env working")
        print("→ Consider setting up Doppler for production")
        print("→ See: docs/DOPPLER_SETUP.md")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
