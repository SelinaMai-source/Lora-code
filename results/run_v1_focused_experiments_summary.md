# Run V1 Focused Experiment Summary

This file summarizes smoke/mini override runs. These runs are intentionally excluded from paper tables.

| suffix | segments | seen_avg | token_f1 | branches | drift_miss | oracle_agreement | note |
|---|---:|---:|---:|---:|---:|---:|---|
| mini_abs_drift_routed | 4 | 0.0625 | 0.3175 | 3 | 0.3333 | 0.5000 | absolute drift sweep; triggers branch spawning |
| mini_default | 4 | 0.1875 | 0.3764 | 1 | 1.0000 | 1.0000 | default compatibility check |
| mini_drift_aggressive | 4 | 0.1250 | 0.3193 | 1 | 1.0000 | 1.0000 | degradation-only aggressive drift check |
| mini_routed_oracle | 4 | 0.1875 | 0.3764 | 1 | 1.0000 | 1.0000 | routed-training path check |
| smoke_default | 2 | 0.0000 | 0.2431 | 1 | 1.0000 | 1.0000 | default compatibility check |
| smoke_drift_sensitive | 2 | 0.0000 | 0.2627 | 1 | 1.0000 | 1.0000 | degradation-only aggressive drift check |
| smoke_routed_oracle | 2 | 0.0000 | 0.2588 | 1 | 1.0000 | 1.0000 | routed-training path check |
