# Ollama Setup Guide for Boon-Tube-Daemon

This guide walks you through setting up Ollama for privacy-first, cost-free AI-powered notifications in Boon-Tube-Daemon.

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

**Ollama** provides local LLM hosting with several advantages:

✅ **Privacy-First:** Your video data never leaves your network  
✅ **Zero API Costs:** Unlimited usage with no per-request fees  
✅ **No Rate Limits:** Process as many videos as your hardware can handle  
✅ **Fast Response:** Local inference with proper hardware  
✅ **Offline Capable:** Works without internet connection  

**Comparison with Google Gemini:**

| Feature | Ollama | Google Gemini |
|---------|--------|---------------|
| Cost | Free (local hardware) | Free tier limited, then paid |
| Privacy | Complete (local only) | Data sent to Google |
| Rate Limits | None | 15 RPM (free tier) |
| Setup Complexity | Medium | Easy |
| Hardware Required | Yes (GPU recommended) | No |

## Quick Start

### 5-Minute Setup

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
   # Recommended: Fast, good quality
   ollama pull gemma2:2b
   
   # Alternative: Higher quality
   ollama pull gemma3:4b
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
   LLM_MODEL=gemma2:2b
   
   # Enable enhanced notifications
   LLM_ENHANCE_NOTIFICATIONS=true
   ```

5. **Test it:**
   ```bash
   python3 tests/test_ollama.py
   ```

That's it! Boon-Tube-Daemon will now use Ollama to generate unique, engaging posts for each social platform.

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

### Recommended Models by Use Case

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| **gemma2:2b** | 2B | ⚡⚡⚡ | ⭐⭐⭐ | **Best balance** (recommended) |
| gemma3:4b | 4B | ⚡⚡ | ⭐⭐⭐⭐ | Higher quality, slight slower |
| llama3.2:3b | 3B | ⚡⚡⚡ | ⭐⭐⭐ | Fast alternative to Gemma |
| qwen2.5:3b | 3B | ⚡⚡⚡ | ⭐⭐⭐⭐ | Technical content |
| mistral:7b | 7B | ⚡ | ⭐⭐⭐⭐⭐ | Best quality, needs 8GB+ VRAM |
| phi3:3b | 3B | ⚡⚡⚡ | ⭐⭐⭐ | Very fast (Microsoft) |

### Hardware Requirements

**Minimum:**
- CPU: Modern multi-core processor
- RAM: 8GB system RAM
- GPU: Optional (CPU inference works)

**Recommended:**
- GPU: NVIDIA/AMD with 4GB+ VRAM
- RAM: 16GB system RAM
- Storage: 5-10GB for models

**Optimal:**
- GPU: NVIDIA RTX 3060+ or AMD 6000+ series
- RAM: 32GB system RAM
- VRAM: 8GB+ for larger models

### Pulling Models

```bash
# Browse available models
# https://ollama.com/library

# Search for models (requires ollama >= 0.1.26)
ollama search llama
ollama search gemma

# List installed models
ollama list

# Pull a model
ollama pull gemma2:2b

# Remove a model
ollama rm gemma2:2b
```

## Testing

### Quick Test

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Should return:
# {"models":[{"name":"gemma2:2b",...}]}
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
✓ Model: gemma2:2b

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

### "Failed to connect to Ollama"

**Solution:**

```bash
# 1. Check Ollama is running
ps aux | grep ollama
# Or: systemctl status ollama (if using systemd)

# 2. Test local connection
curl http://localhost:11434/api/tags

# 3. If remote server, ensure firewall allows port 11434
sudo ufw allow 11434/tcp

# 4. Start Ollama with remote access
OLLAMA_HOST=0.0.0.0 ollama serve

# 5. Check from Boon-Tube-Daemon host
curl http://YOUR_SERVER_IP:11434/api/tags
```

### "Model not found"

**Solution:**

```bash
# Pull the model
ollama pull gemma2:2b

# Verify it's available
ollama list

# Check model name matches .env
# LLM_MODEL=gemma2:2b  (exact match required)
```

### "Ollama Python client not installed"

**Solution:**

```bash
# Install Ollama client
pip install ollama

# Or update requirements
pip install -r requirements.txt
```

### Slow Generation Times

**Causes and solutions:**

1. **CPU Inference (no GPU):**
   - Expected: 30-60s per message
   - Solution: Add GPU for 2-5s generation

2. **Model Too Large:**
   - Try smaller model: `ollama pull gemma2:2b`
   - Switch from 7B → 3B → 2B models

3. **Insufficient VRAM:**
   - Monitor GPU usage: `nvidia-smi` or `rocm-smi`
   - Use smaller model or reduce concurrent requests

4. **Network Latency (remote server):**
   - Check ping: `ping YOUR_OLLAMA_SERVER`
   - Consider running Ollama locally

### GPU Not Detected

**NVIDIA:**

```bash
# Check NVIDIA drivers
nvidia-smi

# Reinstall if needed
sudo apt install nvidia-driver-XXX

# Verify CUDA
ollama run gemma2:2b "test"
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

### Systemd Service (Auto-Start)

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

See [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) for complete setup.

Quick example:

```bash
# GPU 0 (NVIDIA)
CUDA_VISIBLE_DEVICES=0 OLLAMA_HOST=0.0.0.0:11434 ollama serve &

# GPU 1 (AMD)
HSA_OVERRIDE_GFX_VERSION=10.3.0 OLLAMA_HOST=0.0.0.0:11435 ollama serve &

# Configure Boon-Tube-Daemon to use first instance
LLM_OLLAMA_HOST=http://localhost
LLM_OLLAMA_PORT=11434
```

### Model Performance Tuning

```bash
# Keep model loaded in VRAM (faster repeat requests)
export OLLAMA_KEEP_ALIVE=-1

# Increase context window
export OLLAMA_NUM_CTX=4096

# Adjust thread count for CPU inference
export OLLAMA_NUM_THREAD=8
```

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
