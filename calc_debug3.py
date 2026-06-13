import torch
from core.methods.overlap_loss import compute_orthogonal_weight_loss, compute_overlap_loss_torch

class DummyWrapper:
    def list_adapters(self):
        return ["a", "b"]
    def get_adapter_vector(self, name, detach=False):
        return torch.randn(1000000, device="cuda")

loss1 = compute_orthogonal_weight_loss(
    lora_wrapper=DummyWrapper(),
    beta=0.1,
    similarity="frequency_division_multiplexing"
)
print("FDM Weight Loss computed:", loss1)

loss2 = compute_overlap_loss_torch(
    activations_by_branch={"a": torch.randn(1, 64).cuda(), "b": torch.randn(1, 64).cuda()},
    beta=0.1
)
print("Coulomb Activation Loss computed:", loss2)
