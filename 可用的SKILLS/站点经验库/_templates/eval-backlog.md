# Eval Backlog Template

| Date | Domain | Market | Stage | Failure | Target Skill | Eval Type | Status |
|---|---|---|---|---|---|---|---|
| | | | | | | positive / negative / boundary | todo |

## Eval Types

- positive: should trigger and follow workflow
- negative: should not trigger
- boundary: should classify carefully
- regression: should prevent repeated mistake

## Promotion Rule

Backlog item should be moved into `evals/*.yaml` when:

- the failure repeated
- the failure caused wrong implementation
- the failure exposes a missing trigger word
- the failure distinguishes two similar skills

