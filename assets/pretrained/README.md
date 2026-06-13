## 预训练模型权重（pretrained）

本目录建议用于存放 `meta-llama/Llama-3.1-8B-Instruct` 的本地权重副本，便于在算力机上复现实验而不依赖临时网络环境。

### 推荐路径约定

建议将模型放在：

```
assets/pretrained/meta-llama/Llama-3.1-8B-Instruct/
```

然后在 `configs/baseline.yaml` / `configs/ours.yaml` 中设置：
- `model.hf_model_name_or_path: assets/pretrained/meta-llama/Llama-3.1-8B-Instruct`

### 注意事项

- Llama 3.1 系列可能需要 Hugging Face 账号授权与条款同意（访问 gating）。
- 你也可以不把权重拷贝到本仓库目录，而直接把配置指向你的 HF cache 路径；但建议至少在算力机上固定一个可追溯路径用于复现。

### 下载脚手架

请运行 `assets/pretrained/download_model.sh` 查看下一步说明与目录创建逻辑。

