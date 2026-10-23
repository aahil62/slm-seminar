"""Prompts (LiveCodeBench-style) and parsing of model replies."""
from __future__ import annotations

import json
import re

from .dataset import Problem, Test

SYSTEM = ("You are an expert Python programmer. You will be given a programming problem and must "
          "write a correct and efficient Python 3 program that solves it.")

_STDIN_FORMAT = ("Read the inputs from stdin, solve the problem and write the answer to stdout "
                 "(do not directly test on the sample inputs). Enclose your code within delimiters "
                 "as follows.\n```python\n# YOUR CODE HERE\n```")
_FUNC_FORMAT = ("You will use the following starter code to write the solution to the problem and "
                "enclose your code within delimiters.\n```python\n{starter}\n```")


def codegen_messages(p: Problem) -> list[dict]:
    if p.testtype == "script":
        user = (f"### Question:\n{p.content}\nYour code should pass this test:\n"
                f"```python\n{p.public[0].input.strip()}\n```\n\n"
                f"### Format: Write the complete Python function `{p.func_name}` (with any imports and "
                "helpers it needs) and enclose your code within delimiters as follows.\n"
                "```python\n# YOUR CODE HERE\n```\n\n"
                "### Answer: (use the provided format with backticks)\n")
        return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
    fmt = _FUNC_FORMAT.format(starter=p.starter_code.rstrip()) if p.testtype == "functional" else _STDIN_FORMAT
    user = (f"### Question:\n{p.content}\n\n### Format: {fmt}\n\n"
            "### Answer: (use the provided format with backticks)\n")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def selftest_messages(p: Problem, n: int = 5) -> list[dict]:
    ex = p.public[0]
    if p.testtype == "script":
        user = (f"### Question:\n{p.content}\nExample test:\n```python\n{ex.input.strip()}\n```\n"
                f"Write {n} NEW assert statements testing `{p.func_name}` (different from the example), "
                "including edge cases, one per line. Compute each expected value carefully. Reply with "
                "only the assert lines inside one ```python block.")
        return [{"role": "system", "content": "You are a careful software tester."},
                {"role": "user", "content": user}]
    if p.testtype == "functional":
        how = ("Each \"input\" is the function arguments, one JSON value per line, exactly like the "
               "example; each \"output\" is the JSON return value.")
    else:
        how = "Each \"input\" is the full stdin text and each \"output\" is the exact expected stdout."
    user = (f"### Question:\n{p.content}\n\n"
            f"Write {n} NEW test cases for this problem (different from the examples), including edge "
            f"cases. {how}\nExample in the required format:\n"
            f"```json\n{json.dumps([{'input': ex.input, 'output': ex.output}], indent=1)}\n```\n"
            f"Compute each expected output carefully. Reply with only one JSON array of {n} objects "
            "with keys \"input\" and \"output\", inside a ```json block.")
    return [{"role": "system", "content": "You are a careful software tester."},
            {"role": "user", "content": user}]


_THINK = re.compile(r"<think>.*?</think>", re.S)
_FENCE = re.compile(r"```([A-Za-z0-9_+-]*)[ \t]*\n(.*?)```", re.S)


_DEFINES = re.compile(r"^[ \t]*(def|class)[ \t]", re.M)


def _is_program(block: str) -> bool:
    """A block that is the solution itself: it defines something or reads stdin. Echoed example
    asserts / usage snippets are not."""
    return bool(_DEFINES.search(block)) or "input(" in block or "stdin" in block


def _unpaired_fence(text: str) -> str | None:
    """Exactly one fence line and no complete block: an unterminated opening fence (output cut off
    or the closing fence never came) or a closing fence whose opening was never written."""
    lines = text.split("\n")
    fences = [i for i, ln in enumerate(lines) if ln.strip().startswith("```")]
    if len(fences) != 1:
        return None
    i = fences[0]
    tagged = len(lines[i].strip()) > 3
    opening = tagged or not "".join(lines[:i]).strip()
    return "\n".join(lines[i + 1:] if opening else lines[:i])


def extract_code(text: str, prefer_program: bool = True) -> str:
    """The model's final program. prefer_program=False takes the last fenced block as written
    (used for self-test replies, where the asserts themselves are the payload)."""
    text = _THINK.sub("", text or "")
    blocks = _FENCE.findall(text)
    py = [b for lang, b in blocks if lang.lower() in ("python", "python3", "py")]
    pool = py or [b for lang, b in blocks if lang == ""]
    if pool:
        return ([b for b in pool if prefer_program and _is_program(b)] or pool)[-1].strip()
    alone = _unpaired_fence(text)
    return (alone if alone is not None else text).strip()


def _as_text(v) -> str:
    return v if isinstance(v, str) else json.dumps(v)


def _parse_assert_lines(text: str) -> list[Test]:
    import ast
    out = []
    for line in extract_code(text, prefer_program=False).splitlines():
        line = line.strip()
        if not line.startswith("assert "):
            continue
        try:
            ast.parse(line)
        except SyntaxError:
            continue
        out.append(Test(line, "", "script"))
    return out


def parse_selftests(text: str, testtype: str) -> list[Test]:
    if testtype == "script":
        return _parse_assert_lines(text)
    text = _THINK.sub("", text or "")
    candidates = [b for _, b in _FENCE.findall(text)] + [text]
    for c in candidates:
        start, end = c.find("["), c.rfind("]")
        if start < 0 or end <= start:
            continue
        try:
            items = json.loads(c[start:end + 1])
        except json.JSONDecodeError:
            continue
        if not isinstance(items, list):
            continue
        out = []
        for it in items:
            if isinstance(it, dict) and "input" in it and "output" in it \
                    and isinstance(it["input"], str):
                out.append(Test(it["input"], _as_text(it["output"]), testtype))
        return out
    return []
