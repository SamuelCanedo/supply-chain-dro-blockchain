# simulate_live.py

import time
from pipeline.decision_engine import run_decision

while True:
    try:
        print("\n🔄 New cycle...")
        run_decision("wasserstein")

    except Exception as e:
        print(f"❌ Error: {e}")
        
    time.sleep(5)