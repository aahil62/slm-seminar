"""Child-process driver: runs one candidate program against a list of tests.

Invoked as `python -I _driver.py` with a JSON payload on stdin:
  {"code": str, "testtype": "stdin"|"functional"|"script", "func_name": str|None,
   "tests": [{"input": str, "output": str|None}], "stop_on_fail": bool}
Writes one protocol line per test to the original stdout: TAG + json.
Kept free of package imports so it runs isolated (-I) from a temp directory.
"""
import io
import json
import os
import sys

TAG = "@@SLMCHECK@@"
OUTPUT_CAP = 1 << 20

HEADER = ("from typing import *\nfrom collections import *\nfrom itertools import *\n"
          "from functools import *\nfrom heapq import *\nfrom bisect import *\nfrom math import *\n"
          "from builtins import *\n"  # math.pow would otherwise shadow the builtin pow(base, exp, mod)
          "import math, heapq, bisect, itertools, functools, collections, string, re, sys, random\n")


def _tokens(s):
    return s.split()


def outputs_equal(expected, got, testtype):
    if got is None:
        return False
    if testtype == "script":  # an assert script passes when it ran without raising
        return True
    if testtype == "functional":
        try:
            return json.loads(expected) == json.loads(got)
        except (ValueError, TypeError):
            return expected.strip() == got.strip()
    e, g = _tokens(expected), _tokens(got)
    if len(e) != len(g):
        return False
    for a, b in zip(e, g):
        if a == b:
            continue
        try:
            if abs(float(a) - float(b)) > 1e-6:
                return False
        except ValueError:
            return False
    return True


class _Capped(io.RawIOBase):
    def __init__(self):
        self.buf = bytearray()

    def writable(self):
        return True

    def write(self, b):
        if len(self.buf) + len(b) > OUTPUT_CAP:
            raise OSError("output limit exceeded")
        self.buf += b
        return len(b)


def _run_stdin(code_obj, text):
    sys.stdin = io.TextIOWrapper(io.BytesIO(text.encode()), encoding="utf-8")
    raw = _Capped()
    out = io.TextIOWrapper(io.BufferedWriter(raw), encoding="utf-8", write_through=True)
    sys.stdout = out
    try:
        exec(code_obj, {"__name__": "__main__", "__builtins__": __builtins__})
    except SystemExit:
        pass
    finally:
        try:
            out.flush()
        except Exception:
            pass
        sys.stdout = sys.__stdout__
    return raw.buf.decode("utf-8", "replace")


def _run_functional(code_obj, func_name, text):
    ns = {"__name__": "__main__", "__builtins__": __builtins__}
    sys.stdout = io.StringIO()  # discard debug prints
    try:
        exec(code_obj, ns)
        sol = ns["Solution"]()
        args = [json.loads(line) for line in text.split("\n") if line.strip()]
        return json.dumps(getattr(sol, func_name)(*args))
    finally:
        sys.stdout = sys.__stdout__


def _run_script(code_obj, script):
    """MBPP+-style: define the candidate, then run an assert/print script in the same namespace."""
    ns = {"__name__": "__main__", "__builtins__": __builtins__}
    buf = io.StringIO()
    sys.stdout = io.StringIO()
    try:
        exec(code_obj, ns)
        sys.stdout = buf
        exec(compile(script, "<test>", "exec"), ns)
    finally:
        sys.stdout = sys.__stdout__
    return buf.getvalue()


def main():
    payload = json.loads(sys.stdin.read())
    proto = os.fdopen(os.dup(1), "w", encoding="utf-8")
    sys.setrecursionlimit(10 ** 6)

    def emit(i, status, got=None):
        proto.write(TAG + json.dumps({"i": i, "status": status, "got": got}) + "\n")
        proto.flush()

    tests = payload["tests"]
    try:
        code_obj = compile(HEADER + payload["code"], "<candidate>", "exec")
    except Exception:
        for i in range(len(tests)):
            emit(i, "error")
        return
    stop = False
    for i, t in enumerate(tests):
        if stop:
            emit(i, "skipped")
            continue
        try:
            if payload["testtype"] == "functional":
                if not payload.get("func_name"):
                    raise ValueError("no func_name")
                got = _run_functional(code_obj, payload["func_name"], t["input"])
            elif payload["testtype"] == "script":
                got = _run_script(code_obj, t["input"])
            else:
                got = _run_stdin(code_obj, t["input"])
        except AssertionError:
            sys.stdout = sys.__stdout__
            emit(i, "fail" if payload["testtype"] == "script" else "error")
            stop = payload.get("stop_on_fail", False)
            continue
        except BaseException:  # noqa: BLE001 - any candidate failure is an error result
            sys.stdout = sys.__stdout__
            emit(i, "error")
            stop = payload.get("stop_on_fail", False)
            continue
        if t.get("output") is None:
            status = "ran"
        else:
            status = "pass" if outputs_equal(t["output"], got, payload["testtype"]) else "fail"
        emit(i, status, got[:OUTPUT_CAP])
        if status == "fail" and payload.get("stop_on_fail"):
            stop = True


if __name__ == "__main__":
    main()
