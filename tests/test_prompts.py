from slmcheck import prompts
from slmcheck.dataset import load_problems

FIX = "slmcheck/fixtures/problems.jsonl"


def test_extract_last_python_fence():
    text = "x\n```python\nprint(1)\n```\nbetter:\n```python\nprint(2)\n```\n"
    assert prompts.extract_code(text) == "print(2)"


def test_extract_strips_think_block():
    text = "<think>```python\nprint('draft')\n```</think>\n```python\nprint('final')\n```"
    assert prompts.extract_code(text) == "print('final')"


def test_extract_no_fence_returns_text():
    assert prompts.extract_code("  print(3)  ") == "print(3)"


def test_extract_unlabelled_fence():
    assert prompts.extract_code("```\nprint(4)\n```") == "print(4)"


def test_extract_prefers_solution_over_echoed_assert_block():
    """Evidence: deepseek-coder mbpp/418#4 and mbpp/759#3 wrote the function, then a second block that
    only repeats the example assert; taking the last block gave a NameError."""
    text = ("```python\ndef Find_Max(l):\n    return max(l, key=len)\n```\nTest it:\n"
            "```python\nassert Find_Max([[1], [1, 2]]) == [1, 2]\n```\n")
    assert prompts.extract_code(text) == "def Find_Max(l):\n    return max(l, key=len)"


def test_extract_stdin_solution_without_def_wins_over_usage_note():
    text = "```python\nn = int(input())\nprint(n * 2)\n```\nExample:\n```python\nprint(2 * 21)\n```"
    assert prompts.extract_code(text) == "n = int(input())\nprint(n * 2)"


def test_extract_closing_fence_without_opening():
    """Evidence: deepseek-coder mbpp/6#2 started with bare code and ended it with a lone fence."""
    text = "def f(a, b):\n    return a ^ b\n```\nThis function xors."
    assert prompts.extract_code(text) == "def f(a, b):\n    return a ^ b"


def test_extract_unterminated_opening_fence():
    """Output cut off at the token limit: the program starts after the fence, the fence is not code."""
    assert prompts.extract_code("```python\nx = 1\ny = 2\n") == "x = 1\ny = 2"
    assert prompts.extract_code("Sure:\n```python\nx = 1") == "x = 1"


def test_parse_selftests_drops_malformed():
    text = 'Here:\n```json\n[{"input": "1 2\\n", "output": "3\\n"}, {"input": 5}, "junk"]\n```'
    tests = prompts.parse_selftests(text, "stdin")
    assert [(t.input, t.output, t.testtype) for t in tests] == [("1 2\n", "3\n", "stdin")]
    assert prompts.parse_selftests("no json here", "stdin") == []


def test_parse_selftests_functional_nonstring_values():
    text = '[{"input": "[1,2]\\n3", "output": [0, 1]}]'
    t = prompts.parse_selftests(text, "functional")[0]
    assert t.output == "[0, 1]"


def test_codegen_prompt_contains_examples_not_private():
    for p in load_problems(FIX):
        joined = "\n".join(m["content"] for m in prompts.codegen_messages(p))
        assert p.content in joined
        for t in p.private:
            assert t.input.strip() not in joined
        sjoined = "\n".join(m["content"] for m in prompts.selftest_messages(p))
        for t in p.private:
            assert t.input.strip() not in sjoined


def test_functional_prompt_includes_starter_code():
    p = [q for q in load_problems(FIX) if q.func_name][0]
    assert p.starter_code.strip() in prompts.codegen_messages(p)[-1]["content"]


def test_selftest_parsing_keeps_last_block_as_written():
    text = ("```python\nassert f(1) == 1\nassert f(2) == 2\n```\nImplementation:\n"
            "```python\ndef f(x):\n    return x\nassert f(3) == 3\n```")
    assert [t.input for t in prompts.parse_selftests(text, "script")] == ["assert f(3) == 3"]
    assert prompts.extract_code(text).startswith("def f(x)")
