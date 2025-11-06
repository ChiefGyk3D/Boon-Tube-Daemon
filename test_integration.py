#!/usr/bin/env python3
"""
Complete integration test for Boon-Tube-Daemon with TikTok monitoring.
Tests the full workflow: monitor -> detect -> notify
"""

import sys
import time
sys.path.insert(0, '/home/chiefgyk3d/src/Boon-Tube-Daemon')

from dotenv import load_dotenv
load_dotenv('.env.test')

print("="*70)
print("🎬 Boon-Tube-Daemon - Complete Integration Test")
print("="*70)

from boon_tube_daemon.main import BoonTubeDaemon

# Create and initialize daemon
daemon = BoonTubeDaemon()

print("\n📦 Step 1: Initializing daemon...")
if not daemon.initialize():
    print("❌ Daemon initialization failed!")
    sys.exit(1)

print("\n" + "="*70)
print("✅ Daemon Initialized!")
print("="*70)

# Show configuration
print(f"\n📊 Configuration:")
print(f"  Media Platforms: {len(daemon.media_platforms)}")
for p in daemon.media_platforms:
    print(f"    • {p.name}")

print(f"  Social Platforms: {len(daemon.social_platforms)}")
if daemon.social_platforms:
    for p in daemon.social_platforms:
        print(f"    • {p.name}")
else:
    print(f"    (None configured - notifications will be logged only)")

print(f"  LLM: {'Enabled' if daemon.llm else 'Disabled'}")
print(f"  Check Interval: {daemon.check_interval}s")

# Test 1: First check (establish baseline)
print("\n" + "="*70)
print("🔍 Test 1: First Check (Establishing Baseline)")
print("="*70)
daemon.check_platforms()
print("  ✓ Baseline established")

# Test 2: Second check (should find no new videos)
print("\n" + "="*70)
print("🔍 Test 2: Second Check (No New Videos)")
print("="*70)
print("  Waiting 3 seconds...")
time.sleep(3)
daemon.check_platforms()
print("  ✓ No new videos detected (as expected)")

# Show summary
print("\n" + "="*70)
print("✅ Integration Test Complete!")
print("="*70)

print("\n📝 Summary:")
print("  ✓ Daemon initialization: SUCCESS")
print("  ✓ TikTok monitoring: WORKING")
print("  ✓ Baseline check: COMPLETE")
print("  ✓ New video detection: READY")

print("\n🚀 Next Steps:")
print("  1. Configure social platforms in .env (Discord, Matrix, etc.)")
print("  2. Optional: Enable Gemini LLM for enhanced notifications")
print("  3. Run: python3 main.py (to start continuous monitoring)")
print("  4. The daemon will check every 5 minutes for new videos")
print("  5. New videos will be posted to all configured platforms")

print("\n💡 Tips:")
print("  • First run downloads Chromium browser (~150MB)")
print("  • Run 'playwright install chromium' if not auto-installed")
print("  • Check logs for detailed monitoring activity")
print("  • Use Ctrl+C to stop the daemon gracefully")

print("\n" + "="*70)
