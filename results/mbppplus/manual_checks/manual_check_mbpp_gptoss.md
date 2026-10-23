# Manual spot-checks for runs\mbpp

## Extraction (raw_text vs code)


## Grading: hidden_pass=false rows re-run independently

- gpt-oss-120b mbpp/735#0 exec says wrong_answer; manual: failure confirmed (test 5/6 -> fail 'p), exp, 0)\n  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmp_ni_22po\\c.py", line 57, in assertion\n    assert out == exp, f"out: {out}, exp: {exp}"\n           ^^^^^^^^^^\nAssertionError: out: True, exp: 3\n')
- gpt-oss-120b mbpp/310#0 exec says runtime_error; manual: failure confirmed (test 3/4 -> fail " * abs(y))\n                             ~~^~~\nnumpy._core._exceptions._UFuncNoLoopError: ufunc 'subtract' did not contain a loop with signature matching types (dtype('<U1'), dtype('float64')) -> None\n")
- gpt-oss-120b mbpp/759#0 exec says wrong_answer; manual: failure confirmed (test 5/6 -> fail 'exp, 0)\n  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmpntlwotqz\\c.py", line 47, in assertion\n    assert out == exp, f"out: {out}, exp: {exp}"\n           ^^^^^^^^^^\nAssertionError: out: True, exp: False\n')
- gpt-oss-120b mbpp/406#0 exec says wrong_answer; manual: failure confirmed (test 3/4 -> fail 'exp, 0)\n  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmpsjdg60pa\\c.py", line 58, in assertion\n    assert out == exp, f"out: {out}, exp: {exp}"\n           ^^^^^^^^^^\nAssertionError: out: True, exp: False\n')
- gpt-oss-120b mbpp/459#0 exec says wrong_answer; manual: failure confirmed (test 3/4 -> fail 'rs\\Admin\\AppData\\Local\\Temp\\tmpqldrsi6r\\c.py", line 36, in assertion\n    assert out == exp, f"out: {out}, exp: {exp}"\n           ^^^^^^^^^^\nAssertionError: out: hi%^%!s&a(m)est%i*ng, exp: hisamesting\n')

## Grading: hidden_pass=true rows re-run independently

- gpt-oss-120b mbpp/395#0 exec says pass; manual: pass confirmed (all 4 tests passed)
- gpt-oss-120b mbpp/421#0 exec says pass; manual: pass confirmed (all 4 tests passed)
- gpt-oss-120b mbpp/19#0 exec says pass; manual: pass confirmed (all 4 tests passed)

(pool sizes: 40 failing non-empty rows, 160 passing rows)
