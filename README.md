# slmcheck — local SLMs vs cloud LLMs under realistic checkers

Seminar research code. Earlier directions (the main-branch SLM swarm and the `aers-slm/rebuild`
AERS pipeline) are retired: they stay in git history on their own branches. This branch is a fresh
start.

**Research question.** Small code models beat large ones when hidden tests choose among several
answers (Hassid et al., COLM 2024). Developers never have hidden tests. With the checks they do have
(example cases, model-written tests, majority vote), does a free SLM on a laptop GPU still close the
gap to a 70–120B cloud model? How often do those checks accept wrong code? And how should work be
split between local and cloud?

- Design: `docs/DESIGN.md`

## Two machines

| Machine | Where | Does |
|---|---|---|
| **Development** | the student's laptop | design, code, tests on fixtures, runbook, then interpreting results and writing the paper |
| **Runs** | college GPU machine (Windows, RTX 4050) | every step that touches models: setup, generation, execution, verification, bundle |

## Pipeline

```
download -> prepare -> verify(env,data,exec,backend) -> generate -> evaluate -> verify(post) -> report
```

- **Models:**
  - local via Ollama: qwen2.5-coder 1.5b and 7b, deepseek-coder 6.7b, qwen3 4b with thinking off and on
  - cloud via the Groq free tier: gpt-oss-120b, llama-3.3-70b
- **Problems:** LiveCodeBench with `contest_date >= 2025-01-01` (primary), plus MBPP+, a fixed random 200 chosen for its strict hidden tests.
- **Strategies:**
  - S0: first answer
  - S1: oracle best-of-k
  - S2: example cases
  - S3: self-written tests
  - S4: majority vote
  - S5: example cases and majority vote combined
- **Outputs:** accuracy, gap recovered, false-pass rate, silent bugs by type, local-first escalation curves, McNemar tests,
  cost.

## Local check (no models)

```bash
uv venv -p 3.11 .venv && uv pip install -p .venv -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m slmcheck all --fake --run-dir runs/dryrun --out runs/dryrun_bundle
```

The `--fake` run uses fixture problems and scripted fake models. Its output is labelled
`FAKE — NOT RESULTS`.
