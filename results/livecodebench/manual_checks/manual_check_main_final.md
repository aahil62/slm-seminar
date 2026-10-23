# Manual spot-checks for runs\main

## Extraction (raw_text vs code)

- deepseek-coder-6.7b 3709#0: in_raw=True, parses, len(code)=238/len(raw)=732, has_think_tag=False
- deepseek-coder-6.7b abc392_b#0: in_raw=True, parses, len(code)=191/len(raw)=442, has_think_tag=False
- deepseek-coder-6.7b abc390_g#1: in_raw=True, parses, len(code)=399/len(raw)=414, has_think_tag=False
- deepseek-coder-6.7b abc389_d#0: in_raw=True, parses, len(code)=224/len(raw)=673, has_think_tag=False
- deepseek-coder-6.7b 3709#4: in_raw=True, parses, len(code)=440/len(raw)=667, has_think_tag=False
- qwen2.5-coder-1.5b 3791#3: in_raw=True, parses, len(code)=1078/len(raw)=1092, has_think_tag=False
- qwen2.5-coder-1.5b abc397_f#0: in_raw=True, parses, len(code)=606/len(raw)=620, has_think_tag=False
- qwen2.5-coder-1.5b abc391_b#0: in_raw=True, parses, len(code)=556/len(raw)=570, has_think_tag=False
- qwen2.5-coder-1.5b abc395_e#2: in_raw=True, parses, len(code)=877/len(raw)=891, has_think_tag=False
- qwen2.5-coder-1.5b 3754#1: in_raw=True, parses, len(code)=1583/len(raw)=2355, has_think_tag=False
- qwen2.5-coder-7b 3709#1: in_raw=True, parses, len(code)=689/len(raw)=703, has_think_tag=False
- qwen2.5-coder-7b abc400_c#3: in_raw=True, parses, len(code)=414/len(raw)=796, has_think_tag=False
- qwen2.5-coder-7b abc398_c#3: in_raw=True, parses, len(code)=697/len(raw)=711, has_think_tag=False
- qwen2.5-coder-7b arc195_d#2: in_raw=True, parses, len(code)=456/len(raw)=470, has_think_tag=False
- qwen2.5-coder-7b 3791#4: in_raw=True, parses, len(code)=318/len(raw)=332, has_think_tag=False
- qwen3-4b-nothink 3684#0: in_raw=True, parses, len(code)=684/len(raw)=698, has_think_tag=False
- qwen3-4b-nothink 3793#1: in_raw=True, parses, len(code)=1029/len(raw)=1043, has_think_tag=False
- qwen3-4b-nothink 3697#1: in_raw=True, parses, len(code)=914/len(raw)=928, has_think_tag=False
- qwen3-4b-nothink 3801#2: in_raw=True, parses, len(code)=474/len(raw)=488, has_think_tag=False
- qwen3-4b-nothink 3777#3: in_raw=True, SYNTAX ERROR invalid syntax, len(code)=1150/len(raw)=1164, has_think_tag=False
- qwen3-4b-think 3702#0: EMPTY (raw empty: truncated while thinking); completion_tokens=8192
- qwen3-4b-think abc395_c#0: in_raw=True, parses, len(code)=521/len(raw)=535, has_think_tag=False
- qwen3-4b-think 3721#0: in_raw=True, parses, len(code)=1483/len(raw)=3502, has_think_tag=False
- qwen3-4b-think 3704#0: in_raw=True, parses, len(code)=216/len(raw)=1495, has_think_tag=False
- qwen3-4b-think 3763#0: in_raw=True, parses, len(code)=1265/len(raw)=3045, has_think_tag=False

## Grading: hidden_pass=false rows re-run independently

- deepseek-coder-6.7b 3717#1 exec says runtime_error; manual: failure confirmed (test 0/42 -> runtime_error '^^^^^^^^^^^^^^^^^^^^^^^^\n  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmpsvdrf53_\\c.py", line 23, in minOperations\n    if total - minq[0] == x:\n               ~~~~^^^\nIndexError: list index out of range\n')
- qwen2.5-coder-1.5b 3754#1 exec says wrong_answer; manual: failure confirmed (test 0/42 -> wrong_answer '4')
- qwen3-4b-nothink 3733#0 exec says wrong_answer; manual: failure confirmed (test 0/44 -> wrong_answer '1')
- qwen3-4b-nothink abc396_e#3 exec says timeout; manual: failure confirmed (test 0/43 -> timeout '')
- qwen3-4b-nothink abc390_d#4 exec says wrong_answer; manual: failure confirmed (test 0/43 -> wrong_answer '8\n')
- qwen3-4b-nothink 3562#3 exec says runtime_error; manual: failure confirmed (test 0/42 -> runtime_error '  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmpaph3u5nf\\c.py", line 74\n    import json as _j\nIndentationError: expected an indented block after \'for\' statement on line 25\n')
- deepseek-coder-6.7b 3754#0 exec says runtime_error; manual: failure confirmed (test 0/42 -> runtime_error 'C:\\Users\\Admin\\AppData\\Local\\Temp\\tmp32e5x9x4\\c.py", line 17, in maxDistance\n    prefix[i][ord(s[i-1])-ord(\'a\')] = i\n    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^\nIndexError: list assignment index out of range\n')
- deepseek-coder-6.7b 3759#2 exec says wrong_answer; manual: failure confirmed (test 0/42 -> wrong_answer '[-100, -80, -70, -110, -90]')

## Grading: hidden_pass=true rows re-run independently

- qwen3-4b-think 3705#0 exec says pass; manual: pass confirmed (all 34 tests passed)
- deepseek-coder-6.7b abc390_b#4 exec says pass; manual: pass confirmed (all 43 tests passed)
- qwen3-4b-nothink 3723#1 exec says pass; manual: pass confirmed (all 33 tests passed)
- qwen2.5-coder-7b 3778#3 exec says pass; manual: pass confirmed (all 33 tests passed)
- qwen2.5-coder-7b abc390_a#3 exec says pass; manual: pass confirmed (all 44 tests passed)

(pool sizes: 3076 failing non-empty rows, 626 passing rows)
