# v6_sota_2 —— 漂移锚定原型路由器（Drift-Anchored Prototype Router）

日期：2026-06-11
基础版本：v6_sota_1（协议加固版；早停于 segment 12，seen_avg=0.162，明显差于 v4_sota_39 同期 0.306）

## v6_sota_1 失败分析（瓶颈定位）
v6_1 逐 segment 对比 v4_39：seg0-3 完全持平，seg4 起持续走低；eval 路由 oracle 一致率从 seg4 的 0.49 一路崩到 seg12 的 0.15，遗忘升至 0.12。根因在 v5 遗留的 router 实现：
1. 打分函数是 Poincaré 双曲距离 + PID 补偿 + Tsallis q-softmax + Ising/流体惩罚的堆叠，输出概率几乎均匀（决策 margin ~0.006，熵 ~1.1）；
2. 每个 segment 只对 router head 做 **一次** 梯度步（AdamW lr=0.008），新分支行零初始化后根本来不及学（router_train_acc=0.0）；
3. margin 过滤（min_gap=0.05）在 margin~0.006 的尺度下把 100% 训练样本打回 active 分支。
分支数随漂移增长后，路由完全失效 → 旧 segment 得分归零 → seen_avg 崩塌。

## 本版改动（增量、单点）
仅替换 router 打分/更新机制，其余（漂移检测、bank、anti-overlap、训练协议、公平性修复）与 v6_1 完全一致：
- 新增 `router.routing_backend: prototype`（旧实现保留为 `legacy` 供 ablation）。
- **原型构建**：每个 segment 训练后，用 teacher-forced NLL 自一致伪标签（已有机制）把训练样本指派给"最能解释它的分支"，对每个分支用被指派样本的归一化特征均值做 EMA 更新（`prototype_ema=0.8`）。
- **冻结一致性**：分支被 bank 冻结时其原型同步冻结（仅允许一次性初始化），保证旧任务签名不被新任务覆写——这是对"为什么旧分支路由会坏"的直接回答。
- **打分**：余弦相似度 / temperature → softmax，margin 尺度恢复到可解释区间；沿用 soft routing top-3。
- `margin_filter_min_gap` 0.05 → 0.02 适配新 margin 尺度。

## Novelty 论证
最接近工作：S-Prompts / HiDe-Prompt（ViT 上 K-Means 任务原型选 prompt，任务边界已知）、MoE-Adapters（CLIP，可训练 router）、O-LoRA（正交子空间，无路由）。区别：
1. 我们的原型在 **task-agnostic 流**上由漂移检测器触发的分支 spawn 锚定，原型归属由 **teacher-forced NLL 自一致验证**（不是无监督聚类，也不依赖任务 ID）；
2. 原型与 LoRA 分支 **同步冻结**，给出"路由记忆"与"参数记忆"一致性的显式机制，直接针对 router 漂移这一 CL-MoE 社区痛点（v6_1 的 oracle 一致率衰减曲线就是论文里的 motivating figure）。

## 预期与判据
- 预期 oracle_agreement 在多分支段（seg6+）维持 >0.4（v6_1 为 0.15-0.2）；seen_avg 回到 v4_39 轨迹（seg9≈0.35）以上。
- 早停判据：内置 seen_avg<0.2（seg≥3）自动退出；人工判据：seg6-9 若仍低于 v4_39 同期 0.05 以上则杀停换版。

## 运行信息
- tmux 会话：v6_sota_2；日志：/root/autodl-tmp/Lora-code/v6_sota_2.log
- wandb：project=lora-citb-sota, group=v6_sota, tags=[v6_sota_2, ours_full, prototype_router]
- 结果目录：results/runs/paper_instrdialog_ours_full_s123_v6_sota_2/
