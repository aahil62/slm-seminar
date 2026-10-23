# Manual spot-checks for runs\mbpp

## Extraction (raw_text vs code)

- deepseek-v3.1 mbpp/278#0: in_raw=True, parses, len(code)=161/len(raw)=175, has_think_tag=False
- deepseek-v3.1 mbpp/69#0: in_raw=True, parses, len(code)=225/len(raw)=643, has_think_tag=False
- deepseek-v3.1 mbpp/780#0: in_raw=True, parses, len(code)=268/len(raw)=282, has_think_tag=False
- deepseek-v3.1 mbpp/585#0: in_raw=True, parses, len(code)=131/len(raw)=145, has_think_tag=False
- deepseek-v3.1 mbpp/563#0: in_raw=True, parses, len(code)=72/len(raw)=86, has_think_tag=False
- deepseek-v3.1 mbpp/414#0: in_raw=True, parses, len(code)=174/len(raw)=188, has_think_tag=False

## Grading: hidden_pass=false rows re-run independently

- deepseek-v3.1 mbpp/594#0 exec says wrong_answer; manual: failure confirmed (test 3/4 -> fail 'inp), exp, 0)\n  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmp5qlpu99y\\c.py", line 41, in assertion\n    assert out == exp, f"out: {out}, exp: {exp}"\n           ^^^^^^^^^^\nAssertionError: out: 3, exp: -3\n')
- deepseek-v3.1 mbpp/92#0 exec says wrong_answer; manual: failure confirmed (test 3/4 -> fail 'exp, 0)\n  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmpy4u1r7ns\\c.py", line 43, in assertion\n    assert out == exp, f"out: {out}, exp: {exp}"\n           ^^^^^^^^^^\nAssertionError: out: False, exp: True\n')
- deepseek-v3.1 mbpp/260#0 exec says wrong_answer; manual: failure confirmed (test 0/4 -> fail 'Traceback (most recent call last):\n  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmp06l739sr\\c.py", line 21, in <module>\n    assert newman_prime(3) == 7\n           ^^^^^^^^^^^^^^^^^^^^\nAssertionError\n')
- deepseek-v3.1 mbpp/267#0 exec says runtime_error; manual: failure confirmed (test 3/4 -> fail 'mp\\tmps04i3r2o\\c.py", line 11, in square_Sum\n    return sum((2*i + 1)**2 for i in range(n))\n                                     ^^^^^^^^\nTypeError: \'float\' object cannot be interpreted as an integer\n')
- deepseek-v3.1 mbpp/792#0 exec says wrong_answer; manual: failure confirmed (test 3/4 -> fail '*inp), exp, 0)\n  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmpkqo_i1yl\\c.py", line 32, in assertion\n    assert out == exp, f"out: {out}, exp: {exp}"\n           ^^^^^^^^^^\nAssertionError: out: 3, exp: 1\n')
- deepseek-v3.1 mbpp/278#0 exec says wrong_answer; manual: failure confirmed (test 3/4 -> fail '*inp), exp, 0)\n  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmp3ka14og6\\c.py", line 37, in assertion\n    assert out == exp, f"out: {out}, exp: {exp}"\n           ^^^^^^^^^^\nAssertionError: out: 6, exp: 5\n')

## Grading: hidden_pass=true rows re-run independently

- deepseek-v3.1 mbpp/454#0 exec says pass; manual: pass confirmed (all 4 tests passed)
- deepseek-v3.1 mbpp/598#0 exec says pass; manual: pass confirmed (all 4 tests passed)
- deepseek-v3.1 mbpp/2#0 exec says pass; manual: pass confirmed (all 4 tests passed)
- deepseek-v3.1 mbpp/20#0 exec says pass; manual: pass confirmed (all 4 tests passed)

(pool sizes: 42 failing non-empty rows, 158 passing rows)
