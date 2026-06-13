import json
import time
import sys

log_file = "/root/autodl-tmp/Lora-code/v5_sota_38.log"

def check():
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return False
        
    for line in lines:
        if "Eval metrics:" in line:
            json_str = line.split("Eval metrics: ")[1]
            try:
                data = json.loads(json_str)
                seen_avg = data.get("seen_avg_score", 1.0)
                num_seen = data.get("num_seen_segments", 0)
                if num_seen >= 4 and seen_avg < 0.1:
                    print(f"EARLY_STOP_TRIGGERED: num_seen={num_seen}, seen_avg={seen_avg}")
                    return True
            except:
                pass
        if "Done training" in line or "Experiment finished" in line or "Traceback" in line:
            print("RUN_FINISHED")
            return True
            
    return False

while True:
    if check():
        sys.exit(0)
    time.sleep(5)
