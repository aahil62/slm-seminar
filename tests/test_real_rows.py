"""Shape check against 4 genuine LiveCodeBench rows (head of test6.jsonl). Data only, no models."""
from slmcheck import dataset, prompts, verify

RAW = "tests/fixtures/lcb_real_rows.jsonl"


def test_real_rows_decode(tmp_path):
    out = tmp_path / "p.jsonl"
    n = dataset.build_problem_file([RAW], out)
    probs = dataset.load_problems(out)
    assert n == len(probs) >= 1
    for p in probs:
        assert p.public and p.private and p.contest_date >= "2025-01-01"
        assert p.testtype in ("stdin", "functional")
        assert p.testtype == "stdin" or p.func_name
        assert prompts.codegen_messages(p)[-1]["content"].count("```python") == 1


def test_real_rows_pass_data_gate(tmp_path):
    out = tmp_path / "p.jsonl"
    dataset.build_problem_file([RAW], out)
    g = verify.gate_data(tmp_path, dataset.load_problems(out), min_problems=1)
    assert g.status in ("PASS", "FLAG"), g.checks
