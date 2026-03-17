## Checkpoints（训练中间产物）

本目录用于存放训练过程中产生的 checkpoint（建议不提交到 git）。

### 推荐组织方式

建议按 run_id 进行分组，例如：

```
assets/checkpoints/
  <run_id>/
    backbone/               # 未来：主干模型 checkpoint（如有）
    adapters/
      b0/
      b1/
      ...
    router/
      router.pt             # 未来：router 参数
    metadata.json           # 记录分支创建时间、配置快照等
```

### 分支与 router 的关系

- LoRA bank 中每个分支通常对应一个 adapter checkpoint。
- router 需要保存其参数与校准信息，以便复现实验时推理选择一致。

当前仓库在 debug 模式下不保存真实 torch 权重，但 `core/train.py` 已准备好统一落盘目录与元信息写入位置（run artifacts 会写入 `results/runs/<run_id>/`）。

