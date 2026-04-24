# Site Memory Scoring

## Purpose

Score whether Skills learn from normal tests and avoid repeated same-site mistakes.

## Required Checks

- site memory exists for repeated domains
- market/locale/currency/stage are separated
- known failures include root cause and correct handling
- test logs are mined into reusable failure classes
- eval backlog captures repeated mistakes
- change log records version updates
- Skill references/evals are updated when failures generalize

## Score Impact

- Full credit: test failure becomes site memory plus eval or reference update.
- Partial credit: failure is documented but not linked to eval or version.
- No credit: same mistake remains only in conversation/log output.
