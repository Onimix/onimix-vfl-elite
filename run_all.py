#!/usr/bin/env python3
"""ONIMIX VFL + SRL Scanner Runner - All Layers"""
import threading, time, subprocess, sys

SCANNERS = [
    ("Layer 1 - VFL ELITE v8", "layer1_v8.py"),
    ("Layer 2 - VFL 12-Layer v5", "layer2_v5.py"),
    ("MEGA - VFL Accumulator v5", "mega_v5.py"),
]

INTERVAL = 600  # 10 minutes

def run_scanner(name, script):
    while True:
        print(f"\n[{name}] Running...")
        try:
            result = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=120)
            if result.stdout:
                print(f"[{name}] {result.stdout[-200:]}")
            if result.returncode != 0:
                print(f"[{name}] ERROR: {result.stderr[-200:]}")
        except Exception as e:
            print(f"[{name}] Exception: {e}")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    print("=" * 50)
    print("ONIMIX VFL PREDICTION SYSTEM v8")
    print(f"Running {len(SCANNERS)} scanners every {INTERVAL//60} minutes")
    print("=" * 50)
    
    threads = []
    for name, script in SCANNERS:
        t = threading.Thread(target=run_scanner, args=(name, script), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(30)  # Stagger starts by 30 seconds
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nShutting down...")
