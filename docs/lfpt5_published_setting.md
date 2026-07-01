# LFPT5 — published_setting external runner

LFPT5 (ICLR 2022) uses **prompt tuning on LM-adapted T5-large**, not Llama + `core/train.py`.
Configs live at `configs/paper/published_setting/*__lfpt5__s123.yaml` with `runner: lfpt5_external`.

## 状态（2026-06-17 续）

| 项 | 状态 |
| --- | --- |
| 源码 | ✅ `external_baselines/lfpt5/` |
| LM-adapted T5-large PyTorch ckpt | ❌ 未就绪 → **blocked**（5/5 benchmark） |
| Wrapper | ✅ `scripts/run_lfpt5_published_setting.py` |
| InstrDialog / InstrDialog++ stream export | ✅ wrapper 可将 processed JSON 导出到 `results/runs/<run>/lfpt5_export/` |

### 下载尝试（2026-06-17 20:20–20:42）

| 来源 | 代理 | 结果 |
| --- | --- | --- |
| HF `google/t5-large-lm-adapt`（`pytorch_model.bin` ~3.0GB） | clash `127.0.0.1:7890` | ❌ `huggingface_hub` 卡在 ~256MB；`wget`/`curl` 经代理 SSL `unexpected eof`（约 16MB 后失败） |
| GCS `gs://t5-data/.../t5.1.1.lm100k.large/` | 直连（无代理） | ⚠️ 小文件可下（`checkpoint`/`model-info.txt`/`index`）；`model.ckpt-1100000.meta`（78MB）极慢（~100KB/s），4×data shard 未下完 |
| GCS | clash 代理 | ❌ 间歇性 SSL 失败 |

**结论**：checkpoint 仍未落到 `assets/pretrained/lfpt5/lm_adapted_t5_large_torch/pytorch_model.bin`。gap manifest 保持 5 行 `blocked`；未重启 gap tmux（无可跑 queued 项）。

**建议续传**（任选其一，完成后 `python scripts/gen_full_matrix_gap_audit_s123.py && python scripts/gen_published_setting_run_v2_gap_manifest.py` 再启 gap 队列）：

```bash
# A) HF（网络稳定时，可不用代理或换节点）
export https_proxy=http://127.0.0.1:7890
huggingface-cli download google/t5-large-lm-adapt pytorch_model.bin \
  --local-dir assets/pretrained/lfpt5/lm_adapted_t5_large_torch

# B) GCS TF → convert（官方路径，建议直连 + 后台）
mkdir -p assets/pretrained/lfpt5/gcs_tf/t5.1.1.lm100k.large
BASE=https://storage.googleapis.com/t5-data/pretrained_models/t5.1.1.lm100k.large
for f in checkpoint model-info.txt model.ckpt-1100000.* operative_config.gin; do
  curl -L -C - -o "assets/pretrained/lfpt5/gcs_tf/t5.1.1.lm100k.large/$f" "$BASE/$f"
done
# 然后在 external_baselines/lfpt5/ 按 README 运行 convertmodel.py
```

## 阻塞原因

官方复现需：

1. `conda create -n lfll_1 python=3.9.4` + PyTorch 1.7 + 内置 transformers + TensorFlow 2.5
2. 从 GCS 下载 `t5.1.1.lm100k.large` TF checkpoint（gsutil）
3. `python convertmodel.py` → PyTorch `pytorch_model.bin`
4. 目标路径：`assets/pretrained/lfpt5/lm_adapted_t5_large_torch/pytorch_model.bin`

## 最小 smoke（checkpoint 就绪后）

```bash
# 验证 config + 数据导出
python scripts/run_lfpt5_published_setting.py \
  --config configs/paper/published_setting/instrdialog__lfpt5__s123.yaml --dry-run

# 官方分类入口（需在 lfll_1 环境、修改 Classification.sh 路径）
cd external_baselines/lfpt5/Classification
# 参考 Classification.sh；将 --lm_adapted_path 指向上述 pytorch_model.bin
```

## Gap 队列行为

`scripts/run_published_setting_run_v2_gap_queue.sh` 对 LFPT5 行调用 wrapper；无 checkpoint 时标记 `blocked`，**不伪造** `final_metrics.json`。

## 参考

- 官方 README：`external_baselines/lfpt5/README.md`
- Progressive Prompts / O-LoRA 论文中 LFPT5 作为强 baseline
