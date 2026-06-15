## Continual Instruction Tuning with LoRA (CITB + Llama 3.1)

本仓库用于**持续指令微调（Continual Instruction Tuning）**研究：以 `meta-llama/Llama-3.1-8B-Instruct` 为骨干模型，在 **CITB** 基准上进行按段（segment）的持续学习；统一管线同时支持多种 **baseline** 与**我们的方法（漂移检测 + LoRA Bank + 路由 + anti-overlap 正则）**。

你可以在本地 Mac 直接跑通端到端流程（使用 `data/sample/mock_stream.json` 与轻量 debug 模型逻辑），也可以在算力机上下载 CITB 与 Llama 权重后无缝切换到真实实验。

---

## 仓库结构（严格约束）

```
configs/         # 3 个唯一配置入口：debug / baseline / ours
data/            # raw/processed/sample 三层：数据下载说明、处理格式与本地样例
core/            # 唯一统一训练/评估引擎（不分裂成多套系统）
baselines/       # basic_baselines/ 与 advanced_baselines/（后者为复现准备）
assets/          # pretrained/checkpoints/cache（权重与中间文件约定位置）
results/         # logs/tables/figures/runs（训练代码会写入这里）
README.md
requirements.txt
.gitignore
```

---

## 概念映射：Llama 3.1 8B 与 CITB 在本项目中意味着什么

- **Llama 3.1 8B Instruct**：主干大模型，未来在算力机使用 Hugging Face Transformers 加载（本地 debug 不需要下载 8B 权重）。
- **CITB**：持续指令微调基准数据集（本仓库不内置真实数据；`data/raw/` 提供安全下载脚手架与期望文件结构；`core/data.py` 预留处理入口，产物放到 `data/processed/`）。
- **Continual stream**：数据被组织为有序的 segments；每个 segment 有 train/eval 子集，训练按 segment 递进，评估记录“当前性能、历史平均、遗忘”等指标。

---

## 现在本地就能跑什么

你已经可以直接在 Mac 上跑通：

- **端到端训练循环（按段训练）**
- **统一评估接口**（输出 `current_score / seen_avg_score / forgetting / num_seen_segments` 等）
- **basic baseline、advanced baseline scaffold 与 ours 的统一选择/分发逻辑**
- **结果落盘到 `results/`**（每次运行有独立 `results/runs/<run_id>/`）

本地 debug 使用：
- `configs/seq_debug.yaml`
- `data/sample/mock_stream.json`
- `core/models/base_model.py` 内置的轻量 `DebugTextModel`

---

## 在算力机下载模型与基准后能跑什么

完成以下两步后：

1. 下载 CITB 原始数据到 `data/raw/` 并用 `core/data.py` 的预处理入口生成 `data/processed/` 的流式格式
2. 下载 `meta-llama/Llama-3.1-8B-Instruct` 权重到 `assets/pretrained/`（或将配置指向你的 HF cache）

你就可以运行：
- **所有 baselines**（`baseline.yaml` 里切换 `baseline_name`）
- **我们的完整方法与消融**（只改 `ours.yaml` 的模块开关）

---

## 快速开始

### 1) 安装依赖

在仓库根目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) 本地 debug（可立即运行）

```bash
python core/train.py --config configs/seq_debug.yaml
```

输出会写入：
- `results/runs/<run_id>/`：本次运行的配置快照、指标、逐段日志等
- `results/tables/`：汇总表（CSV/JSON）
- `results/logs/`：纯文本日志

### 3) 运行 baselines（统一入口）

编辑 `configs/baseline.yaml` 的 `baseline_name`：
- `sequential_lora`
- `replay_lora`
- `periodic_multilora`
- `router_only`
- `bank_no_router`（重要：无独立文件夹，作为同一 baseline 配置分支处理）

然后运行：

```bash
python core/train.py --config configs/baseline.yaml
```

### 4) 运行我们的方式（含消融）

通过 `configs/ours.yaml` 的开关实现消融：
- `use_drift_detector`
- `use_lora_bank`
- `use_router`
- `use_overlap_loss`

运行：

```bash
python core/train.py --config configs/ours.yaml
```

---

## Baseline 对比如何工作

- 所有 baseline **共享同一条训练/评估管线**：`core/train.py`
- baseline 的差异仅来自：
  - 配置：`configs/baseline.yaml` 的 `baseline_name`
- 实现：基础 baseline 由 `baselines/basic_baselines/<name>/method.py` 提供统一接口（被 `core/train.py` 调用）；advanced baseline 目前位于 `baselines/advanced_baselines/`，为复现准备/待实现 scaffold

这样保证对比公平：数据加载、评估与落盘逻辑一致。

---

## Overfit-8：序列行为诊断（teacher-forced vs 开环 greedy）

当 loss / teacher-forced acc 已接近完美但 greedy EM 仍低时，优先用 **诊断产物** 定位开环轨迹问题，而不是继续改 drift/router 或泛泛调参。说明与 artifact 列表见 **`docs/sequence_behavior_diagnosis.md`**；配置示例 **`configs/baseline_alignment_overfit.yaml`**（含 Part A–F：`enable_sequence_behavior_diagnosis`、`run_decode_ablation`、`run_overfit_ladder`；ladder 较慢可在 YAML 中关）。

---

## Ablation 如何只通过 ours.yaml 完成

`configs/ours.yaml` 提供模块开关与子模块超参：

- **关闭漂移检测**：`use_drift_detector: false`（仍可保留 bank/router）
- **关闭 bank**：`use_lora_bank: false`（退化为单 LoRA 分支/或与 router 组合形成 ablation）
- **关闭 router**：`use_router: false`（得到 bank-no-router 风格）
- **关闭 overlap loss**：`use_overlap_loss: false`

不需要增加新代码入口与新顶层目录，保证扩展点清晰、可复现实验。

---

## Weights & Biases 实验追踪

训练入口 `core/train.py` 已支持可选 W&B 日志（默认关闭）。完整说明见 **`docs/wandb_integration.md`**；配置模板见 **`configs/tracking_wandb.example.yaml`**。

快速开启：

```bash
pip install wandb && wandb login
python core/train.py --config configs/paper/instrdialog__ours_full__s123.yaml
# 在 YAML 中设置 output.tracking.use_wandb: true
```

批量实验：

```bash
bash scripts/run_publication_with_wandb.sh --benchmarks instrdialog --categories main
```

---

## 投稿向工程要点（ACL/ARR）

当前实验结论摘要见 `results/run_v1_results_analysis.md`。投稿前建议：

1. **主方法用 `ours_full`**：anti-overlap 是 ACL/ARR 主实验，`ours_no_overlap` 只作为 ablation。
2. **先跑 anti-overlap smoke/sweep**：`bash scripts/run_acl_antioverlap_experiments.sh smoke`，再跑 full matrix。
3. **Change-point statistics**：默认启用 curriculum anchor split 与 meta-threshold；保留 `ours_no_meta_threshold`、`ours_reverse_curriculum` 做机制消融。
4. **Bank + routing 闭环**：主配置使用 `router.training_strategy: learned_router`，训练和推理都走 branch selection。
5. **至少 3 个 seed**，W&B `wandb_group` 按 benchmark+variant 分组。

