import torch
from core.methods.overlap_loss import compute_orthogonal_weight_loss

class DummyWrapper:
    def list_adapters(self):
        return ["a", "b"]
    def get_adapter_vector(self, name, detach=False):
        return torch.randn(1000000, device="cuda")

loss = compute_orthogonal_weight_loss(
    lora_wrapper=DummyWrapper(),
    beta=0.1,
    similarity="information_bottleneck"
)
print("Loss computed:", loss)
