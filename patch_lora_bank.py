import re

with open("core/methods/lora_bank.py", "r") as f:
    content = f.read()

# Remove merge_most_similar_branches
content = re.sub(r'    def merge_most_similar_branches\(self\) -> None:.*?    def spawn_new_branch', '    def spawn_new_branch', content, flags=re.DOTALL)

# Replace spawn_new_branch logic
old_spawn = """    def spawn_new_branch(self, \*, lora_wrapper: Any, segment_id: int) -> str:
        \"\"\"
        Create a new branch and switch to it.
        If max_branches reached, merge the two most similar frozen branches to free capacity.
        \"\"\"

        self._lora_wrapper = lora_wrapper
        if len(self._branches) >= self.max_branches:
            self.merge_most_similar_branches()
            
        # Find an available name
        for i in range(self.max_branches \+ 100):
            name = f"b\{i\}"
            if name not in self._branches:
                break
        else:
            name = f"b\{len(self._branches)\}_overflow_s\{segment_id\}"

        if name not in lora_wrapper.list_adapters\(\):
            lora_wrapper.create_adapter\(name\)
        lora_wrapper.set_active_adapter\(name\)

        self._branches\[name\] = BranchInfo\(name=name, created_at_segment=segment_id, frozen=False\)
        self._active = name
        return name"""

new_spawn = """    def spawn_new_branch(self, *, lora_wrapper: Any, segment_id: int) -> str:
        \"\"\"
        Create a new branch and switch to it.
        If max_branches reached, apply a simple policy: do not delete; reuse last branch name with suffix.
        (Future: implement eviction/merge policy.)
        \"\"\"

        self._lora_wrapper = lora_wrapper
        if len(self._branches) >= self.max_branches:
            # simple deterministic reuse naming to avoid destructive deletes
            name = f"b{len(self._branches)}_overflow_s{segment_id}"
        else:
            name = f"b{len(self._branches)}"

        if name not in lora_wrapper.list_adapters():
            lora_wrapper.create_adapter(name)
        lora_wrapper.set_active_adapter(name)

        self._branches[name] = BranchInfo(name=name, created_at_segment=segment_id, frozen=False)
        self._active = name
        return name"""

content = re.sub(old_spawn, new_spawn, content)

with open("core/methods/lora_bank.py", "w") as f:
    f.write(content)
