# ONIMIX VFL Scanner Scripts

Autonomous prediction system for SportyBet Virtual Football League (VFL).

## Scripts

| Script | Purpose | Interval |
|--------|---------|----------|
| `layer1_v6_feedback.py` | ELITE matchup scanner (353 verified matchups, 80-98% hit rates) | Every 5 min |
| `layer2_v3_feedback.py` | 12-Layer ONIMIX scoring engine (O0.5, O1.5, BTTS, trend, momentum) | Every 5 min |
| `mega_v3_feedback.py` | 3-tier prematch accumulator (ULTRA/PREMIUM/MEGA) | Every 30 min |
| `feedback_engine_v2.py` | Learning system (blacklist, penalties, cold hours) | Every 30 min |
| `run_all.py` | Local runner - starts all 4 scripts in threads | One-time |

## Quick Start

```bash
pip install requests
python run_all.py
```

## How It Works

1. **Layer 1** scans live VFL matches, filters through 353 ELITE matchups with verified 80-98% Over 1.5 hit rates
2. **Layer 2** applies 12-layer scoring (LOCK ≥11pts, PICK ≥9pts) with ONIMIX logic
3. **Mega** probes 10 rounds ahead via booking API for prematch accumulator picks
4. **Feedback Engine** learns from failures - generates blacklists, penalties, and cold-hour filters

All alerts sent to Telegram with one-tap SportyBet booking codes.

## Coverage

5 leagues: England, Spain, Italy, Germany, France VFL
- 353 ELITE matchups verified across 73,081+ real matches
- ≥92% ELITE = 85% actual hit rate
- ≥88% ELITE = 81% actual hit rate

See [LOCAL_SETUP_GUIDE.md](../LOCAL_SETUP_GUIDE.md) for full setup instructions.
