"""给指定 Skill 生成 evals/ 与 agents/openai.yaml 的骨架。

读 SKILL.md frontmatter 提取 description,生成:
  - agents/openai.yaml (如不存在)
  - evals/001-positive-<slug>.yaml (占位)
  - evals/002-negative-<slug>.yaml (占位)
  - evals/003-regression-<slug>.yaml (占位)

骨架文件 name 字段以 "TODO:" 开头,后续由 agent 填真实 case。
已存在的文件不覆盖。

用法:
  python tools/scaffold_evals.py --skill 2-JS逆向工具层/find-crypto-entry
  python tools/scaffold_evals.py --skill 3-移动逆向工具层/rev-frida --force
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm: dict[str, str] = {}
    current_key = None
    for raw in m.group(1).splitlines():
        if not raw:
            continue
        if raw[0] not in (" ", "\t") and ":" in raw:
            k, _, v = raw.partition(":")
            fm[k.strip()] = v.strip()
            current_key = k.strip()
        elif current_key:
            fm[current_key] = fm[current_key] + " " + raw.strip()
    return fm, m.group(2)


def short_summary(description: str, limit: int = 100) -> str:
    s = re.split(r"(?:[.。]|TRIGGER|DO NOT)", description, maxsplit=1)[0].strip()
    if not s:
        s = description.strip()
    if len(s) > limit:
        s = s[: limit - 1].rstrip() + "…"
    return s.replace('"', "'")


def write_if_missing(path: Path, content: str, force: bool) -> str:
    if path.exists() and not force:
        return f"[skip] {path.relative_to(REPO_ROOT)} 已存在"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"[write] {path.relative_to(REPO_ROOT)}"


def scaffold(skill_dir: Path, force: bool) -> int:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"ERROR: {skill_md} 不存在", file=sys.stderr)
        return 1

    fm, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
    name = fm.get("name", skill_dir.name)
    desc = fm.get("description", "")
    summary = short_summary(desc)

    agents_yaml = skill_dir / "agents" / "openai.yaml"
    agents_content = (
        "interface:\n"
        f'  display_name: "{name}"\n'
        f'  short_description: "{summary}"\n'
        f'  default_prompt: "TODO: write a representative prompt that should activate {name}."\n'
    )
    print(write_if_missing(agents_yaml, agents_content, force))

    eval_specs = [
        (
            "001-positive-placeholder.yaml",
            True,
            f"TODO positive case for {name}",
            f"TODO: write a prompt that should activate {name}.",
            [
                f"TODO: criterion describing the workflow {name} should follow",
                "TODO: criterion describing required outputs / evidence",
                "TODO: criterion describing site-memory / known-failures writeback",
            ],
        ),
        (
            "002-negative-placeholder.yaml",
            False,
            f"TODO negative case for {name}",
            f"TODO: write a prompt that should NOT activate {name}.",
            [
                f"TODO: criterion describing why {name} should stay silent",
                "TODO: criterion describing the correct alternative behavior",
            ],
        ),
        (
            "003-regression-placeholder.yaml",
            True,
            f"TODO regression case for {name}",
            f"TODO: write a regression prompt drawn from a real failure of {name}.",
            [
                "TODO: criterion describing detection of the historical failure mode",
                "TODO: criterion describing the correct handling",
                "TODO: criterion describing site-memory writeback to prevent repeat",
            ],
        ),
    ]

    for filename, expect, eval_name, prompt, criteria in eval_specs:
        path = skill_dir / "evals" / filename
        criteria_lines = "\n".join(f'  - "{c}"' for c in criteria)
        body = (
            f"name: {eval_name}\n"
            f"prompt: >\n"
            f"  {prompt}\n"
            f"criteria:\n"
            f"{criteria_lines}\n"
            f"expect_skill: {str(expect).lower()}\n"
            f"timeout: 120\n"
        )
        print(write_if_missing(path, body, force))

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="为 Skill 生成 evals/agents 骨架")
    parser.add_argument(
        "--skill",
        required=True,
        action="append",
        help="Skill 目录相对仓库根的路径 (可多次)",
    )
    parser.add_argument("--force", action="store_true", help="覆盖已有骨架文件")
    args = parser.parse_args()

    failed = 0
    for s in args.skill:
        skill_dir = (REPO_ROOT / s).resolve()
        if not skill_dir.is_dir():
            print(f"ERROR: {skill_dir} 不是目录", file=sys.stderr)
            failed += 1
            continue
        print(f"\n=== {s} ===")
        rc = scaffold(skill_dir, args.force)
        if rc != 0:
            failed += 1
    return failed


if __name__ == "__main__":
    sys.exit(main())
