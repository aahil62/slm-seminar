# Manual spot-checks for runs\main

## Extraction (raw_text vs code)

- deepseek-v3.1 abc391_g#0: in_raw=True, SYNTAX ERROR invalid character '≤' (U+2264), len(code)=3737/len(raw)=3737, has_think_tag=False
- deepseek-v3.1 arc194_d#0: in_raw=True, SYNTAX ERROR unmatched ')', len(code)=4943/len(raw)=4943, has_think_tag=False
- deepseek-v3.1 abc397_f#0: in_raw=True, SYNTAX ERROR invalid syntax, len(code)=3678/len(raw)=3678, has_think_tag=False
- deepseek-v3.1 abc390_a#0: in_raw=True, parses, len(code)=314/len(raw)=3651, has_think_tag=False
- deepseek-v3.1 abc391_d#0: in_raw=True, SYNTAX ERROR invalid syntax, len(code)=4325/len(raw)=4325, has_think_tag=False
- deepseek-v3.1 3760#0: in_raw=True, parses, len(code)=1571/len(raw)=2106, has_think_tag=False

## Grading: hidden_pass=false rows re-run independently

- deepseek-v3.1 abc400_g#0 exec says runtime_error; manual: failure confirmed (test 0/6 -> runtime_error ' we can generate eight vectors:\n                                                                                                                                 ^\nSyntaxError: invalid decimal literal\n')
- deepseek-v3.1 abc399_d#0 exec says runtime_error; manual: failure confirmed (test 0/2 -> runtime_error '  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmpsfpp1p_f\\c.py", line 34\n    Read N and the list A of length 2N.\n                                    ^\nSyntaxError: invalid decimal literal\n')
- deepseek-v3.1 arc192_b#0 exec says runtime_error; manual: failure confirmed (test 0/43 -> runtime_error 'nce and adding the index to S if it is not already present. The game ends when S contains all indices from 1 to N, and the player who made the last move wins.\n       ^^^^^\nSyntaxError: invalid syntax\n')
- deepseek-v3.1 3783#0 exec says runtime_error; manual: failure confirmed (test 0/43 -> runtime_error '  File "C:\\Users\\Admin\\AppData\\Local\\Temp\\tmpn0j17yrd\\c.py", line 37\n    import json as _j\nIndentationError: expected an indented block after function definition on line 11\n')
- deepseek-v3.1 3781#0 exec says wrong_answer; manual: failure confirmed (test 0/43 -> wrong_answer '4')
- deepseek-v3.1 abc397_f#0 exec says runtime_error; manual: failure confirmed (test 0/42 -> runtime_error 'positions such that the sum of distinct counts in each subarray is maximized. The challenge is to do this efficiently given the constraints (N up to 300,000).\n       ^^^^^\nSyntaxError: invalid syntax\n')

## Grading: hidden_pass=true rows re-run independently

- deepseek-v3.1 abc396_d#0 exec says pass; manual: pass confirmed (all 43 tests passed)
- deepseek-v3.1 3705#0 exec says pass; manual: pass confirmed (all 34 tests passed)
- deepseek-v3.1 abc394_b#0 exec says pass; manual: pass confirmed (all 42 tests passed)
- deepseek-v3.1 abc395_c#0 exec says pass; manual: pass confirmed (all 43 tests passed)

(pool sizes: 123 failing non-empty rows, 59 passing rows)
