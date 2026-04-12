"use client";

import { useEffect, useState, useCallback } from "react";
import { Navbar } from "@/components/Navbar";

interface EliteAlert {
  event: {
    home: string;
    away: string;
    key: string;
    league: string;
    kickoffFormatted: string;
    minutesUntilKick: number;
  };
  matchup: {
    key: string;
    league: string;
    hitRate: number;
  };
}

interface ScanResult {
  timestamp: string;
  totalEventsScanned: number;
  eliteFound: EliteAlert[];
  leaguesScanned: string[];
  scanDurationMs: number;
  telegramSent: boolean;
}

interface LeagueStats {
  league: string;
  totalMatchups: number;
  avgHitRate: number;
  topPicks: { key: string; rate: number }[];
}

interface EliteData {
  totalMatchups: number;
  overallAvgHitRate: number;
  leagues: LeagueStats[];
  allMatchups: Record<string, Record<string, number>>;
}

const leagueEmojis: Record<string, string> = {
  England: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  Spain: "🇪🇸",
  Italy: "🇮🇹",
  Germany: "🇩🇪",
  France: "🇫🇷",
};

const leagueColors: Record<string, string> = {
  England: "border-red-700 bg-red-950/20 text-red-300",
  Spain: "border-yellow-700 bg-yellow-950/20 text-yellow-300",
  Italy: "border-green-700 bg-green-950/20 text-green-300",
  Germany: "border-neutral-600 bg-neutral-900/40 text-neutral-300",
  France: "border-blue-700 bg-blue-950/20 text-blue-300",
};

function HitRateBar({ rate }: { rate: number }) {
  const color =
    rate >= 95
      ? "bg-emerald-400"
      : rate >= 90
        ? "bg-emerald-500"
        : rate >= 85
          ? "bg-blue-500"
          : rate >= 80
            ? "bg-yellow-500"
            : "bg-orange-500";

  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-neutral-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${rate}%` }}
        />
      </div>
      <span className="text-xs font-mono">{rate}%</span>
    </div>
  );
}

export default function ElitePage() {
  const [eliteData, setEliteData] = useState<EliteData | null>(null);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [scanning, setScanning] = useState(false);
  const [selectedLeague, setSelectedLeague] = useState<string>("all");
  const [autoScan, setAutoScan] = useState(false);

  // Load ELITE database
  useEffect(() => {
    fetch("/api/elite")
      .then((r) => r.json())
      .then(setEliteData)
      .catch(console.error);
  }, []);

  // Manual scan
  const runScan = useCallback(async () => {
    setScanning(true);
    try {
      const res = await fetch("/api/scan", { method: "POST" });
      const data = await res.json();
      setScanResult(data);
    } catch (error) {
      console.error("Scan failed:", error);
    }
    setScanning(false);
  }, []);

  // Auto-scan every 5 minutes
  useEffect(() => {
    if (!autoScan) return;
    runScan();
    const interval = setInterval(runScan, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [autoScan, runScan]);

  // Filter matchups by league
  const filteredMatchups = eliteData
    ? selectedLeague === "all"
      ? Object.entries(eliteData.allMatchups).flatMap(([league, matchups]) =>
          Object.entries(matchups).map(([key, rate]) => ({
            key,
            rate,
            league,
          }))
        )
      : Object.entries(eliteData.allMatchups[selectedLeague] ?? {}).map(
          ([key, rate]) => ({ key, rate, league: selectedLeague })
        )
    : [];

  const sortedMatchups = filteredMatchups.sort((a, b) => b.rate - a.rate);

  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      <Navbar />

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-4 pt-10 pb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="inline-flex items-center gap-2 bg-emerald-950/40 border border-emerald-800/40 rounded-full px-4 py-1.5 text-xs text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            ELITE System Active
          </div>
          {scanResult && (
            <span className="text-xs text-neutral-500">
              Last scan:{" "}
              {new Date(scanResult.timestamp).toLocaleTimeString("en-NG", {
                timeZone: "Africa/Lagos",
              })}{" "}
              ({scanResult.scanDurationMs}ms)
            </span>
          )}
        </div>

        <h1 className="text-3xl sm:text-4xl font-black tracking-tight mb-2">
          ELITE Matchup{" "}
          <span className="text-emerald-400">Scanner</span>
        </h1>
        <p className="text-neutral-400 text-sm max-w-xl mb-6">
          353 verified ELITE matchups across 5 VFL leagues. Average 78.5% hit
          rate for Over 1.5 Goals. Real-time scanning with Telegram alerts.
        </p>

        {/* Controls */}
        <div className="flex gap-3 flex-wrap mb-8">
          <button
            onClick={runScan}
            disabled={scanning}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-neutral-700 text-white font-bold rounded-xl transition-colors text-sm"
          >
            {scanning ? "⏳ Scanning..." : "🔍 Scan Now"}
          </button>
          <button
            onClick={() => setAutoScan(!autoScan)}
            className={`px-5 py-2.5 font-bold rounded-xl transition-colors text-sm border ${
              autoScan
                ? "bg-emerald-950 border-emerald-700 text-emerald-300"
                : "bg-neutral-800 border-neutral-700 text-neutral-300 hover:bg-neutral-700"
            }`}
          >
            {autoScan ? "🟢 Auto-Scan ON" : "⏸️ Auto-Scan OFF"}
          </button>
        </div>

        {/* Live Alerts */}
        {scanResult && scanResult.eliteFound.length > 0 && (
          <div className="mb-8 p-4 bg-emerald-950/30 border border-emerald-800/40 rounded-xl">
            <h2 className="text-lg font-bold text-emerald-400 mb-3">
              🎯 LIVE ELITE ALERTS ({scanResult.eliteFound.length})
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {scanResult.eliteFound.map((alert, i) => (
                <div
                  key={i}
                  className="bg-neutral-900 border border-emerald-800/30 rounded-lg p-4"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs text-neutral-400">
                      {leagueEmojis[alert.matchup.league]}{" "}
                      {alert.matchup.league}
                    </span>
                    <span className="text-xs font-mono text-emerald-400">
                      {alert.matchup.hitRate}%
                    </span>
                  </div>
                  <div className="font-bold text-white mb-1">
                    {alert.event.home} vs {alert.event.away}
                  </div>
                  <div className="text-xs text-neutral-500">
                    ⏰ {alert.event.kickoffFormatted} WAT · ⏳{" "}
                    {alert.event.minutesUntilKick} min to kick
                  </div>
                </div>
              ))}
            </div>
            {scanResult.telegramSent && (
              <p className="text-xs text-emerald-600 mt-2">
                ✅ Telegram alert sent
              </p>
            )}
          </div>
        )}

        {scanResult && scanResult.eliteFound.length === 0 && (
          <div className="mb-8 p-4 bg-neutral-900 border border-neutral-800 rounded-xl text-center">
            <p className="text-neutral-500 text-sm">
              No ELITE matches in the 10-minute window right now. Scanned{" "}
              {scanResult.totalEventsScanned} events across{" "}
              {scanResult.leaguesScanned.length} leagues.
            </p>
          </div>
        )}
      </section>

      {/* Stats Cards */}
      {eliteData && (
        <section className="max-w-6xl mx-auto px-4 pb-8">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-8">
            {eliteData.leagues.map((ls) => (
              <button
                key={ls.league}
                onClick={() =>
                  setSelectedLeague(
                    selectedLeague === ls.league ? "all" : ls.league
                  )
                }
                className={`border rounded-xl p-4 text-left transition-all ${
                  selectedLeague === ls.league
                    ? leagueColors[ls.league]
                    : "border-neutral-800 bg-neutral-900 text-neutral-400 hover:border-neutral-700"
                }`}
              >
                <div className="text-lg mb-1">
                  {leagueEmojis[ls.league]} {ls.league}
                </div>
                <div className="text-2xl font-black text-white">
                  {ls.totalMatchups}
                </div>
                <div className="text-xs opacity-70">
                  Avg: {ls.avgHitRate}%
                </div>
              </button>
            ))}
          </div>

          {/* Global Stats Bar */}
          <div className="flex gap-4 mb-6 text-sm text-neutral-400">
            <span>
              📊 Total: <strong className="text-white">{eliteData.totalMatchups}</strong> matchups
            </span>
            <span>
              🎯 Overall: <strong className="text-emerald-400">{eliteData.overallAvgHitRate}%</strong> avg
            </span>
            <span>
              🏆 Showing:{" "}
              <strong className="text-white">
                {selectedLeague === "all" ? "All Leagues" : selectedLeague}
              </strong>
            </span>
          </div>

          {/* Matchup Table */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
            <div className="grid grid-cols-12 gap-2 p-3 border-b border-neutral-800 text-xs text-neutral-500 uppercase tracking-wider font-bold">
              <div className="col-span-1">#</div>
              <div className="col-span-2">League</div>
              <div className="col-span-5">Matchup</div>
              <div className="col-span-4">Hit Rate (Over 1.5)</div>
            </div>

            <div className="max-h-[600px] overflow-y-auto">
              {sortedMatchups.map((m, i) => (
                <div
                  key={`${m.league}-${m.key}`}
                  className="grid grid-cols-12 gap-2 p-3 border-b border-neutral-800/50 hover:bg-neutral-800/30 transition-colors items-center"
                >
                  <div className="col-span-1 text-xs text-neutral-600 font-mono">
                    {i + 1}
                  </div>
                  <div className="col-span-2 text-xs">
                    {leagueEmojis[m.league]}{" "}
                    <span className="text-neutral-400">{m.league}</span>
                  </div>
                  <div className="col-span-5 font-semibold text-sm">
                    {m.key}
                  </div>
                  <div className="col-span-4">
                    <HitRateBar rate={m.rate} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="border-t border-neutral-800 py-6 text-center text-xs text-neutral-600">
        ONIMIX ELITE Engine · 73,081 matches analyzed · 5 VFL Leagues · Built by ONIMIX TECH
      </footer>
    </div>
  );
}
