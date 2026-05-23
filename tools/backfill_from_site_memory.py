"""从站点经验库反推真实任务下限,写入对应 Skill 的 metrics/real-task-summary.md。

逻辑:
  - 扫 站点经验库/<domain>/{known-failures,test-log-lessons,change-log}.md
  - known-failures: 每个 '## Failure:' 算一次真实任务接触
  - test-log-lessons: 每个 '## Pattern:' 或 '## Lesson:' 算一次
  - change-log: 表格里每条版本算一次 (跳过表头与分隔行)
  - 任务下限 = 三者去重后求和
  - 写进指定 Skill 的 metrics/real-task-summary.md,标 "extracted from site memory"

设计原则:
  - 不假装真实数据,标明 "下限" 与来源
  - 只追加新增段落,不覆盖现有内容 (除非显式 --rewrite)
  - dry-run 默认,--apply 才写
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_ROOT = REPO_ROOT / "站点经验库"

FAILURE_RE = re.compile(r"^##\s+Failure[:：]", re.MULTILINE)
LESSON_RE = re.compile(r"^##\s+(?:Pattern|Lesson)[:：]", re.MULTILINE)
CHANGE_TABLE_ROW_RE = re.compile(
    r"^\|\s*(?:\d+\.\d+\.\d+|\d{4}-\d{2}-\d{2}|v?\d+)\s*\|", re.MULTILINE
)

BACKFILL_MARK = "<!-- backfill-from-site-memory:start -->"
BACKFILL_END = "<!-- backfill-from-site-memory:end -->"


def count_failures(path: Path) -> int:
    if not path.exists():
        return 0
    return len(FAILURE_RE.findall(path.read_text(encoding="utf-8", errors="replace")))


def count_lessons(path: Path) -> int:
    if not path.exists():
        return 0
    return len(LESSON_RE.findall(path.read_text(encoding="utf-8", errors="replace")))


def count_changes(path: Path) -> int:
    if not path.exists():
        return 0
    return len(CHANGE_TABLE_ROW_RE.findall(path.read_text(encoding="utf-8", errors="replace")))


def collect_domain(domain: str) -> dict:
    domain_dir = SITE_ROOT / domain
    if not domain_dir.is_dir():
        return {"domain": domain, "exists": False}

    failures = count_failures(domain_dir / "known-failures.md")
    lessons = count_lessons(domain_dir / "test-log-lessons.md")
    changes = count_changes(domain_dir / "change-log.md")
    lower_bound = failures + lessons + changes
    return {
        "domain": domain,
        "exists": True,
        "failures": failures,
        "lessons": lessons,
        "changes": changes,
        "lower_bound": lower_bound,
    }


def render_block(stats: list[dict]) -> str:
    ts = datetime.datetime.now().strftime("%Y-%m-%d")
    lines = [
        BACKFILL_MARK,
        "",
        f"## 真实任务下限(从站点经验库反推 / {ts})",
        "",
        "> 数据来自 `站点经验库/<domain>/`,每个失败模式 / 测试教训 / change-log 版本视为至少一次真实任务接触。",
        "> 这不是严格命中率,只是「已发生过的真实任务下限」。脚本: `tools/backfill_from_site_memory.py`。",
        "",
        "| domain | 已知失败 | 测试教训 | 变更版本 | 任务下限 |",
        "|---|---:|---:|---:|---:|",
    ]
    total = 0
    for s in stats:
        if not s.get("exists"):
            lines.append(f"| {s['domain']} | - | - | - | - (站点目录不存在) |")
            continue
        lines.append(
            f"| {s['domain']} | {s['failures']} | {s['lessons']} | {s['changes']} | {s['lower_bound']} |"
        )
        total += s["lower_bound"]
    lines.append("")
    lines.append(f"- 真实任务下限: {total}")
    lines.append(f"- 触发命中: ≥ {total} (站点经验记录意味着 Skill 至少触发过 {total} 次)")
    lines.append("- 成功率: 待补 (反推数据不包含成功/失败比例)")
    lines.append("")
    lines.append(BACKFILL_END)
    return "\n".join(lines) + "\n"


def update_metrics_file(metrics: Path, block: str, rewrite: bool, apply: bool) -> str:
    if not metrics.exists():
        if not apply:
            return f"[dry-run] 会创建 {metrics} 并写入反推段落"
        metrics.parent.mkdir(parents=True, exist_ok=True)
        header = "---\ntitle: 真实任务统计\ntags:\n  - metrics\n  - real-task\n---\n\n"
        metrics.write_text(header + block, encoding="utf-8")
        return f"[apply] 已创建 {metrics}"

    current = metrics.read_text(encoding="utf-8", errors="replace")
    if BACKFILL_MARK in current and BACKFILL_END in current:
        if not rewrite:
            return f"[skip] {metrics} 已有反推段,加 --rewrite 强制覆盖"
        new = re.sub(
            re.escape(BACKFILL_MARK) + r".*?" + re.escape(BACKFILL_END) + r"\n?",
            block,
            current,
            count=1,
            flags=re.DOTALL,
        )
        if not apply:
            return f"[dry-run] 会覆盖 {metrics} 现有反推段"
        metrics.write_text(new, encoding="utf-8")
        return f"[apply] 已覆盖 {metrics} 反推段"

    if not apply:
        return f"[dry-run] 会在 {metrics} 末尾追加反推段"
    metrics.write_text(current.rstrip() + "\n\n" + block, encoding="utf-8")
    return f"[apply] 已追加到 {metrics}"


def main() -> int:
    parser = argparse.ArgumentParser(description="从站点经验库反推真实任务下限")
    parser.add_argument(
        "--domain",
        action="append",
        required=True,
        help="域名,可多次 (例: --domain thaiairways.com)",
    )
    parser.add_argument(
        "--skill-metrics",
        required=True,
        help="目标 metrics/real-task-summary.md 绝对或相对路径",
    )
    parser.add_argument("--apply", action="store_true", help="真实写入 (默认 dry-run)")
    parser.add_argument("--rewrite", action="store_true", help="覆盖已有反推段")
    args = parser.parse_args()

    metrics = Path(args.skill_metrics)
    if not metrics.is_absolute():
        metrics = REPO_ROOT / metrics

    stats = [collect_domain(d) for d in args.domain]

    print(f"目标文件: {metrics}\n")
    for s in stats:
        if not s.get("exists"):
            print(f"  WARN: {s['domain']} 站点目录不存在")
            continue
        print(
            f"  {s['domain']}: failures={s['failures']} "
            f"lessons={s['lessons']} changes={s['changes']} "
            f"lower_bound={s['lower_bound']}"
        )

    block = render_block(stats)
    print("\n--- 反推段落预览 ---")
    print(block)
    print("--- end ---\n")

    result = update_metrics_file(metrics, block, args.rewrite, args.apply)
    print(result)
    if not args.apply:
        print("\n加 --apply 真实写入。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
