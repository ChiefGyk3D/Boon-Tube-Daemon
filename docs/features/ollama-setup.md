# Ollama Setup Guide for Boon-Tube-Daemon

*Or: How to Make Your GPU Write Social Media Posts So You Don't Have To*

This guide walks you through setting up Ollama for privacy-first, cost-free AI-powered notifications in Boon-Tube-Daemon.

George Carlin would've loved this: We spent decades building supercomputers that can simulate nuclear explosions and predict weather patterns, and now we're using them to write "New video is up! Check it out! 🎬" The future is fucking weird, but at least it's efficient.

## Table of Contents

- [Why Ollama?](#why-ollama)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Model Recommendations](#model-recommendations)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Advanced Setup](#advanced-setup)

## Why Ollama?

*"Because sending your video titles to Google is like shouting your diary entries in a crowded mall."*

**Ollama** provides local LLM hosting with several advantages:

✅ **Privacy-First:** Your video data never leaves your network (unlike your personal info on every other website)  
✅ **Zero API Costs:** Unlimited usage with no per-request fees (your electricity bill is another story)  
✅ **No Rate Limits:** Process as many videos as your hardware can handle  
✅ **Fast Response:** ~1 second with Gemma3 on GPU (faster than you can think of what to post)  
✅ **Offline Capable:** Works without internet connection (for those doomsday preppers among us)  

**Comparison with Google Gemini:**

| Feature | Ollama | Google Gemini |
|---------|--------|---------------|
| Cost | Free (local hardware) | Free tier limited, then paid |
| Privacy | Complete (local only) | Data sent to Google |
| Rate Limits | None | 15 RPM (free tier) |
| Setup Complexity | Medium | Easy |
| Hardware Required | Yes (GPU recommended) | No |
| Speed | ~1s (Gemma3) | ~2s |
| Trust Issues | None | You're feeding Google |

## Quick Start

### 5-Minute Setup

*If you can't set this up in 5 minutes, you might need coffee. Or a better internet connection.*

1. **Install Ollama:**
   ```bash
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # macOS
   brew install ollama
   
   # Windows - download from https://ollama.com/download
   ```

2. **Pull a model:**
   ```bash
   # 🏆 Recommended: Fast AND good quality (~1 second response!)
   ollama pull gemma3:4b
   
   # Alternative for 16GB GPUs: Premium quality
   ollama pull gemma3:12b
   ```

3. **Start Ollama:**
   ```bash
   # Allow remote connections (if Boon-Tube-Daemon is on different machine)
   OLLAMA_HOST=0.0.0.0 ollama serve
   
   # Or just run locally (same machine)
   ollama serve
   ```

4. **Configure Boon-Tube-Daemon (.env file):**
   ```bash
   # Enable LLM
   LLM_ENABLE=true
   
   # Use Ollama provider
   LLM_PROVIDER=ollama
   
   # Ollama server location
   LLM_OLLAMA_HOST=http://localhost  # Or your server IP: http://192.168.1.100
   LLM_OLLAMA_PORT=11434
   LLM_MODEL=gemma3:4b
   
   # Enable enhanced notifications
   LLM_ENHANCE_NOTIFICATIONS=true
   ```

5. **Test it:**
   ```bash
   python3 tests/test_ollama.py
   ```

That's it! Boon-Tube-Daemon will now use Ollama to generate unique, engaging posts for each social platform. Your GPU finally has a purpose beyond mining crypto or playing games.

## Installation

### Option 1: Single GPU (Simple Setup)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull your chosen model
ollama pull gemma2:2b

# Start Ollama (runs as background service)
ollama serve
```

Ollama will automatically:
- Detect your GPU (NVIDIA, AMD, or Apple Silicon)
- Use available VRAM efficiently
- Fall back to CPU if no GPU available

### Option 2: Multi-GPU Setup (Advanced)

For systems with **multiple GPUs** (different vendors/models), see [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) for advanced setup:

```bash
# Clone FrankenLLM
git clone https://github.com/ChiefGyk3D/FrankenLLM.git
cd FrankenLLM

# Run setup wizard
./setup-frankenllm.sh
```

FrankenLLM features:
- Per-GPU Ollama instances on separate ports
- Mixed GPU support (NVIDIA + AMD)
- Automatic model distribution
- Load balancing

### Verifying Installation

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Should return JSON with available models
```

## Configuration

### Basic Configuration

In your `.env` file:

```bash
# ============================================================================
# LLM CONFIGURATION
# ============================================================================

# Enable LLM features
LLM_ENABLE=true

# Choose provider
LLM_PROVIDER=ollama  # Options: ollama, gemini

# Ollama server configuration
LLM_OLLAMA_HOST=http://192.168.1.100  # Your Ollama server IP
LLM_OLLAMA_PORT=11434                  # Default Ollama port
LLM_MODEL=gemma2:2b                    # Model to use

# Enhanced notifications (generates unique posts per platform)
LLM_ENHANCE_NOTIFICATIONS=true

# Platform delay (seconds between LLM API calls)
LLM_PLATFORM_DELAY=2.0
```

### Remote Ollama Server

If running Ollama on a **different machine**:

1. **On Ollama server:**
   ```bash
   # Allow remote connections
   OLLAMA_HOST=0.0.0.0 ollama serve
   
   # Or add to systemd service (if using)
   sudo systemctl edit ollama.service
   # Add: Environment="OLLAMA_HOST=0.0.0.0"
   ```

2. **Allow firewall access:**
   ```bash
   sudo ufw allow 11434/tcp
   ```

3. **In Boon-Tube-Daemon .env:**
   ```bash
   LLM_OLLAMA_HOST=http://192.168.1.100  # Your server's IP
   ```

4. **Test connection:**
   ```bash
   curl http://192.168.1.100:11434/api/tags
   ```

### Network Troubleshooting

**Docker container can't reach Ollama?**

```bash
# Don't use "localhost" in Docker - use host IP or Docker network
LLM_OLLAMA_HOST=http://192.168.1.100  # Host IP
# Or: LLM_OLLAMA_HOST=http://host.docker.internal  # Docker Desktop

# Test from container
docker exec -it boon-tube-daemon curl http://192.168.1.100:11434/api/tags
```

## Model Recommendations

*For the full deep-dive into models, see [LLM Model Recommendations](./llm-model-recommendations.md).*

### 🏆 January 2026 Benchmark Results

Here's the truth: **Gemma3 models are 6-10x faster than Qwen2.5** for generating notifications.

| Model | Speed | Quality | Verdict |
|-------|-------|---------|---------|
| `gemma3:4b` | ~1.0s 🏆 | ⭐⭐⭐⭐⭐ | **RECOMMENDED** |
| `gemma3:12b` | ~1.3s 🏆 | ⭐⭐⭐⭐⭐+ | Premium (16GB GPU) |
| `qwen2.5:7b` | ~11s | ⭐⭐⭐⭐⭐ | Great quality, slow |
| `llama3.1:8b` | ~8s | ⭐⭐⭐⭐ | Good general purpose |
| `mistral:7b` | ~7s | ⭐⭐⭐⭐ | Solid |

**Why Gemma3?** Because waiting 11 seconds for a notification about your cat video feels like an eternity in internet time. Gemma3 does it in 1 second. Math is easy here.

### Recommended Models by VRAM

| VRAM | Model | Why |
|------|-------|-----|
| **4GB** | `gemma3:2b` | It'll fit, it'll work |
| **6-8GB** | `gemma3:4b` 🏆 | Sweet spot - fast & good |
| **12GB** | `gemma3:4b` | Same model, more headroom |
| **16GB** | `gemma3:12b` | Premium quality, still fast |
| **24GB+** | `gemma3:27b` | Maximum quality |

### Qwen3 Thinking Mode (Experimental)

Qwen3 models have a "thinking mode" where they show their reasoning. It's like having a coworker who explains their entire thought process before answering a yes/no question.

If you want to experiment:
```bash
LLM_MODEL=qwen3:4b
LLM_ENABLE_THINKING_MODE=true
LLM_THINKING_TOKEN_MULTIPLIER=4.0
```

But honestly? Just use Gemma3. It doesn't need therapy to write a notification.

### Hardware Requirements

**Minimum:**
- CPU: Modern multi-core processor
- RAM: 8GB system RAM
- GPU: Optional (CPU inference works, just slower)

**Recommended:**
- GPU: NVIDIA/AMD with 6GB+ VRAM
- RAM: 16GB system RAM
- Model: `gemma3:4b`

**Optimal:**
- GPU: NVIDIA RTX 3060+ or AMD 6000+ series
- RAM: 32GB system RAM
- VRAM: 8GB+ for larger models

### Pulling Models

```bash
# Browse available models
# https://ollama.com/library

# List installed models
ollama list

# Pull recommended model
ollama pull gemma3:4b

# Pull premium model (16GB GPU)
ollama pull gemma3:12b

# Remove a model
ollama rm old-model:tag
```

## Testing

### Quick Test

```bash
# Test Ollama connection (moment of truth)
curl http://localhost:11434/api/tags

# Should return something like:
# {"models":[{"name":"gemma3:4b",...}]}
# If you see models, congratulations. You've joined the 21st century.
```

### Comprehensive Test

```bash
# Run Boon-Tube-Daemon test suite
cd /path/to/Boon-Tube-Daemon
python3 tests/test_ollama.py
```

**Expected output:**
```
Testing Ollama Integration
============================================================

Test 1: Initialize Ollama connection
✓ Ollama connection initialized
✓ Connected to: http://192.168.1.100:11434
✓ Model: gemma3:4b

Test 2: Generate Bluesky notification (250 char limit)
✓ Generated Bluesky message (242 chars):
────────────────────────────────────────────────────────────
New video alert! I'm diving into Proxmox home lab setup...

https://youtu.be/dQw4w9WgXcQ
────────────────────────────────────────────────────────────

...

============================================================
✅ SUCCESS: All Ollama tests passed!
============================================================
```

*If you don't see success, don't panic. Check the troubleshooting section below. We've made all the mistakes so you don't have to.*

### Manual Test (Python)

```python
from boon_tube_daemon.llm.ollama import OllamaLLM
from dotenv import load_dotenv

load_dotenv()

llm = OllamaLLM()
if llm.authenticate():
    print("✅ Ollama is ready!")
    
    # Test notification generation
    video = {
        'title': 'Test Video',
        'description': 'Test description',
        'url': 'https://youtube.com/watch?v=test'
    }
    
    message = llm.generate_notification(video, 'YouTube', 'bluesky')
    print(f"Generated: {message}")
else:
    print("❌ Check configuration")
```

## Troubleshooting

*Because something always goes wrong. That's just the nature of running software on hardware designed by committees.*

### "Failed to connect to Ollama"

**Solution:**

```bash
# 1. Check Ollama is running (is anyone home?)
ps aux | grep ollama
# Or: systemctl status ollama (if using systemd)

# 2. Test local connection (talk to yourself)
curl http://localhost:11434/api/tags

# 3. If remote server, ensure firewall allows port 11434
sudo ufw allow 11434/tcp

# 4. Start Ollama with remote access (open the doors)
OLLAMA_HOST=0.0.0.0 ollama serve

# 5. Check from Boon-Tube-Daemon host (phoning home)
curl http://YOUR_SERVER_IP:11434/api/tags
```

### "Model not found"

*The computer equivalent of "we don't carry that brand."*

**Solution:**

```bash
# Pull the model (download the brain)
ollama pull gemma3:4b

# Verify it's available
ollama list

# Check model name matches .env EXACTLY
# LLM_MODEL=gemma3:4b  (typos are not forgiven)
```

### "Ollama Python client not installed"

**Solution:**

```bash
# Install Ollama client
pip install ollama

# Or update requirements (the civilized way)
pip install -r requirements.txt
```

### Slow Generation Times

*Patience is a virtue, but 60 seconds for a notification is ridiculous.*

**Causes and solutions:**

1. **CPU Inference (no GPU):**
   - Expected: 30-60s per message
   - Solution: Add GPU for ~1s generation with Gemma3

2. **Model Too Large:**
   - Try Gemma3: `ollama pull gemma3:4b` (~1 second!)
   - Benchmark before blaming: smaller isn't always faster

3. **Insufficient VRAM:**
   - Monitor GPU usage: `nvidia-smi` or `rocm-smi`
   - Use appropriately sized model for your GPU

4. **Network Latency (remote server):**
   - Check ping: `ping YOUR_OLLAMA_SERVER`
   - Consider running Ollama locally (physics is undefeated)

### GPU Not Detected

*Your expensive graphics card is being wasted on desktop rendering.*

**NVIDIA:**

```bash
# Check NVIDIA drivers (is it alive?)
nvidia-smi

# Reinstall if needed
sudo apt install nvidia-driver-XXX

# Verify GPU is being used
ollama run gemma3:4b "test"
# Should show GPU usage in nvidia-smi
```

**AMD:**

```bash
# Check ROCm installation
rocm-smi

# Ensure ROCm is configured
export HSA_OVERRIDE_GFX_VERSION=10.3.0  # Adjust for your GPU
```

## Advanced Setup

*For those who think "good enough" is never good enough.*

### Systemd Service (Auto-Start)

*Because manually starting Ollama every reboot is so 2019.*

Create `/etc/systemd/system/ollama.service`:

```ini
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
Type=simple
User=youruser
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_MODELS=/home/youruser/.ollama/models"
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ollama.service
sudo systemctl start ollama.service
sudo systemctl status ollama.service
```

### Multiple Ollama Instances (Multi-GPU)

*Because one GPU is for amateurs.*

See [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) for complete multi-GPU setup.

Quick example:

```bash
# GPU 0 - RTX 5060 Ti (the big gun)
CUDA_VISIBLE_DEVICES=0 OLLAMA_HOST=0.0.0.0:11434 ollama serve &

# GPU 1 - RTX 3050 (the sidekick)
CUDA_VISIBLE_DEVICES=1 OLLAMA_HOST=0.0.0.0:11435 ollama serve &

# Configure Boon-Tube-Daemon to use first instance
LLM_OLLAMA_HOST=http://localhost
LLM_OLLAMA_PORT=11434
```

### Model Performance Tuning

*Squeeze every last token per second out of your hardware.*

```bash
# Keep model loaded in VRAM (faster repeat requests)
# -1 means "keep it loaded forever, I have the VRAM"
export OLLAMA_KEEP_ALIVE=-1

# Increase context window (more memory = more context)
export OLLAMA_NUM_CTX=4096

# Adjust thread count for CPU inference
# More threads ≠ always faster. Test and find your sweet spot.
export OLLAMA_NUM_THREAD=8
```

---

*"The whole problem with the world is that fools and fanatics are always so certain of themselves, and wiser people so full of doubts." - Bertrand Russell*

*But when it comes to model selection, I'm pretty certain: use Gemma3.*

### Security Best Practices

1. **Firewall Rules:**
   ```bash
   # Only allow from specific subnet
   sudo ufw allow from 192.168.1.0/24 to any port 11434
   ```

2. **Reverse Proxy (HTTPS):**
   ```nginx
   server {
       listen 443 ssl;
       server_name ollama.example.com;
       
       location / {
           proxy_pass http://localhost:11434;
           proxy_set_header Host $host;
       }
   }
   ```

3. **Authentication:**
   - Ollama doesn't have built-in auth
   - Use reverse proxy with auth (nginx/traefik)
   - Or use VPN/Tailscale for network access

## Additional Resources

- **Ollama Website:** https://ollama.com
- **Model Library:** https://ollama.com/library
- **FrankenLLM (Multi-GPU):** https://github.com/ChiefGyk3D/FrankenLLM
- **Boon-Tube-Daemon README:** [../README.md](../README.md)

## Questions?

Open an issue on [GitHub](https://github.com/ChiefGyk3D/Boon-Tube-Daemon/issues) or check the main documentation!
