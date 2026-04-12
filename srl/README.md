# ONIMIX SRL Prediction System

## Background
SportyBet replaced VFL (Virtual Football League) with SRL (Simulated Reality League).
All old VFL endpoints return 404. This is the new prediction system built from scratch.

**eFootball is excluded** — it's human-controlled (eSports), not algorithmic simulation.

## Data Foundation
- **1,518 SRL match results** extracted from 4 tournaments
- **57 team profiles** with O1.5 rates from real data
- **28 ELITE teams** with 80%+ Over 1.5 hit rate

## Backtest Results (1,518 matches)
| Tier | Matches | O1.5 Hit Rate |
|------|---------|---------------|
| ULTRA (85+) | 235 | **88.9%** |
| PREMIUM (75-84) | 389 | **78.7%** |
| STANDARD (65-74) | 80 | **71.2%** |

## Tournaments
- Premier League SRL (82% O1.5 — best league)
- LaLiga SRL (71% O1.5)
- Serie A SRL (71% O1.5)
- Turkey Super Lig SRL (76% O1.5)

## Top Teams by O1.5 Rate
1. Liverpool SRL — 92.5% (40 games)
2. Bournemouth SRL — 90.0% (40 games)
3. Brighton SRL — 89.7% (39 games)
4. Crystal Palace SRL — 89.7% (39 games)
5. Kocaelispor SRL — 89.7% (29 games)

## Scoring Model
- Base: (home_o15_rate + away_o15_rate) / 2 × 100
- +5 if both teams 80%+ O1.5 (Both ELITE)
- +3 if combined avg goals ≥ 6.0
- +2 if Premier League SRL
- -5 if either team < 65% O1.5
- -3 if combined avg goals < 5.0
- -2 if small sample size (<10 games)

## API Endpoints (Working)
- Live: `GET /api/ng/factsCenter/wapConfigurableIndexLiveEvents?sportId=sr:sport:1&categoryId=sr:category:2123`
- Upcoming: `GET /api/ng/factsCenter/wapConfigurableUpcomingEvents?sportId=sr:sport:1&categoryId=sr:category:2123`
- Results: `GET /api/ng/factsCenter/eventResultList?sportId=sr:sport:1&tournamentId={tid}&pageSize=50&pageNum=1`
- Booking: `POST /api/ng/orders/share` with `{"selections": [...]}`

## Files
- `srl_scanner_v1.py` — Main prediction scanner (deploys as AutoGPT agent)
- `srl_data_collector_v2.py` — Continuous data collection
- `srl_all_results.json` — 1,518 historical results
- `srl_team_profiles.json` — 91 team profiles
