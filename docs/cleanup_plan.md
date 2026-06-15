# 工作区安全清理建议

生成日期：2026-06-14

本清理方案遵循“不永久删除不确定内容”的原则。当前仅创建清理建议文档和 `archive_candidates/`，未删除任何文件。

## 2026-06-14 本轮实际执行记录

本轮只执行归档/收纳，未永久删除任何文件；移动均进入 `archive_candidates/` 下日期目录，并使用 `mv -n` 避免覆盖。

- `archive_candidates/run_scripts_20260614/`：收纳 91 个旧批跑脚本，范围为根目录 `run_v4_sota_*.sh`、`run_v5_sota_*.sh`、`run_v6_sota_*.sh`、`run_v7_sota_*.sh`。
- `archive_candidates/logs_20260614/`：收纳 45 个旧日志/状态文件，范围为根目录 `v5_sota_*.log/.pid`、`v6_sota_*.log`、`v7_sota_*.log`、`SOTA_*.log`。
- `archive_candidates/temp_debug_20260614/`：收纳 18 个临时自动搜索/调试脚本和日志，包括 `auto_sota_loop*`、`auto_sota_v5*`、`monitor_39.py` 到 `monitor_42.py`、`calc_debug*.py`、`tmp.log`。
- `archive_candidates/old_docs_20260614/`：收纳 3 个较早/重复文档：根目录 `实验v3.docx`、`文档记录/实验v3.docx`（改名为 `文档记录_实验v3.docx` 避免覆盖）、`文档记录/实验v4.docx`。

本轮保留了 `v8_sota5_campaign`、`results/`、`experiments/`、`data/`、`core/`、`configs/`、`baselines/`、`文档记录/新版实验方案*`。根目录 `run_v8_sota_*.sh` 与 `v8_sota_*.log` 暂未移动，因为可能仍与当前 v8 最优结果复现相关。

## 本轮新增 baseline scaffold

- 已在统一 baseline 入口注册 `o_lora`、`progressive_prompts`、`continual_t0`。
- 已新增 `configs/baselines/o_lora.yaml`、`configs/baselines/progressive_prompts.yaml`、`configs/baselines/continual_t0.yaml`。
- 这些实现均为 scaffold/smoke-test-ready，不代表完整论文复现；O-LoRA 的正交约束、Progressive Prompts 的 soft prompt 模块、Continual-T0 的原 T0/T5 checkpoint 与 mixture 仍待实现。

## 必须保留

- `core/`：统一训练、评估、LoRA、router、drift、metric 等主代码。
- `configs/baseline.yaml`、`configs/ours.yaml`、`configs/seq_debug.yaml` 及 `configs/paper/v8_sota5_campaign/`：新版实验复用配置基础。
- `data/processed/citb_cl_dialogue_tasks_train50_eval10.json`、`data/processed/citb_cl_38_random_tasks_train50_eval10.json`：当前可直接使用的 CITB-InstrDialog 与 InstrDialog++。
- `data/raw/README.md`、`data/raw/download_citb.sh`：可复现数据准备入口。
- `baselines/basic_baselines/` 与 `baselines/advanced_baselines/`：新版 baseline 结构。
- `results/tables/paper_main_results*.csv`、`results/tables/paper_ablation_results*.csv`、`results/paper_results_summary.md`、`results/run_v1_results_analysis.md`：已有结果汇总与论文表格线索。
- `文档记录/新版实验方案_advanced_baselines_benchmarks.md` 与 `.docx`：本次生成的新实验方案。

## 建议移动到归档 staging，需用户确认

- 根目录大量 `run_v4_sota_*.sh`、`run_v5_sota_*.sh`、`run_v6_sota_*.sh`、`run_v7_sota_*.sh`、`run_v8_sota_*.sh`：多为旧搜索/批跑脚本，可保留最近 v8 或最优配置相关脚本，其余移动到 `archive_candidates/run_scripts_YYYYMMDD/`。
- 根目录大量 `v5_sota_*.log`、`v6_sota_*.log`、`v8_sota_*.log`、`SOTA_*.log`：如果结果已汇总到 CSV/MD，可归档原始日志，仅保留最优 run 的日志和 campaign monitor。
- `auto_sota_loop*.py/.log`、`monitor_39.py` 到 `monitor_42.py`、`calc_debug*.py`、`tmp.log`：看起来是临时自动搜索/调试脚本，建议归档而非直接删除。
- `文档记录/实验v1.docx` 到 `实验v6.docx`：建议保留 `实验v5.docx`、`实验v6.docx` 与本次新版方案，较早版本移动到 `archive_candidates/old_docs_YYYYMMDD/`。
- `experiments/v7_sota_campaign/` 与 `experiments/v8_sota5_campaign/`：如果 v8 是当前最优 campaign，保留 v8，v7 可归档；但需先确认是否仍有未汇总结果。
- `wandb/`：若 W&B 已同步，可归档本地缓存；如包含未同步 run，暂不移动。

## 仍需用户确认

- 根目录 `run_v8_sota_*.sh`、`v8_sota_*.log`：建议确认哪些用于 v8_sota5 复现，确认后再归档非必要项。
- `experiments/v7_sota_campaign/`：可能有未汇总结果，本轮未移动。
- `wandb/`：需确认本地 run 是否已同步，本轮未移动。
- `文档记录/实验v5.docx`、`文档记录/实验v6.docx`：较新旧版实验记录，本轮保留。
- `RP(Lora)_v2.pdf`、`RP(Lora)_v3.md/.pdf`、根目录 `run_v1_results_analysis.pdf`、`SOTA_*` 状态 md/json：需要确认是否仍有论文/复现实验价值。

## 可以考虑删除，但仍建议先归档验证

- 空日志：如 `agent_master_nohup.log`、`auto_sota_v5.log`、`new_sota_targets.log`。
- 明显临时文件：`tmp.log`。
- 重复 PDF/中间报告：如根目录 `实验v3.docx` 与 `文档记录/实验v3.docx` 并存，需要比对后只保留文档目录版本。

## 不建议删除

- `.git/`、`.gitignore`、`requirements.txt`、`README.md`。
- `assets/`：可能包含权重/缓存，未确认前不可删除。
- `archive/`：已有历史归档，不应在本轮再次清理。

## 下一步安全命令建议

仅在用户确认后执行移动归档，例如：

```bash
mkdir -p archive_candidates/run_scripts_20260614
mv -n run_v4_sota_*.sh run_v5_sota_*.sh archive_candidates/run_scripts_20260614/
```

不要使用 `git reset --hard`、`git checkout --` 或直接 `rm -rf` 清理未确认内容。

## 2026-06-15 根目录整理执行结果

- 归档目录：`archive_candidates/root_cleanup_20260615_012746`。
- 本轮只移动归档，未永久删除文件，未执行破坏性 Git 命令。
- `scripts/`：移动 46 项。
- `logs/`：移动 19 项。
- `state/`：移动 8 项。
- `docs/`：移动 2 项。
- `pdfs/`：移动 2 项。
- 暂不移动：`experiments/`、`results/`、`wandb/`，因为检测到 v8_sota5_campaign 训练/监控与 W&B 进程仍在运行；`.venv/` 作为本地环境保留。
- 详细清单见 `archive_candidates/root_cleanup_20260615_012746/MANIFEST.md` 与 `docs/root_cleanup_report.md`。
