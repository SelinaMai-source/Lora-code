## TRACE 原始数据（raw）

本目录用于放置 **TRACE** benchmark 的原始任务 JSON（未做项目内切分）。

### 下载

官方处理后数据（Google Drive）：

https://drive.google.com/file/d/1S0SmU0WEw5okW_XvP2Ns0URflNzZq6sV/view?usp=drive_link

解压后，每个任务应为一个子目录，内含 `train.json`、`eval.json`、`test.json`：

```
data/raw/trace/
  C-STANCE/
    train.json
    eval.json
    test.json
  FOMC/
    ...
  MeetingBank/
  Py150/
  ScienceQA/
  NumGLUE-cm/
  NumGLUE-ds/
  20Minuten/
```

每条样本格式（与 `external_baselines/trace_rcl` 一致）：

```json
{"prompt": "...", "answer": "..."}
```

### 任务顺序（8 segments）

与 TRACE 官方 continual-learning 脚本一致：

`C-STANCE → FOMC → MeetingBank → Py150 → ScienceQA → NumGLUE-cm → NumGLUE-ds → 20Minuten`

### 转换为 processed stream

```bash
python scripts/convert_trace_to_stream.py --mode full \
  --raw-root data/raw/trace \
  --out data/processed/trace_cl_tasks_train50_eval10.json \
  --seed 123 --max-train 50 --max-eval 10
```

### Smoke test（无原始数据时）

```bash
python scripts/convert_trace_to_stream.py --mode toy \
  --out data/processed/trace_cl_tasks_train50_eval10_toy.json \
  --max-train 2 --max-eval 2
```
