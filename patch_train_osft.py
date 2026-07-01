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

# Insert OSFT code near the top
content = content.replace("def _summarize_lora_info", osft_code + "\n\ndef _summarize_lora_info")

# Insert apply_osft_projection in _train_on_active_branch
content = content.replace("step_stats = lora.step_adapter()", "apply_osft_projection(lora)\n            step_stats = lora.step_adapter()")

# Insert apply_osft_projection in _train_with_routed_assignments
# Note: step_stats = lora.step_adapter() appears twice, we replaced both!

# Insert update_osft_subspaces in run_ours, after training
# We can find "train_metrics = _train_with_router(" and "train_metrics = _train_on_active_branch("
# Actually, the end of the segment training is around "logger.log(f\"Train metrics: {json.dumps(train_metrics, ensure_ascii=False)}\")"
content = content.replace("logger.log(f\"Train metrics: {json.dumps(train_metrics, ensure_ascii=False)}\")", 
                          "logger.log(f\"Train metrics: {json.dumps(train_metrics, ensure_ascii=False)}\")\n        update_osft_subspaces(lora, rank=2)")

with open("core/train.py", "w") as f:
    f.write(content)
