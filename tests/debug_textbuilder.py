#!/usr/bin/env python3
"""Debug script to understand TextBuilder.tag() behavior."""

from atproto import client_utils

# Test 1: What we had originally
print("Test 1: tag('TestPost', '#TestPost')")
builder1 = client_utils.TextBuilder()
builder1.tag('TestPost', '#TestPost')
result1 = builder1.build_text()
print(f"Result: '{result1}'")
print()

# Test 2: What we changed to
print("Test 2: tag('TestPost', 'TestPost')")
builder2 = client_utils.TextBuilder()
builder2.tag('TestPost', 'TestPost')
result2 = builder2.build_text()
print(f"Result: '{result2}'")
print()

# Test 3: With # in text but not tag
print("Test 3: tag('#TestPost', 'TestPost')")
builder3 = client_utils.TextBuilder()
builder3.tag('#TestPost', 'TestPost')
result3 = builder3.build_text()
print(f"Result: '{result3}'")
print()

# Test 4: Full example with text before
print("Test 4: Full example")
builder4 = client_utils.TextBuilder()
builder4.text('Check out ')
builder4.tag('#Python', 'Python')
builder4.text(' programming!')
result4 = builder4.build_text()
print(f"Result: '{result4}'")
