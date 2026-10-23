# Manual spot-checks for runs\main

## Extraction (raw_text vs code)


## Grading: hidden_pass=false rows re-run independently

- gpt-oss-120b abc397_d#0 exec says timeout; manual: failure confirmed (test 4/43 -> timeout '')
- gpt-oss-120b 3697#0 exec says wrong_answer; manual: failure confirmed (test 8/43 -> wrong_answer '542485855')
- gpt-oss-120b arc195_d#0 exec says wrong_answer; manual: failure confirmed (test 0/2 -> wrong_answer '5\n4\n11')
- gpt-oss-120b 3762#0 exec says wrong_answer; manual: failure confirmed (test 2/42 -> wrong_answer '4899047300')
- gpt-oss-120b abc394_c#0 exec says wrong_answer; manual: failure confirmed (test 1/43 -> wrong_answer 'WAC')

## Grading: hidden_pass=true rows re-run independently

- gpt-oss-120b 3748#0 exec says pass; manual: pass confirmed (all 43 tests passed)
- gpt-oss-120b abc392_c#0 exec says pass; manual: pass confirmed (all 42 tests passed)
- gpt-oss-120b abc399_a#0 exec says pass; manual: pass confirmed (all 44 tests passed)

(pool sizes: 83 failing non-empty rows, 99 passing rows)
