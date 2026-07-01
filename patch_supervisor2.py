import re
with open("/root/sota_supervisor_sdk.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace start_experiments
new_start = """def start_experiments(version):
    ensure_tmux()
    # To prevent OOM, we launch them in a sequence using a single shell command chain
    window_name = f"{version}_all"
    run_cmd(f"tmux new-window -t {TMUX_SESSION} -n {window_name}")
    
    cmd = ""
    for name, cfg_path in CONFIGS.items():
        cmd += f"cd /root/autodl-tmp/Lora-code && python core/train.py --config {cfg_path} > /root/{version}_{name}.log 2>&1 ; "
    
    run_cmd(f"tmux send-keys -t {TMUX_SESSION}:{window_name} '{cmd}' C-m")
    print(f"[{time.strftime('%H:%M:%S')}] Started {version} experiments sequentially in tmux '{TMUX_SESSION}'.")
"""

content = re.sub(r"def start_experiments\(version\):.*?print\(f\"\[\{time\.strftime\('%H:%M:%S'\)\}\] Started \{version\} experiments in tmux '\{TMUX_SESSION\}'\.\"\)", new_start, content, flags=re.DOTALL)

with open("/root/sota_supervisor_sdk.py", "w", encoding="utf-8") as f:
    f.write(content)
