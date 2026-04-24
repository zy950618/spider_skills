# Test Log Mining

## Purpose

Normal testing should produce reusable knowledge. Do not wait for production incidents. Extract failure patterns from service tests, HTTP API tests, stability loops, WAF tests, and payment dry-run tests.

## Required Extraction

For every failed or surprising test, extract:

- domain
- market
- locale
- currency
- stage
- endpoint/path
- input summary
- normalized upstream payload summary
- session_id / trace_id
- status code
- content type
- business code/message
- raw marker
- failure class
- root cause
- correct handling
- related Skill
- eval backlog entry

## Failure Classes

Use this fixed vocabulary:

- route-decision
- business-error
- payload-mapping
- js-crypto
- browser-env
- waf
- proxy-ip
- session-cache
- 314-integration
- payment-risk
- test-data

## Write-Back Targets

Write extracted lessons to:

```text
../站点经验库/<domain>/known-failures.md
../站点经验库/<domain>/test-log-lessons.md
../站点经验库/<domain>/eval-backlog.md
../站点经验库/<domain>/change-log.md
```

If the failure is market-specific, also update:

```text
../站点经验库/<domain>/market-matrix.md
```

If the failure is caused by official frontend routing or rollout, also update:

```text
../站点经验库/<domain>/route-decisions.md
```

## Promotion To Skill

Promote a site lesson into Skill files when:

- the same failure repeats
- it affects more than one market or site
- it causes a wrong implementation decision
- it distinguishes two Skills
- it exposes a missing trigger word

Promotion targets:

- `SKILL.md` for trigger or workflow changes
- `references/*.md` for reusable details
- `evals/*.yaml` for regression tests
- `references/governance.md` for version and change log

