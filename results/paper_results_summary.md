# Paper Results Summary

- available runs: `15`
- missing runs: `1`

## Available Main Runs

| benchmark | method | n | seen_avg | forgetting | oracle_agreement |
|---|---:|---:|---:|---:|---:|
| instrdialog | BankNoRouter | 1 | 0.0211 | 0.1870 | 0.0000 |
| instrdialog | PeriodicLatest | 1 | 0.0263 | 0.3380 | 0.0000 |
| instrdialog | Replay(10) | 1 | 0.0000 | 0.0778 | 0.0000 |
| instrdialog | Replay(50) | 1 | 0.0000 | 0.0222 | 0.0000 |
| instrdialog | RouterOnly | 1 | 0.0000 | 0.0556 | 0.7204 |
| instrdialog | Sequential | 1 | 0.0000 | 0.0389 | 0.0000 |
| instrdialog | Ours | 1 | 0.0421 | 0.0824 | 0.0806 |
| instrdialog++ | BankNoRouter | 1 | 0.1026 | 0.2756 | 0.0000 |
| instrdialog++ | PeriodicLatest | 1 | 0.0100 | 0.2008 | 0.0000 |
| instrdialog++ | Replay(10) | 1 | 0.0000 | 0.0270 | 0.0000 |
| instrdialog++ | Replay(50) | 1 | 0.0000 | 0.0198 | 0.0000 |

## Missing Runs

- `paper_instrdialogpp_router_only_s123` (instrdialog++ / router_only)
