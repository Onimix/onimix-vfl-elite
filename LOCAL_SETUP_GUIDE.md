# 🏠 ONIMIX VFL Prediction System — Local Setup Guide

## ⚡ Quick Summary
You have 4 Python scripts that scan SportyBet VFL matches, predict Over 1.5 Goals,
and send alerts with booking codes to your Telegram bot. Here's how to run them
on your own computer (Windows, Mac, or Linux).

---

## 📋 Step 1: Install Python

### Windows:
1. Go to https://python.org/downloads
2. Download Python 3.10+ (click the big yellow button)
3. **IMPORTANT**: Check ✅ "Add Python to PATH" during install
4. Open Command Prompt (Win+R → type `cmd` → Enter)
5. Verify: `python --version`

### Mac:
```bash
brew install python3
# or download from python.org
```

### Linux (Ubuntu/Debian):
```bash
sudo apt update && sudo apt install python3 python3-pip -y
```

---

## 📋 Step 2: Install Dependencies

Open terminal/command prompt and run:
```bash
pip install requests
```
That's it — `requests` is the only external dependency. Everything else uses Python built-ins.

---

## 📋 Step 3: Download the Scripts

Create a folder on your computer, e.g. `C:\ONIMIX_VFL` (Windows) or `~/onimix_vfl` (Mac/Linux).

Download these 4 files into that folder:

| Script | dpaste Link | What It Does |
|--------|-------------|--------------|
| `layer1_v6_feedback.py` | https://dpaste.com/HDQYCAZ53.txt | ELITE Scanner — finds 80-98% hit rate matchups |
| `layer2_v3_feedback.py` | https://dpaste.com/DWPGS225C.txt | 12-Layer Engine — deep scoring with 12 factors |
| `mega_v3_feedback.py` | https://dpaste.com/4K3E5PVNX.txt | Mega Accumulator — 3-tier booking codes |
| `feedback_engine_v2.py` | https://dpaste.com/8EG7EL7ZL.txt | Feedback Engine — learns from failed picks |

### How to download:
1. Click each link above
2. Select ALL the text (Ctrl+A)
3. Copy (Ctrl+C)
4. Paste into a new file with the correct name
5. Save as `.py` file

**Or use command line:**
```bash
# Windows (PowerShell):
Invoke-WebRequest -Uri "https://dpaste.com/HDQYCAZ53.txt" -OutFile "layer1_v6_feedback.py"
Invoke-WebRequest -Uri "https://dpaste.com/DWPGS225C.txt" -OutFile "layer2_v3_feedback.py"
Invoke-WebRequest -Uri "https://dpaste.com/4K3E5PVNX.txt" -OutFile "mega_v3_feedback.py"
Invoke-WebRequest -Uri "https://dpaste.com/8EG7EL7ZL.txt" -OutFile "feedback_engine_v2.py"

# Mac/Linux:
curl -o layer1_v6_feedback.py https://dpaste.com/HDQYCAZ53.txt
curl -o layer2_v3_feedback.py https://dpaste.com/DWPGS225C.txt
curl -o mega_v3_feedback.py https://dpaste.com/4K3E5PVNX.txt
curl -o feedback_engine_v2.py https://dpaste.com/8EG7EL7ZL.txt
```

---

## 📋 Step 4: Run the Scripts

### One-time manual scan:
```bash
# Run Layer 1 (ELITE picks)
python layer1_v6_feedback.py

# Run Layer 2 (12-Layer deep scoring)
python layer2_v3_feedback.py

# Run Mega Accumulator (3-tier booking codes)
python mega_v3_feedback.py

# Run Feedback Engine (learn from failures)
python feedback_engine_v2.py
```

Each script will:
1. Scan live SportyBet VFL matches
2. Find qualifying Over 1.5 Goals picks
3. Generate booking codes on SportyBet
4. Send alerts to your Telegram bot (@Virtualonimix_bot)
5. Print results in terminal

---

## 📋 Step 5: Automate (Run on Schedule)

### Windows — Task Scheduler:
1. Open Task Scheduler (search in Start menu)
2. Click "Create Basic Task"
3. Name: `VFL Layer 1 Scanner`
4. Trigger: Daily, repeat every **5 minutes** for 24 hours
5. Action: Start a program
   - Program: `python`
   - Arguments: `C:\ONIMIX_VFL\layer1_v6_feedback.py`
6. Repeat for Layer 2 (every 5 min) and Mega (every 30 min)

### Mac/Linux — Cron:
```bash
crontab -e
```
Add these lines:
```cron
# Layer 1 ELITE Scanner — every 5 minutes
*/5 * * * * cd ~/onimix_vfl && python3 layer1_v6_feedback.py >> /tmp/vfl_layer1.log 2>&1

# Layer 2 12-Layer Engine — every 5 minutes
*/5 * * * * cd ~/onimix_vfl && python3 layer2_v3_feedback.py >> /tmp/vfl_layer2.log 2>&1

# Mega Accumulator — every 30 minutes
*/30 * * * * cd ~/onimix_vfl && python3 mega_v3_feedback.py >> /tmp/vfl_mega.log 2>&1

# Feedback Engine — every 30 minutes
*/30 * * * * cd ~/onimix_vfl && python3 feedback_engine_v2.py >> /tmp/vfl_feedback.log 2>&1
```

### Alternative — Simple Loop Script (easiest!):

Create `run_all.py`:
```python
import subprocess, time, threading

def run_loop(script, interval_min):
    while True:
        try:
            subprocess.run(["python3", script], timeout=120)
        except Exception as e:
            print(f"[ERROR] {script}: {e}")
        time.sleep(interval_min * 60)

# Start all scanners
threading.Thread(target=run_loop, args=("layer1_v6_feedback.py", 5), daemon=True).start()
threading.Thread(target=run_loop, args=("layer2_v3_feedback.py", 5), daemon=True).start()
threading.Thread(target=run_loop, args=("mega_v3_feedback.py", 30), daemon=True).start()
threading.Thread(target=run_loop, args=("feedback_engine_v2.py", 30), daemon=True).start()

print("🚀 All scanners running! Press Ctrl+C to stop.")
while True:
    time.sleep(60)
```

Then just run:
```bash
python run_all.py
```
All 4 scanners run in one terminal! Press Ctrl+C to stop everything.

---

## 📋 Step 6: Keep Your PC Running (Optional)

For 24/7 scanning while your PC sleeps:

### Option A — Use a VPS ($5/month):
1. Get a DigitalOcean/Vultr VPS ($5/month, Ubuntu)
2. SSH in, install Python, upload scripts
3. Run with: `nohup python3 run_all.py &`
4. Or use `screen`: `screen -S vfl` → run script → detach with Ctrl+A+D

### Option B — Keep using AutoGPT agents (current setup):
Your 4 agents on AutoGPT are already running 24/7 for you!
This local setup is for backup/testing or if you want full control.

---

## 🔑 Important Notes

1. **Telegram alerts work instantly** — same bot, same chat, no extra setup
2. **Booking codes are generated automatically** — click them in Telegram to open SportyBet
3. **Feedback file location**: Scripts save to `/tmp/vfl_scanner_feedback.json`
   - On Windows, change `/tmp/` to `C:\temp\` or your preferred folder
4. **dpaste links expire ~30 days** — save the scripts locally now!
5. **No API key needed** — SportyBet VFL API is public
6. **ELITE data is embedded** — all 353 matchups are inside the scripts, no external files needed

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: requests` | Run `pip install requests` |
| `python not found` | Use `python3` instead of `python` |
| No Telegram alerts | Check internet connection |
| Booking code fails | SportyBet may be rate-limiting, wait 1 min |
| Windows path error | Use `\\` or raw strings: `r"C:\path"` |
| Script hangs | SportyBet API may be slow, wait 30sec |

---

## 📊 System Architecture (What You're Running)

```
┌─────────────────────────────────────────────────┐
│              YOUR COMPUTER (Local)               │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Layer 1 v6  │  │  Layer 2 v3  │  Every 5min │
│  │ ELITE Scanner│  │ 12-Layer Eng │             │
│  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                     │
│  ┌──────┴───────┐  ┌──────┴───────┐             │
│  │  Mega v3     │  │  Feedback v2 │  Every 30min│
│  │ Accumulator  │  │  Engine      │             │
│  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                     │
│         ▼                  ▼                     │
│    ┌─────────────────────────────┐               │
│    │  /tmp/vfl_scanner_feedback  │ Shared file   │
│    └─────────────────────────────┘               │
└─────────────────┬───────────────────────────────┘
                  │ HTTP
                  ▼
        ┌─────────────────┐     ┌──────────────┐
        │  SportyBet API  │     │ Telegram Bot  │
        │ (scan + book)   │     │ @Virtualonimix│
        └─────────────────┘     └──────────────┘
```

---

## ✅ You're All Set!

- **AutoGPT agents**: Running 24/7 in the cloud (already active)
- **Local scripts**: Run anytime on your PC for testing or backup
- **Both send to same Telegram bot** — you'll get alerts from both

Questions? Just ask! 🚀
