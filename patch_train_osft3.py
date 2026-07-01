import re

with open("core/train.py", "r") as f:
    content = f.read()

osft_code = """
OSFT_SUBSPACES = {}

def apply_osft_projection(lora_wrapper):
    import torch
    with torch.no_grad():
        for n, p in lora_wrapper.peft_model.named_parameters():
            if "lora_" in n and p.requires_grad and p.grad is not None:
                if n in OSFT_SUBSPACES:
                    P = OSFT_SUBSPACES[n]
                    if "lora_A" in n:
                        p.grad.data = p.grad.data @ P
                    elif "lora_B" in n:
                        p.grad.data = P @ p.grad.data

def update_osft_subspaces(lora_wrapper, rank=2):
    import torch
    for n, p in lora_wrapper.peft_model.named_parameters():
        if "lora_" in n and p.requires_grad:
            with torch.no_grad():
                if p.dim() == 2:
                    U, S, Vh = torch.linalg.svd(p.data.float(), full_matrices=False)
                    if "lora_A" in n:
                        V_k = Vh[:rank, :]
                        P_new = torch.eye(p.size(1), device=p.device) - V_k.T @ V_k
                        if n in OSFT_SUBSPACES:
                            OSFT_SUBSPACES[n] = OSFT_SUBSPACES[n] @ P_new.to(p.dtype)
                        else:
                            OSFT_SUBSPACES[n] = P_new.to(p.dtype)
                    elif "lora_B" in n:
                        U_k = U[:, :rank]
                        P_new = torch.eye(p.size(0), device=p.device) - U_k @ U_k.T
                        if n in OSFT_SUBSPACES:
                            OSFT_SUBSPACES[n] = P_new.to(p.dtype) @ OSFT_SUBSPACES[n]
                        else:
                            OSFT_SUBSPACES[n] = P_new.to(p.dtype)
"""

content = content.replace("def main() -> None:", osft_code + "\n\ndef main() -> None:")
content = content.replace("lora.step_adapter()", "apply_osft_projection(lora)\n            lora.step_adapter()")
content = content.replace("logger.log(f\"Train metrics: {json.dumps(train_metrics, ensure_ascii=False)}\")", 
                          "logger.log(f\"Train metrics: {json.dumps(train_metrics, ensure_ascii=False)}\")\n        update_osft_subspaces(lora, rank=2)")

with open("core/train.py", "w") as f:
    f.write(content)
