## CITB 原始数据（raw）

本目录用于放置 **CITB** 基准的原始下载文件（未做任何项目内处理/切分）。

### 你需要准备什么

- 你需要从 CITB 官方渠道/论文附录/作者提供的下载入口获取数据（不同版本可能有授权或访问控制）。
- 本仓库不会伪造下载成功：`download_citb.sh` 只会创建目录结构与提供安全脚手架。

### 期望的放置方式（约定）

建议下载后将 CITB 放到类似结构中（可按你实际拿到的文件名调整，但尽量保持可追溯）：

```
data/raw/citb/
  README_OR_LICENSE.txt
  tasks/                # 各任务/领域子集（如果数据按任务组织）
  metadata/             # task 列表、版本信息等（如果提供）
  original_files/       # 原始 json/jsonl/csv 等
```

如果你拿到的是压缩包，建议保留原始压缩包（例如 `citb.zip`）以及解压后的文件夹，方便复现实验与校验版本。

### raw -> processed 的关系

- `raw/`：原始数据，尽量保持“下载即所得”，不做修改
- `processed/`：项目统一管线需要的**持续学习流（continual stream）**格式

处理逻辑**不在本目录**，而在 `core/data.py` 中（遵循本仓库的结构约束）。

### 下一步

1. 运行 `data/raw/download_citb.sh` 创建结构并阅读提示
2. 将真实 CITB 数据放入 `data/raw/citb/`
3. 使用 `core/train.py` 运行时，代码会在 `core/data.py` 中检测 processed 数据是否存在；若不存在，会提示你先执行预处理入口（同样在 `core/data.py` 内提供脚手架函数）。

