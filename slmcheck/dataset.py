"""LiveCodeBench loading: download raw JSONL, decode tests safely, filter by date."""
from __future__ import annotations

import base64
import io
import json
import pickle
import random
import re
import time
import urllib.error
import urllib.request
import zlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional

from . import config


@dataclass(frozen=True)
class Test:
    __test__ = False  # not a pytest class
    input: str
    output: str
    testtype: str  # "stdin" | "functional"


@dataclass
class Problem:
    id: str
    title: str
    content: str
    platform: str
    contest_date: str
    difficulty: str
    starter_code: str
    func_name: Optional[str]
    public: list[Test]
    private: list[Test]
    benchmark: str = "livecodebench"

    @property
    def testtype(self) -> str:
        return (self.public or self.private)[0].testtype


class _NoGlobals(pickle.Unpickler):
    """Only primitive pickled data (the LCB payload is a JSON string); no classes or callables."""

    def find_class(self, module, name):
        raise pickle.UnpicklingError(f"global {module}.{name} not allowed")


def decode_tests(raw: str) -> list[Test]:
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        blob = zlib.decompress(base64.b64decode(raw.encode("utf-8")))
        items = json.loads(_NoGlobals(io.BytesIO(blob)).load())
    return [Test(str(t["input"]), str(t["output"]), str(t["testtype"])) for t in items]


def _func_name(metadata: str, starter_code: str) -> Optional[str]:
    try:
        name = json.loads(metadata or "{}").get("func_name")
    except json.JSONDecodeError:
        name = None
    if name:
        return name
    m = re.search(r"def\s+(\w+)\s*\(\s*self", starter_code or "")
    return m.group(1) if m else None


def _row_to_problem(r: dict) -> Problem:
    return Problem(
        id=r["question_id"], title=r["question_title"], content=r["question_content"],
        platform=r["platform"], contest_date=r["contest_date"][:10], difficulty=r["difficulty"],
        starter_code=r.get("starter_code") or "",
        func_name=_func_name(r.get("metadata", ""), r.get("starter_code", "")),
        public=decode_tests(r["public_test_cases"]), private=decode_tests(r["private_test_cases"]),
    )


def download_raw(dest_dir: Path | str) -> list[Path]:
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    got = []
    for name in config.LCB_FILES:
        path = dest / name
        if not path.exists():
            try:
                with urllib.request.urlopen(config.LCB_URL.format(name=name), timeout=120) as resp:
                    tmp = path.with_suffix(".part")
                    with open(tmp, "wb") as f:
                        while chunk := resp.read(1 << 20):
                            f.write(chunk)
                    tmp.replace(path)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue
                raise
        got.append(path)
    return got


def build_problem_file(raw_paths: Iterable[Path | str], out_path: Path | str,
                       since: str = config.SINCE) -> int:
    seen, problems = set(), []
    for raw in raw_paths:
        with open(raw, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if r["contest_date"][:10] < since or r["question_id"] in seen:
                    continue
                seen.add(r["question_id"])
                problems.append(_row_to_problem(r))
    problems.sort(key=lambda p: (p.contest_date, p.id))
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for p in problems:
            f.write(json.dumps(asdict(p)) + "\n")
    return len(problems)


def load_problems(path: Path | str) -> list[Problem]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                d["public"] = [Test(**t) for t in d["public"]]
                d["private"] = [Test(**t) for t in d["private"]]
                out.append(Problem(**d))
    return out


# ---- MBPP+ (EvalPlus) -------------------------------------------------------------------------

def download_mbpp(dest_dir: Path | str) -> Path:
    """Fetch all MBPP+ rows as JSONL via the HF datasets-server rows API (no parquet dependency)."""
    path = Path(dest_dir) / "mbppplus.jsonl"
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    rows, offset = [], 0
    while True:
        for attempt in range(5):  # the rows API occasionally returns an empty body
            try:
                with urllib.request.urlopen(config.MBPP_ROWS_URL.format(offset=offset), timeout=120) as r:
                    d = json.loads(r.read())
                break
            except (OSError, ValueError):
                if attempt == 4:
                    raise
                time.sleep(5 * (attempt + 1))
        batch = [x["row"] for x in d["rows"]]
        rows += batch
        offset += len(batch)
        if not batch or offset >= d["num_rows_total"]:
            break
    tmp = path.with_suffix(".part")
    tmp.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(path)
    return path


def _mbpp_entry_point(row: dict) -> Optional[str]:
    m = re.search(r"assertion\((\w+)\(\*inp\)", row.get("test", ""))
    if m:
        return m.group(1)
    m = re.search(r"assert\s+(?:\w+\()?\s*(\w+)\(", (row.get("test_list") or [""])[0])
    return m.group(1) if m else None


def mbpp_row_to_problem(row: dict) -> Problem:
    imports = "\n".join(row.get("test_imports") or [])
    pre = (imports + "\n") if imports else ""
    tl = list(row["test_list"])
    return Problem(
        id=f"mbpp/{row['task_id']}", title="", content=row["prompt"].strip(), platform="mbppplus",
        contest_date="2021-01-01", difficulty="easy", starter_code="",
        func_name=_mbpp_entry_point(row),
        public=[Test(pre + tl[0], "", "script")],
        private=[Test(pre + t, "", "script") for t in tl[1:]] + [Test(pre + row["test"], "", "script")],
        benchmark="mbppplus",
    )


def build_mbpp_problem_file(raw_path: Path | str, out_path: Path | str,
                            n: int = config.MBPP_SAMPLE, seed: int = config.MBPP_SEED) -> int:
    rows = [json.loads(l) for l in Path(raw_path).read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if int(r["task_id"]) not in config.MBPP_EXCLUDE]
    rows.sort(key=lambda r: int(r["task_id"]))
    if n and n < len(rows):
        rows = sorted(random.Random(seed).sample(rows, n), key=lambda r: int(r["task_id"]))
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(asdict(mbpp_row_to_problem(r))) + "\n")
    return len(rows)
