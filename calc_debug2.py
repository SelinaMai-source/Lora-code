import torch
from core.methods.router import Router

router = Router({
    "vib_beta": 0.05,
    "training_strategy": "learned_router",
    "learning_rate": 0.01,
})

# Initial forward pass to set branch names
router.update_with_pseudo_labels(
    features=torch.randn(1, 4096).cuda(),
    pseudo_labels=["a"],
    branch_names=["a"]
)

# A second one
out = router.update_with_pseudo_labels(
    features=torch.randn(1, 4096).cuda(),
    pseudo_labels=["b"],
    branch_names=["a", "b"]
)
print("Updated successfully:", out)
