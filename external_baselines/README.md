# External Baselines

本目录保存已下载的 advanced baseline 官方或高可信源码。当前阶段的目标是“可复现准备完成”，不是在当前全局环境直接安装旧依赖或启动长训练。

## 当前材料

- 官方 smoke 计划：`official_smoke_plan.md`
- lora-run_v10 strict 接入清单：`../docs/lora_run_v10_official_baseline_integration.md`
- 统一轻量检查脚本：`../scripts/smoke_external_baselines.sh`
- 下载/可达性记录：`download_log.tsv`、`reachability_log.tsv`、`clone_reachable_log.tsv`、`fallback_clone_log.tsv`

## 使用方式

只做轻量入口检查：

```bash
bash scripts/smoke_external_baselines.sh all
```

逐个检查：

```bash
bash scripts/smoke_external_baselines.sh o_lora
bash scripts/smoke_external_baselines.sh progressive_prompts
bash scripts/smoke_external_baselines.sh continual_t0
bash scripts/smoke_external_baselines.sh lfpt5
bash scripts/smoke_external_baselines.sh adaptercl_dialogue
bash scripts/smoke_external_baselines.sh lamol
bash scripts/smoke_external_baselines.sh trace_rcl
```

脚本不安装依赖、不下载数据或权重、不执行长训练。`NEEDS_ENV` 表示官方入口存在，但当前全局环境缺少该仓库独立依赖。

注意：`baselines/advanced_baselines/o_lora`、`lb_cl`、`progressive_prompts`、`continual_t0` 是统一管线 scaffold，不能作为 strict published-paper 结果上报。先按 strict 接入清单绑定官方代码或忠实移植，再排 full single-seed rerun。
