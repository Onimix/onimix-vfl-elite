import type {
  MatchResult,
  MatchAnalysis,
  PreMatchJSON,
  RuleResult,
  TeamEnergyCard,
  TeamFlag,
} from "./types";

// ─── Team Energy Builder ──────────────────────────────────────────────────────

export function buildEnergyCards(results: MatchResult[]): Map<string, TeamEnergyCard> {
  const cards = new Map<string, TeamEnergyCard>();

  for (const match of results) {
    // Home team
    const homeCard = cards.get(match.home) ?? emptyCard(match.home);
    homeCard.lastHomeScore = match.homeScore;
    homeCard.lastHomeDate = match.date;
    homeCard.lastHomeSlot = match.slot;
    homeCard.lastGoalsScored = match.homeScore;
    homeCard.lastGoalsConceeded = match.awayScore;
    cards.set(match.home, homeCard);

    // Away team
    const awayCard = cards.get(match.away) ?? emptyCard(match.away);
    awayCard.lastAwayScore = match.awayScore;
    awayCard.lastAwayDate = match.date;
    awayCard.lastAwaySlot = match.slot;
    awayCard.lastGoalsScored = match.awayScore;
    awayCard.lastGoalsConceeded = match.homeScore;
    cards.set(match.away, awayCard);
  }

  // Assign flags
  for (const [, card] of cards) {
    card.flags = computeFlags(card);
  }

  return cards;
}

function emptyCard(team: string): TeamEnergyCard {
  return {
    team,
    lastHomeScore: null,
    lastAwayScore: null,
    lastHomeDate: null,
    lastAwayDate: null,
    lastHomeSlot: null,
    lastAwaySlot: null,
    lastGoalsConceeded: null,
    lastGoalsScored: null,
    flags: [],
  };
}

function computeFlags(card: TeamEnergyCard): TeamFlag[] {
  const flags: TeamFlag[] = [];

  // No data at all = unknown energy
  if (card.lastHomeScore === null && card.lastAwayScore === null) {
    flags.push("UNKNOWN");
    return flags;
  }

  if (card.lastHomeScore === 0) flags.push("HOME_ZERO_TRAP");
  if (card.lastAwayScore === 0) flags.push("AWAY_ZERO_TRAP");
  if (card.lastGoalsScored !== null && card.lastGoalsScored >= 3) flags.push("COOLDOWN");
  if (card.lastGoalsConceeded !== null && card.lastGoalsConceeded >= 4) flags.push("REPAIR");

  // Low energy flags — scored exactly 1 (not zero, not strong)
  if (card.lastAwayScore === 1) flags.push("LOW_AWAY_ENERGY");
  if (card.lastHomeScore === 1) flags.push("LOW_HOME_ENERGY");

  if (flags.length === 0) flags.push("CLEAN");

  return flags;
}

// ─── ONIMIX Engine ────────────────────────────────────────────────────────────

export function analyzeMatch(
  homeTeam: string,
  awayTeam: string,
  slot: string,
  date: string,
  yesterdayResults: MatchResult[],
  preMatchJSON: PreMatchJSON | null
): MatchAnalysis {
  const energyCards = buildEnergyCards(yesterdayResults);
  const homeCard = energyCards.get(homeTeam);
  const awayCard = energyCards.get(awayTeam);

  const yesterdayRules = evaluateYesterdayRules(homeTeam, awayTeam, homeCard, awayCard, yesterdayResults);
  const jsonRules = preMatchJSON ? evaluateJSONRules(preMatchJSON) : [];

  // Check instant skip triggers
  const instantSkipResult = checkInstantSkips(homeCard, awayCard, homeTeam, awayTeam, yesterdayResults, preMatchJSON);

  let yesterdayScore = 0;
  let jsonScore = 0;

  if (!instantSkipResult.skip) {
    yesterdayScore = Math.min(18, yesterdayRules.reduce((s, r) => s + r.points, 0));
    jsonScore = preMatchJSON ? Math.min(12, jsonRules.reduce((s, r) => s + r.points, 0)) : 0;
  }

  const decision = resolveDecision(yesterdayScore, jsonScore, instantSkipResult.skip, !!preMatchJSON);
  const confidence = resolveConfidence(yesterdayScore, jsonScore, instantSkipResult.skip);

  return {
    homeTeam,
    awayTeam,
    slot,
    date,
    yesterdayScore,
    jsonScore,
    totalScore: yesterdayScore + jsonScore,
    decision,
    confidence,
    instantSkip: instantSkipResult.skip,
    instantSkipReason: instantSkipResult.reason,
    yesterdayRules,
    jsonRules,
  };
}

// ─── Instant Skip Checks ──────────────────────────────────────────────────────

function checkInstantSkips(
  homeCard: TeamEnergyCard | undefined,
  awayCard: TeamEnergyCard | undefined,
  homeTeam: string,
  awayTeam: string,
  yesterdayResults: MatchResult[],
  json: PreMatchJSON | null
): { skip: boolean; reason: string | null } {
  // Skip 1: Zero trap with no override
  if (homeCard?.flags.includes("HOME_ZERO_TRAP")) {
    const overrideOk = checkNewOpponentOverride(awayCard, json);
    if (!overrideOk) {
      return { skip: true, reason: `${homeTeam} HOME ZERO TRAP — away team cannot override` };
    }
  }
  if (awayCard?.flags.includes("AWAY_ZERO_TRAP")) {
    const overrideOk = checkNewOpponentOverride(homeCard, json);
    if (!overrideOk) {
      return { skip: true, reason: `${awayTeam} AWAY ZERO TRAP — home team cannot override` };
    }
  }

  // Skip 2: Repair mode
  if (homeCard?.flags.includes("REPAIR")) {
    return { skip: true, reason: `${homeTeam} in REPAIR MODE (conceded 4+ recently)` };
  }
  if (awayCard?.flags.includes("REPAIR")) {
    return { skip: true, reason: `${awayTeam} in REPAIR MODE (conceded 4+ recently)` };
  }

  // Skip 3: Cooldown
  if (homeCard?.flags.includes("COOLDOWN")) {
    return { skip: true, reason: `${homeTeam} in COOLDOWN (scored 3+ recently)` };
  }
  if (awayCard?.flags.includes("COOLDOWN")) {
    return { skip: true, reason: `${awayTeam} in COOLDOWN (scored 3+ recently)` };
  }

  // Skip 8 (NEW): Both teams played AWAY yesterday and both scored ≤1
  // Combined low away energy — not enough firepower to guarantee 2+ goals today
  const homeWasAway = homeCard?.lastAwayDate !== null && homeCard?.lastHomeDate === null;
  const awayWasAway = awayCard?.lastAwayDate !== null && awayCard?.lastHomeDate === null;
  if (homeWasAway && awayWasAway) {
    const homeAwayScore = homeCard?.lastAwayScore ?? 0;
    const awayAwayScore = awayCard?.lastAwayScore ?? 0;
    if (homeAwayScore <= 1 && awayAwayScore <= 1) {
      return {
        skip: true,
        reason: `Both teams played AWAY yesterday with low scores (${homeTeam} scored ${homeAwayScore}, ${awayTeam} scored ${awayAwayScore}) — combined low energy`,
      };
    }
  }

  // Skip 10 (NEW): Away team played AWAY yesterday with ≤1 goal, now away again
  // Consecutive away with low away energy — unsustainable attacking output
  if (awayCard?.lastAwayDate !== null && awayCard?.lastHomeDate === null) {
    const awayPrevScore = awayCard?.lastAwayScore ?? 0;
    if (awayPrevScore <= 1) {
      return {
        skip: true,
        reason: `${awayTeam} played AWAY yesterday (scored ${awayPrevScore}) and is away again — consecutive low away energy trap`,
      };
    }
  }

  // Skip 11 (NEW): Away team scored 2+ away yesterday but home team scored ≤1 at home
  // Overconfidence imbalance — strong away form vs weak home form often = 0:0 draw trap
  const awayWasAwayForTrap = awayCard?.lastAwayDate !== null && awayCard?.lastHomeDate === null;
  const homeWasHomeForTrap = homeCard?.lastHomeDate !== null && homeCard?.lastAwayDate === null;
  if (awayWasAwayForTrap && homeWasHomeForTrap) {
    const awayScore = awayCard?.lastAwayScore ?? 0;
    const homeScore = homeCard?.lastHomeScore ?? 0;
    if (awayScore >= 2 && homeScore <= 1) {
      return {
        skip: true,
        reason: `${awayTeam} scored ${awayScore} away yesterday but ${homeTeam} only scored ${homeScore} at home — overconfidence imbalance trap`,
      };
    }
  }

  // Skip 12 (NEW): Both teams drew their last matches — draw trap pattern
  const homeDrew =
    homeCard &&
    homeCard.lastGoalsScored !== null &&
    homeCard.lastGoalsConceeded !== null &&
    homeCard.lastGoalsScored === homeCard.lastGoalsConceeded;
  const awayDrew =
    awayCard &&
    awayCard.lastGoalsScored !== null &&
    awayCard.lastGoalsConceeded !== null &&
    awayCard.lastGoalsScored === awayCard.lastGoalsConceeded;
  if (homeDrew && awayDrew) {
    return {
      skip: true,
      reason: `Both teams drew their last matches (${homeTeam}: ${homeCard?.lastGoalsScored}:${homeCard?.lastGoalsConceeded}, ${awayTeam}: ${awayCard?.lastGoalsScored}:${awayCard?.lastGoalsConceeded}) — draw trap pattern`,
    };
  }

  // Skip 13 (NEW): Home team was AWAY yesterday with ≤1 goal, now HOME
  // Position switch low energy — scored poorly away, unreliable at home
  const homeSwitchedFromAway =
    homeCard?.lastAwayDate !== null && homeCard?.lastHomeDate === null;
  if (homeSwitchedFromAway) {
    const homePrevAwayScore = homeCard?.lastAwayScore ?? 0;
    if (homePrevAwayScore <= 1) {
      return {
        skip: true,
        reason: `${homeTeam} scored ${homePrevAwayScore} away yesterday and switched to HOME — position switch low energy trap`,
      };
    }
  }

  // Skip 14 (NEW): Strong home team (2+ home) switching to AWAY vs weak away team (≤1 away) switching to HOME
  // Overconfidence reversal — dominant home team going away + weak away team coming home = 0:0 trap
  const homeSwitchedFromHome =
    homeCard?.lastHomeDate !== null && homeCard?.lastAwayDate === null;
  const awaySwitchedFromAway =
    awayCard?.lastAwayDate !== null && awayCard?.lastHomeDate === null;
  if (homeSwitchedFromHome && awaySwitchedFromAway) {
    const homePrevHomeScore = homeCard?.lastHomeScore ?? 0;
    const awayPrevAwayScore = awayCard?.lastAwayScore ?? 0;
    if (homePrevHomeScore >= 2 && awayPrevAwayScore <= 1) {
      return {
        skip: true,
        reason: `${homeTeam} dominated at home (${homePrevHomeScore}) now away vs ${awayTeam} scored ${awayPrevAwayScore} away now home — overconfidence reversal trap`,
      };
    }
  }

  // Skip 15 (NEW): Away team scored 1 at home yesterday, now AWAY
  // Low home output switching to away — unreliable attack in both positions
  // (0 at home is already caught by HOME_ZERO_TRAP)
  const awaySwitchedFromHome =
    awayCard?.lastHomeDate !== null && awayCard?.lastAwayDate === null;
  if (awaySwitchedFromHome) {
    const awayPrevHomeScore = awayCard?.lastHomeScore ?? 0;
    if (awayPrevHomeScore === 1) {
      return {
        skip: true,
        reason: `${awayTeam} scored only ${awayPrevHomeScore} at home yesterday and switched to AWAY — low home output now away trap`,
      };
    }
  }

  // Skip 16 (NEW): Home team scored 2+ away yesterday vs away team scored ≤1 at home yesterday
  // Overconfidence trap — strong away form carrying into home vs weak home opponent
  // Mirror of Skip 11 (which checks away team strong away vs home team weak home)
  const homeWasAwayS16 = homeCard?.lastAwayDate !== null && homeCard?.lastHomeDate === null;
  const awayWasHomeS16 = awayCard?.lastHomeDate !== null && awayCard?.lastAwayDate === null;
  if (homeWasAwayS16 && awayWasHomeS16) {
    const homePrevAwayScore = homeCard?.lastAwayScore ?? 0;
    const awayPrevHomeScore = awayCard?.lastHomeScore ?? 0;
    if (homePrevAwayScore >= 2 && awayPrevHomeScore <= 1) {
      return {
        skip: true,
        reason: `${homeTeam} scored ${homePrevAwayScore} away yesterday (strong) vs ${awayTeam} scored ${awayPrevHomeScore} at home (weak) — overconfidence trap`,
      };
    }
  }

  // Skip 17 (NEW): Both teams played HOME yesterday and both scored ≤1
  // Combined low home energy — both teams had weak home performances
  const bothHomeS17 =
    homeCard?.lastHomeDate !== null && awayCard?.lastHomeDate !== null;
  if (bothHomeS17) {
    const homePrevHomeScore = homeCard?.lastHomeScore ?? 0;
    const awayPrevHomeScore = awayCard?.lastHomeScore ?? 0;
    if (homePrevHomeScore <= 1 && awayPrevHomeScore <= 1) {
      return {
        skip: true,
        reason: `Both teams played HOME yesterday with low scores (${homeTeam}: ${homePrevHomeScore}, ${awayTeam}: ${awayPrevHomeScore}) — combined low home energy`,
      };
    }
  }

  // Skip 18 (NEW): Both teams scored 2+ yesterday but BOTH switched positions
  // Double position switch trap — strong form from both sides but unreliable venue performance
  const homeSwitched = (homeCard?.lastHomeDate !== null && homeCard?.lastAwayDate === null) ||
    (homeCard?.lastAwayDate !== null && homeCard?.lastHomeDate === null);
  const awaySwitched = (awayCard?.lastHomeDate !== null && awayCard?.lastAwayDate === null) ||
    (awayCard?.lastAwayDate !== null && awayCard?.lastHomeDate === null);
  if (homeSwitched && awaySwitched) {
    const homePrevScore = homeCard?.lastHomeScore ?? homeCard?.lastAwayScore ?? 0;
    const awayPrevScore = awayCard?.lastHomeScore ?? awayCard?.lastAwayScore ?? 0;
    if (homePrevScore >= 2 && awayPrevScore >= 2) {
      return {
        skip: true,
        reason: `Both teams scored 2+ yesterday but BOTH switched positions (${homeTeam}: ${homePrevScore}, ${awayTeam}: ${awayPrevScore}) — double position switch trap`,
      };
    }
  }

  // Skip 9 (NEW): Unknown team energy — no yesterday data + opponent not strong
  if (homeCard?.flags.includes("UNKNOWN") || awayCard?.flags.includes("UNKNOWN")) {
    const unknownTeam = homeCard?.flags.includes("UNKNOWN") ? homeTeam : awayTeam;
    const knownCard = homeCard?.flags.includes("UNKNOWN") ? awayCard : homeCard;
    // Only allow pick if known opponent scored 2+ and is clean
    const knownIsStrong =
      knownCard &&
      !knownCard.flags.includes("UNKNOWN") &&
      !knownCard.flags.includes("COOLDOWN") &&
      !knownCard.flags.includes("REPAIR") &&
      !knownCard.flags.includes("HOME_ZERO_TRAP") &&
      !knownCard.flags.includes("AWAY_ZERO_TRAP") &&
      (knownCard.lastGoalsScored ?? 0) >= 2;
    if (!knownIsStrong) {
      return {
        skip: true,
        reason: `${unknownTeam} has NO yesterday same-slot data (unknown energy) and opponent is not strong enough to carry`,
      };
    }
  }

  // Skip 5: 0:0 probability above 10%
  if (json && json.score00prob > 10) {
    return { skip: true, reason: `0:0 probability ${json.score00prob}% exceeds 10% threshold` };
  }

  // Skip 7: farNearOdds on Under line
  if (json && json.farNearOddsOverLine === 1 && json.farNearOddsLevel === "under") {
    return { skip: true, reason: "farNearOdds:1 on Under line — system targeting low scoring" };
  }

  // Skip 6: Same fixture yesterday in same slot with 0:0 or 1 total goal
  const sameFixture = yesterdayResults.find(
    (r) =>
      ((r.home === homeTeam && r.away === awayTeam) ||
        (r.home === awayTeam && r.away === homeTeam))
  );
  if (sameFixture) {
    const total = sameFixture.homeScore + sameFixture.awayScore;
    if (total <= 1) {
      return { skip: true, reason: `Same fixture yesterday scored only ${total} total goals` };
    }
  }

  return { skip: false, reason: null };
}

function checkNewOpponentOverride(
  opponentCard: TeamEnergyCard | undefined,
  json: PreMatchJSON | null
): boolean {
  if (!opponentCard) return false;
  if (opponentCard.flags.includes("UNKNOWN")) return false; // unknown energy cannot override
  const scored2Plus = (opponentCard.lastHomeScore ?? 0) >= 2 || (opponentCard.lastAwayScore ?? 0) >= 2;
  const noZeroTrap = !opponentCard.flags.includes("HOME_ZERO_TRAP") && !opponentCard.flags.includes("AWAY_ZERO_TRAP");
  const notRepair = !opponentCard.flags.includes("REPAIR");
  const notCooldown = !opponentCard.flags.includes("COOLDOWN");
  const jsonOk = json ? json.over05 >= 75 : false;
  return scored2Plus && noZeroTrap && notRepair && notCooldown && jsonOk;
}

// ─── Yesterday Rules (Part A) ─────────────────────────────────────────────────

function evaluateYesterdayRules(
  homeTeam: string,
  awayTeam: string,
  homeCard: TeamEnergyCard | undefined,
  awayCard: TeamEnergyCard | undefined,
  yesterdayResults: MatchResult[]
): RuleResult[] {
  const rules: RuleResult[] = [];

  // A1 — Home zero trap clear
  const homeZero = homeCard?.lastHomeScore === 0;
  rules.push({
    rule: "A1",
    label: "Home Zero Trap Clear",
    passed: !homeZero,
    points: !homeZero ? 3 : 0,
    maxPoints: 3,
    detail: homeZero
      ? `${homeTeam} scored 0 at home in last same-slot appearance`
      : `${homeTeam} scored ${homeCard?.lastHomeScore ?? "?"} at home — clear`,
  });

  // A2 — Away zero trap clear
  const awayZero = awayCard?.lastAwayScore === 0;
  rules.push({
    rule: "A2",
    label: "Away Zero Trap Clear",
    passed: !awayZero,
    points: !awayZero ? 3 : 0,
    maxPoints: 3,
    detail: awayZero
      ? `${awayTeam} scored 0 away in last same-slot appearance`
      : `${awayTeam} scored ${awayCard?.lastAwayScore ?? "?"} away — clear`,
  });

  // A3 — Position switch zero trap
  const homeSwitchedFromAway = homeCard?.lastAwayScore === 0 && homeCard?.lastHomeScore === null;
  const awaySwitchedFromHome = awayCard?.lastHomeScore === 0 && awayCard?.lastAwayScore === null;
  const switchZeroClear = !homeSwitchedFromAway && !awaySwitchedFromHome;
  rules.push({
    rule: "A3",
    label: "Position Switch Zero Clear",
    passed: switchZeroClear,
    points: switchZeroClear ? 2 : 0,
    maxPoints: 2,
    detail: switchZeroClear
      ? "No position-switched zero trap detected"
      : `Position switch zero trap: ${homeSwitchedFromAway ? homeTeam : awayTeam}`,
  });

  // A4 — No cooldown or repair
  const hasCooldown =
    homeCard?.flags.includes("COOLDOWN") || awayCard?.flags.includes("COOLDOWN");
  const hasRepair =
    homeCard?.flags.includes("REPAIR") || awayCard?.flags.includes("REPAIR");
  const a4Pass = !hasCooldown && !hasRepair;
  rules.push({
    rule: "A4",
    label: "No Cooldown / Repair",
    passed: a4Pass,
    points: a4Pass ? 3 : 0,
    maxPoints: 3,
    detail: a4Pass
      ? "Neither team on cooldown or repair"
      : `${hasCooldown ? "COOLDOWN" : "REPAIR"} active`,
  });

  // A5 — New opponent override (only relevant if a trap exists)
  const trapExists =
    homeCard?.flags.includes("HOME_ZERO_TRAP") ||
    awayCard?.flags.includes("AWAY_ZERO_TRAP");
  const a5Pass = !trapExists; // If no trap, full points by default
  rules.push({
    rule: "A5",
    label: "New Opponent Override",
    passed: a5Pass,
    points: a5Pass ? 2 : 0,
    maxPoints: 2,
    detail: a5Pass
      ? "No trap requiring override"
      : "Trap exists — override check required",
  });

  // A6 — Same pair repeat check
  const samePair = yesterdayResults.find(
    (r) =>
      (r.home === homeTeam && r.away === awayTeam) ||
      (r.home === awayTeam && r.away === homeTeam)
  );
  let a6Pass = true;
  let a6Detail = "No same-pair repeat detected";
  if (samePair) {
    const total = samePair.homeScore + samePair.awayScore;
    if (total <= 1) {
      a6Pass = false;
      a6Detail = `Same pair yesterday: ${samePair.homeScore}:${samePair.awayScore} (${total} total goals)`;
    } else {
      a6Detail = `Same pair yesterday: ${samePair.homeScore}:${samePair.awayScore} — acceptable`;
    }
  }
  rules.push({
    rule: "A6",
    label: "Same Pair Repeat Check",
    passed: a6Pass,
    points: a6Pass ? 2 : 0,
    maxPoints: 2,
    detail: a6Detail,
  });

  // A7 — Both teams home yesterday
  const bothHome =
    homeCard?.lastHomeDate !== null && awayCard?.lastHomeDate !== null;
  if (bothHome) {
    const bothScored =
      (homeCard?.lastHomeScore ?? 0) >= 1 && (awayCard?.lastHomeScore ?? 0) >= 1;
    rules.push({
      rule: "A7",
      label: "Both Teams Home Yesterday Scored",
      passed: bothScored,
      points: bothScored ? 2 : 0,
      maxPoints: 2,
      detail: bothScored
        ? `${homeTeam} scored ${homeCard?.lastHomeScore}, ${awayTeam} scored ${awayCard?.lastHomeScore} at home`
        : `One or both scored 0 at home yesterday`,
    });
  }

  // A8 — Both teams away yesterday (UPGRADED)
  // Scoring: both scored 2+ = 2pts | one scored 2+ one scored 1 = 1pt | both scored exactly 1 = 0pts DANGER | either 0 = already caught by A2
  const homeWasAwayOnly = homeCard?.lastAwayDate !== null && homeCard?.lastHomeDate === null;
  const awayWasAwayOnly = awayCard?.lastAwayDate !== null && awayCard?.lastHomeDate === null;
  if (homeWasAwayOnly && awayWasAwayOnly) {
    const homeAway = homeCard?.lastAwayScore ?? 0;
    const awayAway = awayCard?.lastAwayScore ?? 0;
    const bothScored2Plus = homeAway >= 2 && awayAway >= 2;
    const onlyOneStrong = (homeAway >= 2 && awayAway === 1) || (homeAway === 1 && awayAway >= 2);
    const bothLow = homeAway <= 1 && awayAway <= 1;
    const a8Points = bothScored2Plus ? 2 : onlyOneStrong ? 1 : 0;
    rules.push({
      rule: "A8",
      label: "Both Teams Away Yesterday — Energy Check",
      passed: !bothLow,
      points: a8Points,
      maxPoints: 2,
      detail: bothLow
        ? `DANGER: Both scored ≤1 away (${homeTeam}: ${homeAway}, ${awayTeam}: ${awayAway}) — low combined energy`
        : bothScored2Plus
        ? `Both scored 2+ away (${homeTeam}: ${homeAway}, ${awayTeam}: ${awayAway}) — strong`
        : `Mixed energy: ${homeTeam}: ${homeAway}, ${awayTeam}: ${awayAway} away`,
    });
  } else if (homeCard?.lastAwayDate !== null || awayCard?.lastAwayDate !== null) {
    // One of them was away, one was home — combined check
    const awayTeamAwayScore = awayCard?.lastAwayScore ?? null;
    const homeTeamHomeScore = homeCard?.lastHomeScore ?? null;
    if (awayTeamAwayScore !== null && homeTeamHomeScore !== null) {
      // Both positions have data — check combined energy
      const bothLow = awayTeamAwayScore <= 1 && homeTeamHomeScore <= 1;
      const awayStrong = awayTeamAwayScore >= 2;
      const homeStrong = homeTeamHomeScore >= 2;
      const passed = !bothLow;
      const a8Points = bothLow ? 0 : (awayStrong && homeStrong) ? 2 : 1;
      rules.push({
        rule: "A8",
        label: "Mixed Home/Away Energy Check",
        passed,
        points: a8Points,
        maxPoints: 2,
        detail: bothLow
          ? `DANGER: ${awayTeam} scored ${awayTeamAwayScore} away + ${homeTeam} scored ${homeTeamHomeScore} at home — combined low energy`
          : `${awayTeam} scored ${awayTeamAwayScore} away, ${homeTeam} scored ${homeTeamHomeScore} at home`,
      });
    } else if (awayTeamAwayScore !== null) {
      const passed = awayTeamAwayScore >= 1;
      rules.push({
        rule: "A8",
        label: "Away Team Away Score Yesterday",
        passed,
        points: passed ? (awayTeamAwayScore >= 2 ? 2 : 1) : 0,
        maxPoints: 2,
        detail: `${awayTeam} scored ${awayTeamAwayScore} away yesterday`,
      });
    }
  }

  // A9 (NEW) — Unknown team energy check
  const homeUnknown = homeCard?.flags.includes("UNKNOWN") ?? true;
  const awayUnknown = awayCard?.flags.includes("UNKNOWN") ?? true;
  if (homeUnknown || awayUnknown) {
    const unknownTeams = [homeUnknown ? homeTeam : null, awayUnknown ? awayTeam : null]
      .filter(Boolean)
      .join(", ");
    rules.push({
      rule: "A9",
      label: "Unknown Team Energy",
      passed: false,
      points: 0,
      maxPoints: 3,
      detail: `${unknownTeams} — no yesterday same-slot data. Energy unknown, reduces confidence`,
    });
  } else {
    rules.push({
      rule: "A9",
      label: "Both Teams Have Yesterday Data",
      passed: true,
      points: 3,
      maxPoints: 3,
      detail: `Both ${homeTeam} and ${awayTeam} have same-slot history`,
    });
  }

  // A10 (NEW) — Away-High vs Home-Low Imbalance Trap
  // When away team scored 2+ away yesterday but home team scored ≤1 at home
  // Overconfidence imbalance often results in 0:0 or low-scoring draw
  const awayWasAwayA10 = awayCard?.lastAwayDate !== null && awayCard?.lastHomeDate === null;
  const homeWasHomeA10 = homeCard?.lastHomeDate !== null && homeCard?.lastAwayDate === null;
  if (awayWasAwayA10 && homeWasHomeA10) {
    const a10AwayScore = awayCard?.lastAwayScore ?? 0;
    const a10HomeScore = homeCard?.lastHomeScore ?? 0;
    const imbalanceTrap = a10AwayScore >= 2 && a10HomeScore <= 1;
    rules.push({
      rule: "A10",
      label: "Away-High vs Home-Low Imbalance",
      passed: !imbalanceTrap,
      points: imbalanceTrap ? 0 : 2,
      maxPoints: 2,
      detail: imbalanceTrap
        ? `TRAP: ${awayTeam} scored ${a10AwayScore} away (strong) vs ${homeTeam} scored ${a10HomeScore} at home (weak) — overconfidence imbalance`
        : `${awayTeam} scored ${a10AwayScore} away, ${homeTeam} scored ${a10HomeScore} at home — balanced`,
    });
  }

  // A11 (NEW) — Consecutive Away Low Energy for away team
  // Away team played away yesterday with ≤1 goal, now away again
  const awayConsecutiveAway = awayCard?.lastAwayDate !== null && awayCard?.lastHomeDate === null;
  if (awayConsecutiveAway) {
    const a11AwayScore = awayCard?.lastAwayScore ?? 0;
    const consecutiveLow = a11AwayScore <= 1;
    rules.push({
      rule: "A11",
      label: "Consecutive Away Low Energy",
      passed: !consecutiveLow,
      points: consecutiveLow ? 0 : 2,
      maxPoints: 2,
      detail: consecutiveLow
        ? `TRAP: ${awayTeam} played away yesterday (scored ${a11AwayScore}) and is away again — unsustainable`
        : `${awayTeam} scored ${a11AwayScore} away yesterday — sufficient energy for consecutive away`,
    });
  }

  // A12 (NEW) — Position Switch Low Energy for home team
  // Home team was away yesterday with ≤1 goal, now home — unreliable attack
  const homeSwitchedFromAwayA12 =
    homeCard?.lastAwayDate !== null && homeCard?.lastHomeDate === null;
  if (homeSwitchedFromAwayA12) {
    const a12HomePrevAway = homeCard?.lastAwayScore ?? 0;
    const positionSwitchLow = a12HomePrevAway <= 1;
    rules.push({
      rule: "A12",
      label: "Position Switch Low Energy (Home)",
      passed: !positionSwitchLow,
      points: positionSwitchLow ? 0 : 2,
      maxPoints: 2,
      detail: positionSwitchLow
        ? `TRAP: ${homeTeam} scored ${a12HomePrevAway} away yesterday, now HOME — position switch low energy`
        : `${homeTeam} scored ${a12HomePrevAway} away yesterday, now HOME — sufficient energy`,
    });
  }

  // A13 (NEW) — Overconfidence Reversal
  // Strong home team (2+ home) switching to AWAY vs weak away team (≤1 away) switching to HOME
  const homeStrongSwitchA13 =
    homeCard?.lastHomeDate !== null && homeCard?.lastAwayDate === null;
  const awayWeakSwitchA13 =
    awayCard?.lastAwayDate !== null && awayCard?.lastHomeDate === null;
  if (homeStrongSwitchA13 && awayWeakSwitchA13) {
    const a13HomePrevHome = homeCard?.lastHomeScore ?? 0;
    const a13AwayPrevAway = awayCard?.lastAwayScore ?? 0;
    const reversalTrap = a13HomePrevHome >= 2 && a13AwayPrevAway <= 1;
    rules.push({
      rule: "A13",
      label: "Overconfidence Reversal",
      passed: !reversalTrap,
      points: reversalTrap ? 0 : 2,
      maxPoints: 2,
      detail: reversalTrap
        ? `TRAP: ${homeTeam} dominated at home (${a13HomePrevHome}) now away vs ${awayTeam} weak away (${a13AwayPrevAway}) now home — overconfidence reversal`
        : `${homeTeam} home ${a13HomePrevHome}→away, ${awayTeam} away ${a13AwayPrevAway}→home — balanced`,
    });
  }

  // A14 (NEW) — Away team scored exactly 1 at home yesterday, now AWAY
  // Low home output switching to away — unreliable in both positions
  const awaySwitchedFromHomeA14 =
    awayCard?.lastHomeDate !== null && awayCard?.lastAwayDate === null;
  if (awaySwitchedFromHomeA14) {
    const a14AwayPrevHome = awayCard?.lastHomeScore ?? 0;
    const lowHomeSwitch = a14AwayPrevHome === 1;
    rules.push({
      rule: "A14",
      label: "Low Home Output → Away Switch",
      passed: !lowHomeSwitch,
      points: lowHomeSwitch ? 0 : 2,
      maxPoints: 2,
      detail: lowHomeSwitch
        ? `TRAP: ${awayTeam} scored only 1 at home yesterday, now AWAY — weak attack in both positions`
        : `${awayTeam} scored ${a14AwayPrevHome} at home yesterday, now AWAY — sufficient`,
    });
  }

  // A15 (NEW) — Home team strong away (2+) vs away team weak home (≤1)
  // Overconfidence trap — strong away form into home vs weak home opponent
  const homeWasAwayA15 = homeCard?.lastAwayDate !== null && homeCard?.lastHomeDate === null;
  const awayWasHomeA15 = awayCard?.lastHomeDate !== null && awayCard?.lastAwayDate === null;
  if (homeWasAwayA15 && awayWasHomeA15) {
    const a15HomePrevAway = homeCard?.lastAwayScore ?? 0;
    const a15AwayPrevHome = awayCard?.lastHomeScore ?? 0;
    const overconfTrap = a15HomePrevAway >= 2 && a15AwayPrevHome <= 1;
    rules.push({
      rule: "A15",
      label: "Home Strong Away vs Away Weak Home",
      passed: !overconfTrap,
      points: overconfTrap ? 0 : 2,
      maxPoints: 2,
      detail: overconfTrap
        ? `TRAP: ${homeTeam} scored ${a15HomePrevAway} away (strong) vs ${awayTeam} scored ${a15AwayPrevHome} at home (weak) — overconfidence trap`
        : `${homeTeam} away ${a15HomePrevAway}, ${awayTeam} home ${a15AwayPrevHome} — balanced`,
    });
  }

  // A16 (NEW) — Both teams HOME yesterday with both scoring ≤1
  // Combined low home energy — weak attack from both sides
  const bothHomeA16 =
    homeCard?.lastHomeDate !== null && awayCard?.lastHomeDate !== null;
  if (bothHomeA16) {
    const a16HomePrevHome = homeCard?.lastHomeScore ?? 0;
    const a16AwayPrevHome = awayCard?.lastHomeScore ?? 0;
    const bothLow = a16HomePrevHome <= 1 && a16AwayPrevHome <= 1;
    rules.push({
      rule: "A16",
      label: "Both Home Yesterday Low Energy",
      passed: !bothLow,
      points: bothLow ? 0 : 2,
      maxPoints: 2,
      detail: bothLow
        ? `TRAP: Both teams scored ≤1 at home yesterday (${homeTeam}: ${a16HomePrevHome}, ${awayTeam}: ${a16AwayPrevHome}) — combined low home energy`
        : `${homeTeam} scored ${a16HomePrevHome}, ${awayTeam} scored ${a16AwayPrevHome} at home — acceptable`,
    });
  }

  // A17 (NEW) — Both teams scored 2+ yesterday but BOTH switched positions
  // Double position switch — strong form but unreliable in new venue
  const homeSwitchedA17 = (homeCard?.lastHomeDate !== null && homeCard?.lastAwayDate === null) ||
    (homeCard?.lastAwayDate !== null && homeCard?.lastHomeDate === null);
  const awaySwitchedA17 = (awayCard?.lastHomeDate !== null && awayCard?.lastAwayDate === null) ||
    (awayCard?.lastAwayDate !== null && awayCard?.lastHomeDate === null);
  if (homeSwitchedA17 && awaySwitchedA17) {
    const a17HomePrev = homeCard?.lastHomeScore ?? homeCard?.lastAwayScore ?? 0;
    const a17AwayPrev = awayCard?.lastHomeScore ?? awayCard?.lastAwayScore ?? 0;
    const doubleSwitch = a17HomePrev >= 2 && a17AwayPrev >= 2;
    rules.push({
      rule: "A17",
      label: "Double Position Switch",
      passed: !doubleSwitch,
      points: doubleSwitch ? 0 : 2,
      maxPoints: 2,
      detail: doubleSwitch
        ? `TRAP: Both scored 2+ yesterday but both switched positions (${homeTeam}: ${a17HomePrev}, ${awayTeam}: ${a17AwayPrev}) — double position switch`
        : `${homeTeam} scored ${a17HomePrev}, ${awayTeam} scored ${a17AwayPrev} — acceptable`,
    });
  }

  return rules;
}

// ─── JSON Rules (Part B) ──────────────────────────────────────────────────────

function evaluateJSONRules(json: PreMatchJSON): RuleResult[] {
  const rules: RuleResult[] = [];

  // B1 — Over 0.5 minimum
  const b1Points = json.over05 >= 93 ? 2 : json.over05 >= 90 ? 1 : 0;
  rules.push({
    rule: "B1",
    label: "Over 0.5 Minimum",
    passed: json.over05 >= 90,
    points: b1Points,
    maxPoints: 2,
    detail: `Over 0.5: ${json.over05}% (need 93%+ for full points)`,
  });

  // B2 — Over 1.5 threshold
  const b2Points = json.over15 >= 70 ? 2 : json.over15 >= 60 ? 1 : 0;
  rules.push({
    rule: "B2",
    label: "Over 1.5 Threshold",
    passed: json.over15 >= 60,
    points: b2Points,
    maxPoints: 2,
    detail: `Over 1.5: ${json.over15}% (need 70%+ for full points)`,
  });

  // B3 — farNearOdds spotlight
  let b3Points = 0;
  let b3Detail = "No farNearOdds:1 on Over line";
  if (json.farNearOddsOverLine === 1 && json.farNearOddsLevel) {
    const levelMap = { over35: 3, over25: 2, over15: 1 };
    b3Points = levelMap[json.farNearOddsLevel as keyof typeof levelMap] ?? 0;
    b3Detail = `farNearOdds:1 on ${json.farNearOddsLevel.replace("over", "Over ")} — ${b3Points} pts`;
  }
  rules.push({
    rule: "B3",
    label: "farNearOdds Spotlight",
    passed: b3Points > 0,
    points: b3Points,
    maxPoints: 3,
    detail: b3Detail,
  });

  // B4 — Both teams scoring
  const bothOver65 = json.homeOver05 >= 65 && json.awayOver05 >= 65;
  const bothOver75 = json.homeOver05 >= 75 && json.awayOver05 >= 75;
  const eitherBelow50 = json.homeOver05 < 50 || json.awayOver05 < 50;
  const b4Points = eitherBelow50 ? 0 : bothOver75 ? 2 : bothOver65 ? 1 : 0;
  rules.push({
    rule: "B4",
    label: "Both Teams Scoring Check",
    passed: bothOver65 && !eitherBelow50,
    points: b4Points,
    maxPoints: 2,
    detail: `Home Over 0.5: ${json.homeOver05}% | Away Over 0.5: ${json.awayOver05}%`,
  });

  // B5 — First half signal
  let b5Points = 0;
  let b5Deduct = 0;
  if (json.h1Over05 >= 70) b5Points = 2;
  else if (json.h1Over05 >= 60) b5Points = 1;
  if (json.h1Over05 < 40) b5Deduct = 1;
  rules.push({
    rule: "B5",
    label: "First Half Signal",
    passed: json.h1Over05 >= 60,
    points: Math.max(0, b5Points - b5Deduct),
    maxPoints: 2,
    detail: `H1 Over 0.5: ${json.h1Over05}%${b5Deduct ? " ⚠️ low first half" : ""}`,
  });

  // B6 — GG/NG Check
  const b6Deduct = json.ggYes < 35 ? 1 : 0;
  const b6Points = json.ggYes >= 45 ? 2 : json.ggYes >= 35 ? 1 : 0;
  rules.push({
    rule: "B6",
    label: "GG / NG Check",
    passed: json.ggYes >= 35,
    points: Math.max(0, b6Points - b6Deduct),
    maxPoints: 2,
    detail: `GG Yes: ${json.ggYes}%`,
  });

  // B7 — Correct score safety
  const score10and01 = json.score10prob + json.score01prob;
  let b7Points = 0;
  let b7Deduct = 0;
  if (json.score00prob < 5) b7Points = 2;
  else if (json.score00prob <= 8) b7Points = 1;
  if (score10and01 > 20) b7Deduct = 1;
  rules.push({
    rule: "B7",
    label: "Correct Score Safety",
    passed: json.score00prob < 10,
    points: Math.max(0, b7Points - b7Deduct),
    maxPoints: 2,
    detail: `0:0 prob: ${json.score00prob}% | 1:0+0:1 combined: ${score10and01}%`,
  });

  return rules;
}

// ─── Decision Resolution ──────────────────────────────────────────────────────

function resolveDecision(
  yesterdayScore: number,
  jsonScore: number,
  instantSkip: boolean,
  hasJSON: boolean
): MatchAnalysis["decision"] {
  if (instantSkip) return "SKIP";
  if (yesterdayScore < 12) return "SKIP";
  if (hasJSON && jsonScore < 8) return "SKIP";
  if (yesterdayScore >= 15 && jsonScore >= 10) return "LOCK";
  if (yesterdayScore >= 12 && jsonScore >= 8) return "PICK";
  if (yesterdayScore >= 12 && jsonScore >= 7) return "CONSIDER";
  return "SKIP";
}

function resolveConfidence(
  yesterdayScore: number,
  jsonScore: number,
  instantSkip: boolean
): MatchAnalysis["confidence"] {
  if (instantSkip) return "LOW";
  if (yesterdayScore >= 15 && jsonScore >= 10) return "HIGH";
  if (yesterdayScore >= 12 && jsonScore >= 8) return "MEDIUM";
  return "LOW";
}

// ─── Batch Analysis ───────────────────────────────────────────────────────────

export function analyzeSlot(
  todayFixtures: { home: string; away: string }[],
  slot: string,
  date: string,
  yesterdayResults: MatchResult[],
  jsonDataMap: Map<string, PreMatchJSON>
): MatchAnalysis[] {
  return todayFixtures.map((fixture) => {
    const key = `${fixture.home}v${fixture.away}`;
    const json = jsonDataMap.get(key) ?? null;
    return analyzeMatch(fixture.home, fixture.away, slot, date, yesterdayResults, json);
  });
}

// ─── Parse Pasted Results ─────────────────────────────────────────────────────

export function parseResultsText(text: string, date: string, slot: string): MatchResult[] {
  const results: MatchResult[] = [];
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);

  for (const line of lines) {
    // Matches: "ALA 1:3 BIL" or "ALA 1 - 3 BIL"
    const match = line.match(/^([A-Z]{2,5})\s+(\d+)[:\-\s](\d+)\s+([A-Z]{2,5})$/i);
    if (match) {
      const [, home, homeScore, awayScore, away] = match;
      results.push({
        home: home.toUpperCase(),
        away: away.toUpperCase(),
        homeScore: parseInt(homeScore),
        awayScore: parseInt(awayScore),
        totalGoals: parseInt(homeScore) + parseInt(awayScore),
        slot,
        date,
      });
    }
  }

  return results;
}
