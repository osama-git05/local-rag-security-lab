from app.paths import ROOT
from pathlib import Path

import httpx


response = httpx.post(
    "http://127.0.0.1:11434/api/show",
    json={"model": "qwen3:4b"},
    timeout=30.0,
)
response.raise_for_status()

template = response.json()["template"].replace("\r\n", "\n")

old_prefix = "<|im_start|>assistant\n<think>\n"
new_prefix = "<|im_start|>assistant\n<think>\n\n</think>\n\n"

if template.count(old_prefix) != 1:
    raise ValueError(
        "Expected exactly one generation prefix. No file was changed."
    )

updated_template = template.replace(old_prefix, new_prefix, 1)

modelfile = (
    "FROM qwen3:4b\n"
    'TEMPLATE """'
    + updated_template
    + '"""\n'
)

path = ROOT / "experiments" / "Modelfile.qwen3-lab"
path.write_text(modelfile, encoding="utf-8")

print(f"Created {path.name}")