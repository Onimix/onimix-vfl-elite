// ─── ELITE System Types ──────────────────────────────────────────────────────

export interface EliteMatchup {
  home: string;
  away: string;
  key: string;       // "AST vs ARS"
  league: string;    // "England", "Spain", etc.
  hitRate: number;   // 0-100 percentage
}

export interface LiveEvent {
  eventId: string;
  home: string;
  away: string;
  key: string;
  league: string;
  kickoff: number;      // unix ms
  kickoffFormatted: string;
  minutesUntilKick: number;
}

export interface EliteAlert {
  event: LiveEvent;
  matchup: EliteMatchup;
  alertTime: string;
  status: "upcoming" | "in_window" | "missed";
}

export interface ScanResult {
  timestamp: string;
  totalEventsScanned: number;
  eliteFound: EliteAlert[];
  leaguesScanned: string[];
  scanDurationMs: number;
  telegramSent: boolean;
}

export type LeagueEliteData = Record<string, Record<string, number>>;
// { "England": { "AST vs ARS": 97.6, ... }, ... }
