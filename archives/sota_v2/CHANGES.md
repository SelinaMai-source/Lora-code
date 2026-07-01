# sota-v2 Changes (2026-06-16)

## Motivation
sota-v1 trajectory early-stopped @seg4 (seen=0.24). PLL never fired because oracle=0.65 > threshold 0.55.

## vs sota-v1

| Param | v1 | v2 |
|-------|----|----|
| `prototype_update_steps` | 3 | **4** |
| `oracle_pll_min_agreement` | 0.55 | **0.68** |
| `oracle_pll_bonus_steps` | 2 | **3** |

## Config
`configs/paper/sota_campaign/sota_v2_instrdialogpp_s123.yaml`

## Launch
```bash
bash scripts/launch_sota_v2.sh
```
