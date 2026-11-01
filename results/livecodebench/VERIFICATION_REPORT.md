# Verification report

Gates run by `python -m slmcheck verify`. FAIL = broken, must be repaired. FLAG = suspicious, must be investigated and explained below.

## env: PASS (2026-10-22 18:19:31)

| check | status | evidence |
|---|---|---|
| python>=3.11 | PASS | 3.11.7 |
| ollama reachable | PASS | 6 local models |
| model pulled: qwen2.5-coder:1.5b | PASS | present |
| model pulled: qwen2.5-coder:7b | PASS | present |
| model pulled: deepseek-coder:6.7b | PASS | present |
| model pulled: qwen3:4b-q4_K_M | PASS | present |
| model pulled: qwen3:4b-q4_K_M | PASS | present |
| nvidia GPU visible | PASS | NVIDIA RTX PRO 4000 Blackwell, 24467 MiB, 7582 MiB, 595.97 |
| disk free >= 20 GB | PASS | 2096 GB free |

## data: PASS (2026-10-22 18:05:54)

| check | status | evidence |
|---|---|---|
| problem count >= 150 | PASS | 182 problems |
| every problem has public and private tests | PASS | missing: [] |
| difficulty mix | PASS | {"easy": 45, "medium": 55, "hard": 82} |
| test types | PASS | {"stdin": 112, "functional": 70, "script": 0} |
| functional problems have func_name | PASS | missing: [] |
| no private test input appears in any prompt | PASS | leaks: [] |
| all dates >= 2025-01-01 | PASS | 2025-01-04 .. 2025-04-06 |

## exec: PASS (2026-10-22 18:06:02)

| check | status | evidence |
|---|---|---|
| reference passes: fx_add | PASS | ['pass', 'pass', 'pass', 'pass'] |
| wrong solution fails: fx_add | PASS | ['fail', 'skipped', 'skipped', 'skipped'] |
| reference passes: fx_twosum | PASS | ['pass', 'pass', 'pass'] |
| wrong solution fails: fx_twosum | PASS | ['pass', 'fail', 'skipped'] |
| reference passes: fx_primes | PASS | ['pass', 'pass', 'pass'] |
| wrong solution fails: fx_primes | PASS | ['pass', 'pass', 'fail'] |
| MBPP+ canonical passes: mbpp/2 | PASS | ['pass', 'pass', 'pass', 'pass'] |
| MBPP+ canonical passes: mbpp/3 | PASS | ['pass', 'pass', 'pass', 'pass', 'pass'] |
| MBPP+ wrong solution: passes example, fails hidden: mbpp/3 | PASS | ['pass', 'pass', 'fail', 'pass', 'fail'] |
| MBPP+ canonical passes: mbpp/4 | PASS | ['pass', 'pass', 'pass', 'pass'] |
| timeout kills runaway code | PASS | timeout in 6.1s |

## backend: PASS (2026-10-22 18:26:17)

| check | status | evidence |
|---|---|---|
| qwen2.5-coder-1.5b returns parsable code | PASS | 3/3 parsable; 536 tokens in 11.6s (46.4 tok/s) |
| qwen2.5-coder-7b returns parsable code | PASS | 3/3 parsable; 635 tokens in 20.8s (30.5 tok/s) |
| deepseek-coder-6.7b returns parsable code | PASS | 3/3 parsable; 1068 tokens in 26.6s (40.1 tok/s) |
| qwen3-4b-nothink returns parsable code | PASS | 3/3 parsable; 814 tokens in 20.1s (40.6 tok/s) |
| qwen3-4b-nothink: thinking is OFF | PASS | 0/3 replies contained reasoning (update Ollama if >0) |
| qwen3-4b-think returns parsable code | PASS | 1/3 parsable; 22775 tokens in 315.7s (72.1 tok/s) |
| qwen3-4b-think: thinking is ON | PASS | 3/3 replies contained reasoning (update Ollama if 0) |

## post: FAIL (2026-10-23 19:15:59)

| check | status | evidence |
|---|---|---|
| no duplicate sample keys | PASS | 0 duplicates |
| qwen2.5-coder-1.5b: sample count | PASS | 910/910 |
| qwen2.5-coder-1.5b: empty extractions < 5% | PASS | 0.1% empty, 1 errors |
| qwen2.5-coder-7b: sample count | PASS | 910/910 |
| qwen2.5-coder-7b: empty extractions < 5% | PASS | 0.0% empty, 0 errors |
| deepseek-coder-6.7b: sample count | PASS | 910/910 |
| deepseek-coder-6.7b: empty extractions < 5% | PASS | 0.2% empty, 1 errors |
| qwen3-4b-nothink: sample count | PASS | 910/910 |
| qwen3-4b-nothink: empty extractions < 5% | PASS | 0.0% empty, 0 errors |
| qwen3-4b-think: sample count | PASS | 182/182 |
| qwen3-4b-think: empty extractions < 5% | FAIL | 64.3% empty, 0 errors |
| gpt-oss-120b: sample count | PASS | 182/182 |
| gpt-oss-120b: empty extractions < 5% | PASS | 0.0% empty, 0 errors |
| deepseek-v3.1: sample count | PASS | 182/182 |
| deepseek-v3.1: empty extractions < 5% | PASS | 0.0% empty, 0 errors |
| qwen2.5-coder-1.5b: self-tests usable for >= 50% of problems | PASS | 154/182 |
| qwen2.5-coder-7b: self-tests usable for >= 50% of problems | PASS | 176/182 |
| deepseek-coder-6.7b: self-tests usable for >= 50% of problems | PASS | 169/182 |
| qwen3-4b-nothink: self-tests usable for >= 50% of problems | PASS | 179/182 |
| qwen3-4b-think: self-tests usable for >= 50% of problems | PASS | 135/182 |
| qwen2.5-coder-1.5b: greedy sample reproducible | FLAG | 2/3 identical |
| every sample executed | PASS | 4186 exec rows / 4186 samples |
| some SLM solves at least one easy problem | PASS | harness or prompt problem if not |
| gpt-oss-120b: accuracy >= best SLM S0 | PASS | 0.544 vs 0.319 |
| gpt-oss-120b: accuracy > 0.2 (else suspect harness) | PASS | 0.544 |
| gpt-oss-120b: solves some stdin problems | PASS | 60/112 (0 means the stdin harness is likely broken) |
| gpt-oss-120b: solves some functional problems | PASS | 39/70 (0 means the functional harness is likely broken) |
| deepseek-v3.1: accuracy >= best SLM S0 | PASS | 0.324 vs 0.319 |
| deepseek-v3.1: accuracy > 0.2 (else suspect harness) | PASS | 0.324 |
| deepseek-v3.1: solves some stdin problems | PASS | 36/112 (0 means the stdin harness is likely broken) |
| deepseek-v3.1: solves some functional problems | PASS | 23/70 (0 means the functional harness is likely broken) |

## Run notes (investigations, repairs, deviations)

﻿### Read this first

- **Cloud LLM 1: gpt-oss-120b (Groq).** `llama-3.3-70b-versatile` was not available on Groq (HTTP 404 `model_not_found` on
  2026-10-23, now Enterprise-only), so it was dropped there (commit `a24ff0c`); there is no Llama row anywhere.
  gpt-oss-120b ran on 2026-10-23 after `GROQ_API_KEY` was set, once a User-Agent fix was in (see "Cloud LLM run" below).
  It scores **0.544** (99 of 182) here.
- **Second cloud LLM: DeepSeek-V3.1 (non-thinking) on SambaNova, 0.324 (59 of 182)** — chosen after Llama-3.3-70B
  proved unavailable everywhere we could reach (details in "Second cloud LLM" below). Two caveats dominate its number:
  (1) it was released in August 2025, after this problem window, so contamination is possible; (2) under the frozen
  1,024-token cap 111 of its 182 answers were cut off (59 were still explaining in prose, 52 cut mid-code) and all of
  those fail; of the 71 answers with a complete code block, 59 pass (83%). Treat 0.324 as a lower bound set by the cap.
- `qwen3-4b-think` ran with **k = 1, not 2** (pre-agreed fallback, see Deviations). With one sample per problem, S1 to S5 for that
  config are identical to S0 by construction, so N1 cannot be measured for the thinking config.
- The GPU was shared with a long-running training job of the owner (about 16.4 GB of 24 GB VRAM and 65% utilisation throughout), so
  every timing below is under contention and, for most configs, under 2 to 4 concurrent requests. Do not read `wall_s` as laptop seconds.

## Environment

| item | value |
|---|---|
| Machine | Windows 11 Pro 10.0.26200, Intel Core Ultra 9 285 (24 threads), 127 GB RAM |
| GPU | NVIDIA RTX PRO 4000 Blackwell, 24467 MiB VRAM, driver 595.97 (CUDA 13.2). Shared with another job. Not the RTX 4050 the design assumed. |
| Ollama | 0.40.3 (a dedicated server on port 11435 was used, see Deviations) |
| Python | 3.11.7 (venv `.venv`), matplotlib / numpy / pytest from `requirements.txt` |
| Branch / code | `research/slmcheck`, commits listed under Deviations |
| Benchmark | LiveCodeBench `code_generation_lite`, files `test5.jsonl` and `test6.jsonl` only (`test7`/`test8` return HTTP 404). 182 problems, contest dates 2025-01-04 to 2025-04-06: 45 easy, 55 medium, 82 hard; 112 stdin, 70 functional |
| Model digests | qwen2.5-coder:1.5b `d7372fd82851`; qwen2.5-coder:7b `dae161e27b0e`; deepseek-coder:6.7b `ce298d984115`; qwen3:4b-q4_K_M `2bfd38a7daaf` (both qwen3 configs) |

Contamination: Qwen3 (April 2025) and the contest window overlap closely, so some of these problems may be in its training data. The
window ends 2025-04-06, so the "after 2025-03-01" sub-analysis covers only about five weeks of problems.

## Timeline (local time, 2026-10-22 to 2026-10-23)

| stage | start | end |
|---|---|---|
| clone, venv, tests, model pulls | 22 Oct 17:52 | 18:20 |
| data download + prepare, gates env/data/exec | 18:00 | 18:30 |
| backend gate (first run failed on qwen3 tag, passed after the tag fix) | 18:10 | 18:30 |
| smoke run, 3 problems x all SLM configs | 18:28 | 18:49 |
| generate qwen2.5-coder-1.5b | 18:54 | 19:20 |
| generate qwen2.5-coder-7b | 19:21 | 20:05 |
| generate deepseek-coder-6.7b | 20:06 | 22:19 |
| generate qwen3-4b-nothink | 22:20 | 23:06 |
| generate qwen3-4b-think, first attempt k=2 (aborted after 12 samples) | 23:06 | 23:21 |
| generate qwen3-4b-think, k=1 | 23:21 | 23 Oct 04:10 |
| evaluate (first pass, per config as each finished) | 19:26 | 04:11 |
| evaluate again after the `pow` fix | 04:14 | 05:04 |
| evaluate again after the extraction fix (final results) | 23 Oct 08:48 | 09:40 |
| post gate, manual checks, report, bundle | 11:20 | see bundle timestamp |

## Gate results

`verify --stage env/data/exec/backend` all PASS (backend after the tag fix). `verify --stage post` run per tier (`--tier slm`) printed:

- **FAIL: qwen3-4b-think: empty extractions < 5%: 64.3% empty (117 of 182).** Investigated, not a harness defect. All 117 empty rows
  have `completion_tokens` = 8192 (the frozen cap) and an empty `content`: the model was still inside its reasoning when the cap hit, so
  there is no answer to extract. By difficulty: 78 of 82 hard, 35 of 55 medium, 4 of 45 easy truncated. The 65 that finished are right
  58 times (89%). Raising the cap would change the frozen protocol, so it was left. This FAIL stays in the report on purpose.
- **FLAG: qwen2.5-coder-1.5b greedy sample reproducible: 2/3 identical.** Re-running the same greedy request twice on an idle server
  gives identical text both times (3 of 3 problems), so the model is deterministic. The stored samples were produced with 3 to 4 requests
  decoded together, which changes floating-point results slightly; one of three stored samples therefore differs from a single-stream rerun.
  Expect small run-to-run differences for the same reason if the experiment is repeated.
- All other post checks PASS: no duplicate keys, sample counts complete (910 per k=5 config, 182 for think), self-tests usable for at least 50% of problems.

Errors: 1 sample each for qwen2.5-coder-1.5b and deepseek-coder-6.7b was aborted by Ollama (`prediction aborted, token repeat limit reached`,
a degenerate loop). It was retried three times, stays an empty error row, and counts as a failed sample.

## Manual checks

Done with `tools/manual_check.py` (independent runner: plain `subprocess`, one test per interpreter, not `slmcheck.executor`). Output files
are in `manual_checks/`. Final run (seed 41): 5 random samples per config for extraction, 8 failing rows and 5 passing rows re-run on every public+private test.

1. **Smoke run.** Every config produced code. Thinking OFF check passed for qwen3-4b-nothink (0 of 3 replies contained reasoning) and
   ON for qwen3-4b-think (3 of 3). Measured speed (wall-clock tok/s, one request at a time, shared GPU): 1.5b 63, 7b 36, deepseek 49,
   nothink 53, think 71. The think config hit the cap on 5 of 6 smoke samples, which is what predicted the full-run time and the k=1 decision.
   Estimated full run before starting: 20 to 27 h sequential; actual with concurrency and k=1: 9.3 h of generation for LiveCodeBench.
2. **Extraction.** For every sampled row `code` was a substring of `raw_text`, no reasoning text, no `<think>` tags. Two real defects were
   found and fixed (see Deviations 7 and 8). After the fix the remaining syntax errors are all truncated outputs (qwen3-4b-nothink hits the
   1,024-token cap on 142 of 910 samples = 15.6%, always mid-program; 161 samples overall end in an unterminated fence; none of
   them would pass the hidden tests even with the fence stripped).
3. **Grading, failing rows.** 8 of 8 random `hidden_pass=false` rows fail in the independent re-run as well, with the same kind (wrong answer, runtime error, timeout).
   Earlier rounds in this run found two harness bugs this way (the `pow` shadowing and the echoed-assert extraction); after both fixes every
   later sample agreed with the harness.
4. **Grading, passing rows.** 5 of 5 random `hidden_pass=true` rows pass all 33 to 44 tests in the independent re-run.
5. **Plausibility.** (a) S1 >= S2..S5 >= S0 holds for every SLM (table below). (b) Easy >= medium >= hard for every config. (c) Both test types are solved
   by every SLM: stdin 20 to 41 problems, functional 6 to 21 problems. (d) gpt-oss-120b (0.544) beats the best SLM S0 (0.319) and solves both types (stdin 60 of 112, functional 39 of 70);
   easy 44/45, medium 35/55, hard 20/82. Its 5 failing and 3 passing rows re-run independently all agree with the harness (`manual_checks/manual_check_main_gptoss.md`).

| config | S0 | S1 (pass@5) | S2 | S3 (tau 1.0) | S4 | S5 | easy / medium / hard S0 |
|---|---|---|---|---|---|---|---|
| qwen2.5-coder-1.5b | 0.071 | 0.143 | 0.143 | 0.137 | 0.099 | 0.143 | 12/45, 1/55, 0/82 |
| qwen2.5-coder-7b | 0.203 | 0.258 | 0.258 | 0.231 | 0.242 | 0.258 | 29/45, 7/55, 1/82 |
| deepseek-coder-6.7b | 0.132 | 0.198 | 0.187 | 0.192 | 0.170 | 0.192 | 21/45, 2/55, 1/82 |
| qwen3-4b-nothink | 0.253 | 0.319 | 0.313 | 0.280 | 0.286 | 0.319 | 35/45, 9/55, 2/82 |
| qwen3-4b-think (k=1) | 0.319 | = S0 | = S0 | = S0 | = S0 | = S0 | 40/45, 16/55, 2/82 |

## Deviations and harness fixes (all committed on `research/slmcheck`)

1. **qwen3 tag (commit `15209ab`).** `qwen3:4b` now resolves to Qwen3-4B-Thinking-2507 (256K context, template always opens `<think>`), so
   `think=False` is ignored: the first backend gate run showed 0 of 3 parsable replies for qwen3-4b-nothink (reasoning text filled the 1,024 tokens).
   Both qwen3 configs now use the explicit tag `qwen3:4b-q4_K_M` (digest `2bfd38a7daaf`, the original hybrid Qwen3-4B, 40K context), where
   thinking off and on both work (checked: off gives code directly, on fills the `thinking` field). Pre-agreed fallback "explicit tag".
   Note the stock gate "thinking is OFF" passed even on the broken tag because it only looks at the `thinking` field; the manual probe is what caught it.
2. **qwen3-4b-think k 2 to 1 (commit `f98015f`).** Pre-agreed fallback. At 23:06 the run produced 11 samples in 12.5 minutes (about 7 h for 364 samples plus
   self-tests), far above the design's 5 h. The 12 partial k=2 rows are kept in `_aborted_think_k2/` and are not part of any result. The run was
   restarted with k=1. Generation is resumable: setting k back to 2 and rerunning `generate` would add the missing second sample (about 3.4 h for this run).
3. **Dedicated Ollama server and concurrency (commits `15209ab`, `52e9e1e`).** To stay inside the VRAM that the other job leaves free (about 7 GB), generation used a
   separate Ollama server on port 11435 with one resident model and `NUM_PARALLEL` set per config (1.5b: 4, 7b: 3, deepseek: 1, nothink: 4, think: 2) and
   the harness setting `SLMCHECK_PARALLEL` for the same number of in-flight requests. Output records are identical (one extra field `workers`). Causes the numeric
   noise described under the FLAG above. The default Ollama server (port 11434) was only used for the gate checks.
4. **Only `test5` and `test6`** exist on the Hugging Face dataset, so the window has 182 problems and ends 2025-04-06 (the design expected "roughly 175+").
5. **Test-only encoding fix (commit `6d68a84`).** Two report tests read UTF-8 files with the Windows default codepage and failed on the em dash. Library code already used UTF-8.
6. **Error rows regenerate on rerun (commit `b72cfcd`) and the executor temp dir cleanup (commit `80a96d8`).** `generate` used to count a backend-error row as done forever. `evaluate`
   crashed once on Windows with `PermissionError` while deleting a temp dir still held by a just-killed process; cleanup is now best-effort with retries. Test added for both.
7. **Header shadowing `pow` (commit `71051de`).** Evidence: qwen3-4b-nothink arc192_e#1 and abc399_f#4 failed with `TypeError: pow expected 2 arguments, got 3`
   because the candidate header `from math import *` replaced the builtin `pow`. 62 samples use 3-argument `pow`. Fixed by importing `builtins` after `math`; a test
   fails without the fix. `exec.jsonl` was deleted and re-run; the old file is kept as `_superseded/exec_before_pow_fix.jsonl`. Seven samples flipped from fail to pass
   (deepseek 4, qwen2.5-coder-7b 2, nothink 1). Samples were not regenerated.
8. **Extraction (commit `2078b28`).** Evidence on MBPP+ (deepseek-coder `mbpp/418#4`, `mbpp/759#3`, `mbpp/6#2`): the model wrote the function in one block and repeated the example
   assert in a second block, and the extractor took the last block (the assert only, a `NameError`); another reply ended with a lone closing fence and was graded with the explanation text.
   New rule: among fenced blocks prefer the last one that defines a function/class or reads stdin; an unpaired fence is stripped. Self-test parsing keeps the old
   "last block" rule (verified: 0 of 1,910 saved self-test rows change). `slmcheck.reextract` recomputed `code` from `raw_text` (model replies untouched), changing 172 rows in this
   run (deepseek 13, 1.5b 14, 7b 2, nothink 142, think 1) and 119 in the MBPP+ run; originals are in `_superseded/samples_before_reextract/`; changed rows carry `"code_reextracted": true`.
   `exec.jsonl` was re-run from scratch afterwards (previous copy kept as `_superseded/exec_before_reextract.jsonl`). Tests added.
9. **Smaller changes.** `evaluate --cfg` (commit `12bdce6`) lets finished configs be executed while others still generate; `SLMCHECK_OLLAMA_URL` overrides the server URL (commit `15209ab`).
   The run supervisor script (not part of the repo) relaunched stopped configs. One bug in it (its completeness check used `python -I` and so always answered
   "incomplete", relaunching a finished config) was found and fixed within 30 minutes; it only caused harmless re-runs of already complete configs.

Not changed: models and tags (except item 1), k and seeds (except item 2), temperatures, max tokens, problem window, prompts, strategies S0 to S5, tau values, timeouts, metrics.

## Cloud LLM run (gpt-oss-120b, Groq free tier)

- **403 incident.** The first attempt (11:30) got `HTTP 403 "error code: 1010"` on every call: Groq's Cloudflare front blocks urllib's default
  `Python-urllib/x.y` agent. Evidence: `gpt-oss-120b 3634#0` error row. Fix: explicit `User-Agent` on Groq requests, with a test (commit `3ec9fd0`).
  The 2 error rows were dropped and regenerated automatically on restart (commit `b72cfcd` behaviour). One probe call per model confirmed the fix and found Llama retired.
- **Timeline.** LiveCodeBench 11:36 to 11:59, MBPP+ 11:59 to 12:02, evaluate 12:05 to 12:07 (2026-10-23). 0 errors, 0 empty extractions, 322,599 completion tokens on LiveCodeBench.
- **Rate limits.** Groq returned a few short per-minute 429s (14 s sleeps), handled by `generate`; the daily token limit was never reached, so the design's "3 to 5 days" did not apply.
- **Gate.** `verify --stage post` (all configs) now passes every LLM check: sample count 182/182, accuracy above best SLM S0, accuracy > 0.2, solves stdin and functional.
  The only FAIL left is the qwen3-4b-think truncation explained above.

## Second cloud LLM (DeepSeek-V3.1 on SambaNova)

- **Why not Llama-3.3-70B.** Groq made `llama-3.3-70b-versatile` Enterprise-only (404 `model_not_found`); NVIDIA's API retired
  `meta/llama-3.3-70b-instruct` on 2026-08-26 (410 Gone); DeepInfra serves only an FP8 "Turbo" build and requires a $5 prepay
  (declined); SambaNova lists it but answered HTTP 429 "currently experiencing high demand" to every request from
  13:13 to 16:13 (about 170 attempts, 0 samples; the empty sample file is in `_superseded/`). Providers added for this, with tests:
  DeepInfra (`240985b`), SambaNova (`05541bb`); config switched to DeepSeek-V3.1 (`6b66086`).
- **Model and settings.** `DeepSeek-V3.1` on SambaNova, frozen LLM settings (temperature 0, one sample, max 1,024 output tokens,
  same prompts). It is a hybrid model; a probe showed SambaNova serves it non-thinking by default (no reasoning field, no `<think>`,
  identical output with `chat_template_kwargs.enable_thinking=false`), so no flag is sent.
- **Run.** 2026-10-23 LiveCodeBench 17:44 to 18:45, MBPP+ 18:45 to 19:11, evaluate 19:12. 0 errors. Tokens: LiveCodeBench 100,267 in /
  152,052 out; MBPP+ 29,838 in / 22,476 out. Cost at SambaNova's listed $3 / $4.50 per million: about $1.20 (plus a few probe calls).
- **Truncation (important).** DeepSeek-V3.1 tends to explain at length before or after its code. 121 of 182 LiveCodeBench answers
  reached the 1,024-token cap: 59 contain no code at all (prose only), 52 stop mid-code, 10 have a complete block followed by
  cut-off prose. All 111 answers without a complete code block fail; 59 of the 71 with one pass (83%). On MBPP+ only 5 of 200 hit the cap.
  The cap is part of the frozen protocol for non-thinking configs and was not changed.
- **Checks.** Manual re-runs (seed 51, `manual_checks/manual_check_main_deepseek.md`): 6 of 6 failures and 4 of 4 passes reproduced independently;
  the extraction samples with syntax errors are exactly the truncated prose / mid-code outputs above. Solves both test types
  (stdin 36, functional 23); by difficulty 43/45 easy, 12/55 medium, 4/82 hard. It beats the best SLM S0 only marginally
  (0.324 vs 0.319) because of the truncation; gpt-oss-120b (which reasons briefly and writes compact code) stays far ahead.
- **Contamination split** (script `tools/contamination_split.py`, output `contamination_split.md`): accuracy before
  vs on/after 2025-03-01 (102 vs 80 problems). DeepSeek-V3.1 34.3% vs 30.0%, gpt-oss-120b 53.9% vs 55.0%, qwen3-4b-think 32.4% vs 31.2%,
  qwen2.5-coder-7b 22.5% vs 17.5%, deepseek-coder-6.7b 15.7% vs 10.0%. Every model loses a few points after the cut-off, including models
  released long before it, and the later period has relatively fewer easy problems (18/80 vs 27/102), so the split shows no clear
  memorisation signal for DeepSeek-V3.1; intervals overlap for every model.

## Notes for interpreting these results

- **Gap recovered (all difficulties, gpt-oss-120b as the LLM).** Small on this window: S2 recovers 13% (deepseek) to 21% (qwen3-nothink) of the gap; even oracle S1 recovers only 15% to 23%.
  Most of the gap is in medium and hard problems that no SLM sample solves. On easy problems the picture is better (for example deepseek S1 35%, S5 30%).
- **Local-first escalation (N2).** With escalation triggered by S5, qwen3-nothink keeps 29% of problems local and reaches 0.533 (cloud alone 0.544, random escalation at the same rate 0.478, oracle 0.566);
  qwen2.5-coder-7b keeps 20% local at 0.527. S2 keeps more local (42% to 46%) at 0.47 to 0.51. See `tables/cascade.csv`.
- **N1 results here:** the realistic checks barely help the weaker SLMs on this window and false-pass rates are high. For example qwen2.5-coder-7b: S2 accepts 42.3% of problems and 39.0% of the accepted ones are wrong; S5 accepts 19.8%
  with a false-pass rate of 13.9%. S5 (public tests AND majority) is the only strategy with consistently low false passes. Hard problems are near zero for every SLM (0 to 2 of 82), so the easy and medium tiers carry the signal, as the design expected.
- **Thinking config.** In this setup it is the best single-sample config (0.319, 0.889 among completed answers) but at 6.6k tokens per sample on average and 64% of samples truncated. Compare it with nothink on accuracy per problem
  attempted, not per sample.
- **Silent-bug fail kinds.** 161 truncated outputs are labelled by the executor as `runtime_error`/`wrong_answer` rather than `empty`; they are failures either way and never accepted by S2, so the silent-bug table is not affected.
- **Wall times** are per request under concurrency on a shared GPU. Token counts (`completion_tokens`) are the portable cost measure.
- **Reference solutions** for the MBPP+ gate were checked in the MBPP+ run notes (one item, 590, stays excluded as in `config.py`).


