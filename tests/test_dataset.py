import base64
import json
import os
import pickle
import zlib

import pytest

from slmcheck import dataset


def _row(date="2025-02-01", private=None, func_name=None):
    pub = [{"input": "1 2\n", "output": "3\n", "testtype": "stdin"}]
    priv = private if private is not None else json.dumps(
        [{"input": "5 6\n", "output": "11\n", "testtype": "stdin"}])
    return {
        "question_title": "Add", "question_content": "Add two ints.", "platform": "atcoder",
        "question_id": "abc_x", "contest_id": "abc", "contest_date": date + "T00:00:00",
        "starter_code": "", "difficulty": "easy", "public_test_cases": json.dumps(pub),
        "private_test_cases": priv,
        "metadata": json.dumps({"func_name": func_name} if func_name else {}),
    }


def test_decode_plain_json():
    tests = dataset.decode_tests(json.dumps([{"input": "a", "output": "b", "testtype": "stdin"}]))
    assert tests == [dataset.Test("a", "b", "stdin")]


def test_decode_compressed_pickle():
    payload = json.dumps([{"input": "x", "output": "y", "testtype": "functional"}])
    raw = base64.b64encode(zlib.compress(pickle.dumps(payload))).decode()
    assert dataset.decode_tests(raw) == [dataset.Test("x", "y", "functional")]


def test_restricted_unpickler_rejects_globals():
    raw = base64.b64encode(zlib.compress(pickle.dumps(os.system))).decode()
    with pytest.raises(pickle.UnpicklingError):
        dataset.decode_tests(raw)


def test_build_problem_file_filters_by_date(tmp_path):
    raw = tmp_path / "raw.jsonl"
    rows = [_row("2024-12-31"), _row("2025-01-01"), _row("2025-03-05")]
    rows[1]["question_id"], rows[2]["question_id"] = "b", "c"
    raw.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    out = tmp_path / "problems.jsonl"
    assert dataset.build_problem_file([raw], out, since="2025-01-01") == 2
    probs = dataset.load_problems(out)
    assert [p.id for p in probs] == ["b", "c"]
    assert probs[0].private == [dataset.Test("5 6\n", "11\n", "stdin")]


def test_func_name_from_metadata(tmp_path):
    raw = tmp_path / "raw.jsonl"
    raw.write_text(json.dumps(_row(func_name="twoSum")) + "\n", encoding="utf-8")
    out = tmp_path / "p.jsonl"
    dataset.build_problem_file([raw], out)
    assert dataset.load_problems(out)[0].func_name == "twoSum"
