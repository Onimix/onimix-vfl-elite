import type { EliteAlert, LiveEvent, ScanResult, LeagueEliteData } from "./elite-types";
import eliteData from "@/data/elite-matchups.json";

const SPORT_ID = "sr:sport:202120001";
const SPORTYBET_API = "https://www.sportybet.com/api/ng/factsCenter/liveOrPrematchEvents";
const ALERT_WINDOW_MINUTES = 20;

// Build flat lookup: "AST vs ARS" -> { league, rate }
function buildEliteLookup(): Map<string, { league: string; rate: number }> {
  const lookup = new Map<string, { league: string; rate: number }>();
  const data = eliteData as LeagueEliteData;

  for (const [league, matchups] of Object.entries(data)) {
    for (const [key, rate] of Object.entries(matchups)) {
      lookup.set(key, { league, rate });
    }
  }
  return lookup;
}

function abbreviateTeam(name: string): string {
  // SportyBet uses names like "Aston Villa (AST)" — extract the abbreviation
  const match = name.match(/\(([A-Z]{2,4})\)/);
  if (match) return match[1];
  // Fallback: first 3 chars uppercase
  return name.replace(/[^a-zA-Z]/g, "").substring(0, 3).toUpperCase();
}

export async function scanForElite(): Promise<ScanResult> {
  const startTime = Date.now();
  const eliteLookup = buildEliteLookup();
  const eliteFound: EliteAlert[] = [];
  const leaguesScanned = new Set<string>();

  try {
    const url = `${SPORTYBET_API}?sportId=${encodeURIComponent(SPORT_ID)}&_t=${Date.now()}`;
    const response = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0",
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`SportyBet API returned ${response.status}`);
    }

    const json = await response.json();
    let tournaments = json?.data ?? [];

    // Handle both list and dict formats
    if (tournaments && !Array.isArray(tournaments)) {
      tournaments = tournaments.tournaments ?? [];
    }

    const now = Date.now();
    let totalEvents = 0;

    for (const tournament of tournaments) {
      const events = tournament?.events ?? [];
      const tournamentName = tournament?.name ?? tournament?.categoryName ?? "Unknown";

      for (const event of events) {
        totalEvents++;
        const homeRaw = event?.homeTeamName ?? "";
        const awayRaw = event?.awayTeamName ?? "";
        const homeAbbr = abbreviateTeam(homeRaw);
        const awayAbbr = abbreviateTeam(awayRaw);
        const key = `${homeAbbr} vs ${awayAbbr}`;
        const kickoff = Number(event?.estimateStartTime ?? event?.gameTime ?? 0);

        const minutesUntilKick = (kickoff - now) / 60000;

        // Check if this is an ELITE matchup in the alert window
        const eliteInfo = eliteLookup.get(key);
        if (eliteInfo && minutesUntilKick > 0 && minutesUntilKick <= ALERT_WINDOW_MINUTES) {
          leaguesScanned.add(eliteInfo.league);

          const kickoffDate = new Date(kickoff);
          const liveEvent: LiveEvent = {
            eventId: event?.eventId ?? "",
            home: homeRaw,
            away: awayRaw,
            key,
            league: eliteInfo.league,
            kickoff,
            kickoffFormatted: kickoffDate.toLocaleTimeString("en-NG", {
              hour: "2-digit",
              minute: "2-digit",
              timeZone: "Africa/Lagos",
            }),
            minutesUntilKick: Math.round(minutesUntilKick),
          };

          eliteFound.push({
            event: liveEvent,
            matchup: {
              home: homeAbbr,
              away: awayAbbr,
              key,
              league: eliteInfo.league,
              hitRate: eliteInfo.rate,
            },
            alertTime: new Date().toISOString(),
            status: minutesUntilKick <= ALERT_WINDOW_MINUTES ? "in_window" : "upcoming",
          });
        }

        // Track all leagues seen
        if (eliteLookup.has(key)) {
          leaguesScanned.add(eliteLookup.get(key)!.league);
        }
      }
    }

    return {
      timestamp: new Date().toISOString(),
      totalEventsScanned: totalEvents,
      eliteFound,
      leaguesScanned: Array.from(leaguesScanned),
      scanDurationMs: Date.now() - startTime,
      telegramSent: false,
    };
  } catch (error) {
    return {
      timestamp: new Date().toISOString(),
      totalEventsScanned: 0,
      eliteFound: [],
      leaguesScanned: [],
      scanDurationMs: Date.now() - startTime,
      telegramSent: false,
    };
  }
}
