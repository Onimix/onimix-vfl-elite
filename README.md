# ONIMIX VFL ELITE Prediction System v8

## 🔥 VFL is BACK ONLINE!
SportyBet Virtual Football League prediction system rebuilt with correct API endpoints.

## System Architecture
- **Layer 1 (ELITE)**: 690 verified ELITE matchups with ≥80% Over 1.5 hit rate from 11,822 fresh matches
- **Layer 2 (12-Layer)**: ONIMIX scoring engine (O0.5, O1.5, O2.5, BTTS, ATK, DEF, VEN, TRD, MOM, ELT, LGB, ODS)
- **MEGA**: 3-tier accumulator (ULTRA MEGA, MEGA MIX, FULL HOUSE) with booking codes
- **SRL Scanner**: Simulated Reality League predictions (separate system)

## API Endpoints (CORRECT)
- Sport: `sr:sport:202120001` (vFootball)
- Categories: `sv:category:202120001-5` (England/Spain/Italy/Germany/France)
- Tournaments: `sv:league:1-5`
- Results: `/api/ng/factsCenter/eventResultList`
- Upcoming: `/api/ng/factsCenter/wapConfigurableUpcomingEvents`
- Live: `/api/ng/factsCenter/wapConfigurableIndexLiveEvents`
- Booking: `POST /api/ng/orders/share` with `{"selections": [...]}`

## Stats (April 2026)
- 11,822 matches analyzed (7 days)
- 690 ELITE matchups (≥80% O1.5)
- 221 ULTRA matchups (≥90% O1.5)
- 96 team profiles across 5 leagues
- Overall O1.5 rate: 71.1%

## Files
| File | Description |
|------|-------------|
| `layer1_v8.py` | VFL ELITE Scanner (needs data files) |
| `layer2_v5.py` | VFL 12-Layer Engine (needs data files) |
| `mega_v5.py` | VFL MEGA Accumulator (needs data files) |
| `*_embedded.py` | Self-contained versions with embedded data |
| `run_all.py` | Local runner for all scanners |
| `vfl_elite_lookup.json` | 690 ELITE matchup database |
| `vfl_elite_fresh.json` | Full ELITE + PREMIUM data |
| `srl/` | SRL prediction system |

## Quick Start (Local)
```bash
pip install requests
python run_all.py
```

## Telegram Bot
- Bot: @Virtualonimix_bot
- Predictions delivered with booking codes every 10 minutes

## Deployed Agents (AutoGPT)
- ONIMIX VFL ELITE Scanner v8 (every 10 min)
- ONIMIX VFL 12-Layer Engine v5 (every 10 min)
- ONIMIX VFL MEGA Accumulator v5 (every 10 min)
- ONIMIX SRL ELITE Scanner v1 (every 10 min)
- SRL Data Collector v2 (every 15 min)
