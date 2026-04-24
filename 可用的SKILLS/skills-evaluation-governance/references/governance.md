# Governance

## Version

Current version: 0.2.0

## Change Log

- 0.1.0: Initial usable Skill package with SKILL.md, references, agents metadata, and evals.
- 0.2.0: Added stricter scorecard, new Skill admission gate, local score script, and Karpathy-style behavior checks.

## Drift Tests

Run evals when:

- description trigger words change
- workflow or boundary rules change
- a real task exposes a missed trigger or false trigger
- a target site or anti-bot behavior changes

Track:

- positive trigger pass rate
- negative trigger pass rate
- behavior criteria pass rate
- repeated failure patterns

## Long-Term Governance

Keep examples current, add negative cases for near misses, and do not overfit one real-world incident at the expense of general behavior.
