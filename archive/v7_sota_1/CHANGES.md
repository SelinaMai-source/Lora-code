# v7_sota_1 —— 置信度校准原型路由 + 不确定性门控 NLL 仲裁

日期：2026-06-12
基础版本：v6_sota_2（最佳 v6，seen_avg=0.35 @seg18）

## 失败分析（v6_sota_3..6）
| 版本 | 关键变更 | 结果 |
|---|---|---|
| v6_3 | 5ep + soft blend | seg4 早停：混合摧毁特化分支 |
| v6_4 | 5ep + hard route | seg3 早停：无对冲的路由错误致命 |
| v6_5 | 3ep + soft blend | seg4=0.2 杀停 |
| v6_6 | 3ep + hard + NLL仲裁 | seg3 seen=0.05 杀停：3ep 欠拟合 + 硬路由无 soft 缓冲 |

结论：v6_sota_2 的 **1ep/batch=2/soft top-3** 预算是正确的；路由改进必须在**不增加训练预算**、**不破坏 soft 路由高置信收益**的前提下进行。

## 本版改动（单点假设）
**假设**：原型路由的主要误差来自 (1) 低支持度原型的过度自信匹配；(2) 低 margin 时 soft blending 的破坏性干扰。用**支持度校准**抑制稀疏原型，用**仅低 margin 的 NLL 验证-再路由**替代混合。

1. `core/methods/router.py`
   - 新增 `prototype_calibration` + `prototype_calibration_prior`（默认 10）
   - 打分：`sim_cal = sim * count/(count+prior)` — 贝叶斯式可靠性加权，稀疏分支 logits 被拉向均匀

2. `core/evaluate.py`
   - NLL 仲裁不再要求 `soft_routing=false`；低 margin（<0.12）时触发
   - 仲裁后对该样本 **硬路由**到 NLL 赢家，跳过 soft blending（`arbitrated_low_margin` 门控）
   - 高 margin 样本保持 v6_sota_2 的 soft top-3 混合

3. `core/train.py`
   - 新增轨迹早停：seg≥3 时若 `seen_avg < v6_sota_2[seg] - 0.05` 则杀停

4. 配置：`epochs=1, batch=2`（同 v6_2）；`prototype_calibration=true`；`nll_arbitration=true, arbitration_margin=0.12`

## Novelty 论证
最接近：**温度缩放校准**（Guo et al., ICML 2017）、**DEMix 困惑度路由**（Gururangan et al., 2022）、**MoE 不确定性门控**（Shazeer et al., 2017）。
区别：
1. 校准对象不是分类头而是 **CL 动态 spawn 的原型**，支持度来自 teacher-forced NLL 伪标签计数（非监督聚类规模）；
2. NLL 仲裁与 soft blending **按 margin 解耦**：高置信走特征空间混合，低置信走参数空间似然级联——针对 v6 系列发现的"专精化-干扰权衡"；
3. 全程无任务 ID、无标签泄漏（prompt-NLL 仅用输入）。

## 判据
- seg3 seen_avg ≥ 0.20（v6_2=0.25，轨迹地板 0.20）
- seg4 seen_avg ≥ 0.29（v6_2=0.34，地板 0.29）
- oracle_agreement 在 seg6+ 维持 >0.45（v6_2≈0.47-0.53）
- nll_arbitration_changed/num_routed 比率合理（5-30%）

## 运行信息
- tmux: v7_sota_1 | 日志 v7_sota_1.log
- wandb: project=lora-citb-sota, group=v7_sota, tags=[v7_sota_1]
- 结果：results/runs/paper_instrdialog_ours_full_s123_v7_sota_1/
