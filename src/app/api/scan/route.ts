import { NextResponse } from "next/server";
import { scanForElite } from "@/lib/scanner";
import { sendTelegramAlert } from "@/lib/telegram";

// Rate limiting: track last scan time (in-memory, resets on cold start)
let lastScanTime = 0;
const MIN_SCAN_INTERVAL_MS = 60_000; // 1 minute minimum between scans

// Verify cron secret for Vercel Cron calls
function isCronAuthorized(request: Request): boolean {
  const authHeader = request.headers.get("authorization");
  const cronSecret = process.env.CRON_SECRET;
  if (!cronSecret) return false;
  return authHeader === `Bearer ${cronSecret}`;
}

async function handleScan(request: Request, source: "cron" | "client" | "external") {
  // Rate limit client-side requests (not cron)
  if (source === "client") {
    const now = Date.now();
    if (now - lastScanTime < MIN_SCAN_INTERVAL_MS) {
      return NextResponse.json(
        { error: "Rate limited. Please wait 60 seconds between scans.", retryAfterMs: MIN_SCAN_INTERVAL_MS - (now - lastScanTime) },
        { status: 429 }
      );
    }
    lastScanTime = now;
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

  return NextResponse.json({ ...result, source });
}

// GET: Vercel Cron (daily health check) OR external cron service
export async function GET(request: Request) {
  const source = isCronAuthorized(request) ? "cron" : "external";

  // External cron services (cron-job.org) can call without secret
  // They're rate-limited by the service itself
  return handleScan(request, source);
}

// POST: Client-side polling from the dashboard (rate-limited)
export async function POST(request: Request) {
  return handleScan(request, "client");
}
