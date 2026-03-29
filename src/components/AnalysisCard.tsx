"use client";

import type { MatchAnalysis } from "@/lib/types";
import { Badge } from "./ui/Badge";
import { Card } from "./ui/Card";

interface AnalysisCardProps {
  analysis: MatchAnalysis;
  onAddToTracker?: (analysis: MatchAnalysis) => void;
}

function decisionBadgeVariant(decision: MatchAnalysis["decision"]) {
  switch (decision) {
    case "LOCK": return "green";
    case "PICK": return "blue";
    case "CONSIDER": return "yellow";
    case "SKIP": return "red";
  }
}

function decisionIcon(decision: MatchAnalysis["decision"]) {
  switch (decision) {
    case "LOCK": return "🔒";
    case "PICK": return "✅";
    case "CONSIDER": return "⚠️";
    case "SKIP": return "❌";
  }
}

function ScoreBar({ score, max, label }: { score: number; max: number; label: string }) {
  const pct = Math.min(100, Math.round((score / max) * 100));
  const color = pct >= 80 ? "bg-emerald-500" : pct >= 60 ? "bg-blue-500" : pct >= 40 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-neutral-400">
        <span>{label}</span>
        <span className="text-white font-mono">{score}/{max}</span>
      </div>
      <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function AnalysisCard({ analysis, onAddToTracker }: AnalysisCardProps) {
  const borderColor =
    analysis.decision === "LOCK"
      ? "border-emerald-700"
      : analysis.decision === "PICK"
      ? "border-blue-700"
      : analysis.decision === "CONSIDER"
      ? "border-yellow-700"
      : "border-neutral-800";

  return (
    <Card className={`border ${borderColor} space-y-4`}>
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <div className="text-xl font-bold text-white">
            {analysis.homeTeam} <span className="text-neutral-500">vs</span> {analysis.awayTeam}
          </div>
          <div className="text-xs text-neutral-500 mt-0.5">{analysis.date} · {analysis.slot}</div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-2xl">{decisionIcon(analysis.decision)}</span>
          <Badge variant={decisionBadgeVariant(analysis.decision)} size="md">
            {analysis.decision}
          </Badge>
          <Badge
            variant={analysis.confidence === "HIGH" ? "green" : analysis.confidence === "MEDIUM" ? "yellow" : "gray"}
            size="md"
          >
            {analysis.confidence}
          </Badge>
        </div>
      </div>

      {/* Instant skip */}
      {analysis.instantSkip && (
        <div className="bg-red-950/40 border border-red-800/50 rounded-lg p-3 text-sm text-red-300">
          <span className="font-bold">INSTANT SKIP:</span> {analysis.instantSkipReason}
        </div>
      )}

      {/* Score bars */}
      {!analysis.instantSkip && (
        <div className="space-y-2">
          <ScoreBar score={analysis.yesterdayScore} max={18} label="Yesterday Score (60%)" />
          <ScoreBar score={analysis.jsonScore} max={12} label="JSON Score (40%)" />
        </div>
      )}

      {/* Rules accordion */}
      <details className="group">
        <summary className="cursor-pointer text-sm text-neutral-400 hover:text-white transition-colors list-none flex items-center gap-1">
          <span className="group-open:rotate-90 transition-transform inline-block">▶</span>
          Rule breakdown ({analysis.yesterdayRules.length + analysis.jsonRules.length} rules)
        </summary>
        <div className="mt-3 space-y-1.5">
          {[...analysis.yesterdayRules, ...analysis.jsonRules].map((rule) => (
            <div key={rule.rule} className="flex items-start gap-2 text-xs">
              <span className={rule.passed ? "text-emerald-400" : "text-red-400"}>
                {rule.passed ? "✓" : "✗"}
              </span>
              <span className="text-neutral-400 font-mono w-6 shrink-0">{rule.rule}</span>
              <span className={rule.passed ? "text-neutral-300" : "text-neutral-500"}>
                {rule.label}: {rule.detail}
              </span>
              <span className="ml-auto font-mono text-neutral-500 shrink-0">
                {rule.points}/{rule.maxPoints}
              </span>
            </div>
          ))}
        </div>
      </details>

      {/* Add to tracker */}
      {onAddToTracker && (analysis.decision === "LOCK" || analysis.decision === "PICK" || analysis.decision === "CONSIDER") && (
        <button
          onClick={() => onAddToTracker(analysis)}
          className="w-full py-2 px-4 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-sm text-neutral-300 hover:text-white transition-colors border border-neutral-700 hover:border-neutral-600"
        >
          + Add to Tracker
        </button>
      )}
    </Card>
  );
}
