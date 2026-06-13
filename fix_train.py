import sys

with open('/root/autodl-tmp/Lora-code/core/train.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "raise ValueError(f\"Unknown router.training_strategy:" in line:
        new_lines.append(f'        raise ValueError(f"Unknown router.training_strategy: {{strategy}}. Expected one of: active_branch | oracle_min_nll | learned_router")\n')
        skip = True
    elif skip and "        )" in line:
        skip = False
    elif skip:
        pass
    else:
        new_lines.append(line)

with open('/root/autodl-tmp/Lora-code/core/train.py', 'w') as f:
    f.writelines(new_lines)
