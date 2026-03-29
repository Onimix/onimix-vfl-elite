"use client";

import { useState } from "react";
import type { MatchResult } from "@/lib/types";
import { parseResultsText } from "@/lib/onimix-engine";

interface ResultsInputProps {
  label: string;
  onResults: (results: MatchResult[]) => void;
  date: string;
  slot: string;
}

const PLACEHOLDER = `ALA 1:3 BIL
ATM 1:0 OSA
CEL 3:2 MAL
FCB 2:1 VIL
GIR 2:1 SEV`;

export function ResultsInput({ label, onResults, date, slot }: ResultsInputProps) {
  const [text, setText] = useState("");
  const [parsed, setParsed] = useState<MatchResult[]>([]);
  const [error, setError] = useState("");

  function handleParse() {
    setError("");
    const results = parseResultsText(text, date, slot);
    if (results.length === 0) {
      setError("No valid matches found. Format: TEAM1 score1:score2 TEAM2");
      return;
    }
    setParsed(results);
    onResults(results);
  }

  function handleClear() {
    setText("");
    setParsed([]);
    setError("");
    onResults([]);
  }

  return (
    <div className="space-y-3">
      <label className="block text-sm font-semibold text-neutral-300">{label}</label>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={PLACEHOLDER}
        rows={10}
        className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-3 text-sm font-mono text-neutral-100 placeholder:text-neutral-600 focus:outline-none focus:border-blue-600 resize-none"
      />
      {error && <p className="text-red-400 text-xs">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={handleParse}
          disabled={!text.trim()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-neutral-700 disabled:text-neutral-500 text-white text-sm font-semibold rounded-lg transition-colors"
        >
          Parse Results
        </button>
        {parsed.length > 0 && (
          <button
            onClick={handleClear}
            className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-400 text-sm rounded-lg transition-colors border border-neutral-700"
          >
            Clear
          </button>
        )}
      </div>
      {parsed.length > 0 && (
        <div className="bg-neutral-800/50 border border-neutral-700 rounded-lg p-3 space-y-1">
          <p className="text-xs text-emerald-400 font-semibold mb-2">✓ {parsed.length} matches parsed</p>
          {parsed.map((m, i) => (
            <div key={i} className="flex items-center gap-2 text-xs font-mono text-neutral-300">
              <span className="text-neutral-500 w-4">{i + 1}.</span>
              <span className="font-bold text-white w-12">{m.home}</span>
              <span className="text-emerald-400">{m.homeScore}:{m.awayScore}</span>
              <span className="font-bold text-white w-12">{m.away}</span>
              <span className="ml-auto text-neutral-500">{m.totalGoals} goals</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
