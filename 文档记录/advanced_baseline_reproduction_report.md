# Advanced Baseline 复现盘点报告

生成日期：2026-06-15
工作区：`/root/autodl-tmp/Lora-code`

## 执行摘要

本轮在上一阶段“源码下载完成 + 本项目 scaffold smoke 通过”的基础上，推进到“可复现准备完成”。已对照官方 README、官方入口脚本、本项目 `configs/baselines` 和 `baselines/advanced_baselines/*/method.py`，为已下载 external baseline 建立最小官方 smoke 计划与统一脚本，并补齐 O-LoRA / LB-CL 的最小 faithful hook。

本项目统一入口侧，`O-LoRA`、`Progressive Prompts`、`Continual-T0`、`LB-CL` 四个 smoke 仍可跑通。其中 `O-LoRA` 已从“adapter-per-segment scaffold”补到可执行 orthogonal regularization/projection hook；`LB-CL` 已从占位缓存补到 compact SVD triplet summary 与可验证 gradient projection hook。注意：这些 smoke 证明实现路径可执行，不代表已经复现论文完整结果。

## 目录盘点

- `baselines/advanced_baselines/`：已有 11 个方法目录；其中 `o_lora`、`progressive_prompts`、`continual_t0`、`lb_cl` 有本项目统一入口 scaffold。
- `external_baselines/`：官方/可信源码下载区；损坏的 partial clone/zip 均移动到 `archive_candidates/partial_external_baselines_20260615/`，未永久删除。
- 生成/修改的统一入口配置位于 `configs/baselines/`。

## Baseline 状态总览

| baseline | 复现状态 | 仓库 URL | commit |
| --- | --- | --- | --- |
| o_lora | downloaded + local smoke-tested with orthogonal hooks | https://github.com/cmnfriend/O-LoRA.git | a712f54 |
| lb_cl | faithful scaffold + local smoke-tested | 未找到官方公开代码仓库 | 无 |
| progressive_prompts | downloaded + local scaffold smoke-tested | https://github.com/arazd/ProgressivePrompts.git | 01572d6 |
| lfpt5 | downloaded as GitHub archive | https://github.com/qcwthu/Lifelong-Fewshot-Language-Learning | archive from branch `lfll` |
| continual_t0 | downloaded + local scaffold smoke-tested | https://github.com/ThomasScialom/T0_continual_learning.git | 4841ca2 |
| lamol | downloaded | https://github.com/jojotenya/LAMOL.git | 03c31d9 |
| trace_rcl | downloaded | https://github.com/BeyonderXX/TRACE.git | 462e39f |
| inf_lora | downloaded | https://github.com/liangyanshuo/InfLoRA.git | e08b00e |
| adaptercl_dialogue | downloaded | https://github.com/andreamad8/ToDCL.git | e70c1ed |
| arper_dialog_nlg | downloaded as GitHub archive | https://github.com/MiFei/Continual-Learning-for-NLG | archive from branch `master` |
| tm_bnnm_dialog_nlg | scaffold-only / blocked | 未找到官方公开代码仓库；仅下载 BNNM reference | 无 |
| bnm_reference | downloaded as GitHub archive | https://github.com/cuishuhao/BNM | archive from branch `BNMv1` |

## 实际运行的命令与结果

- 直连 `git clone --depth 1` 多次因 GitHub 443 timeout 失败。
- 使用 `configs/clash/d18255a-GS.yaml` 启动 `mihomo` 时，原配置因 MMDB/GEOIP 下载失败无法启动；本轮生成临时运行配置 `configs/clash/runtime/d18255a-GS.no_geoip.yaml`，仅过滤 `GEOIP` 规则，原配置未改动。
- 代理端口 `127.0.0.1:7890` 验证通过，GitHub HTTP 访问返回 200。
- 通过代理与明确分支完成 git checkout：`o_lora`、`progressive_prompts`、`continual_t0`、`inf_lora`、`adaptercl_dialogue`，并保留已有 `lamol`、`trace_rcl`。
- 通过 GitHub codeload zip 完成 archive 下载：`lfpt5`、`arper_dialog_nlg`、`bnm_reference`。
- `python -m py_compile core/models/lora_wrapper.py baselines/advanced_baselines/o_lora/method.py baselines/advanced_baselines/lb_cl/method.py`：通过。
- `python core/train.py --config configs/baselines/smoke_o_lora.yaml`：通过，2 个 mock segment；新增指标显示 orthogonal hook 已接通，第二段记录非零 orthogonal penalty proxy，结果在 `results/logs/smoke_o_lora.log` 和 `results/tables/smoke_o_lora_segment_metrics.csv`。
- `python core/train.py --config configs/baselines/smoke_lb_cl.yaml`：通过，2 个 mock segment；新增指标显示每段记录 compact SVD triplet summary，并调用 projection hook，结果在 `results/logs/smoke_lb_cl.log` 和 `results/tables/smoke_lb_cl_segment_metrics.csv`。
- `python core/train.py --config configs/baselines/smoke_progressive_prompts.yaml`：通过，结果在 `results/logs/smoke_progressive_prompts.log` 和 `results/tables/smoke_progressive_prompts_segment_metrics.csv`。
- `python core/train.py --config configs/baselines/smoke_continual_t0.yaml`：通过，结果在 `results/logs/smoke_continual_t0.log` 和 `results/tables/smoke_continual_t0_segment_metrics.csv`。
- `bash scripts/smoke_external_baselines.sh o_lora`：官方 `engine.py` 与 `src/run_uie_lora.py` 可 `py_compile`；`--help` 需要官方独立依赖环境。
- `bash scripts/smoke_external_baselines.sh progressive_prompts`：T5/BERT 训练入口可 `py_compile`；`--help` 需要官方独立依赖环境。
- `bash scripts/smoke_external_baselines.sh continual_t0`：`setup.py` 可 `py_compile`。
- `bash scripts/smoke_external_baselines.sh lfpt5`：`convertmodel.py` 可 `py_compile`，classification shell 入口语法检查通过。
- `bash scripts/smoke_external_baselines.sh adaptercl_dialogue`：`train.py` 可 `py_compile`；`--help` 需要官方独立依赖环境。
- `bash scripts/smoke_external_baselines.sh lamol`：`train.py` 可 `py_compile`，`train.sh` / `test.sh` shell 语法检查通过。
- `bash scripts/smoke_external_baselines.sh trace_rcl`：`train.py`、`training/main.py` 可 `py_compile`，核心 shell 脚本语法检查通过。
- `bash scripts/smoke_external_baselines.sh inf_lora`：`main.py` 可 `py_compile`。
- `bash scripts/smoke_external_baselines.sh arper_dialog_nlg`：`run.sh` / `preprocess.sh` shell 语法检查通过。
- `bash scripts/smoke_external_baselines.sh bnm_reference`：DA/BNM 参考训练入口可 `py_compile`。
- 尚未在官方仓库中启动论文训练；未安装各仓库独立依赖，避免污染当前项目环境。

## 官方 smoke 计划

新增 `external_baselines/official_smoke_plan.md` 与 `scripts/smoke_external_baselines.sh`。覆盖 `O-LoRA`、`Progressive Prompts`、`Continual-T0`、`LFPT5`、`AdapterCL/ToDCL`、`LAMOL`、`TRACE/RCL`、`InfLoRA`、`ARPER Dialogue NLG`、`BNM reference` 的最小官方 smoke、独立环境草案和剩余数据/权重阻塞。

脚本约束：

- 只执行 `py_compile`、`--help`、`bash -n` 等轻量检查。
- 不安装依赖、不下载数据或权重、不启动长训练。
- `NEEDS_ENV` 表示官方入口存在，但当前全局环境缺少对应仓库独立依赖。

## 已知 Cursor 内部错误处理策略

本轮检查未发现 `.cursor/error-autofix/queue.jsonl` 或 `.cursor/error-autofix/` 下的待处理失败队列；当前 BAD_DECRYPT / background task completion action 类报错判断为 Cursor 内部后台通知/解密链路噪声，未发现会影响本项目已落盘代码、报告、smoke 日志或结果表的证据。

后续规避建议：

- 关键复现实验尽量使用单 worker 串行推进，减少后台 completion action 并发通知。
- 重要结论优先前台执行并写入本地报告、日志或结果表，不把 subagent completion action 当作唯一结果载体。
- 后台任务若只用于轻量检查，应同步保留本地命令、产物路径和阻塞原因，避免 Cursor 内部通知失败导致上下文丢失。

## 是否能直接复跑论文结果

当前仍不建议直接启动完整论文级训练。原因不是源码缺失，而是论文复跑需要额外准备：

- O-LoRA：官方仓库可用，入口可编译；论文设置与本项目 Llama-3.1/CITB 不完全一致，需要确认原始任务流、T5/LLaMA 分支脚本、模型权重和 metrics。
- Progressive Prompts：官方代码已下载；论文结果主要基于 BERT/T5 prompt tuning，需要独立环境和对应数据集。
- LFPT5：源码已下载；需要 LM-adapted T5-large checkpoint，并按官方说明做 TF checkpoint 到 PyTorch 的转换。
- Continual-T0：源码已下载；官方说明以 notebook/Google Drive 数据为主，需要 T0/T5 checkpoint 和 1% rehearsal 数据。
- LAMOL：源码已下载；依赖较旧，建议独立虚拟环境安装，不污染当前项目。
- TRACE/RCL：源码已下载；通常需要 LLaMA-2-chat、Deepspeed、多任务数据与评估脚本。
- InfLoRA：源码已下载；原论文偏 CV continual learning，需要判断迁移到 NLP/LLM LoRA 是否公平。
- AdapterCL / ARPER：源码已下载；需要 MultiWOZ/TOD37/DailyDialog 等 dialogue 数据准备。
- LB-CL：未发现官方仓库；本项目已补 compact SVD triplet summary 与 gradient projection hook，但仍需论文级 sensitivity 排序和 triplet injection。
- TM-BNNM：未发现官方专属仓库，只能基于论文和 BNNM reference 重写 Text-Mixup + BNNM。

可在用户确认后优先尝试的短复现实验：

1. O-LoRA：在独立官方环境中复跑 `--help`，确认 T5/LLaMA 分支参数；随后将本项目 hook 对齐到官方矩阵级 orthogonal loss。
2. Progressive Prompts：在独立环境跑官方最小任务；本项目侧补 soft prompt 参数、prompt concatenation 与 non-oracle prompt routing。
3. Continual-T0：准备 T0/T5 checkpoint 和官方 rehearsal 数据；本项目侧做 replay ratio 对照。
4. LFPT5：下载 LM-adapted T5-large 并完成 checkpoint 转换后，再跑官方脚本。
5. AdapterCL/ARPER：准备 MultiWOZ/TOD37 数据，先跑 NLG setting 的单 domain smoke。
6. LAMOL/TRACE：在独立虚拟环境安装各自依赖后跑官方最小脚本；不要污染当前项目环境。

## 新增或修改的本项目文件

- `baselines/advanced_baselines/o_lora/README.md`：更新源码状态、官方 smoke 与本项目 hook 状态。
- `baselines/advanced_baselines/lb_cl/README.md`：更新 SVD triplet summary 与 projection hook 状态。
- `baselines/advanced_baselines/o_lora/method.py`：新增 orthogonal regularization/projection scaffold。
- `baselines/advanced_baselines/lb_cl/method.py`：新增 compact SVD triplet summary 与 projection hook 调用。
- `core/models/lora_wrapper.py`：新增 `summarize_adapter_svd`、`project_active_adapter_gradients`，并为 debug wrapper 增加稳定 adapter 向量。
- `configs/baselines/lb_cl.yaml`：新增 LB-CL 主配置。
- `configs/baselines/smoke_o_lora.yaml`
- `configs/baselines/smoke_lb_cl.yaml`
- `configs/baselines/smoke_progressive_prompts.yaml`
- `configs/baselines/smoke_continual_t0.yaml`
- `external_baselines/README.md`
- `external_baselines/official_smoke_plan.md`
- `scripts/smoke_external_baselines.sh`
- `文档记录/advanced_baseline_reproduction_report.md`
- `文档记录/advanced_baseline_reproduction_report.docx`：已由 Markdown 报告重新导出。
- `core/train.py`：已在上一阶段注册 `baseline_name: lb_cl`。
- `external_baselines/download_log.tsv`
- `external_baselines/reachability_log.tsv`
- `external_baselines/clone_reachable_log.tsv`
- `external_baselines/fallback_clone_log.tsv`
- `external_baselines/<method>/`：已下载官方/可信源码。
- `configs/clash/runtime/d18255a-GS.no_geoip.yaml`：临时代理运行配置，仅过滤 GEOIP 规则。

## 下一步建议队列

1. 将 O-LoRA 的 adapter-vector proxy 对齐到官方 LoRA A / loranew_A 矩阵级 orthogonal loss，并在真实 PEFT smoke 上验证非零梯度投影。
2. 将 LB-CL 的 compact SVD summary 升级为论文级 triplet sensitivity 排序与初始化注入。
3. 为 O-LoRA、Progressive Prompts、AdapterCL 等依赖阻塞的官方入口创建独立 conda/env 文件，并在隔离环境中复跑 `--help`。
4. 准备最小论文数据子集：CITB train2/eval2、本项目 mock、TRACE 1-task sample、MultiWOZ NLG toy split。
5. 用户确认权重、数据和 GPU 时间后，再启动任何多 GPU或长时间论文复跑。
