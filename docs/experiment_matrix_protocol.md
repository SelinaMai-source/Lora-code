# Experiment Matrix Protocol

This protocol separates paper runs, ablations, sweeps, and diagnostics so that artifact generation cannot mix them accidentally.

## Paper Main Runs

Each benchmark should include the following main methods:

- `Sequential`
- `Replay(10)`
- `Replay(50)`
- `PeriodicLatest`
- `BankNoRouter`
- `RouterOnly`
- `OursFull`

Main tables must show `num_runs` and `seeds`. A method with fewer completed seeds should remain visible, but it should not be interpreted as equally complete.

## Ablations

The ablation table is separate from the main table:

- `OursNoDrift`: drift detector contribution.
- `OursNoRouter`: router contribution.
- `OursNoBank`: LoRA bank contribution.
- `OursNoOverlap`: anti-overlap contribution.

Ablations can explain why `OursFull` underperforms, but they must not replace the declared main method unless the paper explicitly changes the method definition.

## Diagnostic Runs

Smoke, mini, pilot, ACL validation, and sweep runs are diagnostic. They must:

- use a non-empty `run_name_suffix`, or an override that changes data/training/model/method semantics;
- be recorded in availability reports with an `excluded_reason`;
- stay out of official paper main and ablation tables.

Tracking-only overrides such as `output.tracking.*` are not semantic experiment overrides and must not exclude a run.

## Artifact Consistency

Artifact builders should report:

- `execution_status`
- `has_final_metrics`
- `reporting_status`
- `excluded_reason`
- `metrics_path`

If many canonical runs have `final_metrics.json` but only a tiny number enter the tables, artifact generation should warn or fail. A summary with `running` or `missing` runs is allowed, but it must make that incompleteness explicit.

## Full Matrix Rerun Gate

Do not rerun the full matrix until:

- task-aware scoring has passed smoke tests;
- eval error audit has explained the main strict-EM failure types;
- router/drift diagnostics have identified whether the issue is method behavior or reporting;
- artifact availability matches the canonical run manifest.
