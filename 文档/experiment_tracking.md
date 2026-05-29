# 实验记录规范：Version / Trial / W&B

## 推荐结论

本项目建议使用 **Weights & Biases + 本地 results 落盘**：

- W&B：看曲线、比较 run、记录超参、做 sweep、生成报告。
- `results/runs/<run_id>/`：保留 config snapshot、逐段 JSON、最终 metrics。
- `results/tables/*.csv`：作为论文表格和脚本统计的权威输入。

不要只依赖 W&B，也不要只靠散落的 CSV。投稿前需要两者互相校验。

## 命名规则

建议每一次正式实验都显式设置 `output.run_name`：

```yaml
output:
  run_name: "v3_instrdialog_ours_no_overlap_s123_trial01"
```

推荐格式：

```text
v{方法版本}_{benchmark}_{method_or_ablation}_s{seed}_trial{编号}
```

例子：

- `v3_instrdialog_ours_no_overlap_s123_trial01`
- `v3_instrdialogpp_router_only_s123_trial01`
- `v3_instrdialog_replay50_s456_trial02`

## 每个 trial 必须记录什么

每个 trial 至少要能回答这些问题：

- 代码版本：git commit hash、是否有 dirty diff。
- 数据版本：benchmark、raw 数据来源、processed 文件名、segment 顺序。
- 方法版本：baseline / ours / ablation 名称。
- 关键超参：seed、LoRA rank、lr、batch size、epochs、replay budget、branch budget、drift threshold、anchor size、router 设置、overlap beta。
- 结果指标：final、seen_avg、forgetting、token_f1、routing / drift / overlap 诊断。
- 失败备注：是否出现 generation 格式漂移、first-token 问题、branch collapse、detector miss。

## 如何开启 W&B

先安装依赖并登录：

```bash
pip install -r requirements.txt
wandb login
```

然后在对应 config 中打开：

```yaml
output:
  tracking:
    use_wandb: true
    wandb_project: "lora-citb"
    wandb_entity: ""
    wandb_mode: "online"
    wandb_tags: ["ours", "instrdialog"]
```

离线跑算力机实验时可以用：

```yaml
wandb_mode: "offline"
```

之后运行：

```bash
python core/train.py --config configs/ours.yaml
```

代码会自动记录：

- 完整 config
- 每个 segment 的 train/eval 指标
- final metrics summary
- run tags 与 run name

## 投稿前的最低记录标准

AAAI 投稿前，至少需要形成：

- 主表：每个 benchmark 上所有 baselines + ours，至少 3 seeds。
- 消融：w/o drift、w/o bank、w/o router、w/o overlap，至少在主 benchmark 上 3 seeds。
- 诊断：drift quality、router quality、branch utilization、overlap、sequence behavior。
- 可复现包：config snapshots、result CSV、figure script、论文中每个数字能追溯到 run_id。
