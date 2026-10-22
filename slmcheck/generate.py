"""Resumable generation of code samples and self-tests. One model config at a time."""
from __future__ import annotations

import json
import time
import zlib
from pathlib import Path
from typing import Callable, Optional, Sequence

from . import config, prompts
from .backends import Backend, BackendError, RateLimited, make_backend
from .config import ModelConfig
from .dataset import Problem


def seed_for(problem_id: str, sample_idx: int) -> int:
    return 1000 * sample_idx + zlib.crc32(problem_id.encode()) % 1000


def _repair_tail(path: Path) -> None:
    """Drop a partially written last line left by a crash."""
    if path.exists() and path.stat().st_size:
        data = path.read_bytes()
        if not data.endswith(b"\n"):
            path.write_bytes(data[: data.rfind(b"\n") + 1])


def _drop_error_rows(path: Path) -> int:
    """Remove rows recorded as backend errors (no model output) so a rerun regenerates them."""
    if not path.exists() or not path.stat().st_size:
        return 0
    keep, dropped = [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            if json.loads(line).get("error"):
                dropped += 1
                continue
        except json.JSONDecodeError:
            pass
        keep.append(line)
    if dropped:
        path.write_text("".join(line + "\n" for line in keep), encoding="utf-8")
    return dropped


def _keys(path: Path, fields: Sequence[str]) -> set:
    out = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            out.add(tuple(r[f] for f in fields))
    return out


def _call(backend: Backend, messages, temperature, top_p, seed, max_tokens, log):
    """Retry rate limits forever and other errors 3 times; return (Completion|None, error)."""
    errors = 0
    while True:
        try:
            return backend.complete(messages, temperature, top_p, seed, max_tokens), None
        except RateLimited as e:
            log(f"rate limited, sleeping {e.retry_after_s:.0f}s")
            time.sleep(max(1.0, e.retry_after_s))
        except (BackendError, OSError, ValueError) as e:
            errors += 1
            if errors >= 3:
                return None, f"{type(e).__name__}: {e}"[:500]
            log(f"backend error ({errors}/3): {e}")
            time.sleep(10 * errors)


def samples_path(run: Path, cfg_name: str) -> Path:
    return run / f"samples__{cfg_name}.jsonl"


def selftests_path(run: Path, cfg_name: str) -> Path:
    return run / f"selftests__{cfg_name}.jsonl"


def load_all(run: Path | str, kind: str) -> list[dict]:
    """All rows of one kind ("samples" or "selftests") across the per-config files."""
    rows = []
    for path in sorted(Path(run).glob(f"{kind}__*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def generate(run_dir: Path | str, problems: Sequence[Problem], cfgs: Sequence[ModelConfig],
             backend_factory: Callable[[ModelConfig], Backend] = make_backend,
             limit: Optional[int] = None) -> dict[str, int]:
    """One file per config, so an SLM run and a Groq run can proceed in parallel processes."""
    run = Path(run_dir)
    run.mkdir(parents=True, exist_ok=True)
    probs = list(problems)[:limit] if limit else list(problems)
    counts = {}

    with open(run / "progress.log", "a", encoding="utf-8") as logf:
        def log(msg):
            logf.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
            logf.flush()

        for cfg in cfgs:
            samples_p, selftests_p = samples_path(run, cfg.name), selftests_path(run, cfg.name)
            for p in (samples_p, selftests_p):
                _repair_tail(p)
                if _drop_error_rows(p):
                    log(f"{cfg.name}: dropped error rows in {p.name}; they will be regenerated")
            done = _keys(samples_p, ("cfg", "problem_id", "sample_idx"))
            done_st = _keys(selftests_p, ("cfg", "problem_id"))
            todo = [(p, i) for p in probs for i in range(cfg.k) if (cfg.name, p.id, i) not in done]
            need_st = cfg.tier == "slm" and any((cfg.name, p.id) not in done_st for p in probs)
            counts[cfg.name] = sum(1 for p in probs for i in range(cfg.k)
                                   if (cfg.name, p.id, i) in done)
            if not todo and not need_st:
                continue
            log(f"start {cfg.name}: {len(todo)} samples to generate")
            backend = backend_factory(cfg)
            with open(samples_p, "a", encoding="utf-8") as sf:
                for n, (p, i) in enumerate(todo, 1):
                    temp = 0.0 if i == 0 else config.SAMPLE_TEMPERATURE
                    top_p = 1.0 if i == 0 else config.SAMPLE_TOP_P
                    seed = seed_for(p.id, i)
                    comp, err = _call(backend, prompts.codegen_messages(p), temp, top_p, seed,
                                      cfg.max_tokens, log)
                    rec = {"cfg": cfg.name, "tier": cfg.tier, "problem_id": p.id, "sample_idx": i,
                           "temperature": temp, "seed": seed,
                           "code": prompts.extract_code(comp.text) if comp else "",
                           "raw_text": comp.text if comp else "",
                           "thinking_chars": len(comp.thinking) if comp else 0,
                           "prompt_tokens": comp.prompt_tokens if comp else 0,
                           "completion_tokens": comp.completion_tokens if comp else 0,
                           "wall_s": round(comp.wall_s, 3) if comp else 0.0,
                           "model_digest": comp.model_digest if comp else None,
                           "error": err, "ts": time.time()}
                    sf.write(json.dumps(rec) + "\n")
                    sf.flush()
                    counts[cfg.name] += 1
                    log(f"{cfg.name} {p.id} #{i} ({n}/{len(todo)}) tok={rec['completion_tokens']} "
                        f"wall={rec['wall_s']}s{' ERROR ' + err if err else ''}")
            if cfg.tier == "slm":
                with open(selftests_p, "a", encoding="utf-8") as tf:
                    for p in probs:
                        if (cfg.name, p.id) in done_st:
                            continue
                        comp, err = _call(backend, prompts.selftest_messages(p, config.N_SELFTESTS),
                                          0.0, 1.0, seed_for(p.id, 99), cfg.max_tokens, log)
                        tests = prompts.parse_selftests(comp.text, p.testtype) if comp else []
                        tf.write(json.dumps({"cfg": cfg.name, "problem_id": p.id,
                                             "tests": [{"input": t.input, "output": t.output}
                                                       for t in tests],
                                             "raw_text": comp.text if comp else "", "error": err,
                                             "wall_s": round(comp.wall_s, 3) if comp else 0.0}) + "\n")
                        tf.flush()
                        done_st.add((cfg.name, p.id))
            log(f"done {cfg.name}")
    return counts
