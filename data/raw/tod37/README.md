## TOD37 原始数据（raw）

TOD37 来自 AdapterCL/ToDCL（EMNLP 2021）对 TM19 + TM20 + SGD + MultiWOZ 四数据集联合预处理后的 37-domain continual dialogue benchmark。

### 官方来源

| 资源 | URL |
| --- | --- |
| ToDCL/AdapterCL 代码 | https://github.com/andreamad8/ToDCL.git |
| 数据下载脚本 | `external_baselines/adaptercl_dialogue/data/download.sh` |
| 预处理入口 | `external_baselines/adaptercl_dialogue/utils/preprocess.py` |

### 依赖数据集（需全部下载后联合预处理）

- Taskmaster-1: https://github.com/google-research-datasets/Taskmaster.git
- Taskmaster-2: 同上
- Schema Guided Dialogue: https://github.com/google-research-datasets/dstc8-schema-guided-dialogue.git
- MultiWOZ: https://github.com/budzianowski/multiwoz.git（**本项目已下载**，见 `data/raw/multiwoz/`）

### 当前状态

- MultiWOZ 部分：**已下载**
- TM19/TM20/SGD：**未下载**（需独立 env + `adaptercl_dialogue/data/download.sh`）
- TOD37 processed stream：**未生成**（阻塞于四数据集联合预处理）

### 下一步

```bash
cd external_baselines/adaptercl_dialogue/data
bash download.sh   # 需 pytorch_lightning 等独立环境
# 然后按 README 运行 preprocess → 导出 NLG domain stream converter
```
