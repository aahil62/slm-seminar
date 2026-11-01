"""Show which MBPP+ hidden inputs a given saved candidate gets wrong (for the worked examples).

Runs the candidate and the EvalPlus script in a subprocess with the script's `assertion` replaced
by a recorder, so every mismatching input is listed instead of stopping at the first.
    python analysis/probe_plus.py qwen2.5-coder-7b mbpp/435 0
"""
from __future__ import annotations

import json
import subprocess
import sys

from common import load

RECORDER = '''
_fails = []
def assertion(out, exp, atol):
    try:
        ok = (out == exp) or (atol and abs(out - exp) <= max(atol, 1e-6))
    except Exception:
        ok = False
    if not ok:
        _fails.append((repr(globals().get('_cur'))[:60], repr(out)[:60], repr(exp)[:60]))
'''


def main(cfg, pid, idx):
    _, problems, samples, _ = load("mbpp")
    code = samples[(cfg, pid, int(idx))]["code"]
    prob = problems[pid]
    priv = prob["private"]
    priv = eval(priv) if isinstance(priv, str) else priv
    base = [t["input"] for t in priv if "def assertion" not in t["input"]]
    plus = next(t["input"] for t in priv if "def assertion" in t["input"])
    plus = plus.replace("def assertion(", "def _orig_assertion(")
    plus = plus.replace("for i, (inp, exp) in enumerate(zip(inputs, results)):",
                        "for i, (inp, exp) in enumerate(zip(inputs, results)):\n    _cur = inp")
    prog = (code + "\n" + RECORDER + "\nimport json as _j\n_base_fail=[]\n"
            + "".join(f"try:\n    {b.strip()}\nexcept Exception as e:\n    _base_fail.append({b.strip()!r})\n"
                      for b in base)
            + "\ntry:\n" + "\n".join("    " + ln for ln in plus.splitlines())
            + "\nexcept Exception as e:\n    _fails.append(('EXC', repr(e)[:120]))\n"
            + "print('BASE_FAIL', _j.dumps(_base_fail))\nprint('N_INPUTS', len(inputs))\n"
            + "print('PLUS_FAIL', len(_fails), _fails[:6])\n")
    r = subprocess.run([sys.executable, "-I", "-c", prog], capture_output=True, text=True, timeout=60)
    print(code)
    print(r.stdout[-3000:], r.stderr[-1500:])


if __name__ == "__main__":
    main(*sys.argv[1:4])
