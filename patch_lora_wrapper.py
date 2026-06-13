import re

with open("core/models/lora_wrapper.py", "r") as f:
    content = f.read()

# Remove get_adapter_vector and merge_adapters
content = re.sub(r'    def get_adapter_vector\(self, name: str, \*, detach: bool = True\) -> torch\.Tensor:.*?    def step_adapter\(self\) -> Dict\[str, Any\]:', '    def step_adapter(self) -> Dict[str, Any]:', content, flags=re.DOTALL)

with open("core/models/lora_wrapper.py", "w") as f:
    f.write(content)
