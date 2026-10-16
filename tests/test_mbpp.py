"""MBPP+ support, checked against 3 genuine MBPP+ rows (task 2, 3, 4). Data only, no models."""
import json

from slmcheck import dataset, prompts, verify
from slmcheck.evaluate import _execute, _probe_scripts

ROWS = verify.FIXTURES / "mbpp_rows.jsonl"


def _rows():
    return [json.loads(l) for l in ROWS.read_text().splitlines()]


def test_mbpp_row_to_problem():
    p = dataset.mbpp_row_to_problem(_rows()[1])
    assert p.id == "mbpp/3" and p.func_name == "is_not_prime" and p.benchmark == "mbppplus"
    assert p.testtype == "script" and len(p.public) == 1
    assert "assertion(is_not_prime(*inp)" in p.private[-1].input  # the plus test script is hidden


def test_build_mbpp_problem_file_sampling(tmp_path):
    out = tmp_path / "p.jsonl"
    assert dataset.build_mbpp_problem_file(ROWS, out, n=2, seed=1) == 2
    again = tmp_path / "q.jsonl"
    dataset.build_mbpp_problem_file(ROWS, again, n=2, seed=1)
    assert out.read_text() == again.read_text()  # fixed seed -> same subset


def test_mbpp_prompt_shows_one_example_and_hides_plus_tests():
    p = dataset.mbpp_row_to_problem(_rows()[1])
    text = prompts.codegen_messages(p)[-1]["content"]
    assert "is_not_prime(2)" in text and "is_not_prime(35)" not in text and "inputs = [" not in text


def test_false_pass_on_real_mbpp_problem():
    p = dataset.mbpp_row_to_problem(_rows()[1])
    wrong = "def is_not_prime(n):\n    return n % 2 == 0 and n != 2\n"
    r = _execute(wrong, p, [])
    assert r["public"] == [True] and not r["hidden_pass"] and r["fail_kind"] == "wrong_answer"


def test_selftests_and_probes_for_scripts():
    text = "```python\nassert is_not_prime(4) == True\nnot an assert\nassert is_not_prime(7) == False\n```"
    tests = prompts.parse_selftests(text, "script")
    assert [t.input for t in tests] == ["assert is_not_prime(4) == True", "assert is_not_prime(7) == False"]
    probes = _probe_scripts(tests)
    assert [t.input for t in probes] == ["print(repr(is_not_prime(4)))", "print(repr(is_not_prime(7)))"]


def test_agreement_signature_separates_different_behaviour():
    p = dataset.mbpp_row_to_problem(_rows()[1])
    st = prompts.parse_selftests("assert is_not_prime(9) == True\nassert is_not_prime(4) == True", "script")
    good, wrong = _rows()[1]["code"], "def is_not_prime(n):\n    return n % 2 == 0 and n != 2\n"
    a, b = _execute(good, p, st), _execute(wrong, p, st)
    assert a["self"] == [True, True] and b["self"] == [False, True]
    assert a["sig"] and b["sig"] and a["sig"] != b["sig"]


def test_data_gate_accepts_mbpp_dates(tmp_path):
    out = tmp_path / "p.jsonl"
    dataset.build_mbpp_problem_file(ROWS, out, n=0)
    g = verify.gate_data(tmp_path, dataset.load_problems(out), min_problems=1)
    assert g.status in ("PASS", "FLAG"), g.checks


def test_data_gate_grades_mbpp_reference_solutions(tmp_path):
    out = tmp_path / "p.jsonl"
    dataset.build_mbpp_problem_file(ROWS, out, n=0)
    g = verify.gate_data(tmp_path, dataset.load_problems(out), min_problems=1, mbpp_raw=ROWS)
    chk = [c for c in g.checks if c["name"].startswith("MBPP+ reference")][0]
    assert chk["status"] == "PASS"


def test_excluded_task_never_sampled(tmp_path, monkeypatch):
    from slmcheck import config
    monkeypatch.setattr(config, "MBPP_EXCLUDE", {3: "test"})
    out = tmp_path / "p.jsonl"
    dataset.build_mbpp_problem_file(ROWS, out, n=0)
    assert "mbpp/3" not in {p.id for p in dataset.load_problems(out)}
