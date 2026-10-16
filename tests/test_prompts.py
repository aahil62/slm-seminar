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
