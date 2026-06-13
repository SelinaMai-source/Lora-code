#!/bin/bash
set -e
cd /root/autodl-tmp/Lora-code

# 1. router_only
cat << 'INNER_EOF' > run_fair_router_only.sh
#!/bin/bash
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids router_only \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix fair_15 \
  --set router.num_initial_branches=15 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_router_only.log
INNER_EOF
chmod +x run_fair_router_only.sh
tmux new-session -d -s fair_router_only ./run_fair_router_only.sh

# 2. periodic_latest
cat << 'INNER_EOF' > run_fair_periodic.sh
#!/bin/bash
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids periodic_latest \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix fair_15 \
  --set periodic.max_branches=15 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_periodic.log
INNER_EOF
chmod +x run_fair_periodic.sh
tmux new-session -d -s fair_periodic ./run_fair_periodic.sh

# 3. bank_no_router
cat << 'INNER_EOF' > run_fair_bank.sh
#!/bin/bash
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids bank_no_router \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix fair_15 \
  --set bank.max_branches=15 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_bank.log
INNER_EOF
chmod +x run_fair_bank.sh
tmux new-session -d -s fair_bank ./run_fair_bank.sh

# 4. replay
cat << 'INNER_EOF' > run_fair_replay.sh
#!/bin/bash
export CUDA_VISIBLE_DEVICES=0
WANDB_MODE=online python3 scripts/run_paper_matrix.py \
  --benchmarks instrdialog \
  --modes baseline \
  --variant-ids replay_b50 \
  --epochs-per-segment 1 \
  --batch-size 2 \
  --run-name-suffix fair_200 \
  --set replay.buffer_size=200 \
  --skip-existing 2>&1 | tee results/overnight_logs/fair_replay.log
INNER_EOF
chmod +x run_fair_replay.sh
tmux new-session -d -s fair_replay ./run_fair_replay.sh

