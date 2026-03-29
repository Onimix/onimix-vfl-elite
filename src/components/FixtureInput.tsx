"use client";

import { useState } from "react";

interface Fixture {
  home: string;
  away: string;
}

interface FixtureInputProps {
  onFixtures: (fixtures: Fixture[]) => void;
}

const PLACEHOLDER = `ALA BIL
ATM OSA
CEL MAL
FCB VIL
GIR SEV`;

export function FixtureInput({ onFixtures }: FixtureInputProps) {
  const [text, setText] = useState("");
  const [parsed, setParsed] = useState<Fixture[]>([]);
  const [error, setError] = useState("");

  function handleParse() {
    setError("");
    const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
    const fixtures: Fixture[] = [];

    for (const line of lines) {
      const parts = line.split(/\s+/);
      if (parts.length >= 2) {
        fixtures.push({ home: parts[0].toUpperCase(), away: parts[1].toUpperCase() });
      }
    }

    if (fixtures.length === 0) {
      setError("No valid fixtures found. Format: HOMETEAM AWAYTEAM");
      return;
    }

    setParsed(fixtures);
    onFixtures(fixtures);
  }

  function handleClear() {
    setText("");
    setParsed([]);
    setError("");
    onFixtures([]);
  }

  return (
    <div className="space-y-3">
      <label className="block text-sm font-semibold text-neutral-300">
        Today&apos;s Fixtures <span className="text-neutral-500 font-normal">(one per line: HOME AWAY)</span>
      </label>
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
          Parse Fixtures
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
          <p className="text-xs text-emerald-400 font-semibold mb-2">✓ {parsed.length} fixtures parsed</p>
          {parsed.map((f, i) => (
            <div key={i} className="flex items-center gap-2 text-xs font-mono text-neutral-300">
              <span className="text-neutral-500 w-4">{i + 1}.</span>
              <span className="font-bold text-white">{f.home}</span>
              <span className="text-neutral-500">vs</span>
              <span className="font-bold text-white">{f.away}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
