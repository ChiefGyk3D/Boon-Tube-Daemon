# LLM Model Recommendations by Hardware

🎯 **Choose the right model for your GPU** - Maximize quality within your VRAM limits.

## Overview

*Or: A Guide to Buying More GPU Than You Need to Generate Social Media Posts*

Look, here's the thing about AI models and VRAM - it's like buying a car. You *could* get a sensible Honda Civic, but some asshole at NVIDIA convinced you that you need a Ferrari to drive to the grocery store. And now you've got a $2,000 graphics card generating "New video! Check it out! 🎬" 

The good news? Boon-Tube-Daemon actually uses that expensive silicon. The bad news? You're still using a supercomputer to write notifications about cat videos. Welcome to 2026.

**Key Insight:** Bigger models = better instruction following. It's that simple. The goal is to cram the fattest model possible into your GPU without it crying for help.

Think of VRAM like a hot dog eating contest. You want to shove as many parameters in there as physically possible before everything comes back up. Except instead of vomiting, you get "CUDA out of memory" errors. Same energy, different consequences.

---

## Quick Reference Table

*For those of you with the attention span of a goldfish (so, everyone in 2026):*

| VRAM | Primary Model | Backup Model | Quality | Speed |
|------|---------------|--------------|---------|-------|
| **4GB** | `gemma3:2b` | `phi3:mini` | ⭐⭐⭐ | ⚡⚡⚡ |
| **6GB** | `gemma3:4b` | `qwen2.5:3b` | ⭐⭐⭐⭐ | ⚡⚡⚡ |
| **8GB** | `gemma3:4b` | `qwen2.5:7b` | ⭐⭐⭐⭐⭐ | **⚡⚡⚡ ~1s** |
| **12GB** | `gemma3:4b` | `llama3.1:8b` | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ |
| **16GB** | `gemma3:12b` | `qwen2.5:14b` | ⭐⭐⭐⭐⭐+ | **⚡⚡⚡ ~1.3s** |
| **24GB+** | `gemma3:27b` | `qwen2.5:32b` | ⭐⭐⭐⭐⭐+ | ⚡⚡ |

> **🏆 January 2026 Benchmark Winner:** Gemma3 models are **6-10x faster** than Qwen2.5 for notifications (~1s vs ~11s). For social media posts, speed wins.

---

## Complete Model Comparison Table

*Every model you might consider, all in one place. You're welcome.*

### All Models At-A-Glance

| Model | Params | VRAM | Speed | Quality | Instruction | Best For |
|-------|--------|------|-------|---------|-------------|----------|
| **Gemma 3 Family** |||||||
| `gemma3:2b` | 2B | ~2GB | ~1.5s ⚡ | ⭐⭐⭐ | Good | CPU/4GB GPU |
| `gemma3:4b` | 4B | ~3GB | **~1.0s** 🏆 | ⭐⭐⭐⭐⭐ | Very Good | **6-12GB GPU (RECOMMENDED)** |
| `gemma3:12b` | 12B | ~8GB | ~1.3s ⚡ | ⭐⭐⭐⭐⭐+ | Excellent | **16GB GPU (PREMIUM)** |
| `gemma3:27b` | 27B | ~17GB | ~2s | ⭐⭐⭐⭐⭐+ | Excellent | 24GB+ GPU |
| **Qwen 2.5 Family** |||||||
| `qwen2.5:1.5b` | 1.5B | ~1GB | ~2s | ⭐⭐ | Good | Minimal systems |
| `qwen2.5:3b` | 3B | ~2GB | ~4s | ⭐⭐⭐ | Excellent | 4-6GB GPU |
| `qwen2.5:7b` | 7B | ~5GB | ~11s | ⭐⭐⭐⭐⭐ | **Exceptional** | 8GB GPU (precise tasks) |
| `qwen2.5:14b` | 14B | ~9GB | ~11s | ⭐⭐⭐⭐⭐+ | **Exceptional** | 16GB GPU |
| `qwen2.5:32b` | 32B | ~20GB | ~15s | ⭐⭐⭐⭐⭐++ | Near-Perfect | 24GB+ GPU |
| **Qwen 3 Family** ⚠️ *Thinking Mode* |||||||
| `qwen3:4b` | 4B | ~2.5GB | ~6s* | ⭐⭐⭐⭐⭐ | Excellent | Experimental |
| `qwen3:8b` | 8B | ~5GB | ~8s* | ⭐⭐⭐⭐⭐ | Excellent | Experimental |
| `qwen3:14b` | 14B | ~9GB | ~10s* | ⭐⭐⭐⭐⭐+ | Excellent | Experimental |
| **LLaMA 3 Family** |||||||
| `llama3.2:1b` | 1B | ~1GB | ~1s | ⭐⭐ | Fair | Speed over quality |
| `llama3.2:3b` | 3B | ~2GB | ~2s | ⭐⭐⭐ | Good | Fast backup |
| `llama3.1:8b` | 8B | ~5GB | ~8s | ⭐⭐⭐⭐ | Good | General purpose |
| `llama3.1:70b` | 70B | ~40GB | ~30s | ⭐⭐⭐⭐⭐+ | Excellent | Multi-GPU only |
| **Mistral Family** |||||||
| `mistral:7b` | 7B | ~4GB | ~7s | ⭐⭐⭐⭐ | Good | French efficiency |
| `mixtral:8x7b` | 47B MoE | ~26GB | ~12s | ⭐⭐⭐⭐⭐+ | Very Good | 24GB+ (MoE) |
| **Microsoft Phi** |||||||
| `phi3:mini` | 3.8B | ~2GB | ~2s | ⭐⭐⭐ | Good | CPU/Low VRAM |
| `phi3:medium` | 14B | ~8GB | ~8s | ⭐⭐⭐⭐ | Good | 12GB GPU |
| **Other Notable Models** |||||||
| `openhermes:latest` | 7B | ~4GB | ~7s | ⭐⭐⭐⭐ | Very Good | Instruction following |
| `neural-chat:7b` | 7B | ~4GB | ~7s | ⭐⭐⭐⭐ | Good | Conversational |
| `zephyr:7b` | 7B | ~4GB | ~7s | ⭐⭐⭐⭐ | Good | DPO-tuned |
| `solar:10.7b` | 10.7B | ~6GB | ~9s | ⭐⭐⭐⭐ | Good | General purpose |
| `nous-hermes2:10.7b` | 10.7B | ~6GB | ~9s | ⭐⭐⭐⭐ | Good | Creative tasks |
| `deepseek-coder:6.7b` | 6.7B | ~4GB | ~6s | ⭐⭐⭐⭐ | Good | **Code only** |

**Legend:**
- 🏆 = Benchmark champion for notifications
- ⚡ = Sub-2 second response time
- ⚠️ = Requires `LLM_ENABLE_THINKING_MODE=true`
- *Speed with thinking mode enabled and token multiplier

### Speed vs Quality Trade-offs

```
SPEED (Response Time)                    QUALITY (Output)
─────────────────────────────────────────────────────────────
⚡ FAST (<2s)          │ gemma3:2b, gemma3:4b, gemma3:12b, llama3.2:3b, phi3:mini
   MODERATE (2-8s)     │ mistral:7b, openhermes, neural-chat, zephyr, llama3.1:8b
   SLOW (8-15s)        │ qwen2.5:7b, qwen2.5:14b, qwen3 family, solar, nous-hermes2
🐌 VERY SLOW (15s+)    │ qwen2.5:32b, llama3.1:70b, mixtral

⭐⭐⭐     BASIC      │ gemma3:2b, llama3.2:1b, qwen2.5:1.5b
⭐⭐⭐⭐   GOOD       │ llama3.2:3b, phi3:mini, mistral:7b, neural-chat, zephyr
⭐⭐⭐⭐⭐ EXCELLENT  │ gemma3:4b, gemma3:12b, qwen2.5:7b, llama3.1:8b
⭐⭐⭐⭐⭐+PREMIUM    │ qwen2.5:14b, qwen3:14b, gemma3:27b, qwen2.5:32b
```

### Recommendation Summary

| Your Priority | Choose This | Why |
|---------------|-------------|-----|
| **Speed** 🏎️ | `gemma3:4b` | ~1s response, great quality |
| **Quality** 📝 | `qwen2.5:14b` | Best instruction following |
| **Balance** ⚖️ | `gemma3:12b` | Fast AND excellent quality |
| **Budget GPU** 💰 | `gemma3:2b` | Works on 4GB VRAM |
| **No GPU** 🖥️ | `phi3:mini` | CPU-friendly |
| **Experimental** 🧪 | `qwen3:4b` | Thinking mode, cutting edge |

---

## Detailed Recommendations by VRAM Tier

*Because apparently we need to categorize everything. Here's your GPU caste system:*

### 4GB VRAM (GTX 1650, RTX 3050 Mobile)

**The "I'm Just Happy to Be Here" Tier**

You've got 4GB of VRAM. That's adorable. That's what flagship phones had in 2020. 
You're basically asking a calculator to write poetry, but you know what? It'll fucking work.

Just expect some CPU offloading - which is tech speak for "your GPU gave up and your CPU is picking up the slack."

| Model | Size | Quality | Speed | Notes |
|-------|------|---------|-------|-------|
| `gemma3:2b` | ~2GB | ⭐⭐⭐ | ~1.5s ⚡ | Best option |
| `phi3:mini` | ~2GB | ⭐⭐⭐ | ~2s | Good alternative |
| `llama3.2:3b` | ~2GB | ⭐⭐⭐ | ~2s | Fast |

**Recommended Configuration:**
```bash
LLM_MODEL=gemma3:2b
```

---

### 6-8GB VRAM (RTX 3050, RTX 3060, RTX 4060)

**The "Sweet Spot" Tier**

8GB is where the magic happens. And thanks to Google's Gemma 3, you can generate 
notifications in about ONE SECOND. ONE. SECOND.

Meanwhile, some models take 11 seconds to write "New video is up! Check it out!" 
That's enough time to make a sandwich. Choose wisely.

| Model | Size | Quality | Speed | Notes |
|-------|------|---------|-------|-------|
| **`gemma3:4b`** | ~3GB | ⭐⭐⭐⭐⭐ | **~1.0s** 🏆 | **RECOMMENDED** |
| `qwen2.5:7b` | ~5GB | ⭐⭐⭐⭐⭐ | ~11s | Great instruction following |
| `llama3.1:8b` | ~5GB | ⭐⭐⭐⭐ | ~8s | Good general purpose |

**Why Gemma3:4b?** 

Benchmark testing showed Gemma3:4b completing notifications in ~1 second while Qwen2.5:7b took ~11 seconds. That's a 10x speed difference. For generating social media posts, speed wins.

**Recommended Configuration:**
```bash
LLM_MODEL=gemma3:4b
```

---

### 16GB VRAM (RTX 4080, RTX 5060 Ti, RX 7800 XT)

**The "I Made Some Good Life Choices" Tier**

16GB. Now you're playing with the big boys. With Gemma3:12b, you get premium 
quality at near-instant speeds (~1.3 seconds).

| Model | Size | Quality | Speed | Notes |
|-------|------|---------|-------|-------|
| **`gemma3:12b`** | ~8GB | ⭐⭐⭐⭐⭐+ | **~1.3s** 🏆 | **PREMIUM CHOICE** |
| `qwen2.5:14b` | ~9GB | ⭐⭐⭐⭐⭐+ | ~11s | Exceptional instruction following |

**Recommended Configuration:**
```bash
LLM_MODEL=gemma3:12b
```

---

### 24GB+ VRAM (RTX 3090, RTX 4090, A100)

**The "I Either Mine Crypto, Do ML Research, or Have a Problem" Tier**

24 gigabytes of video memory. You magnificent bastard.

| Model | Size | Quality | Speed | Notes |
|-------|------|---------|-------|-------|
| `gemma3:27b` | ~17GB | ⭐⭐⭐⭐⭐+ | ~2s | Maximum quality |
| `qwen2.5:32b` | ~20GB | ⭐⭐⭐⭐⭐++ | ~15s | Near-perfect |

---

## Qwen3 Thinking Mode

**What is it?** Qwen3 models have a "thinking mode" where they show their reasoning before giving an answer. It's like that kid in class who has to explain their entire thought process.

**The Problem:** The thinking consumes tokens and can leave the actual content field empty.

**The Solution:** Boon-Tube-Daemon supports thinking mode extraction:

```bash
LLM_MODEL=qwen3:4b
LLM_ENABLE_THINKING_MODE=true
LLM_THINKING_TOKEN_MULTIPLIER=4.0
```

**Should you use it?** Probably not for notifications. Gemma3 is faster and doesn't philosophize about hashtags.

---

## Multi-GPU Setups (FrankenLLM)

Got multiple GPUs? Maybe an old one and a new one? Different brands? Check out [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) for running multiple Ollama instances.

```bash
# Port 11434 = GPU 0 (RTX 5060 Ti) - Big models
# Port 11435 = GPU 1 (RTX 3050) - Fast models
```

---

## See Also

- [Ollama Setup Guide](./ollama-setup.md) - Installation and configuration
- [FrankenLLM](https://github.com/ChiefGyk3D/FrankenLLM) - Multi-GPU setup
- [Ollama Model Library](https://ollama.com/library) - Browse all models

---

## The Bottom Line

Use **gemma3:4b** (or gemma3:12b if you have 16GB). They're fast, they're reliable, and they don't need therapy to write a notification.

As George Carlin might say: "We've managed to create artificial intelligence that can write social media posts in less time than it takes you to come up with an excuse for why you didn't post. The robots are already better at your job."
