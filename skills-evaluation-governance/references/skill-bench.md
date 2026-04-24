# Skill Bench

## Minimum Layout

```text
skill-name/
  SKILL.md
  evals/*.yaml
```

Recommended:

```text
skill-name/
  agents/openai.yaml
  references/*.md
```

## Eval Design

Each eval should include:

- `name`
- `prompt`
- `criteria`
- `expect_skill`
- `timeout`

Use both:

- should-trigger prompts
- should-not-trigger prompts

## CI Notes

GitHub Actions runners cannot see local Obsidian or `$CODEX_HOME` paths unless mirrored into the repository. Keep a repo-visible copy when official Skill Bench CI is required.

