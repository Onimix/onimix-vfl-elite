import { NextResponse } from "next/server";
import eliteData from "@/data/elite-matchups.json";
import type { LeagueEliteData } from "@/lib/elite-types";

export async function GET() {
  const data = eliteData as LeagueEliteData;

  // Build summary stats
  const stats = Object.entries(data).map(([league, matchups]) => {
    const entries = Object.entries(matchups);
    const rates = entries.map(([, rate]) => rate);
    const avgRate = rates.reduce((a, b) => a + b, 0) / rates.length;
    const topPicks = entries
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([key, rate]) => ({ key, rate }));

    return {
      league,
      totalMatchups: entries.length,
      avgHitRate: Math.round(avgRate * 10) / 10,
      topPicks,
    };
  });

  const totalMatchups = stats.reduce((sum, s) => sum + s.totalMatchups, 0);
  const overallAvg =
    Math.round(
      (stats.reduce((sum, s) => sum + s.avgHitRate * s.totalMatchups, 0) /
        totalMatchups) *
        10
    ) / 10;

  return NextResponse.json({
    totalMatchups,
    overallAvgHitRate: overallAvg,
    leagues: stats,
    allMatchups: data,
  });
}
