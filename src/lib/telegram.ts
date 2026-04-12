import type { EliteAlert } from "./elite-types";

export async function sendTelegramAlert(
  alerts: EliteAlert[],
  botToken: string,
  chatId: string
): Promise<boolean> {
  if (alerts.length === 0) return false;

  const leagueEmojis: Record<string, string> = {
    England: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    Spain: "🇪🇸",
    Italy: "🇮🇹",
    Germany: "🇩🇪",
    France: "🇫🇷",
  };

  let message = "🎯 *ELITE ALERT — Over 1.5 Goals*\n\n";

  for (const alert of alerts) {
    const emoji = leagueEmojis[alert.matchup.league] || "⚽";
    const stars = alert.matchup.hitRate >= 90 ? "🔥🔥🔥" : alert.matchup.hitRate >= 85 ? "🔥🔥" : "🔥";

    message += `${emoji} *${alert.matchup.league}*\n`;
    message += `${alert.event.home} vs ${alert.event.away}\n`;
    message += `⏰ Kickoff: ${alert.event.kickoffFormatted} WAT\n`;
    message += `📊 Hit Rate: *${alert.matchup.hitRate}%* ${stars}\n`;
    message += `⏳ ${alert.event.minutesUntilKick} min to kick\n\n`;
  }

  message += "_Powered by ONIMIX ELITE Engine_";

  try {
    const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text: message,
        parse_mode: "Markdown",
      }),
    });
    return response.ok;
  } catch {
    return false;
  }
}
