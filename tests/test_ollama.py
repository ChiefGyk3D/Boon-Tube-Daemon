#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test script for Ollama integration with Boon-Tube-Daemon.

Usage:
    python3 tests/test_ollama.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from boon_tube_daemon.llm.ollama import OllamaLLM


def is_ollama_configured():
    """Check if Ollama is properly configured."""
    return (
        os.getenv('LLM_ENABLE', '').lower() == 'true' and
        os.getenv('LLM_PROVIDER', '').lower() == 'ollama' and
        os.getenv('LLM_OLLAMA_HOST') and
        os.getenv('LLM_MODEL')
    )


def test_ollama_integration():
    """Test Ollama integration."""
    print("\n" + "="*60)
    print("Testing Ollama Integration")
    print("="*60 + "\n")
    
    # Check configuration
    if not is_ollama_configured():
        print("❌ FAILED: Ollama not configured")
        print("\nRequired .env settings:")
        print("  LLM_ENABLE=True")
        print("  LLM_PROVIDER=ollama")
        print("  LLM_OLLAMA_HOST=http://192.168.1.100")
        print("  LLM_OLLAMA_PORT=11434")
        print("  LLM_MODEL=gemma2:2b")
        return False
    
    # Test 1: Initialize Ollama
    print("Test 1: Initialize Ollama connection")
    llm = OllamaLLM()
    if not llm.authenticate():
        print("❌ FAILED: Could not authenticate with Ollama")
        return False
    
    print(f"✓ Ollama connection initialized")
    print(f"✓ Connected to: {llm.ollama_host}")
    print(f"✓ Model: {llm.model}")
    print()
    
    # Test video data
    test_video = {
        'title': 'Setting Up a Home Lab Server with Proxmox',
        'description': 'In this video, I walk through setting up a home lab server using Proxmox VE. We\'ll cover installation, basic configuration, and creating your first VM.',
        'url': 'https://youtu.be/dQw4w9WgXcQ'
    }
    
    # Test 2: Generate Bluesky notification (300 char limit)
    print("Test 2: Generate Bluesky notification (250 char limit)")
    try:
        bluesky_message = llm.generate_notification(
            test_video,
            'YouTube',
            'bluesky'
        )
        
        if bluesky_message:
            print(f"✓ Generated Bluesky message ({len(bluesky_message)} chars):")
            print(f"{'─'*60}")
            print(bluesky_message)
            print(f"{'─'*60}")
            print()
        else:
            print("❌ FAILED: No message generated for Bluesky")
            return False
    except Exception as e:
        print(f"❌ FAILED: Error generating Bluesky message: {e}")
        return False
    
    # Test 3: Generate Mastodon notification (500 char limit)
    print("Test 3: Generate Mastodon notification (400 char limit)")
    try:
        mastodon_message = llm.generate_notification(
            test_video,
            'YouTube',
            'mastodon'
        )
        
        if mastodon_message:
            print(f"✓ Generated Mastodon message ({len(mastodon_message)} chars):")
            print(f"{'─'*60}")
            print(mastodon_message)
            print(f"{'─'*60}")
            print()
        else:
            print("❌ FAILED: No message generated for Mastodon")
            return False
    except Exception as e:
        print(f"❌ FAILED: Error generating Mastodon message: {e}")
        return False
    
    # Test 4: Generate Discord notification (no hashtags)
    print("Test 4: Generate Discord notification (no hashtags)")
    try:
        discord_message = llm.generate_notification(
            test_video,
            'YouTube',
            'discord'
        )
        
        if discord_message:
            print(f"✓ Generated Discord message ({len(discord_message)} chars):")
            print(f"{'─'*60}")
            print(discord_message)
            print(f"{'─'*60}")
            print()
        else:
            print("❌ FAILED: No message generated for Discord")
            return False
    except Exception as e:
        print(f"❌ FAILED: Error generating Discord message: {e}")
        return False
    
    # Test 5: Generate Matrix notification (no hashtags)
    print("Test 5: Generate Matrix notification (no hashtags)")
    try:
        matrix_message = llm.generate_notification(
            test_video,
            'YouTube',
            'matrix'
        )
        
        if matrix_message:
            print(f"✓ Generated Matrix message ({len(matrix_message)} chars):")
            print(f"{'─'*60}")
            print(matrix_message)
            print(f"{'─'*60}")
            print()
        else:
            print("❌ FAILED: No message generated for Matrix")
            return False
    except Exception as e:
        print(f"❌ FAILED: Error generating Matrix message: {e}")
        return False
    
    # All tests passed
    print("="*60)
    print("✅ SUCCESS: All Ollama tests passed!")
    print("="*60)
    return True


if __name__ == "__main__":
    success = test_ollama_integration()
    sys.exit(0 if success else 1)
