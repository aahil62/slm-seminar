"""Run candidate code against tests in a separate, killable process."""
from __future__ import annotations

import json
import os
import queue
import signal
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional, Sequence

from ._driver import TAG, outputs_equal  # noqa: F401 - re-exported
from .dataset import Test

DRIVER = str(Path(__file__).with_name("_driver.py"))
STARTUP_GRACE_S = 5.0  # interpreter start + payload parse before the first test result
Status = Literal["pass", "fail", "error", "timeout", "skipped", "ran"]


@dataclass(frozen=True)
class TestResult:
    __test__ = False  # not a pytest class
    passed: bool
    status: Status
    got: Optional[str] = None


def _kill_tree(proc: subprocess.Popen) -> None:
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        pass
    proc.kill()


def run_tests(code: str, tests: Sequence[Test], func_name: Optional[str], timeout_s: float,
              stop_on_fail: bool = False, expect_outputs: bool = True) -> list[TestResult]:
    """Return one TestResult per test. With expect_outputs=False, only collects outputs ("ran")."""
    if not tests:
        return []
    payload = json.dumps({
        "code": code, "testtype": tests[0].testtype, "func_name": func_name,
        "stop_on_fail": stop_on_fail,
        "tests": [{"input": t.input, "output": t.output if expect_outputs else None} for t in tests],
    })
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" \
        else {"start_new_session": True}
    results: dict[int, TestResult] = {}
    with tempfile.TemporaryDirectory(prefix="slmcheck_") as tmp:
        proc = subprocess.Popen([sys.executable, "-I", DRIVER], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=tmp,
                                **kwargs)
        lines: queue.Queue = queue.Queue()

        def pump():
            for raw in proc.stdout:
                lines.put(raw)
            lines.put(None)

        threading.Thread(target=pump, daemon=True).start()
        try:
            proc.stdin.write(payload.encode("utf-8"))
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        # Per-test deadline: each result line must arrive within timeout_s of the previous one
        # (plus a start-up grace for the first). A silent test means it is hung: kill the tree.
        deadline = time.monotonic() + timeout_s + STARTUP_GRACE_S
        while len(results) < len(tests):
            try:
                raw = lines.get(timeout=max(0.0, deadline - time.monotonic()))
            except queue.Empty:
                _kill_tree(proc)
                break
            if raw is None:
                break
            line = raw.decode("utf-8", "replace")
            if not line.startswith(TAG):
                continue
            try:
                d = json.loads(line[len(TAG):])
            except json.JSONDecodeError:
                continue
            results[d["i"]] = TestResult(d["status"] == "pass", d["status"], d.get("got"))
            deadline = time.monotonic() + timeout_s
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            proc.wait()
    return [results.get(i, TestResult(False, "timeout")) for i in range(len(tests))]
