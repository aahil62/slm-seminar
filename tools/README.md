# tools

Operational scripts used on the GPU machine during the real runs (they lived outside the repo in
`D:\slm\ops`). They are not part of the harness and have no tests; paths at the top of each script are
the ones used there (`D:\slm\seminar`), adjust before reuse. None of them contains or logs an API key.

| script | purpose |
|---|---|
| `manual_check.py` | independent spot checks (plain `subprocess`, not `slmcheck.executor`): extraction, failing rows, passing rows; prints markdown |
| `contamination_split.py` | LiveCodeBench accuracy before vs on/after 2025-03-01 per model (contamination check for DeepSeek-V3.1) |
| `results_table.py` | prints the README headline table from `bundle/<benchmark>/tables/accuracy_by_strategy.csv` (or `results/`) |
