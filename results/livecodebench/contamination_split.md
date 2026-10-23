# Contamination split, LiveCodeBench (D:\slm\seminar\runs\main)

Problems before 2025-03-01: 102; on/after 2025-03-01: 80. Difficulty mix (before / after): easy 27/18, medium 30/25, hard 45/37

| config | S0 before 2025-03-01 | S0 on/after 2025-03-01 | difference (pp) | S1 before | S1 on/after |
|---|---|---|---|---|---|
| deepseek-coder-6.7b | 15.7% [10, 24] (16/102) | 10.0% [5, 19] (8/80) | -5.7 | 21.6% [15, 31] (22/102) | 17.5% [11, 27] (14/80) |
| deepseek-v3.1 | 34.3% [26, 44] (35/102) | 30.0% [21, 41] (24/80) | -4.3 | = S0 | = S0 |
| gpt-oss-120b | 53.9% [44, 63] (55/102) | 55.0% [44, 65] (44/80) | +1.1 | = S0 | = S0 |
| qwen2.5-coder-1.5b | 7.8% [4, 15] (8/102) | 6.2% [3, 14] (5/80) | -1.6 | 17.6% [11, 26] (18/102) | 10.0% [5, 19] (8/80) |
| qwen2.5-coder-7b | 22.5% [16, 32] (23/102) | 17.5% [11, 27] (14/80) | -5.0 | 26.5% [19, 36] (27/102) | 25.0% [17, 35] (20/80) |
| qwen3-4b-nothink | 26.5% [19, 36] (27/102) | 23.8% [16, 34] (19/80) | -2.7 | 29.4% [21, 39] (30/102) | 35.0% [25, 46] (28/80) |
| qwen3-4b-think | 32.4% [24, 42] (33/102) | 31.2% [22, 42] (25/80) | -1.1 | = S0 | = S0 |

A drop after the cut-off for a model trained after it would hint at memorisation of the earlier problems; the difficulty mix differs between the two periods, so compare models within a column rather than absolute values.
