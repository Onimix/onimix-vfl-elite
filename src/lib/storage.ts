import type { SlotSession, TrackedPick } from "./types";

// ─── LocalStorage Keys ────────────────────────────────────────────────────────

const SESSIONS_KEY = "onimix_sessions";
const PICKS_KEY = "onimix_picks";

// ─── Sessions ─────────────────────────────────────────────────────────────────

export function getSessions(): SlotSession[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(SESSIONS_KEY);
    return raw ? (JSON.parse(raw) as SlotSession[]) : [];
  } catch {
    return [];
  }
}

export function saveSession(session: SlotSession): void {
  if (typeof window === "undefined") return;
  const sessions = getSessions();
  const idx = sessions.findIndex((s) => s.id === session.id);
  if (idx >= 0) {
    sessions[idx] = session;
  } else {
    sessions.unshift(session);
  }
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
}

export function deleteSession(id: string): void {
  if (typeof window === "undefined") return;
  const sessions = getSessions().filter((s) => s.id !== id);
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
}

// ─── Tracked Picks ────────────────────────────────────────────────────────────

export function getPicks(): TrackedPick[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(PICKS_KEY);
    return raw ? (JSON.parse(raw) as TrackedPick[]) : [];
  } catch {
    return [];
  }
}

export function savePick(pick: TrackedPick): void {
  if (typeof window === "undefined") return;
  const picks = getPicks();
  const idx = picks.findIndex((p) => p.id === pick.id);
  if (idx >= 0) {
    picks[idx] = pick;
  } else {
    picks.unshift(pick);
  }
  localStorage.setItem(PICKS_KEY, JSON.stringify(picks));
}

export function deletePick(id: string): void {
  if (typeof window === "undefined") return;
  const picks = getPicks().filter((p) => p.id !== id);
  localStorage.setItem(PICKS_KEY, JSON.stringify(picks));
}

// ─── Stats ────────────────────────────────────────────────────────────────────

export interface PickStats {
  total: number;
  wins: number;
  losses: number;
  pending: number;
  winRate: number;
  lockWinRate: number;
  pickWinRate: number;
}

export function computeStats(picks: TrackedPick[]): PickStats {
  const settled = picks.filter((p) => p.outcome !== "PENDING");
  const wins = picks.filter((p) => p.outcome === "WIN").length;
  const losses = picks.filter((p) => p.outcome === "LOSS").length;
  const pending = picks.filter((p) => p.outcome === "PENDING").length;

  const lockSettled = settled.filter((p) => p.decision === "LOCK");
  const lockWins = lockSettled.filter((p) => p.outcome === "WIN").length;

  const pickSettled = settled.filter((p) => p.decision === "PICK");
  const pickWins = pickSettled.filter((p) => p.outcome === "WIN").length;

  return {
    total: picks.length,
    wins,
    losses,
    pending,
    winRate: settled.length > 0 ? Math.round((wins / settled.length) * 100) : 0,
    lockWinRate: lockSettled.length > 0 ? Math.round((lockWins / lockSettled.length) * 100) : 0,
    pickWinRate: pickSettled.length > 0 ? Math.round((pickWins / pickSettled.length) * 100) : 0,
  };
}

// ─── ID Generator ─────────────────────────────────────────────────────────────

export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}
