import re
with open("/root/autodl-tmp/Lora-code/core/train.py", "r", encoding="utf-8") as f:
    content = f.read()

# Insert router prototype update
router_update_str = """
        # Update router prototypes using all training prompts for the current active branch
        if router is not None:
            all_prompts = [_format_prompt(ex.instruction, ex.input) for ex in seg.train]
            active_b = lora.get_active_adapter_name()
            # Feed current branch as the pseudo label
            router.update_with_pseudo_labels(
                batch_prompts=all_prompts,
                pseudo_labels=[active_b] * len(all_prompts),
                branch_names=[active_b]
            )
            logger.log(f"Updated router prototypes for branch {active_b} with {len(all_prompts)} examples.")
"""

# Find where to insert it: right before "Drift update after seeing eval results"
# Let's just insert it after the "Train metrics" logging
content = content.replace("        logger.log(f\"Train metrics: {json.dumps(train_metrics, ensure_ascii=False)}\")", 
                          "        logger.log(f\"Train metrics: {json.dumps(train_metrics, ensure_ascii=False)}\")\n" + router_update_str)

with open("/root/autodl-tmp/Lora-code/core/train.py", "w", encoding="utf-8") as f:
    f.write(content)
