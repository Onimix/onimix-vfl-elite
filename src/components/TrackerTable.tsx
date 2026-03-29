"use client";

import { useState } from "react";
import type { TrackedPick, PickOutcome } from "@/lib/types";
import { Badge } from "./ui/Badge";
import { savePick, deletePick } from "@/lib/storage";

interface TrackerTableProps {
  picks: TrackedPick[];
  onUpdate: () => void;
}

function outcomeBadge(outcome: PickOutcome) {
  switch (outcome) {
    case "WIN": return <Badge variant="green">WIN</Badge>;
    case "LOSS": return <Badge variant="red">LOSS</Badge>;
    case "PENDING": return <Badge variant="gray">PENDING</Badge>;
  }
}

function decisionBadge(decision: string) {
  switch (decision) {
    case "LOCK": return <Badge variant="green">LOCK</Badge>;
    case "PICK": return <Badge variant="blue">PICK</Badge>;
    case "CONSIDER": return <Badge variant="yellow">CONSIDER</Badge>;
    default: return <Badge variant="gray">{decision}</Badge>;
  }
}

export function TrackerTable({ picks, onUpdate }: TrackerTableProps) {
  const [editing, setEditing] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<TrackedPick>>({});

  function startEdit(pick: TrackedPick) {
    setEditing(pick.id);
    setEditData({ outcome: pick.outcome, actualScore: pick.actualScore, notes: pick.notes });
  }

  function saveEdit(pick: TrackedPick) {
    savePick({ ...pick, ...editData });
    setEditing(null);
    onUpdate();
  }

  function handleDelete(id: string) {
    if (confirm("Remove this pick from tracker?")) {
      deletePick(id);
      onUpdate();
    }
  }

  if (picks.length === 0) {
    return (
      <div className="text-center py-16 text-neutral-600">
        <div className="text-4xl mb-3">📋</div>
        <div className="text-sm">No tracked picks yet.</div>
        <div className="text-xs mt-1">Analyze a slot and add picks to track them here.</div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-neutral-800 text-left">
            <th className="pb-3 text-xs text-neutral-500 font-semibold uppercase">Date/Slot</th>
            <th className="pb-3 text-xs text-neutral-500 font-semibold uppercase">Match</th>
            <th className="pb-3 text-xs text-neutral-500 font-semibold uppercase">Decision</th>
            <th className="pb-3 text-xs text-neutral-500 font-semibold uppercase">Score</th>
            <th className="pb-3 text-xs text-neutral-500 font-semibold uppercase">Market</th>
            <th className="pb-3 text-xs text-neutral-500 font-semibold uppercase">Result</th>
            <th className="pb-3 text-xs text-neutral-500 font-semibold uppercase">Outcome</th>
            <th className="pb-3 text-xs text-neutral-500 font-semibold uppercase">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-800/50">
          {picks.map((pick) => (
            <tr key={pick.id} className="hover:bg-neutral-800/20 transition-colors">
              <td className="py-3 pr-3 text-neutral-500 text-xs whitespace-nowrap">
                {pick.date}<br/>{pick.slot}
              </td>
              <td className="py-3 pr-3 font-mono font-semibold text-white whitespace-nowrap">
                {pick.homeTeam} vs {pick.awayTeam}
              </td>
              <td className="py-3 pr-3">{decisionBadge(pick.decision)}</td>
              <td className="py-3 pr-3 font-mono text-xs text-neutral-400">
                Y:{pick.yesterdayScore}/18<br/>J:{pick.jsonScore}/12
              </td>
              <td className="py-3 pr-3 text-neutral-300 text-xs">{pick.market}</td>
              <td className="py-3 pr-3">
                {editing === pick.id ? (
                  <input
                    value={editData.actualScore ?? ""}
                    onChange={(e) => setEditData((d) => ({ ...d, actualScore: e.target.value }))}
                    placeholder="2:1"
                    className="w-16 bg-neutral-700 border border-neutral-600 rounded px-2 py-1 text-xs font-mono text-white"
                  />
                ) : (
                  <span className="font-mono text-neutral-300">{pick.actualScore || "—"}</span>
                )}
              </td>
              <td className="py-3 pr-3">
                {editing === pick.id ? (
                  <select
                    value={editData.outcome}
                    onChange={(e) => setEditData((d) => ({ ...d, outcome: e.target.value as PickOutcome }))}
                    className="bg-neutral-700 border border-neutral-600 rounded px-2 py-1 text-xs text-white"
                  >
                    <option value="PENDING">PENDING</option>
                    <option value="WIN">WIN</option>
                    <option value="LOSS">LOSS</option>
                  </select>
                ) : (
                  outcomeBadge(pick.outcome)
                )}
              </td>
              <td className="py-3">
                <div className="flex gap-1">
                  {editing === pick.id ? (
                    <>
                      <button
                        onClick={() => saveEdit(pick)}
                        className="px-2 py-1 bg-emerald-700 hover:bg-emerald-600 text-white text-xs rounded transition-colors"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditing(null)}
                        className="px-2 py-1 bg-neutral-700 hover:bg-neutral-600 text-neutral-300 text-xs rounded transition-colors"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => startEdit(pick)}
                        className="px-2 py-1 bg-neutral-700 hover:bg-neutral-600 text-neutral-300 text-xs rounded transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(pick.id)}
                        className="px-2 py-1 bg-red-900/50 hover:bg-red-800/50 text-red-400 text-xs rounded transition-colors"
                      >
                        Del
                      </button>
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
