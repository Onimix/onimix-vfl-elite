"use client";

import { useState, useCallback } from "react";
import type { MatchResult, MatchAnalysis, PreMatchJSON } from "@/lib/types";
import { analyzeMatch, buildEnergyCards } from "@/lib/onimix-engine";
import { savePick, generateId } from "@/lib/storage";
import { Navbar } from "@/components/Navbar";
import { ResultsInput } from "@/components/ResultsInput";
import { FixtureInput } from "@/components/FixtureInput";
import { AnalysisCard } from "@/components/AnalysisCard";
import { EnergyCards } from "@/components/EnergyCards";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";

const today = new Date().toISOString().split("T")[0];
const yesterday = new Date(Date.now() - 86400000).toISOString().split("T")[0];

export default function AnalyzePage() {
  // Slot config
  const [slot, setSlot] = useState("13:10");
  const [analyzeDate, setAnalyzeDate] = useState(today);
  const [yesterdayDate, setYesterdayDate] = useState(yesterday);
  const [league, setLeague] = useState("Spain Virtual");

  // Data
  const [yesterdayResults, setYesterdayResults] = useState<MatchResult[]>([]);
  const [todayFixtures, setTodayFixtures] = useState<{ home: string; away: string }[]>([]);
  const [analyses, setAnalyses] = useState<MatchAnalysis[]>([]);
  const [showEnergyCards, setShowEnergyCards] = useState(false);

  // Step tracking
  const [step, setStep] = useState<1 | 2 | 3>(1);

  const energyCards = yesterdayResults.length > 0
    ? Array.from(buildEnergyCards(yesterdayResults).values())
    : [];

  function handleYesterdayResults(results: MatchResult[]) {
    setYesterdayResults(results);
    if (results.length > 0) setStep(2);
  }

  function handleFixtures(fixtures: { home: string; away: string }[]) {
    setTodayFixtures(fixtures);
    if (fixtures.length > 0) setStep(3);
  }

  function runAnalysis() {
    if (todayFixtures.length === 0) return;
    const results = todayFixtures.map((f) =>
      analyzeMatch(f.home, f.away, slot, analyzeDate, yesterdayResults, null)
    );
    setAnalyses(results);
  }

  const handleAddToTracker = useCallback((analysis: MatchAnalysis) => {
    savePick({
      id: generateId(),
      date: analysis.date,
      slot: analysis.slot,
      homeTeam: analysis.homeTeam,
      awayTeam: analysis.awayTeam,
      decision: analysis.decision,
      confidence: analysis.confidence,
      yesterdayScore: analysis.yesterdayScore,
      jsonScore: analysis.jsonScore,
      market: "Over 1.5",
      outcome: "PENDING",
      actualScore: "",
      notes: "",
    });
    alert(`${analysis.homeTeam} vs ${analysis.awayTeam} added to tracker!`);
  }, []);

  const locks = analyses.filter((a) => a.decision === "LOCK");
  const picks = analyses.filter((a) => a.decision === "PICK");
  const considers = analyses.filter((a) => a.decision === "CONSIDER");
  const skips = analyses.filter((a) => a.decision === "SKIP");

  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      <Navbar />

      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-black text-white mb-2">Slot Analyzer</h1>
          <p className="text-neutral-500 text-sm">
            Paste yesterday&apos;s results, enter today&apos;s fixtures, run ONIMIX analysis.
          </p>
        </div>

        {/* Config */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Session Config</CardTitle>
          </CardHeader>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-neutral-500 mb-1">League</label>
              <input
                value={league}
                onChange={(e) => setLeague(e.target.value)}
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-600"
              />
            </div>
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Slot</label>
              <input
                value={slot}
                onChange={(e) => setSlot(e.target.value)}
                placeholder="13:10"
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-600"
              />
            </div>
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Yesterday&apos;s Date</label>
              <input
                type="date"
                value={yesterdayDate}
                onChange={(e) => setYesterdayDate(e.target.value)}
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-600"
              />
            </div>
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Today&apos;s Date</label>
              <input
                type="date"
                value={analyzeDate}
                onChange={(e) => setAnalyzeDate(e.target.value)}
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-600"
              />
            </div>
          </div>
        </Card>

        {/* Step 1 & 2 inputs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Step 1 */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <span className={`w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center ${yesterdayResults.length > 0 ? "bg-emerald-600 text-white" : "bg-neutral-700 text-neutral-400"}`}>
                  {yesterdayResults.length > 0 ? "✓" : "1"}
                </span>
                <CardTitle>Yesterday&apos;s Results</CardTitle>
              </div>
            </CardHeader>
            <ResultsInput
              label={`${league} — ${yesterdayDate} ${slot}`}
              onResults={handleYesterdayResults}
              date={yesterdayDate}
              slot={slot}
            />
            {energyCards.length > 0 && (
              <div className="mt-4">
                <button
                  onClick={() => setShowEnergyCards(!showEnergyCards)}
                  className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                >
                  {showEnergyCards ? "Hide" : "Show"} energy cards ({energyCards.length} teams)
                </button>
                {showEnergyCards && (
                  <div className="mt-3">
                    <EnergyCards cards={energyCards} />
                  </div>
                )}
              </div>
            )}
          </Card>

          {/* Step 2 */}
          <Card className={step < 2 ? "opacity-50 pointer-events-none" : ""}>
            <CardHeader>
              <div className="flex items-center gap-2">
                <span className={`w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center ${todayFixtures.length > 0 ? "bg-emerald-600 text-white" : "bg-neutral-700 text-neutral-400"}`}>
                  {todayFixtures.length > 0 ? "✓" : "2"}
                </span>
                <CardTitle>Today&apos;s Fixtures</CardTitle>
              </div>
            </CardHeader>
            <FixtureInput onFixtures={handleFixtures} />
          </Card>
        </div>

        {/* Run button */}
        {step >= 2 && todayFixtures.length > 0 && (
          <div className="text-center mb-8">
            <button
              onClick={runAnalysis}
              className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl transition-colors text-base"
            >
              Run ONIMIX Analysis
            </button>
          </div>
        )}

        {/* Results */}
        {analyses.length > 0 && (
          <div className="space-y-8">
            {/* Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: "LOCK", count: locks.length, color: "text-emerald-400 border-emerald-800 bg-emerald-950/20" },
                { label: "PICK", count: picks.length, color: "text-blue-400 border-blue-800 bg-blue-950/20" },
                { label: "CONSIDER", count: considers.length, color: "text-yellow-400 border-yellow-800 bg-yellow-950/20" },
                { label: "SKIP", count: skips.length, color: "text-red-400 border-red-800 bg-red-950/20" },
              ].map((s) => (
                <div key={s.label} className={`border rounded-xl p-4 text-center ${s.color}`}>
                  <div className="text-3xl font-black">{s.count}</div>
                  <div className="text-xs font-semibold opacity-70">{s.label}</div>
                </div>
              ))}
            </div>

            {/* Locks & Picks first */}
            {[...locks, ...picks, ...considers, ...skips].map((analysis, i) => (
              <AnalysisCard
                key={`${analysis.homeTeam}-${analysis.awayTeam}-${i}`}
                analysis={analysis}
                onAddToTracker={handleAddToTracker}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
