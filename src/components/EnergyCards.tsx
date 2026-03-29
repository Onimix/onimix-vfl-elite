"use client";

import type { TeamEnergyCard } from "@/lib/types";
import { Badge } from "./ui/Badge";

interface EnergyCardsProps {
  cards: TeamEnergyCard[];
}

function flagBadge(flag: string) {
  switch (flag) {
    case "HOME_ZERO_TRAP": return <Badge key={flag} variant="red">HOME ZERO TRAP</Badge>;
    case "AWAY_ZERO_TRAP": return <Badge key={flag} variant="red">AWAY ZERO TRAP</Badge>;
    case "COOLDOWN": return <Badge key={flag} variant="orange">COOLDOWN</Badge>;
    case "REPAIR": return <Badge key={flag} variant="orange">REPAIR</Badge>;
    case "LOW_AWAY_ENERGY": return <Badge key={flag} variant="yellow">LOW AWAY</Badge>;
    case "LOW_HOME_ENERGY": return <Badge key={flag} variant="yellow">LOW HOME</Badge>;
    case "UNKNOWN": return <Badge key={flag} variant="gray">UNKNOWN</Badge>;
    case "CLEAN": return <Badge key={flag} variant="green">CLEAN</Badge>;
    default: return null;
  }
}

export function EnergyCards({ cards }: EnergyCardsProps) {
  if (cards.length === 0) return null;

  const clean = cards.filter((c) => c.flags.includes("CLEAN"));
  const warning = cards.filter((c) => c.flags.includes("LOW_AWAY_ENERGY") || c.flags.includes("LOW_HOME_ENERGY") || c.flags.includes("UNKNOWN"));
  const danger = cards.filter((c) => !c.flags.includes("CLEAN") && !c.flags.includes("LOW_AWAY_ENERGY") && !c.flags.includes("LOW_HOME_ENERGY") && !c.flags.includes("UNKNOWN"));

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-neutral-400 mb-2 uppercase tracking-wider">
          Team Energy Cards
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {cards.map((card) => (
            <div
              key={card.team}
              className={`flex items-center justify-between p-3 rounded-lg border text-sm ${
                card.flags.includes("CLEAN")
                  ? "bg-emerald-950/20 border-emerald-800/30"
                  : card.flags.includes("LOW_AWAY_ENERGY") || card.flags.includes("LOW_HOME_ENERGY") || card.flags.includes("UNKNOWN")
                  ? "bg-yellow-950/20 border-yellow-800/30"
                  : "bg-red-950/20 border-red-800/30"
              }`}
            >
              <span className="font-bold font-mono text-white">{card.team}</span>
              <div className="flex flex-wrap gap-1 justify-end">
                {card.flags.map((f) => flagBadge(f))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="bg-emerald-950/20 border border-emerald-800/30 rounded-lg p-3">
          <div className="text-emerald-400 font-semibold mb-1">✅ Clean ({clean.length})</div>
          <div className="font-mono text-emerald-300 text-xs">
            {clean.map((c) => c.team).join(", ") || "—"}
          </div>
        </div>
        <div className="bg-yellow-950/20 border border-yellow-800/30 rounded-lg p-3">
          <div className="text-yellow-400 font-semibold mb-1">⚠️ Low Energy ({warning.length})</div>
          <div className="font-mono text-yellow-300 text-xs">
            {warning.map((c) => c.team).join(", ") || "—"}
          </div>
        </div>
        <div className="bg-red-950/20 border border-red-800/30 rounded-lg p-3">
          <div className="text-red-400 font-semibold mb-1">🚨 Avoid ({danger.length})</div>
          <div className="font-mono text-red-300 text-xs">
            {danger.map((c) => c.team).join(", ") || "—"}
          </div>
        </div>
      </div>
    </div>
  );
}
