import json

from slmcheck import verify
from slmcheck.__main__ import FAKE_CONFIGS, fake_factory, main
from slmcheck.dataset import load_problems

FIX = verify.FIXTURES / "problems.jsonl"


def test_verify_data_gate_passes_on_fixture_problems(tmp_path):
    g = verify.gate_data(tmp_path, load_problems(FIX), min_problems=3)
    assert g.status in ("PASS", "FLAG"), g.checks
    assert (tmp_path / "VERIFICATION_REPORT.md").exists()


def test_verify_data_gate_fails_on_too_few(tmp_path):
    assert verify.gate_data(tmp_path, load_problems(FIX), min_problems=150).status == "FAIL"


def test_verify_exec_gate_passes(tmp_path):
    assert verify.gate_exec(tmp_path).status == "PASS"


def test_verify_post_gate_flags_missing_samples(tmp_path):
    probs = load_problems(FIX)
    (tmp_path / "samples__fake-llm.jsonl").write_text(json.dumps(
        {"cfg": "fake-llm", "problem_id": probs[0].id, "sample_idx": 0, "code": "x", "seed": 0}) + "\n")
    g = verify.gate_post(tmp_path, probs, FAKE_CONFIGS, backend_factory=None)
    assert g.status == "FAIL"
    assert any(c["name"] == "fake-llm: sample count" and c["status"] == "FAIL" for c in g.checks)


def test_cli_all_on_fake_backend(tmp_path):
    run, out = tmp_path / "run", tmp_path / "bundle"
    assert main(["all", "--fake", "--run-dir", str(run), "--out", str(out)]) == 0
    md = (out / "RESULTS.md").read_text()
    assert md.startswith("# FAKE — NOT RESULTS")
    report = (run / "VERIFICATION_REPORT.md").read_text()
    assert "## post:" in report and "## data: PASS" in report and "## exec: PASS" in report
    assert (out / "VERIFICATION_REPORT.md").exists()
    # resumable: a second run regenerates nothing
    before = sorted((run).glob("samples__*.jsonl")); before = [p.read_text() for p in before]
    assert main(["all", "--fake", "--run-dir", str(run), "--out", str(out)]) == 0
    assert [p.read_text() for p in sorted(run.glob("samples__*.jsonl"))] == before


def test_cli_backend_gate_with_fake(tmp_path):
    from slmcheck import verify as v
    g = v.gate_backend(tmp_path, load_problems(FIX), FAKE_CONFIGS, backend_factory=fake_factory)
    assert g.status == "PASS"


def test_backend_gate_detects_think_mode_not_applied(tmp_path):
    from slmcheck.backends import FakeBackend
    from slmcheck.config import ModelConfig
    cfg = ModelConfig("t", "fake", "fake", k=1, think=False)
    leaky = lambda c: FakeBackend(lambda m, s: "<think>hmm</think>\n```python\nprint(1)\n```")
    g = verify.gate_backend(tmp_path, load_problems(FIX), [cfg], backend_factory=leaky)
    assert any(c["name"] == "t: thinking is OFF" and c["status"] == "FAIL" for c in g.checks)
