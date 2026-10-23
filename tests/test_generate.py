import json
from slmcheck import backends, generate
from slmcheck.config import ModelConfig
from slmcheck.dataset import load_problems

FIX = "slmcheck/fixtures/problems.jsonl"
SLM = ModelConfig("fake-slm", "fake", "fake", k=3)
LLM = ModelConfig("fake-llm", "fake", "fake", k=1, tier="llm")


def factory(calls=None, fail_once=None):
    state = {"failed": False}

    def script(messages, seed):
        if calls is not None:
            calls.append(seed)
        if fail_once and not state["failed"]:
            state["failed"] = True
            raise fail_once
        if "test cases" in messages[-1]["content"]:
            return '```json\n[{"input": "1 1\\n", "output": "2\\n"}]\n```'
        return "```python\nprint(1)\n```"

    return lambda cfg: backends.FakeBackend(script)


def test_generate_writes_k_samples_per_problem(tmp_path):
    probs = load_problems(FIX)
    counts = generate.generate(tmp_path, probs, [SLM, LLM], backend_factory=factory())
    rows = generate.load_all(tmp_path, "samples")
    assert counts == {"fake-slm": 9, "fake-llm": 3}
    assert len(rows) == 12
    s0 = [r for r in rows if r["cfg"] == "fake-slm" and r["sample_idx"] == 0]
    assert all(r["temperature"] == 0.0 and r["code"] == "print(1)" for r in s0)
    assert {r["temperature"] for r in rows if r["sample_idx"] > 0} == {0.8}


def test_seeds_are_stable(tmp_path):
    probs = load_problems(FIX)
    a, b = [], []
    generate.generate(tmp_path / "a", probs, [SLM], backend_factory=factory(a))
    generate.generate(tmp_path / "b", probs, [SLM], backend_factory=factory(b))
    assert a == b


def test_resume_skips_existing_keys(tmp_path):
    probs = load_problems(FIX)
    generate.generate(tmp_path, probs, [SLM], backend_factory=factory())
    p = tmp_path / "samples__fake-slm.jsonl"
    text = p.read_text(encoding="utf-8")
    p.write_text(text[: len(text) - 25], encoding="utf-8")  # simulate crash mid-write
    calls = []
    generate.generate(tmp_path, probs, [SLM], backend_factory=factory(calls))
    rows = generate.load_all(tmp_path, "samples")
    keys = [(r["cfg"], r["problem_id"], r["sample_idx"]) for r in rows]
    assert len(keys) == len(set(keys)) == 9
    assert len([c for c in calls]) == 1  # only the truncated sample regenerated


def test_rate_limited_is_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(generate.time, "sleep", lambda s: None)
    probs = load_problems(FIX)[:1]
    generate.generate(tmp_path, probs, [LLM],
                      backend_factory=factory(fail_once=backends.RateLimited(0)))
    assert len(generate.load_all(tmp_path, "samples")) == 1


def test_backend_error_recorded_not_fatal(tmp_path, monkeypatch):
    monkeypatch.setattr(generate.time, "sleep", lambda s: None)

    def bad(cfg):
        def script(m, s):
            raise backends.BackendError("boom")
        return backends.FakeBackend(script)

    generate.generate(tmp_path, load_problems(FIX)[:1], [LLM], backend_factory=bad)
    row = generate.load_all(tmp_path, "samples")[0]
    assert row["error"] and row["code"] == ""


def test_parallel_workers_write_every_sample_once(tmp_path, monkeypatch):
    monkeypatch.setenv("SLMCHECK_PARALLEL", "3")
    probs = load_problems(FIX)
    generate.generate(tmp_path, probs, [SLM], backend_factory=factory())
    rows = generate.load_all(tmp_path, "samples")
    keys = [(r["cfg"], r["problem_id"], r["sample_idx"]) for r in rows]
    assert len(keys) == len(set(keys)) == 9 and {r["workers"] for r in rows} == {3}
    assert len(generate.load_all(tmp_path, "selftests")) == 3


def test_error_rows_are_regenerated_on_rerun(tmp_path, monkeypatch):
    monkeypatch.setattr(generate.time, "sleep", lambda s: None)

    def bad(cfg):
        def script(m, s):
            raise backends.BackendError("ollama down")
        return backends.FakeBackend(script)

    probs = load_problems(FIX)[:1]
    generate.generate(tmp_path, probs, [LLM], backend_factory=bad)
    assert generate.load_all(tmp_path, "samples")[0]["error"]
    generate.generate(tmp_path, probs, [LLM], backend_factory=factory())
    rows = generate.load_all(tmp_path, "samples")
    assert len(rows) == 1 and not rows[0]["error"] and rows[0]["code"] == "print(1)"


def test_selftests_written_once_per_slm_problem(tmp_path):
    probs = load_problems(FIX)
    generate.generate(tmp_path, probs, [SLM, LLM], backend_factory=factory())
    generate.generate(tmp_path, probs, [SLM, LLM], backend_factory=factory())
    st = generate.load_all(tmp_path, "selftests")
    assert len(st) == 3 and {r["cfg"] for r in st} == {"fake-slm"}
    assert st[0]["tests"] == [{"input": "1 1\n", "output": "2\n"}]


def test_reextract_rewrites_code_from_raw_text_and_keeps_a_backup(tmp_path):
    from slmcheck import reextract
    raw = "```python\ndef f():\n    return 1\n```\n```python\nassert f() == 1\n```"
    row = {"cfg": "m", "problem_id": "p", "sample_idx": 0, "raw_text": raw, "code": "assert f() == 1"}
    ok = {"cfg": "m", "problem_id": "q", "sample_idx": 0, "raw_text": "print(1)", "code": "print(1)"}
    p = tmp_path / "samples__m.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in (row, ok)), encoding="utf-8")
    assert reextract.reextract(tmp_path) == {"samples__m.jsonl": 1}
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["code"] == "def f():\n    return 1" and rows[0]["code_reextracted"] and "code_reextracted" not in rows[1]
    assert (tmp_path / "_superseded" / "samples_before_reextract" / "samples__m.jsonl").exists()
    assert reextract.reextract(tmp_path) == {"samples__m.jsonl": 0}
