# 🦙 Ollama + Classic AutoGPT — Complete Offline Setup Guide
> For: Mumeen (ONIMIX TECH) | Created: April 2026

---

## 📊 Hardware Requirements at a Glance

| Model Size | RAM Needed | Disk Space | GPU VRAM | Best For |
|-----------|-----------|------------|----------|----------|
| **7-8B** (llama3.1:8b) | **8 GB minimum**, 16 GB recommended | ~5 GB | 6-8 GB | Basic tasks, fast responses, low-end PCs |
| **13B** (llama3.1:13b) | **16 GB minimum**, 32 GB recommended | ~8 GB | 10-12 GB | Better reasoning, good balance |
| **70B** (llama3.1:70b) | **64 GB minimum** | ~40 GB | 40+ GB | Near-GPT-4 quality, needs beefy machine |
| **Mistral 7B** | **8 GB minimum**, 16 GB recommended | ~4.5 GB | 6 GB | Fast, efficient, good for agents |
| **DeepSeek Coder V2** | **16 GB minimum** | ~9 GB | 10 GB | Code-heavy tasks |
| **Qwen2.5:14b** | **16 GB minimum** | ~9 GB | 10 GB | Excellent function calling |

### 🎯 My Recommendation for You
**Start with `llama3.1:8b` or `mistral:7b`** — they run on most laptops with 8-16 GB RAM.
If you have 16+ GB RAM, try `qwen2.5:14b` — it has the BEST function calling support (critical for AutoGPT agents).

### Minimum PC Specs
- **CPU**: Any modern 4-core processor (Intel i5/Ryzen 5 or better)
- **RAM**: 8 GB absolute minimum (16 GB recommended)
- **Disk**: 20 GB free space (for Ollama + 1-2 models)
- **GPU**: Optional but speeds things up 3-10x
  - NVIDIA: GTX 1060+ (6GB VRAM) with CUDA
  - AMD: RX 6600+ with ROCm (Linux only)
  - Apple M1/M2/M3: Works great natively
- **OS**: Windows 10/11, macOS 12+, or Linux

---

## 🔧 Step 1: Install Ollama

### Windows
1. Go to **https://ollama.com/download**
2. Download the Windows installer (.exe)
3. Run the installer — it installs to `C:\Users\<you>\AppData\Local\Ollama`
4. Ollama runs as a background service automatically
5. Open **Command Prompt** or **PowerShell** and verify:
   ```
   ollama --version
   ```

### macOS
```bash
# Option A: Download from https://ollama.com/download
# Option B: Using Homebrew
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Verify Installation
```bash
ollama --version
# Should show something like: ollama version 0.x.x
```

---

## 🧠 Step 2: Download a Model

```bash
# Recommended starter (4.7 GB download, runs on 8GB RAM)
ollama pull llama3.1:8b

# Better for agents if you have 16GB+ RAM (9 GB download)
ollama pull qwen2.5:14b

# Alternative lightweight option (4.1 GB)
ollama pull mistral:7b

# For coding tasks
ollama pull deepseek-coder-v2:16b
```

### Verify Model Works
```bash
# Quick test
ollama run llama3.1:8b "Say hello in one sentence"

# Check it's serving the API
curl http://localhost:11434/v1/models
```

You should see your model listed. Ollama automatically serves an **OpenAI-compatible API** on `http://localhost:11434`.

---

## 📦 Step 3: Clone Classic AutoGPT

```bash
# Clone YOUR fork
git clone https://github.com/Onimix/AutoGPT.git
cd AutoGPT/classic

# Or if you already have it downloaded, just navigate to it
cd /path/to/AutoGPT/classic
```

---

## ⚙️ Step 4: Configure Classic AutoGPT for Ollama

### 4a. Create your .env file
```bash
# Copy the template
cp .env.template .env
```

### 4b. Edit .env with these settings
Open `.env` in any text editor (Notepad, VS Code, nano) and set:

```env
################################################################################
### OLLAMA / LOCAL LLM CONFIGURATION
################################################################################

# Point AutoGPT to Ollama's OpenAI-compatible API
OPENAI_API_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama

# OR use the llamafile provider (same protocol)
# LLAMAFILE_API_BASE=http://localhost:11434/v1

# Set your model names
SMART_LLM=llama3.1:8b
FAST_LLM=llama3.1:8b

# If using qwen2.5 (recommended for better agent behavior):
# SMART_LLM=qwen2.5:14b
# FAST_LLM=qwen2.5:14b

# Embeddings — use Ollama's built-in embedding model
EMBEDDING_MODEL=nomic-embed-text

################################################################################
### OPTIONAL SETTINGS
################################################################################

# Disable telemetry (offline mode)
DISABLE_TELEMETRY=true

# Workspace settings
RESTRICT_TO_WORKSPACE=true

# Browser (if you want web browsing to work)
# HEADLESS_BROWSER=true
# USE_WEB_BROWSER=chrome
```

### 4c. Pull the embedding model too
```bash
ollama pull nomic-embed-text
# This is small (~274 MB) and needed for memory/context
```

---

## 🐍 Step 5: Install Python Dependencies

```bash
# Make sure you have Python 3.10+
python --version

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Step 6: Run Classic AutoGPT

```bash
# Make sure Ollama is running first
ollama serve
# (On Windows, it's usually already running as a service)

# In another terminal, run AutoGPT
python -m autogpt
```

### First Run Checklist
1. ✅ Ollama is running (`curl http://localhost:11434/v1/models` returns models)
2. ✅ `.env` file is configured
3. ✅ Model is downloaded (`ollama list` shows your model)
4. ✅ Embedding model downloaded (`nomic-embed-text`)
5. ✅ Python venv activated
6. ✅ Dependencies installed

---

## ⚠️ Known Limitations (Important!)

### 1. Function Calling
- Most local models have **limited function calling** compared to GPT-4
- **Qwen2.5** and **Mistral** have the best function calling support
- Llama 3.1 supports it but sometimes formats responses incorrectly
- **Workaround**: AutoGPT Classic falls back to text parsing when function calling fails

### 2. Context Length
- Local 8B models: typically **8K-32K tokens** (vs GPT-4's 128K)
- This means AutoGPT may "forget" things in long sessions
- **Workaround**: Keep tasks focused and short

### 3. Speed
- CPU-only (no GPU): Expect **1-5 tokens/second** (slow but works)
- With GPU (6GB VRAM): **20-50 tokens/second** (usable)
- With strong GPU (12GB+ VRAM): **50-100+ tokens/second** (smooth)

### 4. Quality
- 8B models are roughly **GPT-3.5 level** — good for simple agent tasks
- 14B models approach **GPT-4-mini level** — decent agent behavior
- 70B models approach **GPT-4 level** — but need serious hardware

### 5. No Internet by Default
- Classic AutoGPT CAN browse the web if you configure a browser
- But the LLM itself is 100% offline — no API calls to OpenAI

### 6. Embeddings
- `nomic-embed-text` works well for memory/retrieval
- Quality is slightly below OpenAI's `text-embedding-3-small` but perfectly usable

---

## 🔄 Running Your VFL Scanners with Local AutoGPT

Since your VFL scanners are pure Python scripts (no LLM needed), you can run them directly:

```bash
# Navigate to your project
cd /path/to/onimix-vfl-elite

# Install requirements
pip install requests

# Set Telegram credentials
export TELEGRAM_BOT_TOKEN="8616919960:AAFY5dY8-MyOgahSKpVeDKD_ESPZVVJ-tb8"
export TELEGRAM_CHAT_ID="1745848158"

# Run all scanners
python scanners/run_all.py
```

**Note**: Your VFL scanners don't need AutoGPT or an LLM — they're standalone Python scripts. The LLM (via AutoGPT) would only be needed if you want an AI agent to DECIDE what to scan or modify strategies dynamically.

---

## 📱 Quick Reference Card

| Action | Command |
|--------|---------|
| Start Ollama | `ollama serve` |
| List models | `ollama list` |
| Pull new model | `ollama pull <model>` |
| Test model | `ollama run <model> "test"` |
| Check API | `curl http://localhost:11434/v1/models` |
| Run AutoGPT | `python -m autogpt` |
| Stop Ollama | `Ctrl+C` or stop the service |
| Update Ollama | Re-run installer from ollama.com |

---

## 💰 Total Cost: $0

Everything is free and open source:
- ✅ Ollama — free
- ✅ LLM models — free (open weights)
- ✅ Classic AutoGPT — free (MIT license)
- ✅ Your VFL scanners — your own code
- ✅ No API keys needed
- ✅ No internet needed (except for VFL scanner API calls to SportyBet)

---

## 🎯 TL;DR — Fastest Path

```bash
# 1. Install Ollama from https://ollama.com
# 2. Pull a model
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# 3. Clone and configure
git clone https://github.com/Onimix/AutoGPT.git
cd AutoGPT/classic
cp .env.template .env
# Edit .env: set OPENAI_API_BASE_URL=http://localhost:11434/v1

# 4. Install and run
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m autogpt
```

**Total disk space needed**: ~10 GB (Ollama + one 8B model + AutoGPT code)
**Total RAM needed**: 8 GB minimum, 16 GB recommended

---

*Guide created by AutoPilot for ONIMIX TECH | April 2026*
