# Scorecard Rubric

## Purpose

Use this rubric to score every existing or new Skill. A Skill is not considered "usable" until it passes structure validation, eval coverage, and backtest requirements.

## Score Dimensions

| Dimension | Points | Evidence |
|---|---:|---|
| Structure validity | 15 | `SKILL.md`, frontmatter, `agents/openai.yaml`, references |
| Trigger accuracy | 15 | clear description, Chinese/English triggers, positive and negative cases |
| Progressive disclosure | 10 | concise `SKILL.md`, details in references, no giant monolithic prompt |
| Execution behavior | 15 | assumptions surfaced, boundaries clear, success criteria defined |
| Backtest coverage | 20 | eval count, criteria quality, negative and regression cases |
| Experience capture | 10 | site memory, known failures, change log, eval backlog |
| CI and drift | 10 | local backtest or GitHub Skill Bench workflow |
| Maintainability | 5 | versioning, naming, readable layout |

## Karpathy-Derived Behavior Checks

Score execution behavior by checking whether the Skill makes the agent:

- state assumptions instead of silently guessing
- keep scope narrow instead of absorbing adjacent tasks
- avoid speculative abstractions
- define verifiable success criteria
- loop through tests and evidence

## Required Backtests

For each Skill:

- 1 positive trigger eval
- 1 negative trigger eval
- 1 boundary/regression eval
- quick_validate
- local score script

For high-risk crawler/reverse Skills:

- stage-specific test
- WAF/business-error distinction
- site memory write-back
- version/change-log update

