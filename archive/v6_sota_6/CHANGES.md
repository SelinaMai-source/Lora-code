# v6_sota_6 —— Verify-then-Route：低置信路由的 prompt-NLL 仲裁

日期：2026-06-12
基础版本：v6_sota_2 方法 + epochs=3（v6_5 预算）

## 动机（v6_3/v6_4/v6_5 三连败的系统结论）
| 版本 | 预算 | 评测路由 | 结果 |
|---|---|---|---|
| v6_2 | 1ep | soft top-3 混合 | 0.350（基线，分支欠拟合封顶） |
| v6_3 | 5ep | soft top-3 混合 | seg4 早停：混合摧毁特化分支（训练 0.998/评测 0） |
| v6_4 | 5ep | hard top-1 | seg3 早停：路由错误无对冲（agree 0.35-0.61） |
| v6_5 | 3ep | soft top-3 混合 | seg4=0.2 杀停：3ep 混合破坏依旧显著 |

结论：**参数级 blending 在冻结-特化分支库中破坏性随预算单调增长；纯硬路由又承受不了原型路由的错误率**。需要不动参数的"对冲"机制。

## 本版改动
1. `core/models/base_model.py`：新增 `score_prompt_nlls(prompts)` —— 对已格式化 prompt 文本做 teacher-forced 自身 NLL（逐 token 平均）。**只用输入 x，不碰任何标签** → 评测公平。
2. `core/methods/router.py`：新增配置 `nll_arbitration / arbitration_margin(0.15) / arbitration_top_k(3)`。
3. `core/evaluate.py`：硬路由决策的 top1-top2 概率差 < margin 时，对 top-3 候选分支分别计算 prompt-NLL，取最小者作为最终分支（统计 `nll_arbitration_count/changed`）。
4. 配置：epochs=3, batch=1, soft_routing=false, nll_arbitration=true；其余同 v6_2/v6_5。

## Novelty 论证
最接近工作：**DEMix Layers (Gururangan et al., 2022)** 用专家对输入的困惑度估计域后验做加权集成；**ZOOTER/路由集成**类工作用奖励/困惑度选模型。区别：
1. DEMix 是预训练期固定域专家 + 概率加权混合（输出级），我们是**漂移触发动态 spawn 的冻结 LoRA 分支 + 不确定性门控的级联仲裁**——仅低置信样本付出额外 NLL 前向（top-3），高置信样本零开销；
2. 仲裁与原型路由形成两级证据融合（特征空间余弦 → 参数空间似然），针对 CL 中 router 记忆与分支记忆解耦这一具体失败模式（v6_1 的 oracle 衰减曲线 + v6_3/4/5 的权衡证据链是论文 motivation）；
3. 显式禁用参数混合的决策来自我们的"专精化-干扰权衡"发现，与 soft-MoE 文献的默认假设相反。

## 公平性自查
- prompt-NLL 仅用输入文本，无标签泄漏；不用任务 ID；额外计算只发生在评测期路由（与 baseline 的对比仍按训练预算对齐：均为 3ep？——注意：baseline 是 5ep，本版 3ep 是对 ours 更不利的预算，公平性方向安全）。

## 判据
- 内置早停（seg≥3 seen<0.2）。
- seg3/seg4 当场分恢复 ≥0.9/0.9 → 假设成立；seg4 ≤0.5 → 杀停（仲裁不足以救路由，转 epochs=1+仲裁 或重新审视原型特征）。
- seg6-8 seen_avg 须 ≥ v6_2 同期-0.05（0.426/0.373/0.294）。
- 关注 wandb/metrics 中 nll_arbitration_count/changed 与 oracle_agreement 是否较 v6_4 上升。

## 运行信息
- tmux: v6_sota_6 | 日志 v6_sota_6.log | wandb run qkd8bynz
- 结果目录：results/runs/paper_instrdialog_ours_full_s123_v6_sota_6/
