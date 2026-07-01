import os
import subprocess

def run(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

# 1. Setup branch
os.chdir('/root/autodl-tmp/Lora-code')
run('git checkout main')
run('git pull || true')
try:
    run('git branch -D v14-optimization')
except:
    pass
run('git checkout -b v14-optimization')

# We will directly write the V14 logic using python script since subagents keep failing due to internal network encryption bug.
print("V14 Branch created.")
