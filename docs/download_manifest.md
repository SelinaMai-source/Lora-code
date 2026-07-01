# 下载清单（Download Manifest）

**生成日期**：2026-06-17  
**工作目录**：`/root/autodl-tmp/Lora-code`  
**原则**：所有条目均来自官方/论文指定来源；下载失败如实记录阻塞原因。

---

## 1. External Baselines（代码）

| 方法 | 来源 URL | 本地路径 | Commit/版本 | 状态 | 日期 |
| --- | --- | --- | --- | --- | --- |
| O-LoRA | https://github.com/cmnfriend/O-LoRA.git | `external_baselines/o_lora/` | `a712f54` | ✅ 已 clone | 2026-06-15 |
| Progressive Prompts | https://github.com/arazd/ProgressivePrompts.git | `external_baselines/progressive_prompts/` | `01572d6` | ✅ 已 clone | 2026-06-15 |
| Continual-T0 | https://github.com/ThomasScialom/T0_continual_learning.git | `external_baselines/continual_t0/` | `4841ca2` | ✅ 已 clone | 2026-06-15 |
| LB-CL | （统一入口 scaffold，无独立官方 NLP repo） | `baselines/advanced_baselines/lb_cl/` | — | ✅ 项目内实现 | — |
| LFPT5 | https://github.com/qcwthu/Lifelong-Fewshot-Language-Learning | `external_baselines/lfpt5/` | branch `lfll` archive | ✅ 已解压 | 2026-06-15 |
| LAMOL | https://github.com/jojotenya/LAMOL.git | `external_baselines/lamol/` | `03c31d9` | ✅ 已 clone | 2026-06-15 |
| TRACE/RCL | https://github.com/BeyonderXX/TRACE.git | `external_baselines/trace_rcl/` | `462e39f` | ✅ 已 clone | 2026-06-15 |
| AdapterCL/ToDCL | https://github.com/andreamad8/ToDCL.git | `external_baselines/adaptercl_dialogue/` | `e70c1ed` | ✅ 已 clone | 2026-06-15 |
| ARPER NLG | https://github.com/MiFei/Continual-Learning-for-NLG | `external_baselines/arper_dialog_nlg/` | master archive | ✅ 已解压 | 2026-06-15 |
| InfLoRA | https://github.com/liangyanshuo/InfLoRA.git | `external_baselines/inf_lora/` | `e08b00e` | ✅ 已 clone | 2026-06-15 |
| Sequential/Replay LoRA | （项目统一入口） | `baselines/basic_baselines/` | — | ✅ 项目内实现 | — |

**Smoke 检查**（2026-06-17）：`bash scripts/smoke_external_baselines.sh all` — 全部 py_compile/shell 语法通过；`--help` 因缺 `datasets`/`pytorch_lightning` 等标记为 `NEEDS_ENV`（预期行为）。

---

## 2. Benchmark 数据

### 2.1 CITB InstrDialog / InstrDialog++

| 项 | 值 |
| --- | --- |
| 来源 | CITB 项目内 processed（2026-03-20 生成） |
| Processed 路径 | `data/processed/citb_cl_dialogue_tasks_train50_eval10.json` |
| | `data/processed/citb_cl_38_random_tasks_train50_eval10.json` |
| SHA256 | `1340aec3…` (19-seg) / `00604c79…` (38-seg) |
| 状态 | ✅ 已就绪 |

### 2.2 TRACE

| 项 | 值 |
| --- | --- |
| 官方 URL | https://drive.google.com/file/d/1S0SmU0WEw5okW_XvP2Ns0URflNzZq6sV/view?usp=drive_link |
| 目标路径 | `data/raw/trace/{C-STANCE,FOMC,...}/train.json` |
| 下载命令 | `gdown "https://drive.google.com/uc?id=1S0SmU0WEw5okW_XvP2Ns0URflNzZq6sV" -O data/raw/trace/_downloads/trace_benchmark.zip` |
| 状态 | ❌ **下载失败**（2026-06-17，`Network is unreachable` / Google Drive 连接超时；**06:50 重试仍失败**） |
| Toy processed | ✅ `data/processed/trace_cl_tasks_train50_eval10_toy.json` (SHA256: `ed1782ba…`) |
| Full processed | ❌ 阻塞于 raw 数据缺失 |
| Converter | ✅ `scripts/convert_trace_to_stream.py` |

### 2.3 MultiWOZ NLG

| 项 | 值 |
| --- | --- |
| 官方 repo | https://github.com/budzianowski/multiwoz.git |
| Clone 命令 | `git clone --depth 1 https://github.com/budzianowski/multiwoz.git data/raw/multiwoz/multiwoz_repo` |
| Commit | `fe0c8e6`（2026-06-17 clone） |
| Raw 路径 | `data/raw/multiwoz/multiwoz_repo/data/MultiWOZ_2.2/data.json` |
| SHA256 (data.json) | `4c2975bd56bf84e242acc0ca29727048aa5fbfd27b6ff96733e81f1101f4599e` |
| SHA256 (2.1 zip) | `8db3f6afe591383b8523b271f07727693e73012ecce47f3ac7987191e09b7523` |
| Processed 全量 | ✅ `data/processed/multiwoz_nlg_cl_domains_train50_eval10.json` (5 domain, SHA256: `8f4ded3e…`) |
| Processed toy | ✅ `data/processed/multiwoz_nlg_cl_domains_train50_eval10_toy.json` |
| Converter | ✅ `scripts/convert_multiwoz_to_stream.py` |

### 2.4 Seq-GLUE

| 项 | 值 |
| --- | --- |
| 来源 | HuggingFace GLUE + SuperGLUE + IMDB（组合 stream，无单一官方包） |
| HF 示例 | `datasets.load_dataset("glue", "sst2")` |
| 5-dataset CL | http://goo.gl/JyCnZq |
| 本地路径 | `data/raw/seqglue/`（仅 README；**2026-06-17 HF 重试失败**：`Network is unreachable`） |
| Processed | ❌ 未生成（需 converter） |
| 说明 | 见 `data/raw/seqglue/README.md` |

---

## 3. 模型权重（未在本阶段下载）

| 资源 | 说明 |
| --- | --- |
| Llama-3.1-8B-Instruct | 本地 `assets/pretrained/meta-llama/Llama-3.1-8B-Instruct`（项目已有） |
| T5/T0 checkpoints | Continual-T0/LFPT5 官方复现需独立下载（Google Drive / gsutil） |
| LLaMA-2-chat | TRACE 官方训练需 LLaMA-2（本项目统一入口用 Llama-3.1） |

---

## 4. 可审计下载命令汇总

```bash
# MultiWOZ（已成功，2026-06-17）
git clone --depth 1 https://github.com/budzianowski/multiwoz.git data/raw/multiwoz/multiwoz_repo
cd data/raw/multiwoz/multiwoz_repo/data && unzip -o MultiWOZ_2.1.zip

# TRACE（失败 — 需网络可达 Google Drive 后重试）
pip install gdown
gdown "https://drive.google.com/uc?id=1S0SmU0WEw5okW_XvP2Ns0URflNzZq6sV" \
  -O data/raw/trace/_downloads/trace_benchmark.zip
unzip data/raw/trace/_downloads/trace_benchmark.zip -d data/raw/trace/

# TOD37 retired from active matrix; no TOD37 download is required.

# Converter 生成 processed
python scripts/convert_trace_to_stream.py --mode full --raw-root data/raw/trace \
  --out data/processed/trace_cl_tasks_train50_eval10.json --seed 123
python scripts/convert_multiwoz_to_stream.py --mode full \
  --out data/processed/multiwoz_nlg_cl_domains_train50_eval10.json --seed 123
```

---

## 5. 变更日志

| 日期 | 事件 |
| --- | --- |
| 2026-06-15 | external_baselines 批量 clone/archive（部分初次因 GitHub 超时，后续 fallback 成功） |
| 2026-06-17 | MultiWOZ repo clone + 2.1 解压 + converter 全量/toy processed JSON |
| 2026-06-17 | TRACE gdown 下载失败（Network unreachable） |
| 2026-06-17 | TRACE gdown + Seq-GLUE HF **重试仍失败**（Network unreachable） |
| 2026-06-17 | MultiWOZ ROUGE-L/BLEU 接入 `core/evaluate.py`；5-method toy configs |
| 2026-06-17 | published_setting Sequential/Replay LoRA configs + manifest 更新 |
| 2026-06-17 | 创建本 manifest |
