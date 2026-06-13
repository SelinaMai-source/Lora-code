# v6_sota_1 —— 协议加固版重基线（fairness-fixed re-baseline）

日期：2026-06-11
基础版本：v4_sota_39（历史最佳完整跑：seen_avg=0.3518, task_aware=0.3833, forgetting=0.0500, task_aware_forgetting=0.0389, token_f1=0.4352, lcs=0.4753）

## 背景
- v5 系列（v5_sota_1..42）尝试了 thermodynamic drift、CDMA 相似度、VIB router 等改动，整体显著差于 v4_sota_39（最好的 v5 完整跑 seen_avg≈0.25，v5_42 在 segment 13 被早停，seen_avg=0.179）。
- 以 CCF-A 审稿人视角自查当前代码（v5_42 状态），发现两处协议漏洞，必须先修复再谈创新，否则一切数字不可信。

## 修复的两个评测协议漏洞（本版核心改动）
1. **任务边界信息泄漏**（`core/methods/drift_detector.py`）：
   v5 代码在 `DriftDetector.update()` 中对"segment_id 变化"无条件 `force_trigger=True`，即用 ground-truth 任务边界强制 spawn 新分支，却对外宣称是 task-agnostic 漂移检测。这等于"用 task-aware 信息冒充 task-agnostic"。
   修复：默认关闭强制触发，新增配置 `drift.force_spawn_on_segment_boundary`（默认 false，仅供 ablation）；分支 spawn 必须由 CUSUM 信号本身触发。v4_sota_39 当时的 9 次 drift 事件全部是 `probe_cusum_and_core_guard` 信号触发，证明信号驱动可行。
2. **测试集污染**（`core/methods/drift_detector.py` + `core/train.py`）：
   漂移监控 anchor set 一直取自各 segment 的 **eval split**（连同其参考答案算 NLL），anti-overlap 的激活 anchor 兜底也用 `seg.eval[:8]`。虽然不直接训练，但方法决策（何时 spawn 分支）依赖了测试样本，属于评测集污染。
   修复：新增 `drift.anchor_source: train`（v6 起默认配置使用 train），anchor 全部改取 train split；`train.py` 中 overlap 兜底 prompts 改为 `seg.train[:8]`。

## 配置
- 完全继承 v4_sota_39 的 config snapshot（lr=2e-4, batch=2, epochs=1, r=16, drift.threshold=0.025, calibration_window=1, shift_stat=absolute, score_ema=0.0, max_branches=15, router lr=0.008, margin_filter=0.05, soft_routing top3@T=0.08, overlap beta=0.05/abs_cosine），仅叠加上述两个修复及 wandb tracking。
- 启动方式：`python3 core/train.py --config configs/paper/v6_sota_1.yaml`（tmux 会话 v6_sota_1，日志 v6_sota_1.log）。
- wandb：project=lora-citb-sota, group=v6_sota, tags=[v6_sota_1, ours_full, fairness_fixed]，逐 segment 指标 + 最终 summary。

## Novelty / 影响力论证
本版定位是**正确性迭代**而非创新迭代（迭代规则第 5 条优先于第 1 条：发现漏洞立即修复并重跑）。它建立后续所有创新版本的可信基线：
- 与最接近工作的区别：与 O-LoRA / MoE-CL 等方法的对比实验中常见的隐式 task-boundary 假设在本版被显式移除并以配置开关留作 ablation，这本身是论文 fairness 章节的素材（task-agnostic 声明的可验证性）。
- 对社区的影响：task-agnostic 持续学习的评测可信性是 CCF-A 审稿的硬门槛；本版给出"信号驱动 spawn vs 边界泄漏 spawn"的对照锚点。

## 预期
- 修复 anchor 来源后漂移信号尺度变化（train 样本 NLL 更低、漂移偏差更明显），预计 spawn 频率与 v4_39 相近或略高。
- 目标：复现 v4_39 量级（seen_avg≈0.35）。若显著低于（早期 segment 与 v4_39 同期差距大）则早停，分析信号尺度并调 threshold。

## 下一步（v6_sota_2+ 候选，按瓶颈选择）
- 瓶颈诊断（来自 v4_39 最终指标）：eval 路由 oracle_agreement 仅 0.488，oracle_margin_mean 0.343 —— 路由错误是 seen_avg 的最大损失来源；其次是单任务学习上限（task_aware 也只有 0.38）。
- 候选方向：路由置信度滞回（Schmitt-trigger hysteresis routing）、分支证据累积（sequential probability ratio test 路由）、对 token_f1/lcs 的生成前缀对齐。
