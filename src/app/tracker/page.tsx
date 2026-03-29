"use client";

import { useState, useEffect, useCallback } from "react";
import type { TrackedPick } from "@/lib/types";
import { getPicks, computeStats } from "@/lib/storage";
import { Navbar } from "@/components/Navbar";
import { TrackerTable } from "@/components/TrackerTable";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

const BASELINE_WIN_RATE = 67; // typical over 1.5 hit rate in virtual football

export default function TrackerPage() {
  const [picks, setPicks] = useState<TrackedPick[]>([]);
  const [filter, setFilter] = useState<"ALL" | "LOCK" | "PICK" | "CONSIDER">("ALL");

  const load = useCallback(() => {
    setPicks(getPicks());
  }, []);

  // Load picks on mount and when tracker updates
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPicks(getPicks());
  }, []);

  const stats = computeStats(picks);
  const filtered = filter === "ALL" ? picks : picks.filter((p) => p.decision === filter);

  const edge = stats.winRate - BASELINE_WIN_RATE;

  function exportCSV() {
    const header = "Date,Slot,Home,Away,Decision,Yesterday,JSON,Market,Outcome,Score\n";
    const rows = picks
      .map(
        (p) =>
          `${p.date},${p.slot},${p.homeTeam},${p.awayTeam},${p.decision},${p.yesterdayScore},${p.jsonScore},${p.market},${p.outcome},${p.actualScore}`
      )
      .join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `onimix-picks-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      <Navbar />

      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-start justify-between flex-wrap gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-black text-white mb-2">Pick Tracker</h1>
            <p className="text-neutral-500 text-sm">
              Track outcomes and validate the ONIMIX system&apos;s real edge.
            </p>
          </div>
          {picks.length > 0 && (
            <button
              onClick={exportCSV}
              className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-sm font-semibold rounded-lg border border-neutral-700 transition-colors"
            >
              Export CSV
            </button>
          )}
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
          <Card className="text-center">
            <div className="text-2xl font-black text-white">{stats.total}</div>
            <div className="text-xs text-neutral-500 mt-0.5">Total Picks</div>
          </Card>
          <Card className="text-center">
            <div className="text-2xl font-black text-emerald-400">{stats.wins}</div>
            <div className="text-xs text-neutral-500 mt-0.5">Wins</div>
          </Card>
          <Card className="text-center">
            <div className="text-2xl font-black text-red-400">{stats.losses}</div>
            <div className="text-xs text-neutral-500 mt-0.5">Losses</div>
          </Card>
          <Card className="text-center">
            <div className="text-2xl font-black text-neutral-400">{stats.pending}</div>
            <div className="text-xs text-neutral-500 mt-0.5">Pending</div>
          </Card>
          <Card className="text-center">
            <div className={`text-2xl font-black ${stats.winRate >= BASELINE_WIN_RATE ? "text-emerald-400" : "text-red-400"}`}>
              {stats.winRate}%
            </div>
            <div className="text-xs text-neutral-500 mt-0.5">Win Rate</div>
          </Card>
          <Card className="text-center">
            <div className={`text-2xl font-black ${edge >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {edge >= 0 ? "+" : ""}{edge}%
            </div>
            <div className="text-xs text-neutral-500 mt-0.5">vs Baseline</div>
          </Card>
        </div>

        {/* Lock vs Pick breakdown */}
        {stats.total > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
            <Card>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-neutral-400">LOCK Win Rate</span>
                <Badge variant={stats.lockWinRate >= BASELINE_WIN_RATE ? "green" : "red"} size="md">
                  {stats.lockWinRate}%
                </Badge>
              </div>
              <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${stats.lockWinRate >= BASELINE_WIN_RATE ? "bg-emerald-500" : "bg-red-500"}`}
                  style={{ width: `${stats.lockWinRate}%` }}
                />
              </div>
              <div className="text-xs text-neutral-600 mt-1">Baseline: {BASELINE_WIN_RATE}%</div>
            </Card>
            <Card>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-semibold text-neutral-400">PICK Win Rate</span>
                <Badge variant={stats.pickWinRate >= BASELINE_WIN_RATE ? "green" : "red"} size="md">
                  {stats.pickWinRate}%
                </Badge>
              </div>
              <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${stats.pickWinRate >= BASELINE_WIN_RATE ? "bg-blue-500" : "bg-red-500"}`}
                  style={{ width: `${stats.pickWinRate}%` }}
                />
              </div>
              <div className="text-xs text-neutral-600 mt-1">Baseline: {BASELINE_WIN_RATE}%</div>
            </Card>
          </div>
        )}

        {/* Validation message */}
        {stats.total >= 20 && stats.total < 50 && (
          <div className="bg-yellow-950/30 border border-yellow-800/40 rounded-xl p-4 mb-6 text-sm text-yellow-300">
            <span className="font-bold">Early data ({stats.total} picks).</span> Minimum 50 picks needed for statistically significant results.
          </div>
        )}
        {stats.total >= 50 && edge > 5 && (
          <div className="bg-emerald-950/30 border border-emerald-800/40 rounded-xl p-4 mb-6 text-sm text-emerald-300">
            <span className="font-bold">Edge confirmed.</span> {stats.winRate}% win rate beats the {BASELINE_WIN_RATE}% baseline by +{edge}% over {stats.total} picks.
          </div>
        )}
        {stats.total >= 50 && edge <= 0 && (
          <div className="bg-red-950/30 border border-red-800/40 rounded-xl p-4 mb-6 text-sm text-red-300">
            <span className="font-bold">No edge detected.</span> Win rate ({stats.winRate}%) is at or below the {BASELINE_WIN_RATE}% baseline over {stats.total} picks.
          </div>
        )}

        {/* Filter tabs */}
        {picks.length > 0 && (
          <div className="flex gap-2 mb-4 flex-wrap">
            {(["ALL", "LOCK", "PICK", "CONSIDER"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-colors ${
                  filter === f
                    ? "bg-blue-600 text-white"
                    : "bg-neutral-800 text-neutral-400 hover:text-white hover:bg-neutral-700"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        )}

        {/* Table */}
        <Card>
          <TrackerTable picks={filtered} onUpdate={load} />
        </Card>
      </div>
    </div>
  );
}
