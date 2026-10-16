import time

from slmcheck.dataset import Test
from slmcheck.executor import outputs_equal, run_tests

ADD_OK = "a,b=map(int,input().split())\nprint(a+b)\n"
S = lambda i, o: Test(i, o, "stdin")


def test_stdin_correct_passes():
    r = run_tests(ADD_OK, [S("1 2\n", "3\n"), S("5 5\n", "10")], None, 5)
    assert [x.status for x in r] == ["pass", "pass"]


def test_stdin_wrong_fails():
    r = run_tests(ADD_OK, [S("1 2\n", "4\n")], None, 5)
    assert r[0].status == "fail" and r[0].got.strip() == "3"


def test_stdin_buffer_reading():
    code = "import sys\na,b=map(int,sys.stdin.buffer.read().split())\nsys.stdout.write(str(a*b)+'\\n')\n"
    assert run_tests(code, [S("3 4\n", "12\n")], None, 5)[0].passed


def test_functional_correct_passes():
    code = ("class Solution:\n    def twoSum(self, nums: List[int], target: int) -> List[int]:\n"
            "        d={}\n        for i,x in enumerate(nums):\n"
            "            if target-x in d: return [d[target-x], i]\n            d[x]=i\n")
    r = run_tests(code, [Test("[2,7,11,15]\n9", "[0, 1]", "functional")], "twoSum", 5)
    assert r[0].status == "pass"


def test_functional_missing_method_is_error():
    code = "class Solution:\n    def other(self, x):\n        return x\n"
    r = run_tests(code, [Test("1", "1", "functional")], "twoSum", 5)
    assert r[0].status == "error"


def test_infinite_loop_times_out_quickly():
    t0 = time.time()
    r = run_tests("while True:\n    pass\n", [S("", "1"), S("", "1")], None, 1.0)
    assert [x.status for x in r] == ["timeout", "timeout"]
    assert time.time() - t0 < 10


def test_exit_call_handled():
    r = run_tests("print(7)\nexit()\nprint(8)\n", [S("", "7")], None, 5)
    assert r[0].status == "pass"


def test_syntax_error_is_error():
    assert run_tests("def (:\n", [S("", "1")], None, 5)[0].status == "error"


def test_runtime_error_is_error():
    assert run_tests("print(1/0)", [S("", "1")], None, 5)[0].status == "error"


def test_float_tolerance():
    assert outputs_equal("0.3333333333\n", "0.333333333", "stdin")
    assert not outputs_equal("0.33\n", "0.34", "stdin")
    assert outputs_equal("1 2\n3\n", "1 2 \n3", "stdin")


def test_huge_output_capped():
    r = run_tests("while True:\n    print('x'*1000)\n", [S("", "x")], None, 5)
    assert r[0].status in ("error", "timeout")


def test_stop_on_fail_skips_rest():
    code = "x=int(input())\nprint(x)\n"
    r = run_tests(code, [S("1", "2"), S("3", "3")], None, 5, stop_on_fail=True)
    assert [x.status for x in r] == ["fail", "skipped"]


def test_empty_tests():
    assert run_tests(ADD_OK, [], None, 5) == []


def test_fixture_reference_solutions():
    import json
    from slmcheck.dataset import load_problems
    sols = json.load(open("slmcheck/fixtures/solutions.json"))
    for p in load_problems("slmcheck/fixtures/problems.jsonl"):
        tests = p.public + p.private
        good = run_tests(sols[p.id]["good"], tests, p.func_name, 6)
        bad = run_tests(sols[p.id]["bad"], tests, p.func_name, 2, stop_on_fail=True)
        assert all(r.passed for r in good), (p.id, good)
        assert not all(r.passed for r in bad), p.id


def test_timeout_is_per_test_not_total():
    code = "x=input()\nif x=='hang':\n    while True: pass\nprint(x)\n"
    tests = [S("hang", "1")] + [S(str(i), str(i)) for i in range(20)]
    t0 = time.time()
    r = run_tests(code, tests, None, 1.0)
    assert r[0].status == "timeout" and time.time() - t0 < 10


def test_script_mode_assert_pass_fail_error():
    code = "def add(a, b):\n    return a + b\n"
    tests = [Test("assert add(1, 2) == 3", "", "script"), Test("assert add(1, 2) == 4", "", "script"),
             Test("assert undefined_fn(1)", "", "script")]
    r = run_tests(code, tests, "add", 5)
    assert [x.status for x in r] == ["pass", "fail", "error"]


def test_script_mode_collects_printed_output():
    code = "def sq(x):\n    return x * x\n"
    r = run_tests(code, [Test("print(repr(sq(3)))", "", "script")], "sq", 5, expect_outputs=False)
    assert r[0].status == "ran" and r[0].got.strip() == "9"
