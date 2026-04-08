# Final Paper Package

- generated_at: `2026-04-07T13:09:57.129166+00:00`
- main_rows: `8`
- ablation_rows: `4`

## Main Table Snapshot

| benchmark | method | n | seen_avg | forgetting | token_f1 | oracle_agreement |
|---|---|---:|---:|---:|---:|---:|
| instrdialog | BankNoRouter | 1 | 0.0211 | 0.1870 | 0.1247 | 0.0000 |
| instrdialog | PeriodicLatest | 1 | 0.0263 | 0.3380 | 0.1552 | 0.0000 |
| instrdialog | Replay(10) | 1 | 0.0000 | 0.0778 | 0.0654 | 0.0000 |
| instrdialog | Replay(50) | 1 | 0.0000 | 0.0222 | 0.0438 | 0.0000 |
| instrdialog | RouterOnly | 1 | 0.0000 | 0.0556 | 0.0731 | 0.7204 |
| instrdialog | Sequential | 1 | 0.0000 | 0.0389 | 0.0000 | 0.0000 |
| instrdialog | Ours | 1 | 0.1053 | 0.1583 | 0.2174 | 0.6398 |
| instrdialog++ | BankNoRouter | 1 | 0.1026 | 0.2756 | 0.1545 | 0.0000 |

## Ablation Snapshot

| benchmark | method | seen_avg | forgetting | token_f1 |
|---|---|---:|---:|---:|
| instrdialog | OursNoBank | 0.0000 | 0.0556 | 0.0467 |
| instrdialog | OursNoDrift | 0.0000 | 0.2269 | 0.0683 |
| instrdialog | OursNoOverlap | 0.0728 | 0.1778 | 0.1782 |
| instrdialog | OursNoRouter | 0.0368 | 0.2204 | 0.1397 |
