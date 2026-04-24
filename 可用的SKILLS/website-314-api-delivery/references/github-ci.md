# GitHub CI For Skill Bench

## When To Use

Use GitHub CI when the Skills should be scored automatically on pull requests or on a schedule.

Local Obsidian paths are not visible to GitHub runners. Mirror the Skills into a repository-visible folder:

```text
repo/
  skills/
    website-314-api-delivery/
    reverse-js-crawler/
    imperva-waf-reese84/
    site-api-adapter/
    skills-evaluation-governance/
  .github/
    workflows/
      skill-bench.yml
```

## Repository Setup

1. Create a private repository, for example `crawler-skills`.
2. Copy each Skill folder under `skills/`.
3. Do not commit real cookies, tokens, payment data, passenger data, or private proxy credentials.
4. Add repository secret:

```text
ANTHROPIC_API_KEY
```

## Workflow Example

```yaml
name: Skill Bench

on:
  pull_request:
    paths:
      - "skills/**"
      - ".github/workflows/skill-bench.yml"
  schedule:
    - cron: "0 2 * * 1"
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: write

jobs:
  skill-bench:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        skill:
          - website-314-api-delivery
          - reverse-js-crawler
          - imperva-waf-reese84
          - site-api-adapter
          - skills-evaluation-governance
    steps:
      - uses: actions/checkout@v6
        with:
          persist-credentials: false
      - uses: skill-bench/skill-eval-action@v1
        with:
          skill-name: ${{ matrix.skill }}
          skill-path: skills/${{ matrix.skill }}
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          pass-threshold: "80"
          timeout: "120"
```

## Operating Rule

- PR run catches regressions before merging Skill changes.
- Weekly schedule catches drift.
- Manual dispatch tests urgent changes.
- Failing evals must be classified: bad Skill, bad eval, changed model behavior, or changed domain reality.
- Run quick_validate locally before opening a PR so formatting errors are caught before GitHub CI.
