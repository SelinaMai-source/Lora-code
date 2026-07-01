import re
with open("/root/autodl-tmp/Lora-code/core/train.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace get_features logic in train.py
new_get_features = """
        def get_features(p):
            vec = [0.0] * 256
            p_text = p[:200].lower()
            if len(p_text) < 3: p_text = p_text.ljust(3, ' ')
            for i in range(len(p_text) - 2):
                tri = p_text[i:i+3]
                idx = sum(ord(c)*(31**j) for j,c in enumerate(tri)) % 256
                vec[idx] += 1.0
            return vec
"""

content = re.sub(r'        def get_features\(p\):\n            h = hashlib\.sha256\(p\.encode\("utf-8"\)\)\.digest\(\)\n            return \[float\(b\) / 255\.0 for b in h\]', new_get_features, content)

with open("/root/autodl-tmp/Lora-code/core/train.py", "w", encoding="utf-8") as f:
    f.write(content)
