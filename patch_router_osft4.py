import re

with open("core/methods/router.py", "r") as f:
    content = f.read()

# Replace predict_branch to not use hashing
new_predict = """    def predict_branch(self, prompt: str, branch_names: List[str], branch_meta: Dict[str, Any], segment_id: int = 0, **kwargs) -> RoutingDecision:
        latest = branch_names[-1]
        scores = {b: (1.0 if b == latest else 0.0) for b in branch_names}
        return RoutingDecision(branch_name=latest, scores=scores, hard=True, reason="osft_single_branch_routing")
"""

content = re.sub(r"    def predict_branch\(self.*?return RoutingDecision\(branch_name=best_b, scores=scores, hard=True, reason=\"bures_routing\"\)", new_predict, content, flags=re.DOTALL)

with open("core/methods/router.py", "w") as f:
    f.write(content)
