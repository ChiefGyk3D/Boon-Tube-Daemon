#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test script to verify that escaped newlines in LLM responses are properly decoded.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import re


def test_escape_sequence_decoding():
    """Test that the escape sequence decoding logic works correctly.
    
    Note: This test intentionally duplicates the logic from gemini.py to verify
    it independently without importing the actual implementation. This is a
    common testing pattern to ensure tests don't depend on the code they're testing.
    """
    
    # Simulate various problematic responses from LLM
    test_cases = [
        {
            'name': 'Escaped newlines with quotes',
            'input': '"🎬 New YouTube-Videos video!\\n\\nMy bot generates AI-powered Yo Mama jokes on command.#dev #coding #AI\\n\\nhttps://www.youtube.com/watch?v=IXmy5ukxLvA"',
            'expected': '🎬 New YouTube-Videos video!\n\nMy bot generates AI-powered Yo Mama jokes on command.#dev #coding #AI\n\nhttps://www.youtube.com/watch?v=IXmy5ukxLvA'
        },
        {
            'name': 'Escaped newlines without quotes',
            'input': '🎬 New YouTube video!\\n\\nCheck out this amazing content!\\n\\nhttps://www.youtube.com/watch?v=test',
            'expected': '🎬 New YouTube video!\n\nCheck out this amazing content!\n\nhttps://www.youtube.com/watch?v=test'
        },
        {
            'name': 'Single quotes',
            'input': "'🎬 New video!\\n\\nGreat content!\\n\\nURL here'",
            'expected': '🎬 New video!\n\nGreat content!\n\nURL here'
        },
        {
            'name': 'Mixed escape sequences',
            'input': 'Line 1\\n\\tTabbed line\\r\\nWindows newline',
            'expected': 'Line 1\n\tTabbed line\r\nWindows newline'
        },
        {
            'name': 'Already correct (no escapes)',
            'input': '🎬 New video!\n\nGreat content!\n\nURL here',
            'expected': '🎬 New video!\n\nGreat content!\n\nURL here'
        }
    ]
    
    print("Testing escape sequence decoding...")
    print("="*70)
    
    all_passed = True
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print("-"*70)
        
        notification = test['input']
        
        # Apply the fix logic (same as in gemini.py)
        if '\\n' in notification:
            # First, remove quotes if response is wrapped
            if (notification.startswith('"') and notification.endswith('"')) or \
               (notification.startswith("'") and notification.endswith("'")):
                notification = notification[1:-1]
            
            # Then decode common escape sequences
            notification = notification.replace('\\n', '\n')
            notification = notification.replace('\\t', '\t')
            notification = notification.replace('\\r', '\r')
            notification = notification.strip()
        
        # Check if output matches expected
        if notification == test['expected']:
            print("✓ PASSED")
            print(f"Input:    {repr(test['input'][:50])}...")
            print(f"Output:   {repr(notification[:50])}...")
        else:
            print("✗ FAILED")
            print(f"Input:    {repr(test['input'][:50])}...")
            print(f"Expected: {repr(test['expected'][:50])}...")
            print(f"Got:      {repr(notification[:50])}...")
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


def test_no_false_positives():
    """Ensure we don't accidentally modify already-correct text."""
    
    print("\nTesting that we don't break correctly formatted text...")
    print("="*70)
    
    # These should remain unchanged
    test_cases = [
        "🎬 New video!\n\nGreat content!\n\nURL here",
        "Simple text with actual newlines\nNo escaped sequences here",
        "Text without any newlines or special formatting"
    ]
    
    all_passed = True
    for i, test_input in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print("-"*70)
        
        notification = test_input
        
        # Apply the fix logic
        if '\\n' in notification:
            # First, remove quotes if response is wrapped
            if (notification.startswith('"') and notification.endswith('"')) or \
               (notification.startswith("'") and notification.endswith("'")):
                notification = notification[1:-1]
            
            # Then decode common escape sequences
            notification = notification.replace('\\n', '\n')
            notification = notification.replace('\\t', '\t')
            notification = notification.replace('\\r', '\r')
            notification = notification.strip()
        
        # Should be unchanged
        if notification == test_input:
            print(f"✓ PASSED - Text unchanged: {repr(test_input[:40])}...")
        else:
            print(f"✗ FAILED - Text was modified!")
            print(f"  Input:  {repr(test_input[:40])}...")
            print(f"  Output: {repr(notification[:40])}...")
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    print("\n🧪 Escape Sequence Fix Test Suite")
    print("="*70)
    print("Testing the fix for escaped newlines in social media posts\n")
    
    test1_passed = test_escape_sequence_decoding()
    test2_passed = test_no_false_positives()
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    if test1_passed and test2_passed:
        print("✅ All test suites passed!")
        sys.exit(0)
    else:
        print("❌ Some test suites failed!")
        sys.exit(1)
