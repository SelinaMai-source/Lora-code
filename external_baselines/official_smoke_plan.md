# External Advanced Baselines: Official Smoke Plan

更新日期：2026-06-15

本文件把 `external_baselines/` 从“源码已下载”推进到“可复现准备完成”。所有命令均以官方仓库为边界，不安装依赖、不下载权重、不启动长训练；如果命令需要旧依赖或数据，只记录阻塞原因。

统一脚本：

```bash
bash scripts/smoke_external_baselines.sh all
```

也可以逐个执行：

```bash
bash scripts/smoke_external_baselines.sh o_lora
bash scripts/smoke_external_baselines.sh progressive_prompts
bash scripts/smoke_external_baselines.sh continual_t0
bash scripts/smoke_external_baselines.sh lfpt5
bash scripts/smoke_external_baselines.sh adaptercl_dialogue
bash scripts/smoke_external_baselines.sh lamol
bash scripts/smoke_external_baselines.sh trace_rcl
bash scripts/smoke_external_baselines.sh inf_lora
bash scripts/smoke_external_baselines.sh arper_dialog_nlg
bash scripts/smoke_external_baselines.sh bnm_reference
```

## 环境原则

- 不污染当前项目环境：优先使用各官方仓库自带 `requirements.txt`、`environment.yaml` 或 README 命令创建独立环境。
- 本阶段只做静态/轻量检查：`python -m py_compile`、`python <entry> --help`、shell 脚本语法检查。
- 不启动完整训练，不执行数据下载脚本，不拉取 Google Drive/HF/gsutil 大文件。
- 如果 `--help` 因缺少依赖失败，视为“官方入口存在但需独立环境”，不是本项目实现失败。

## Baseline 计划

| baseline | 本地源码状态 | 最小官方 smoke | 独立环境草案 | 仍需准备 |
| --- | --- | --- | --- | --- |
| O-LoRA | `external_baselines/o_lora`，commit `a712f54` | `py_compile` 官方 `engine.py`、`src/run_uie_lora.py`；尝试 `src/run_uie_lora.py --help` | 使用官方 `requirements.txt` 创建隔离 env；T5/LLaMA 分支分开验证 | 原论文任务配置、T5/LLaMA 权重、完整 task configs |
| Progressive Prompts | `external_baselines/progressive_prompts`，commit `01572d6` | `py_compile` T5/BERT 入口；尝试 `train_t5_cl.py --help` 和 `train_cl2.py --help` | 官方 `environment.yaml`，Python 3.8/PyTorch 1.10/transformers 4.20 | HF/本地 CL 数据集、T5/BERT 权重 |
| Continual-T0 | `external_baselines/continual_t0`，commit `4841ca2` | `py_compile` `setup.py`；检查 README/requirements 可读 | 独立 env 安装 `requirements.txt` 后再跑 notebook/脚本 | T0/T5 checkpoint、Google Drive processed data、rehearsal 数据 |
| LFPT5 | `external_baselines/lfpt5` archive | `py_compile` `convertmodel.py` 与轻量任务脚本；不运行转换 | README 指定 `conda create --name lfll_1 python=3.9.4`，安装内置 transformers | LM-adapted T5-large TF checkpoint、gsutil、checkpoint 转换 |
| AdapterCL/ToDCL | `external_baselines/adaptercl_dialogue`，commit `e70c1ed` | `py_compile train.py`；尝试 `train.py --help` | 独立 env 安装 `requirements.txt` | TM19/TM20/SGD/MultiWOZ 数据和预处理 |
| LAMOL | `external_baselines/lamol`，commit `03c31d9` | `py_compile train.py`；shell 语法检查 `train.sh`/`test.sh` | 独立旧版 transformers/GPT2 env，按 `env.example` 写本地 `env` | 官方转换数据包、模型输出目录、旧 CUDA/Python 兼容性 |
| TRACE/RCL | `external_baselines/trace_rcl`，commit `462e39f` | `py_compile train.py`、`training/main.py`；shell 语法检查训练/推理脚本 | 独立 torch 2.0.1/CUDA 12.2 env，按 `requirements.txt` | TRACE 数据、LLaMA-2-chat 权重、Deepspeed/flash-attn |
| InfLoRA | `external_baselines/inf_lora`，commit `e08b00e` | `py_compile main.py`；不跑 CV 训练 | 官方 `environment.yaml` | CV 数据集；需决定是否纳入 NLP/LLM 对比 |
| ARPER Dialogue NLG | `external_baselines/arper_dialog_nlg` archive | shell 语法检查 `run.sh`/`preprocess.sh`；检查 config README | 独立 dialogue NLG env，按 README/config 准备 | NLG 数据、预处理产物、论文具体 setting |
| BNM reference | `external_baselines/bnm_reference` archive | `py_compile` DA/BNM 训练入口 | 独立 CV/domain adaptation env | 仅为 TM-BNNM 参考，不是 TM-BNNM 官方代码 |

## 与本项目 scaffold 的差距

- 本项目 `O-LoRA` 已从 adapter-per-segment scaffold 补到可执行 orthogonal regularization/projection hook；论文级复现仍需官方 T5/LLaMA 数据与权重。
- 本项目 `LB-CL` 已从占位缓存补到 SVD triplet summary 和 projection hook；论文级复现仍需 triplet sensitivity 排序、初始化注入策略和完整 benchmark。
- `Progressive Prompts` 当前仍是 prompt schedule scaffold，缺 soft prompt 参数模块、prompt concatenation 和 non-oracle routing。
- `Continual-T0` 当前实现 instruction replay wiring，缺 T0/T5 checkpoint、官方 mixture 和 1% rehearsal 数据。
- `LFPT5`、`AdapterCL/ToDCL`、`LAMOL`、`TRACE/RCL` 已具备官方 smoke 入口计划，但完整复现必须在独立环境和数据权重就绪后执行。
