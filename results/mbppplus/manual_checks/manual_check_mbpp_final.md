# Manual spot-checks for runs\mbpp

## Extraction (raw_text vs code)

- deepseek-coder-6.7b mbpp/578#4: in_raw=True, parses, len(code)=122/len(raw)=793, has_think_tag=False
- deepseek-coder-6.7b mbpp/91#4: in_raw=True, parses, len(code)=187/len(raw)=202, has_think_tag=False
- deepseek-coder-6.7b mbpp/16#0: in_raw=True, parses, len(code)=145/len(raw)=160, has_think_tag=False
- deepseek-coder-6.7b mbpp/619#4: in_raw=True, parses, len(code)=189/len(raw)=739, has_think_tag=False
- deepseek-coder-6.7b mbpp/235#1: in_raw=True, parses, len(code)=261/len(raw)=276, has_think_tag=False
- qwen2.5-coder-1.5b mbpp/170#0: in_raw=True, parses, len(code)=302/len(raw)=316, has_think_tag=False
- qwen2.5-coder-1.5b mbpp/138#4: in_raw=True, parses, len(code)=285/len(raw)=299, has_think_tag=False
- qwen2.5-coder-1.5b mbpp/98#2: in_raw=True, parses, len(code)=128/len(raw)=142, has_think_tag=False
- qwen2.5-coder-1.5b mbpp/618#4: in_raw=True, parses, len(code)=60/len(raw)=214, has_think_tag=False
- qwen2.5-coder-1.5b mbpp/88#3: in_raw=True, parses, len(code)=496/len(raw)=878, has_think_tag=False
- qwen2.5-coder-7b mbpp/596#2: in_raw=True, parses, len(code)=153/len(raw)=167, has_think_tag=False
- qwen2.5-coder-7b mbpp/619#3: in_raw=True, parses, len(code)=424/len(raw)=438, has_think_tag=False
- qwen2.5-coder-7b mbpp/765#3: in_raw=True, parses, len(code)=788/len(raw)=802, has_think_tag=False
- qwen2.5-coder-7b mbpp/455#3: in_raw=True, parses, len(code)=203/len(raw)=217, has_think_tag=False
- qwen2.5-coder-7b mbpp/77#4: in_raw=True, parses, len(code)=402/len(raw)=416, has_think_tag=False
- qwen3-4b-nothink mbpp/478#4: in_raw=True, parses, len(code)=102/len(raw)=116, has_think_tag=False
- qwen3-4b-nothink mbpp/392#2: in_raw=True, parses, len(code)=298/len(raw)=312, has_think_tag=False
- qwen3-4b-nothink mbpp/18#2: in_raw=True, parses, len(code)=351/len(raw)=365, has_think_tag=False
- qwen3-4b-nothink mbpp/18#0: in_raw=True, parses, len(code)=330/len(raw)=344, has_think_tag=False
- qwen3-4b-nothink mbpp/86#0: in_raw=True, parses, len(code)=202/len(raw)=216, has_think_tag=False
- qwen3-4b-think mbpp/233#0: in_raw=True, parses, len(code)=77/len(raw)=91, has_think_tag=False
- qwen3-4b-think mbpp/247#0: in_raw=True, parses, len(code)=718/len(raw)=732, has_think_tag=False
- qwen3-4b-think mbpp/573#0: in_raw=True, parses, len(code)=68/len(raw)=82, has_think_tag=False
- qwen3-4b-think mbpp/620#0: in_raw=True, parses, len(code)=230/len(raw)=244, has_think_tag=False
- qwen3-4b-think mbpp/19#0: in_raw=True, parses, len(code)=61/len(raw)=75, has_think_tag=False

## Grading: hidden_pass=false rows re-run independently

- qwen3-4b-nothink mbpp/265#2 exec says wrong_answer; manual: failure confirmed (test 0/4 -> fail ", 'l']]\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nAssertionError\n")
- qwen2.5-coder-1.5b mbpp/113#4 exec says wrong_answer; manual: failure confirmed (test 3/4 -> fail 'exp, 0)\n  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmplb0u2522\\c.py", line 43, in assertion\n    assert out == exp, f"out: {out}, exp: {exp}"\n           ^^^^^^^^^^\nAssertionError: out: False, exp: None\n')
- qwen3-4b-nothink mbpp/751#0 exec says runtime_error; manual: failure confirmed (test 0/4 -> fail 'kiqw7t\\c.py", line 22, in check_min_heap\n    if arr[i] > arr[left_child] or arr[i] > arr[right_child]:\n                                            ~~~^^^^^^^^^^^^^\nIndexError: list index out of range\n')
- qwen3-4b-nothink mbpp/130#2 exec says wrong_answer; manual: failure confirmed (test 3/4 -> fail '*inp), exp, 0)\n  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmp94ebkeb2\\c.py", line 44, in assertion\n    assert out == exp, f"out: {out}, exp: {exp}"\n           ^^^^^^^^^^\nAssertionError: out: 8, exp: 6\n')
- qwen2.5-coder-7b mbpp/310#0 exec says wrong_answer; manual: failure confirmed (test 0/4 -> fail 'ule>\n    assert string_to_tuple("python 3.0") == (\'p\', \'y\', \'t\', \'h\', \'o\', \'n\', \'3\', \'.\', \'0\')\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nAssertionError\n')
- qwen2.5-coder-1.5b mbpp/245#2 exec says wrong_answer; manual: failure confirmed (test 0/4 -> fail 'AppData\\Local\\Temp\\tmpxemxp00g\\c.py", line 28, in <module>\n    assert max_sum([1, 15, 51, 45, 33, 100, 12, 18, 9]) == 194\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nAssertionError\n')
- qwen2.5-coder-7b mbpp/459#0 exec says wrong_answer; manual: failure confirmed (test 3/4 -> fail 'rs\\Admin\\AppData\\Local\\Temp\\tmp0563u81q\\c.py", line 39, in assertion\n    assert out == exp, f"out: {out}, exp: {exp}"\n           ^^^^^^^^^^\nAssertionError: out: hi%^%!s&a(m)est%i*ng, exp: hisamesting\n')
- qwen3-4b-nothink mbpp/421#1 exec says runtime_error; manual: failure confirmed (test 0/4 -> fail 'rs\\Admin\\AppData\\Local\\Temp\\tmpxu00ss9b\\c.py", line 12, in concatenate_tuple\n    return delimiter.join(tup)\n           ^^^^^^^^^^^^^^^^^^^\nTypeError: sequence item 2: expected str instance, int found\n')

## Grading: hidden_pass=true rows re-run independently

- qwen2.5-coder-1.5b mbpp/644#2 exec says pass; manual: pass confirmed (all 4 tests passed)
- deepseek-coder-6.7b mbpp/19#2 exec says pass; manual: pass confirmed (all 4 tests passed)
- deepseek-coder-6.7b mbpp/796#2 exec says pass; manual: pass confirmed (all 4 tests passed)
- qwen2.5-coder-7b mbpp/591#3 exec says pass; manual: pass confirmed (all 4 tests passed)
- qwen2.5-coder-7b mbpp/125#2 exec says pass; manual: pass confirmed (all 4 tests passed)

(pool sizes: 1407 failing non-empty rows, 2775 passing rows)
