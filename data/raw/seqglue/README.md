## Seq-GLUE / Long-CL 原始数据（raw）

Seq-GLUE 并非单一官方打包数据集，而是由 GLUE + SuperGLUE + IMDB 等分类任务按序组合构成的 continual learning stream（见 Progressive Prompts、Long-CL 等论文）。

### 推荐来源

| 任务集 | 下载方式 |
| --- | --- |
| GLUE (SST-2, MRPC, QQP, RTE, …) | HuggingFace `datasets.load_dataset("glue", "<task>")` |
| SuperGLUE (WiC, CB, COPA, …) | HuggingFace `datasets.load_dataset("super_glue", "<task>")` |
| IMDB | HuggingFace `datasets.load_dataset("imdb")` |
| 5-dataset CL benchmark (AGNews 等) | http://goo.gl/JyCnZq（Progressive Prompts 附录） |

### 当前状态

- **已下载**（2026-06-17，clash 代理 + parquet 源：`SetFit/sst2`、`nyu-mll/glue`、`aps/super_glue`）→ `data/raw/seqglue/glue_*` / `super_glue_*`
- **Processed**：`data/processed/seqglue_cl_tasks_train50_eval10.json`（8 segments, train50/eval10）
- Converter：`scripts/convert_seqglue_to_stream.py`

### 参考论文任务序

Progressive Prompts (ICLR 2023) 使用 5-dataset CL + 4 GLUE + 5 SuperGLUE + IMDB 共 15 任务长序列。具体顺序见论文附录 A.1。
