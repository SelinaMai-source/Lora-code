## MultiWOZ 原始数据（raw）

### 来源

| 资源 | URL | 本地路径 |
| --- | --- | --- |
| MultiWOZ 官方仓库 | https://github.com/budzianowski/multiwoz.git | `data/raw/multiwoz/multiwoz_repo/` |
| MultiWOZ 2.1 zip（仓库内置） | 同上 repo `data/MultiWOZ_2.1.zip` | 已解压至 `multiwoz_repo/data/MultiWOZ_2.1/` |
| MultiWOZ 2.2 | 同上 repo `data/MultiWOZ_2.2/` | `multiwoz_repo/data/MultiWOZ_2.2/data.json` |

Clone 命令（2026-06-17 已执行）：

```bash
git clone --depth 1 https://github.com/budzianowski/multiwoz.git data/raw/multiwoz/multiwoz_repo
cd data/raw/multiwoz/multiwoz_repo/data
unzip -o MultiWOZ_2.1.zip
```

### 转换为 processed stream

```bash
# 全量 5 domain × train50/eval10
python scripts/convert_multiwoz_to_stream.py --mode full \
  --out data/processed/multiwoz_nlg_cl_tasks_train50_eval10.json

# Smoke toy
python scripts/convert_multiwoz_to_stream.py --mode toy \
  --out data/processed/multiwoz_nlg_cl_tasks_train50_eval10_toy.json
```

Domain 顺序：restaurant → hotel → attraction → train → taxi
