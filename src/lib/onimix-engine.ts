import type {
  MatchResult,
  MatchAnalysis,
  RuleResult,
  TeamEnergyCard,
  TeamFlag,
} from "./types";

export function buildEnergyCards(results: MatchResult[]): Map<string, TeamEnergyCard> {
  const cards = new Map<string, TeamEnergyCard>();

  for (const match of results) {
    const homeCard = cards.get(match.home) ?? emptyCard(match.home);
    homeCard.lastHomeScore = match.homeScore;
    homeCard.lastHomeDate = match.date;
    homeCard.lastHomeSlot = match.slot;
    homeCard.lastGoalsScored = match.homeScore;
    homeCard.lastGoalsConceded = match.awayScore;
    homeCard.lastHomeTotalGoals = match.homeScore + match.awayScore;
    cards.set(match.home, homeCard);

    const awayCard = cards.get(match.away) ?? emptyCard(match.away);
    awayCard.lastAwayScore = match.awayScore;
    awayCard.lastAwayDate = match.date;
    awayCard.lastAwaySlot = match.slot;
    awayCard.lastGoalsScored = match.awayScore;
    awayCard.lastGoalsConceded = match.homeScore;
    awayCard.lastAwayTotalGoals = match.homeScore + match.awayScore;
    cards.set(match.away, awayCard);
  }

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
    lastGoalsConceded: null,
    lastGoalsScored: null,
    lastHomeTotalGoals: null,
    lastAwayTotalGoals: null,
    flags: [],
  };
}

function computeFlags(card: TeamEnergyCard): TeamFlag[] {
  const flags: TeamFlag[] = [];

  if (card.lastHomeScore === null && card.lastAwayScore === null) {
    flags.push("UNKNOWN");
    return flags;
  }

  if (card.lastGoalsScored !== null && card.lastGoalsScored >= 3) {
    flags.push("HIGH_SCORER");
  }
  if (card.lastGoalsConceded !== null && card.lastGoalsConceded >= 4) {
    flags.push("REPAIR");
  }

  if (flags.length === 0) {
    flags.push("CLEAN");
  }

  return flags;
}

export function analyzeMatch(
  homeTeam: string,
  awayTeam: string,
  slot: string,
  date: string,
  yesterdayResults: MatchResult[]
): MatchAnalysis {
  const sameSlotResults = yesterdayResults.filter((r) => r.slot === slot);
  const energyCards = buildEnergyCards(sameSlotResults);
  const homeCard = energyCards.get(homeTeam);
  const awayCard = energyCards.get(awayTeam);

  const skipResult = checkInstantSkips(homeTeam, awayTeam, homeCard, awayCard, sameSlotResults);

  let score = 0;

  if (!skipResult.skip) {
    const scoringRules = evaluateScoringRules(homeTeam, awayTeam, homeCard, awayCard, sameSlotResults);
    score = Math.min(14, scoringRules.reduce((s, r) => s + r.points, 0));
  }

  const decision = resolveDecision(score, skipResult.skip);
  const confidence = resolveConfidence(score, skipResult.skip);

  return {
    homeTeam,
    awayTeam,
    slot,
    date,
    yesterdayScore: score,
    jsonScore: 0,
    totalScore: score,
    decision,
    confidence,
    instantSkip: skipResult.skip,
    instantSkipReason: skipResult.reason,
    yesterdayRules: evaluateScoringRules(homeTeam, awayTeam, homeCard, awayCard, sameSlotResults),
    jsonRules: [],
  };
}

function checkInstantSkips(
  homeTeam: string,
  awayTeam: string,
  homeCard: TeamEnergyCard | undefined,
  awayCard: TeamEnergyCard | undefined,
  yesterdayResults: MatchResult[]
): { skip: boolean; reason: string | null } {
  if (!homeCard || !awayCard) {
    return { skip: false, reason: null };
  }

  const homeScoredAny = homeCard.lastHomeScore ?? homeCard.lastAwayScore;
  const awayScoredAny = awayCard.lastHomeScore ?? awayCard.lastAwayScore;

  const homeConcededAny = homeCard.lastHomeDate !== null
    ? homeCard.lastGoalsConceded
    : homeCard.lastAwayDate !== null
      ? homeCard.lastGoalsConceded
      : null;
  const awayConcededAny = awayCard.lastHomeDate !== null
    ? awayCard.lastGoalsConceded
    : awayCard.lastAwayDate !== null
      ? awayCard.lastGoalsConceded
      : null;

  const homePlayedHome = homeCard.lastHomeDate !== null;
  const homePlayedAway = homeCard.lastAwayDate !== null;
  const awayPlayedHome = awayCard.lastHomeDate !== null;
  const awayPlayedAway = awayCard.lastAwayDate !== null;

  const homeSwitched = (homePlayedHome && !homePlayedAway) || (homePlayedAway && !homePlayedHome);
  const awaySwitched = (awayPlayedHome && !awayPlayedAway) || (awayPlayedAway && !awayPlayedHome);

  const homeScoredYesterday = homeCard.lastHomeScore ?? homeCard.lastAwayScore ?? 0;
  const awayScoredYesterday = awayCard.lastHomeScore ?? awayCard.lastAwayScore ?? 0;

  const homeHighYesterday = homeScoredYesterday >= 3;
  const awayHighYesterday = awayScoredYesterday >= 3;

  const homeFlip = homeSwitched && homeHighYesterday;
  const awayFlip = awaySwitched && awayHighYesterday;

  if (homeScoredAny !== null && homeScoredAny === 0) {
    return { skip: true, reason: `${homeTeam} scored 0 - zero trap` };
  }

  if (awayScoredAny !== null && awayScoredAny === 0) {
    return { skip: true, reason: `${awayTeam} scored 0 - zero trap` };
  }

  if (homeConcededAny !== null && homeConcededAny >= 4) {
    return { skip: true, reason: `${homeTeam} conceded 4+ - repair mode` };
  }

  if (awayConcededAny !== null && awayConcededAny >= 4) {
    return { skip: true, reason: `${awayTeam} conceded 4+ - repair mode` };
  }

  if (homeFlip || awayFlip) {
    if (homeFlip && awayFlip) {
      return { skip: true, reason: "Both teams flipping after 3+ scores" };
    }
    if (homeFlip) {
      return { skip: true, reason: `${homeTeam} scored 3+ and switched positions - compression` };
    }
    return { skip: true, reason: `${awayTeam} scored 3+ and switched positions - compression` };
  }

  const awayTeamStrongHome = awayPlayedHome && !awayPlayedAway && (awayCard.lastHomeScore ?? 0) >= 2;
  if (awayTeamStrongHome) {
    return { skip: true, reason: `${awayTeam} scored 2+ at home, now away - home-to-away suppression` };
  }

  const homeLowSamePosition = homePlayedHome && !homePlayedAway && (homeCard.lastHomeScore ?? 0) === 1;
  if (homeLowSamePosition) {
    return { skip: true, reason: `${homeTeam} scored 1 at home, same position - low energy` };
  }

  const awayTeamHomeToAway = awayPlayedHome && !awayPlayedAway && (awayCard.lastHomeScore ?? 0) >= 2;
  if (awayTeamHomeToAway) {
    return { skip: true, reason: `${awayTeam} scored 2+ at home, now away - home-to-away switch` };
  }

  const homePlayedAwayYesterday = homeCard.lastAwayDate !== null;
  const awayPlayedHomeYesterday = awayCard.lastHomeDate !== null;
  const bothSwitched = homePlayedAwayYesterday && awayPlayedHomeYesterday;
  if (bothSwitched) {
    return { skip: true, reason: "Both teams switched positions - double position switch" };
  }

  const awayTeamLowHomeScorer = awayPlayedHome && !awayPlayedAway && (awayCard.lastHomeScore ?? 0) === 1;
  if (awayTeamLowHomeScorer) {
    return { skip: true, reason: `${awayTeam} scored 1 at home, now away - low home output switch` };
  }

  if (homeScoredYesterday === 1 && awayScoredYesterday === 1) {
    return { skip: true, reason: "Both scored exactly 1 - combined low energy" };
  }

  const sameFixture = yesterdayResults.find(
    (r) =>
      (r.home === homeTeam && r.away === awayTeam) ||
      (r.home === awayTeam && r.away === homeTeam)
  );

  if (sameFixture) {
    const total = sameFixture.homeScore + sameFixture.awayScore;
    if (total <= 1) {
      return { skip: true, reason: `Same fixture scored ${total} total - low repeat` };
    }
  }

  return { skip: false, reason: null };
}

function evaluateScoringRules(
  homeTeam: string,
  awayTeam: string,
  homeCard: TeamEnergyCard | undefined,
  awayCard: TeamEnergyCard | undefined,
  yesterdayResults: MatchResult[]
): RuleResult[] {
  const rules: RuleResult[] = [];

  if (!homeCard || !awayCard) {
    return rules;
  }

  const homeScored = homeCard.lastHomeScore ?? homeCard.lastAwayScore ?? 0;
  const awayScored = awayCard.lastHomeScore ?? awayCard.lastAwayScore ?? 0;

  const bothScored = homeScored >= 1 && awayScored >= 1;
  rules.push({
    rule: "R1",
    label: "Both Teams Scored",
    passed: bothScored,
    points: bothScored ? 4 : 0,
    maxPoints: 4,
    detail: bothScored ? "Strongest OVER indicator" : "One or both failed",
  });

  const homeTotal = homeCard.lastHomeTotalGoals ?? homeCard.lastAwayTotalGoals ?? 0;
  const homeHighTotal = homeTotal >= 3;
  rules.push({
    rule: "R2",
    label: "Home Team High Total",
    passed: homeHighTotal,
    points: homeHighTotal ? 2 : 0,
    maxPoints: 2,
    detail: homeHighTotal ? `Home total: ${homeTotal} goals` : `Home total: ${homeTotal}`,
  });

  const awayTotal = awayCard.lastHomeTotalGoals ?? awayCard.lastAwayTotalGoals ?? 0;
  const awayHighTotal = awayTotal >= 3;
  rules.push({
    rule: "R3",
    label: "Away Team High Total",
    passed: awayHighTotal,
    points: awayHighTotal ? 2 : 0,
    maxPoints: 2,
    detail: awayHighTotal ? `Away total: ${awayTotal} goals` : `Away total: ${awayTotal}`,
  });

  const homeScored2 = homeScored >= 2;
  rules.push({
    rule: "R4",
    label: "Home Team 2+",
    passed: homeScored2,
    points: homeScored2 ? 2 : 0,
    maxPoints: 2,
    detail: homeScored2 ? `${homeTeam} scored ${homeScored}` : `${homeTeam} scored ${homeScored}`,
  });

  const awayScored2 = awayScored >= 2;
  rules.push({
    rule: "R5",
    label: "Away Team 2+",
    passed: awayScored2,
    points: awayScored2 ? 2 : 0,
    maxPoints: 2,
    detail: awayScored2 ? `${awayTeam} scored ${awayScored}` : `${awayTeam} scored ${awayScored}`,
  });

  const homePlayedHome = homeCard.lastHomeDate !== null;
  const homeConsistent = homePlayedHome && homeScored >= 1;
  rules.push({
    rule: "R6",
    label: "Home Consistent Position",
    passed: homeConsistent,
    points: homeConsistent ? 1 : 0,
    maxPoints: 1,
    detail: homeConsistent ? "Same position, scored 1+" : "Position inconsistent",
  });

  const bothHaveData = (homeCard.lastHomeDate !== null || homeCard.lastAwayDate !== null) &&
    (awayCard.lastHomeDate !== null || awayCard.lastAwayDate !== null);
  rules.push({
    rule: "R7",
    label: "Both Have Data",
    passed: bothHaveData,
    points: bothHaveData ? 1 : 0,
    maxPoints: 1,
    detail: bothHaveData ? "Reliable data for both" : "Missing data",
  });

  return rules;
}

function resolveDecision(score: number, instantSkip: boolean): MatchAnalysis["decision"] {
  if (instantSkip) return "SKIP";
  if (score >= 10) return "LOCK";
  if (score >= 6) return "PICK";
  if (score >= 3) return "CONSIDER";
  return "SKIP";
}

function resolveConfidence(score: number, instantSkip: boolean): MatchAnalysis["confidence"] {
  if (instantSkip) return "LOW";
  if (score >= 10) return "HIGH";
  if (score >= 6) return "MEDIUM";
  return "LOW";
}

export function analyzeSlot(
  todayFixtures: { home: string; away: string }[],
  slot: string,
  date: string,
  yesterdayResults: MatchResult[]
): MatchAnalysis[] {
  return todayFixtures.map((fixture) => {
    return analyzeMatch(fixture.home, fixture.away, slot, date, yesterdayResults);
  });
}

export function parseResultsText(text: string, date: string, slot: string): MatchResult[] {
  const results: MatchResult[] = [];
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);

  for (const line of lines) {
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