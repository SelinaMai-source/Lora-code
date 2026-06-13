## 处理后数据（processed）：统一持续学习流格式

本目录存放从 `data/raw/` 的 CITB 原始数据转换得到的**持续学习流（continual stream）**文件，供 `core/train.py` 的统一管线直接读取。

### 期望的格式（建议 JSON）

处理后的核心对象是一个 segments 列表，每个 segment 同时包含 train 与 eval：

```json
{
  "benchmark": "CITB",
  "version": "unknown",
  "stream": [
    {
      "segment_id": 0,
      "segment_name": "domain_or_task_name",
      "train": [
        {"instruction": "...", "input": "...", "output": "..."}
      ],
      "eval": [
        {"instruction": "...", "input": "...", "output": "..."}
      ]
    }
  ]
}
```

### segment 的含义

- segment 是持续学习的最小时间步：训练按 segment 递进（先 0 段，再 1 段……）。
- 每个 segment 必须提供：
  - `train`: 用于该段的微调样本
  - `eval`: 用于评估该段及“已见段”的表现

### train/eval 的样本格式

每条样本必须是指令微调风格三元组：
- `instruction`: 任务指令
- `input`: 可为空字符串（无额外输入时）
- `output`: 目标回答

### 谁负责生成 processed

处理逻辑放在 `core/data.py`（本仓库不新增额外 preprocessing 脚本文件）。你可以：
- 先将 raw CITB 放入 `data/raw/citb/`
- 再运行 `core/data.py` 中提供的处理入口（目前是安全脚手架 + 结构校验 + 留出扩展点）
- 生成 processed JSON 到 `data/processed/`

