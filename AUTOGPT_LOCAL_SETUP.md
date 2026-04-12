# 🚀 Run AutoGPT Platform Locally on Your PC

## What You Get
The full AutoGPT agent builder + runner on YOUR machine — same UI you use at agpt.co, but self-hosted. You can build, run, and schedule agents locally with zero cloud dependency.

---

## Prerequisites

| Tool | Install |
|------|---------|
| **Git** | [git-scm.com](https://git-scm.com/downloads) |
| **Docker Desktop** | [docker.com/get-started](https://www.docker.com/products/docker-desktop/) |
| **Node.js 18+** | [nodejs.org](https://nodejs.org/) |

> ⚠️ **Windows Users**: When installing Docker Desktop, choose **WSL 2** (NOT Hyper-V). Hyper-V causes database issues.

---

## Option 1: Quick Setup (Recommended)

### Mac / Linux
```bash
curl -fsSL https://setup.agpt.co/install.sh -o install.sh && bash install.sh
```

### Windows (PowerShell as Admin)
```powershell
powershell -c "iwr https://setup.agpt.co/install.bat -o install.bat; ./install.bat"
```

This handles everything — Docker, dependencies, config, and launch.

---

## Option 2: Manual Setup (Full Control)

### Step 1: Clone the repo
```bash
git clone https://github.com/Significant-Gravitas/AutoGPT.git
cd AutoGPT/autogpt_platform
```

### Step 2: Configure environment
```bash
cp .env.example .env
```
The defaults work out of the box. You only NEED to add API keys for the LLM providers you want to use (OpenAI, Anthropic, etc.).

### Step 3: Build & launch
```bash
docker compose up -d --build
```
This starts the backend server, database, and frontend. First build takes 5-10 minutes.

### Step 4: Open the UI
Visit **http://localhost:3000** in your browser.

You now have the full AutoGPT platform running locally! 🎉

---

## Adding Your API Keys

Edit the `.env` file to add your LLM keys:

```env
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

Then restart:
```bash
docker compose down
docker compose up -d
```

---

## Importing Your VFL Scanner Agents

Once your local platform is running, you can recreate your 4 agents:

1. Open **http://localhost:3000**
2. Click **"Create Agent"**
3. Add an **"Execute Python Code"** block
4. Paste your scanner code from GitHub: `github.com/Onimix/onimix-vfl-elite`
5. Set up cron schedules:
   - Layer 1 & Layer 2: Every 5 minutes (`*/5 * * * *`)
   - Mega & Feedback: Every 30 minutes (`*/30 * * * *`)

Your 4 agents:
- `layer1_v6_feedback.py` — ELITE Scanner
- `layer2_v3_feedback.py` — 12-Layer ONIMIX Engine
- `mega_v3_feedback.py` — Mega Prematch Accumulator
- `feedback_engine_v2.py` — Learning/Feedback System

---

## Keeping It Running

### Start platform (after reboot)
```bash
cd AutoGPT/autogpt_platform
docker compose up -d
```

### Stop platform
```bash
docker compose down
```

### Update to latest version
```bash
git pull
docker compose up -d --build
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Docker won't start on Windows | Make sure WSL 2 is enabled, not Hyper-V |
| Port 3000 already in use | Change the port in `.env` or stop the other service |
| Build fails on Mac M1/M2/M3 | Run `getconf PAGESIZE` — if it shows 16384, see ARM fix in docs |
| Database unhealthy | Delete volumes: `docker compose down -v` then rebuild |

---

## Alternative: Just Run Your Scanners Locally (Simpler)

If you just want the VFL scanners without the full platform UI:

```bash
git clone https://github.com/Onimix/onimix-vfl-elite.git
cd onimix-vfl-elite
pip install requests
python scanners/run_all.py
```

This runs all 4 scanners + feedback engine with zero dependencies except Python.

---

## Resources
- [AutoGPT GitHub](https://github.com/Significant-Gravitas/AutoGPT)
- [Official Docs](https://docs.agpt.co/platform/getting-started/)
- [Your VFL Scanner Repo](https://github.com/Onimix/onimix-vfl-elite)
