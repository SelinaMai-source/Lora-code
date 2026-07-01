import re

with open("core/methods/router.py", "r") as f:
    content = f.read()

content = re.sub(
    r"base = _stable_hash_float\(prompt\)\n\s*for i, b in enumerate\(branch_names\):\n\s*age_bonus = \(i \+ 1\) / max\(1, len\(branch_names\)\)\n\s*scores\[b\] = 0\.7 \* age_bonus \+ 0\.3 \* base",
    "for i, b in enumerate(branch_names):\n            age_bonus = (i + 1) / max(1, len(branch_names))\n            scores[b] = age_bonus",
    content
)

with open("core/methods/router.py", "w") as f:
    f.write(content)
