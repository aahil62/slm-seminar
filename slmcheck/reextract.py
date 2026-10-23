"""Recompute each saved sample's `code` from its `raw_text` after an extractor fix.

The model's reply (`raw_text`) is the data; `code` is derived from it. Originals are copied to
<run>/_superseded/samples_before_reextract/ first. Changed rows get "code_reextracted": true.
Never calls a model. Usage: python -m slmcheck.reextract runs/main runs/mbpp
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from .prompts import extract_code


def reextract(run_dir: Path | str) -> dict[str, int]:
    run = Path(run_dir)
    backup = run / "_superseded" / "samples_before_reextract"
    changed: dict[str, int] = {}
    for path in sorted(run.glob("samples__*.jsonl")):
        rows, n = [], 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            new = extract_code(r.get("raw_text", ""))
            if new != r.get("code", ""):
                r["code"], r["code_reextracted"] = new, True
                n += 1
            rows.append(r)
        if n:
            backup.mkdir(parents=True, exist_ok=True)
            if not (backup / path.name).exists():
                shutil.copy2(path, backup / path.name)
            path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        changed[path.name] = n
    return changed


if __name__ == "__main__":
    for d in sys.argv[1:]:
        print(d, reextract(d))
