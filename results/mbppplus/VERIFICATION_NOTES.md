### Read this first

- **Cloud LLM 1: gpt-oss-120b (Groq).** Ran 2026-10-23 11:59 to 12:02 after the User-Agent fix (commit `3ec9fd0`; incident details in the LiveCodeBench notes): 200/200 samples, 0 errors, and **0.800** (160 of 200).
- **Cloud LLM 2: DeepSeek-V3.1, non-thinking (SambaNova), 0.790 (158 of 200).** Replaces Llama-3.3-70B, which was unavailable on every provider we could
  reach (history in the LiveCodeBench notes, "Second cloud LLM"). Ran 18:45 to 19:11, 0 errors, 29,838 input / 22,476 output tokens, only 5 of 200 answers
  hit the 1,024-token cap. Released August 2025, so it has very likely seen MBPP (as have all models here). Manual re-runs (seed 52,
  `manual_checks/manual_check_mbpp_deepseek.md`): 6 extraction samples clean, 6 of 6 failures and 4 of 4 passes reproduced independently.
- `qwen3-4b-think` ran with **k = 1, not 2** (pre-agreed fallback), so S1 to S5 for that config equal S0 by construction.
- The shared GPU (another training job on the same card), concurrent requests and one dedicated Ollama server were used exactly as described in
  the LiveCodeBench notes (`../livecodebench/VERIFICATION_NOTES.md`). Timings are not laptop timings. The deviations and harness fixes there apply to this run too.
- MBPP dates from 2021, so contamination is likely. Treat this as the checker-strictness benchmark, as the design says; LiveCodeBench is the primary result.

## Environment

Same machine, GPU (RTX PRO 4000 Blackwell, 24 GB, shared), driver 595.97, Ollama 0.40.3, Python 3.11.7 as in the LiveCodeBench notes. Model digests:
qwen2.5-coder:1.5b `d7372fd82851`; qwen2.5-coder:7b `dae161e27b0e`; deepseek-coder:6.7b `ce298d984115`; qwen3:4b-q4_K_M `2bfd38a7daaf`.
Data: EvalPlus MBPP+ through the Hugging Face rows API, 378 problems, fixed random 200 with seed 20261016 after excluding task 590 (as in `config.MBPP_EXCLUDE`); all 200 use the `script` test type (first original assert = public example, the remaining original asserts + the EvalPlus plus script = hidden).

## Timeline (local time, 23 Oct 2026 unless noted)

| stage | start | end |
|---|---|---|
| download + prepare + gates data/exec | 22 Oct 18:00 | 18:10 |
| generate qwen2.5-coder-1.5b | 04:11 | 04:26 |
| generate qwen2.5-coder-7b | 04:26 | 04:57 |
| generate deepseek-coder-6.7b | 04:57 | 06:23 |
| generate qwen3-4b-nothink | 06:23 | 06:42 |
| generate qwen3-4b-think (k=1, 200 samples + 200 self-tests) | 06:43 | 08:41 |
| evaluate, first pass | 05:04 | 08:44 |
| evaluate again after the `pow` fix and after the extraction fix (final) | 08:48 | 09:04 |
| post gate, manual checks, report, bundle | 11:20 | see bundle timestamp |

## Gate results

`verify --stage data` PASS, including "MBPP+ reference solutions pass their own tests on this machine" (no broken item in the 200). `verify --stage exec` PASS. `verify --stage post --tier slm`:

- **FAIL: qwen3-4b-think: empty extractions < 5%: 9.0% empty (18 of 200).** Not a harness defect: all 18 have `completion_tokens` = 8192 and an empty `content` (reasoning still running at the frozen cap).
  The cap was not changed. The other 182 finished and 154 of 200 problems have a passing thinking sample (0.770 S0).
- **FLAG: qwen2.5-coder-1.5b greedy sample reproducible: 2/3 identical.** Same explanation as in the LiveCodeBench notes: single-stream greedy reruns are identical to each other, stored samples were decoded 3 to 4 requests at a time.
- Everything else PASS (no duplicate keys, complete counts, self-tests usable, 0 error rows).

## Manual checks

Independent runner `manual_check.py` (plain `subprocess`, the candidate followed by the test script, outputs in `manual_checks/`). Final run (seed 42): 5 random samples per config for extraction,
8 failing and 5 passing rows re-run independently.

1. **Smoke run.** Only LiveCodeBench problems were in the smoke run; MBPP+ was covered by its own 1.5b first-pass check (S0 0.59, 0.72 of samples passed the public example).
2. **Extraction.** Found and fixed the "last block is only the echoed assert" defect and the lone closing fence defect here first: 113 of deepseek-coder's 1,000 samples (11%), 5 of qwen2.5-coder-1.5b, 1 of qwen2.5-coder-7b changed
   (commit `2078b28`, details and tests in the LiveCodeBench notes, deviation 8). Afterwards every sampled `code` is a substring of `raw_text` and parses.
3. **Grading, failing rows.** 8 of 8 re-run failures reproduce independently (assertion error or runtime error on the same test index). **Passing rows:** 5 of 5 pass all 4 tests in the independent re-run.
4. **Plausibility.** S1 >= S2..S5 >= S0 holds for every SLM. All 200 problems are `script` tests and every SLM solves some (144 to 162 problems by pass@5). Hidden tests are stricter than the example, which is the point of this
   benchmark: of the problems where S2 accepts a sample (it passed the example), 13.5% to 25.3% are still wrong on hidden tests. LLM checks: gpt-oss-120b (0.800) beats the best SLM S0 (0.770, qwen3-4b-think) and solves script problems;
   `verify --stage post` passes every LLM check; its 5 failing and 3 passing rows re-run independently all agree with the harness (`manual_checks/manual_check_mbpp_gptoss.md`).

| config | S0 | S1 (pass@5) | S2 | S3 (tau 1.0) | S4 | S5 | S2 accepts / false-pass | S5 accepts / false-pass |
|---|---|---|---|---|---|---|---|---|
| qwen2.5-coder-1.5b | 0.590 | 0.720 | 0.665 | 0.660 | 0.650 | 0.685 | 0.890 / 0.253 | 0.675 / 0.133 |
| qwen2.5-coder-7b | 0.720 | 0.810 | 0.760 | 0.745 | 0.765 | 0.765 | 0.965 / 0.212 | 0.850 / 0.153 |
| deepseek-coder-6.7b | 0.705 | 0.775 | 0.740 | 0.755 | 0.745 | 0.750 | 0.920 / 0.196 | 0.790 / 0.127 |
| qwen3-4b-nothink | 0.675 | 0.745 | 0.720 | 0.715 | 0.700 | 0.720 | 0.895 / 0.196 | 0.805 / 0.161 |
| qwen3-4b-think (k=1) | 0.770 | = S0 | = S0 | = S0 | = S0 | = S0 | 0.890 / 0.135 | 0.890 / 0.135 |

## Deviations and harness fixes

Identical to the LiveCodeBench notes (qwen3 tag, think k=1, dedicated Ollama server with concurrency, test encoding, error-row regeneration, executor temp cleanup, `pow` header, extraction fix + re-extraction, `evaluate --cfg`).
Specific to this run: the extraction fix (commit `2078b28`) changed MBPP+ results (the `pow` header fix of commit `71051de` was already in place when MBPP+ was first executed) (deepseek-coder S0 moved from 0.685 to 0.705; the other configs' S0 did not change). The MBPP+ first-pass `exec.jsonl` was produced after the `pow` fix, so only the extraction fix needed a rerun: `exec.jsonl` was deleted and rebuilt (previous copy: `_superseded/exec_before_reextract.jsonl`). Original sample rows are in `_superseded/samples_before_reextract/`.

## Notes for interpreting these results

- **The gap is small here** (gpt-oss-120b 0.800 against SLM S0 0.59 to 0.72), so gap recovered is large and noisy: S2 recovers 36% to 50%, S5 36% to 56%. Oracle S1 for qwen2.5-coder-7b is 1.125
  (its pass@5, 0.81, beats the LLM's single sample), which is the Hassid-style effect; realistic checkers recover about half of it.
- **Local-first escalation (N2).** Escalating only when S5 rejects keeps 85% of problems local for qwen2.5-coder-7b at 0.790 (cloud alone 0.800, random escalation 0.770, oracle 0.865) and 80% for qwen3-nothink at 0.795. See `tables/cascade.csv`.
- **MBPP+ is easy for these SLMs** (S0 0.59 to 0.77), so the checkers matter more here than on LiveCodeBench: example-only checking (S2) accepts 89% to 97% of problems and 20% to 25% of what it accepts is wrong; requiring both the example and a majority (S5)
  lowers the false-pass rate from 20% to 25% down to 13% to 16% (qwen3-4b-think stays at 13.5%) and accepts 0 to 21 points fewer problems. Self-test based selection (S3) was at or below S2 for 3 of the 4 multi-sample configs (deepseek-coder was the exception).
- **Contamination** is likely (2021 benchmark), so absolute accuracies are optimistic; the differences between checkers are the result to use.
- **Wall times** are concurrent and on a shared GPU; use `completion_tokens` (mean about 85 to 136 tokens for the non-thinking configs, about 2,300 for thinking) as the cost measure.
- **Reference solutions:** all 200 pass their own tests on this machine (gate PASS).
