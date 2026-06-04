# Paper Results Summary

- available runs: `36`
- missing runs: `0`
- running runs: `2`
- skipped_existing without metrics: `0`
- excluded diagnostic runs: `11`

## Available Main Runs

| benchmark | method | n | strict_seen_avg | task_aware_seen_avg | token_f1 | forgetting | oracle_agreement |
|---|---:|---:|---:|---:|---:|---:|---:|
| instrdialog | BankNoRouter | 3 | 0.0316 | 0.0316 | 0.1293 | 0.2512 | N/A |
| instrdialog | PeriodicLatest | 3 | 0.0088 | 0.0088 | 0.1128 | 0.3188 | N/A |
| instrdialog | Replay(10) | 3 | 0.0000 | 0.0000 | 0.0267 | 0.0630 | N/A |
| instrdialog | Replay(50) | 3 | 0.0000 | 0.0000 | 0.0236 | 0.0500 | N/A |
| instrdialog | RouterOnly | 3 | 0.0000 | 0.0000 | 0.0725 | 0.1034 | 0.7536 |
| instrdialog | Sequential | 3 | 0.0000 | 0.0000 | 0.0213 | 0.0654 | N/A |
| instrdialog | Ours | 1 | 0.0000 | 0.0000 | 0.0000 | 0.1370 | 0.0853 |
| instrdialog++ | BankNoRouter | 3 | 0.0351 | 0.0351 | 0.0993 | 0.3036 | N/A |
| instrdialog++ | PeriodicLatest | 3 | 0.0051 | 0.0051 | 0.1024 | 0.1897 | N/A |
| instrdialog++ | Replay(10) | 3 | 0.0000 | 0.0000 | 0.0473 | 0.0297 | N/A |
| instrdialog++ | Replay(50) | 1 | 0.0000 | 0.0000 | 0.0343 | 0.0198 | N/A |
| instrdialog++ | RouterOnly | 1 | 0.0531 | 0.0531 | 0.1664 | 0.1368 | 0.7888 |
| instrdialog++ | Sequential | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0490 | N/A |
| instrdialog++ | Ours | 1 | 0.0793 | 0.0793 | 0.1917 | 0.2167 | 0.4440 |

## Missing Runs

_No missing runs._

## Run Availability

| status | count |
|---|---:|
| available | 36 |
| excluded | 11 |
| running | 2 |
