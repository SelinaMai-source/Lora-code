#!/usr/bin/env bash
set -euo pipefail

echo "[Model] Download scaffolding script"
echo
echo "Target model: meta-llama/Llama-3.1-8B-Instruct"
echo
echo "This script creates a safe directory layout and provides guidance."
echo "It does NOT pretend to download weights if access is gated."
echo

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PRETRAINED_DIR="${ROOT_DIR}/assets/pretrained"
TARGET_DIR="${PRETRAINED_DIR}/meta-llama/Llama-3.1-8B-Instruct"

mkdir -p "${TARGET_DIR}"

cat <<'EOF'
Created:
  assets/pretrained/meta-llama/Llama-3.1-8B-Instruct/

How to download (recommended on compute machine):
  1) Ensure you have accepted the model terms on Hugging Face (gated access may apply).
  2) Authenticate:
       huggingface-cli login
  3) Download using huggingface_hub (example):
       python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='meta-llama/Llama-3.1-8B-Instruct', local_dir='assets/pretrained/meta-llama/Llama-3.1-8B-Instruct', local_dir_use_symlinks=False)"

Notes:
  - You may alternatively rely on the default HF cache, but then set
    configs/*.yaml -> model.hf_model_name_or_path accordingly.
  - This repository intentionally does NOT include model weights.
EOF

