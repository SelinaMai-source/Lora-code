# Router And Drift Diagnostics

| run | routed | branch_entropy | oracle_agreement | collapse | drift_miss | drift_triggers | recommendation |
|---|---:|---:|---:|---|---:|---:|---|
| `20260407_213933_citb_ours_smoke_bosfix` | 10 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `20260407_214118_citb_ours_smoke_bosfix` | 10 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `20260407_214258_citb_ours_smoke_bosfix` | 10 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_bank_no_router_s123` | 0 | 0.0000 | 0.0000 | False | 0.8333 | 3 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_bank_no_router_s456` | 0 | 0.0000 | 0.0000 | False | 0.9444 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_bank_no_router_s789` | 0 | 0.0000 | 0.0000 | False | 0.9444 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_K100_s123_pilot` | 3 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_K50_s123_pilot` | 3 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_M128_s123_pilot` | 3 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_M256_s123_pilot` | 3 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_M64_s123_pilot` | 3 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_br4_s123_pilot` | 3 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_br8_s123_pilot` | 3 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123` | 211 | 0.1908 | 0.0853 | True | 0.8333 | 4 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_acl_overlap_active` | 16 | -0.0000 | 1.0000 | False | 0.6667 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_acl_overlap_forced` | 12 | -0.0000 | 0.4167 | False | 0.5000 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_acl_overlap_train` | 20 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_acl_validation` | 8 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_pilot2_beta0` | 5 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_pilot2_default` | 5 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_pilot2_rw0` | 5 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_pilot2_thr010` | 5 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_pilot3_stress` | 50 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_pilot3_stress_beta0_fix1` | 50 | -0.0000 | 0.3000 | False | 0.8889 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_pilot3_stress_fix1` | 50 | -0.0000 | 0.3800 | False | 0.8889 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_pilot3_stress_thr010_beta0_fix1` | 50 | -0.0000 | 0.6000 | False | 0.8889 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_pilot3_stress_thr010_fix1` | 50 | -0.0000 | 0.3600 | False | 0.8889 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_full_s123_pilot4_routerfix` | 50 | -0.0000 | 0.4000 | False | 0.8889 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_no_drift_s123` | 211 | -0.0000 | 1.0000 | False | 0.0000 | 0 |  |
| `paper_instrdialog_ours_no_overlap_s123` | 211 | 0.2183 | 0.0806 | True | 0.8889 | 5 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_no_overlap_s123_mini_abs_drift_routed` | 16 | -0.0000 | 0.5000 | False | 0.3333 | 2 |  |
| `paper_instrdialog_ours_no_overlap_s123_mini_default` | 16 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_no_overlap_s123_mini_drift_aggressive` | 16 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_no_overlap_s123_mini_routed_oracle` | 16 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_no_overlap_s123_pilot4_routerfix` | 50 | -0.0000 | 0.4400 | False | 0.8889 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_no_overlap_s123_pilot5_cachefix` | 50 | 0.3669 | 0.5600 | False | 0.8889 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_no_overlap_s123_smoke_default` | 4 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_no_overlap_s123_smoke_drift_sensitive` | 4 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_no_overlap_s123_smoke_routed_oracle` | 4 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_no_router_s123` | 0 | 0.0000 | 0.0000 | False | 0.9444 | 4 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_r16_s123_pilot` | 3 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_r32_s123_pilot` | 3 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_ours_r8_s123_pilot` | 3 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialog_router_only_s123` | 211 | -0.0000 | 0.7204 | False | 0.0000 | 0 |  |
| `paper_instrdialog_router_only_s456` | 211 | -0.0000 | 0.7583 | False | 0.0000 | 0 |  |
| `paper_instrdialog_router_only_s789` | 211 | -0.0000 | 0.7820 | False | 0.0000 | 0 |  |
| `paper_instrdialogpp_bank_no_router_s123` | 0 | 0.0000 | 0.0000 | False | 0.8649 | 5 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialogpp_bank_no_router_s456` | 0 | 0.0000 | 0.0000 | False | 0.9730 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialogpp_bank_no_router_s789` | 0 | 0.0000 | 0.0000 | False | 0.8919 | 4 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialogpp_ours_full_s123` | 464 | -0.0000 | 0.4440 | False | 0.9459 | 2 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialogpp_ours_full_s123_pilot3_stress_fix1` | 50 | -0.0000 | 0.2000 | False | 0.8889 | 1 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `paper_instrdialogpp_router_only_s123` | 464 | -0.0000 | 0.7888 | False | 0.0000 | 0 |  |
| `smoke_anchor_drift` | 0 | 0.0000 | 0.0000 | False | 0.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
| `smoke_metrics_schema` | 2 | -0.0000 | 1.0000 | False | 1.0000 | 0 | threshold,shift_stat=absolute,calibration_window,core_guard_scale |
