import json

from slmcheck import report


def _rows():
    rows = []
    for k, pid in enumerate(["a", "b", "c", "d"]):
        diff = ["easy", "medium", "hard", "easy"][k]
        for i in range(3):
            rows.append({"cfg": "slm1", "tier": "slm", "problem_id": pid, "sample_idx": i,
                         "difficulty": diff, "hidden_pass": (k + i) % 2 == 0,
                         "public": [(k + i) % 3 != 1], "self": [True, (k + i) % 2 == 0],
                         "sig": f"s{(k + i) % 2}", "empty": False})
        rows.append({"cfg": "llm1", "tier": "llm", "problem_id": pid, "sample_idx": 0,
                     "difficulty": diff, "hidden_pass": k != 2, "public": [True], "self": [],
                     "sig": "x", "empty": False})
    return rows


def test_report_writes_all_files_from_fixture_run(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    rows = _rows()
    (run / "exec.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    samples = [{"cfg": r["cfg"], "problem_id": r["problem_id"], "sample_idx": r["sample_idx"],
                "code": "x", "wall_s": 1.0, "completion_tokens": 10, "model_digest": "fake"}
               for r in rows]
    (run / "samples__all.jsonl").write_text("".join(json.dumps(s) + "\n" for s in samples))
    out = report.report(run, tmp_path / "bundle")
    for name in ["accuracy_by_strategy", "gap_recovered", "false_pass", "silent_bugs", "cascade", "mcnemar", "cost"]:
        assert (out / "tables" / f"{name}.csv").stat().st_size > 50
    assert (out / "figures" / "fig_cascade_llm1.png").exists()
    md = (out / "RESULTS.md").read_text()
    assert md.startswith("# FAKE — NOT RESULTS")
    meta = json.loads((out / "run_metadata.json").read_text())
    assert meta["fake"] and meta["n_problems"] == 4
