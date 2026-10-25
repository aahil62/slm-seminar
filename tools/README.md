# tools

Helper scripts from the real runs, kept because the results depend on them. They are not part of the harness
and have no tests; a path at the top of a script may still be the GPU machine's (`D:\slm\seminar`), adjust
before reuse.

| script | purpose |
|---|---|
| `manual_check.py` | independent spot checks (plain `subprocess`, not `slmcheck.executor`): extraction, failing rows, passing rows; prints markdown |
| `contamination_split.py` | LiveCodeBench accuracy before vs on/after 2025-03-01 per model (contamination check for DeepSeek-V3.1) |
| `results_table.py` | prints the README headline table from `bundle/<benchmark>/tables/accuracy_by_strategy.csv` (or `results/`) |
