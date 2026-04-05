// ─── Core Data Types ─────────────────────────────────────────────────────────

export interface MatchResult {
  home: string;
  away: string;
  homeScore: number;
  awayScore: number;
  totalGoals: number;
  slot: string; // e.g. "13:10"
  date: string; // e.g. "2024-03-28"
}

export interface TeamEnergyCard {
  team: string;
  lastHomeScore: number | null;
  lastAwayScore: number | null;
  lastHomeDate: string | null;
  lastAwayDate: string | null;
  lastHomeSlot: string | null;
  lastAwaySlot: string | null;
  lastGoalsConceded: number | null;
  lastGoalsScored: number | null;
  lastHomeTotalGoals: number | null;
  lastAwayTotalGoals: number | null;
  flags: TeamFlag[];
}

export type TeamFlag =
  | "HOME_ZERO_TRAP"
  | "AWAY_ZERO_TRAP"
  | "COOLDOWN"
  | "REPAIR"
  | "LOW_AWAY_ENERGY"   // scored exactly 1 away yesterday — weak signal
  | "LOW_HOME_ENERGY"   // scored exactly 1 home yesterday — weak signal
  | "UNKNOWN"           // no data in yesterday's same-slot results
  | "CLEAN"
  | "HIGH_SCORER";

// ─── Rule Evaluation ──────────────────────────────────────────────────────────

export interface RuleResult {
  rule: string;
  label: string;
  passed: boolean;
  points: number;
  maxPoints: number;
  detail: string;
}

export interface MatchAnalysis {
  homeTeam: string;
  awayTeam: string;
  slot: string;
  date: string;
  yesterdayScore: number;
  jsonScore: number;
  totalScore: number;
  decision: "LOCK" | "PICK" | "CONSIDER" | "SKIP";
  confidence: "HIGH" | "MEDIUM" | "LOW";
  instantSkip: boolean;
  instantSkipReason: string | null;
  yesterdayRules: RuleResult[];
  jsonRules: RuleResult[];
}

// ─── JSON Pre-match Data ──────────────────────────────────────────────────────

export interface PreMatchJSON {
  over05: number; // percentage 0-100
  over15: number;
  over25: number;
  over35: number;
  farNearOddsOverLine: 0 | 1 | null; // 1 = farNearOdds:1 on an Over line
  farNearOddsLevel: "over35" | "over25" | "over15" | "under" | null;
  homeOver05: number;
  awayOver05: number;
  h1Over05: number;
  ggYes: number;
  score00prob: number;
  score10prob: number;
  score01prob: number;
}

// ─── Tracker ──────────────────────────────────────────────────────────────────

export type PickOutcome = "WIN" | "LOSS" | "PENDING";

export interface TrackedPick {
  id: string;
  date: string;
  slot: string;
  homeTeam: string;
  awayTeam: string;
  decision: MatchAnalysis["decision"];
  confidence: MatchAnalysis["confidence"];
  yesterdayScore: number;
  jsonScore: number;
  market: string; // e.g. "Over 1.5"
  outcome: PickOutcome;
  actualScore: string; // e.g. "2:1"
  notes: string;
}

// ─── Session State ────────────────────────────────────────────────────────────

export interface SlotSession {
  id: string;
  date: string;
  slot: string;
  league: string;
  results: MatchResult[];
  analyses: MatchAnalysis[];
  createdAt: string;
}
