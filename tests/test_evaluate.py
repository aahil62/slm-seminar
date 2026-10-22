import json

from slmcheck import evaluate
from slmcheck.dataset import load_problems

FIX = "slmcheck/fixtures/problems.jsonl"
SOLS = json.load(open("slmcheck/fixtures/solutions.json"))


def _write(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def test_evaluate_can_be_limited_to_finished_configs(tmp_path):
    probs = load_problems(FIX)[:1]
    rows = [{"cfg": c, "problem_id": probs[0].id, "sample_idx": 0, "code": "print(1)"} for c in ("a", "b")]
    _write(tmp_path / "samples__ab.jsonl", rows)
    assert evaluate.evaluate(tmp_path, probs, ["a"]) == 1
    assert evaluate.evaluate(tmp_path, probs) == 1  # the other config is picked up later


def test_evaluate_end_to_end_on_fixtures(tmp_path):
    probs = load_problems(FIX)
    samples, selftests = [], []
    for p in probs:
        for i, kind in enumerate(["good", "bad", "good"]):
            samples.append({"cfg": "m", "problem_id": p.id, "sample_idx": i,
                            "code": SOLS[p.id][kind] if p.id != "fx_primes" or kind == "good" else ""})
    selftests.append({"cfg": "m", "problem_id": "fx_add",
                      "tests": [{"input": "2 2\n", "output": "4\n"}, {"input": "1 1\n", "output": "3\n"}]})
    _write(tmp_path / "samples__m.jsonl", samples)
    _write(tmp_path / "selftests__m.jsonl", selftests)
    assert evaluate.evaluate(tmp_path, probs) == 9
    assert evaluate.evaluate(tmp_path, probs) == 0  # resumable
    rows = {(r["problem_id"], r["sample_idx"]): r for r in
            map(json.loads, open(tmp_path / "exec.jsonl"))}
    assert rows[("fx_add", 0)]["hidden_pass"] and not rows[("fx_add", 1)]["hidden_pass"]
    assert rows[("fx_add", 0)]["self"] == [True, False]
    assert rows[("fx_add", 0)]["sig"] == rows[("fx_add", 2)]["sig"] != rows[("fx_add", 1)]["sig"]
    assert rows[("fx_twosum", 0)]["hidden_pass"] and rows[("fx_twosum", 1)]["public"] == [True]
    assert not rows[("fx_twosum", 1)]["hidden_pass"]  # passes the example, fails hidden: a false pass
    assert rows[("fx_primes", 1)]["empty"] and rows[("fx_primes", 1)]["sig"] is None


def test_fail_kind_categories():
    from slmcheck.evaluate import _execute
    p = [q for q in load_problems(FIX) if q.id == "fx_add"][0]
    assert _execute(SOLS["fx_add"]["good"], p, [])["fail_kind"] is None
    assert _execute(SOLS["fx_add"]["bad"], p, [])["fail_kind"] == "wrong_answer"
    assert _execute("print(1/0)", p, [])["fail_kind"] == "runtime_error"
    assert _execute("", p, [])["fail_kind"] == "empty"
    tricky = "a,b=map(int,input().split())\nprint(a+b if a<10 else 0)\n"  # passes example, fails hidden
    r = _execute(tricky, p, [])
    assert r["public"] == [True] and r["fail_kind"] == "wrong_answer"
