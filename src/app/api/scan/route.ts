import { NextResponse } from "next/server";
import { scanForElite } from "@/lib/scanner";
import { sendTelegramAlert } from "@/lib/telegram";

// Verify cron secret to prevent unauthorized access
function isAuthorized(request: Request): boolean {
  const authHeader = request.headers.get("authorization");
  const cronSecret = process.env.CRON_SECRET;

  // Allow if no secret is configured (development mode)
  if (!cronSecret) return true;

  return authHeader === `Bearer ${cronSecret}`;
}

export async function GET(request: Request) {
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const result = await scanForElite();

  // Send Telegram alerts if ELITE matches found
  if (result.eliteFound.length > 0) {
    const botToken = process.env.TELEGRAM_BOT_TOKEN;
    const chatId = process.env.TELEGRAM_CHAT_ID;

    if (botToken && chatId) {
      result.telegramSent = await sendTelegramAlert(
        result.eliteFound,
        botToken,
        chatId
      );
    }
  }

  return NextResponse.json(result);
}

// Vercel Cron calls GET, but support POST for manual triggers
export async function POST(request: Request) {
  return GET(request);
}
