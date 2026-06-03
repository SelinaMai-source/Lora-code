# ACL/ARR Anti-Overlap Validation Summary

This summary records small validation runs after promoting anti-overlap to the main ACL/ARR method. These runs are engineering smoke checks and are excluded from the paper tables because they use `run_name_suffix` overrides.

| run suffix | segments | purpose | result |
|---|---:|---|---|
| `acl_validation` | 2 | Verify `ours_full` + W&B + learned-router training starts from the generated paper config. | Completed and synced to W&B project `lora-citb-acl`; single-branch warmup path is stable. |
| `acl_overlap_active` | 4 | Check sensitive drift can spawn a new branch under override settings. | Completed; drift triggered at the final segment and spawned `b1`, but no later segment used multi-branch training. |
| `acl_overlap_train` | 5 | Check a longer small run under sensitive drift. | Completed; no branch was spawned in that random sample, so anti-overlap stayed inactive. |
| `acl_overlap_forced` | 3 | Force an early branch split to validate anti-overlap backprop and metrics. | Completed; segment 2 trained with 2 branches and logged nonzero `anti_overlap_total_loss=0.0140` over 8 steps. |

Key validation facts from `acl_overlap_forced`:

- `train.routed_train_num_branches = 2`
- `train.anti_overlap_beta = 0.03`
- `train.anti_overlap_activation_beta = 0.015`
- `train.anti_overlap_weight_beta = 0.015`
- `train.anti_overlap_total_loss = 0.014011`
- `train.anti_overlap_steps = 8`
- `train.router_orthogonal_head_loss = 0.000087`
- `routing.oracle_agreement_rate = 0.4167`

Interpretation: the new ACL/ARR main path is executable with W&B, routed training, branch spawning, and anti-overlap regularization. The forced run is not a scientific result; it only proves the multi-branch anti-overlap training path is active and logged correctly.
