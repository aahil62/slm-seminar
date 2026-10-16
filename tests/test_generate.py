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


def _lines(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def test_generate_writes_k_samples_per_problem(tmp_path):
    probs = load_problems(FIX)
    counts = generate.generate(tmp_path, probs, [SLM, LLM], backend_factory=factory())
    rows = _lines(tmp_path / "samples.jsonl")
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
    p = tmp_path / "samples.jsonl"
    text = p.read_text(encoding="utf-8")
    p.write_text(text[: len(text) - 25], encoding="utf-8")  # simulate crash mid-write
    calls = []
    generate.generate(tmp_path, probs, [SLM], backend_factory=factory(calls))
    rows = _lines(p)
    keys = [(r["cfg"], r["problem_id"], r["sample_idx"]) for r in rows]
    assert len(keys) == len(set(keys)) == 9
    assert len([c for c in calls]) == 1  # only the truncated sample regenerated


def test_rate_limited_is_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(generate.time, "sleep", lambda s: None)
    probs = load_problems(FIX)[:1]
    generate.generate(tmp_path, probs, [LLM],
                      backend_factory=factory(fail_once=backends.RateLimited(0)))
    assert len(_lines(tmp_path / "samples.jsonl")) == 1


def test_backend_error_recorded_not_fatal(tmp_path, monkeypatch):
    monkeypatch.setattr(generate.time, "sleep", lambda s: None)

    def bad(cfg):
        def script(m, s):
            raise backends.BackendError("boom")
        return backends.FakeBackend(script)

    generate.generate(tmp_path, load_problems(FIX)[:1], [LLM], backend_factory=bad)
    row = _lines(tmp_path / "samples.jsonl")[0]
    assert row["error"] and row["code"] == ""


def test_selftests_written_once_per_slm_problem(tmp_path):
    probs = load_problems(FIX)
    generate.generate(tmp_path, probs, [SLM, LLM], backend_factory=factory())
    generate.generate(tmp_path, probs, [SLM, LLM], backend_factory=factory())
    st = _lines(tmp_path / "selftests.jsonl")
    assert len(st) == 3 and {r["cfg"] for r in st} == {"fake-slm"}
    assert st[0]["tests"] == [{"input": "1 1\n", "output": "2\n"}]
