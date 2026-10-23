# results

Small result files copied from the bundle (`bundle/<benchmark>/`, not in git; full bundle with raw samples:
`slmcheck_bundle.zip`, ~110 MB, distributed separately).

- `tables/*.csv`: accuracy by strategy (with Wilson 95 % CIs), false passes, silent bugs, gap recovered, local-first
  cascade, McNemar tests (Holm-corrected), cost.
- `RESULTS.md`: the generated summary; `VERIFICATION_REPORT.md`: gate results; `VERIFICATION_NOTES.md`: the
  run notes (environment, timeline, deviations, harness fixes, manual checks); `run_metadata.json`.
- `manual_checks/`: independent re-runs by `tools/manual_check.py`.
- `livecodebench/contamination_split.md`: accuracy before vs on/after 2025-03-01 (`tools/contamination_split.py`).
