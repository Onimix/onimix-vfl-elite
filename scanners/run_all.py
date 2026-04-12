"""
ONIMIX VFL Prediction System — All-in-One Runner
Run this single script to start all 4 scanners locally.
Usage: python run_all.py
"""
import subprocess, time, threading, sys, os

SCRIPTS = [
    ("layer1_v6_feedback.py",  5),   # ELITE Scanner — every 5 min
    ("layer2_v3_feedback.py",  5),   # 12-Layer Engine — every 5 min
    ("mega_v3_feedback.py",    30),  # Mega Accumulator — every 30 min
    ("feedback_engine_v2.py",  30),  # Feedback Engine — every 30 min
]

def run_loop(script, interval_min):
    py = sys.executable
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, script)
    while True:
        try:
            print(f"\n{'='*50}")
            print(f"▶ Running {script}...")
            print(f"{'='*50}")
            result = subprocess.run([py, path], timeout=120, capture_output=False)
            if result.returncode != 0:
                print(f"⚠ {script} exited with code {result.returncode}")
        except subprocess.TimeoutExpired:
            print(f"⏰ {script} timed out after 120s")
        except Exception as e:
            print(f"❌ {script} error: {e}")
        print(f"💤 {script} sleeping {interval_min} min...")
        time.sleep(interval_min * 60)

if __name__ == "__main__":
    print("🚀 ONIMIX VFL Prediction System")
    print("=" * 50)
    print(f"Starting {len(SCRIPTS)} scanners...\n")
    
    threads = []
    for script, interval in SCRIPTS:
        t = threading.Thread(target=run_loop, args=(script, interval), daemon=True)
        t.start()
        threads.append(t)
        print(f"  ✅ {script} — every {interval} min")
        time.sleep(2)  # stagger starts to avoid API flooding
    
    print(f"\n🟢 All scanners running! Press Ctrl+C to stop.\n")
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all scanners... Goodbye!")
        sys.exit(0)
