import sys
with open("/root/sota_supervisor_sdk.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix regex
content = content.replace(r"re.findall(r'Eval metrics:\s*({.*?})', logs)", r"re.findall(r'Eval metrics:\s*({.*})', logs)")

# Fix parallel execution to sequential or just single active monitoring.
# Actually, the user's script runs them in separate tmux windows.
# If they all run in tmux simultaneously, they will OOM.
# Let's modify start_experiments to sleep between launches or wait for one to finish?
# No, we can just run them one by one sequentially in the same tmux window, or launch them in series.
# A simpler way: only run 'standard' for rapid iteration, or sequentially run them.
