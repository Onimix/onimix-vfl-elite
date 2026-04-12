# 🎯 ONIMIX ELITE — Virtual Football Prediction Engine

> Real-time Over 1.5 Goals predictions for SportyBet Virtual Football across 5 leagues, powered by data from 73,081 real matches.

![Next.js](https://img.shields.io/badge/Next.js-16-black) ![TypeScript](https://img.shields.io/badge/TypeScript-5.9-blue) ![Vercel](https://img.shields.io/badge/Deploy-Vercel-black)

## 🏆 What It Does

- **353 ELITE matchups** across England, Spain, Italy, Germany & France VFL
- **78.5% verified hit rate** (vs 71.9% baseline) for Over 1.5 Goals
- **Real-time scanning** of SportyBet's live API every 5 minutes
- **Telegram alerts** sent 10 minutes before ELITE matches kick off
- **Interactive dashboard** to browse all matchups, filter by league, and trigger manual scans

## 📊 ELITE Database Stats

| League  | Matchups | Top Hit Rate |
|---------|----------|-------------|
| 🏴󠁧󠁢󠁥󠁮󠁧󠁿 England | 158      | 97.6% (AST vs ARS) |
| 🇩🇪 Germany | 78       | 95.2% |
| 🇫🇷 France  | 77       | 95.2% |
| 🇮🇹 Italy   | 33       | 92.9% |
| 🇪🇸 Spain   | 7        | 90.5% |

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Onimix/onimix-vfl-elite.git
cd onimix-vfl-elite
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env.local
```

Edit `.env.local`:
- `TELEGRAM_BOT_TOKEN` — Your Telegram bot token
- `TELEGRAM_CHAT_ID` — Your Telegram chat ID
- `CRON_SECRET` — (Optional) Protects the scan endpoint from abuse

### 3. Run Locally

```bash
npm run dev
```

Open [http://localhost:3000/elite](http://localhost:3000/elite) to see the ELITE dashboard.

## 🌐 Deploy to Vercel (Free Plan)

### One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FOnimix%2Fonimix-vfl-elite)

### Manual Deploy

1. Push to GitHub
2. Import project on [vercel.com](https://vercel.com)
3. Add environment variables in Vercel Dashboard:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Deploy!

### ⚡ How Scanning Works (Free Plan)

This app is designed to work on Vercel's **free Hobby plan** with 3 scanning methods:

| Method | How It Works | Setup |
|--------|-------------|-------|
| **Dashboard Auto-Scan** | Opens the `/elite` page → auto-polls every 5 min | Just keep the tab open |
| **Free External Cron** | cron-job.org pings `/api/scan` every 5 min | Free, set up in 2 min (see below) |
| **AutoGPT Agent** | Background agent scans 24/7 independently | Already running |

#### Option A: Dashboard (Easiest)
Just open your deployed site at `/elite`. Auto-scan starts automatically and polls every 5 minutes. Alerts appear in real-time and are sent to Telegram.

#### Option B: Free External Cron (Recommended for 24/7)
1. Go to [cron-job.org](https://cron-job.org) (free account)
2. Create a new cron job:
   - **URL**: `https://your-app.vercel.app/api/scan`
   - **Schedule**: Every 5 minutes
   - **Method**: GET
3. Done! The endpoint will scan and send Telegram alerts automatically.

> 💡 The daily Vercel cron (`0 0 * * *` in `vercel.json`) runs once at midnight as a health check. The real scanning comes from the dashboard or external cron.

## 🛠 API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/scan` | GET/POST | Scans SportyBet API for ELITE matches, sends Telegram alerts |
| `/api/elite` | GET | Returns full ELITE database with stats |

## 📁 Project Structure

```
src/
├── app/
│   ├── api/
│   │   ├── scan/route.ts      # Live scanner endpoint
│   │   └── elite/route.ts     # ELITE data endpoint
│   ├── elite/page.tsx          # ELITE dashboard (auto-scan)
│   ├── analyze/page.tsx        # ONIMIX analysis engine
│   └── tracker/page.tsx        # Pick tracker
├── components/
│   └── Navbar.tsx
├── data/
│   └── elite-matchups.json     # 353 verified ELITE matchups
└── lib/
    ├── scanner.ts              # SportyBet API scanner
    ├── telegram.ts             # Telegram alert sender
    ├── elite-types.ts          # TypeScript types
    └── onimix-engine.ts        # Original ONIMIX engine
```

## 📈 How ELITE Matchups Are Found

1. **73,081 real VFL matches** extracted from SportyBet API (Mar 1 - Apr 11, 2026)
2. Each unique matchup (e.g., "AST vs ARS") analyzed for Over 1.5 Goals hit rate
3. Only matchups with **78%+ hit rate** AND **40+ sample size** qualify as ELITE
4. Cross-validated across time periods to confirm stability

## 🔗 Tech Stack

- **Next.js 16** — React framework with App Router
- **TypeScript** — Full type safety
- **Tailwind CSS 4** — Styling
- **Vercel** — Hosting (Free Hobby plan)
- **SportyBet API** — Live match data
- **Telegram Bot API** — Alert delivery

---

Built by **ONIMIX TECH** · Powered by data, not guesswork.
