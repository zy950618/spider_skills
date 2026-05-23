"""对 snapshot_diff.py 的 diff 结果做二次分类：BREAKING vs COMPATIBLE。

输入: snapshot_diff.py --json 产出的 JSON 文件 (单个 diff 或 list)

分类规则:
  BREAKING (破坏性):
    - 字段删除                  (missing 非空)
    - 字段类型变化              (mismatched 中 reason 含 "type mismatch")
    - 嵌套层级变化              (mismatched 中 expected/actual 是 "dict"/"list" 但对不上)
    - required 字段消失         (missing 中字段名在 meta.required 列表里)
    - status code 不匹配        (status_match=False)

  COMPATIBLE (兼容性扩展):
    - 字段新增                  (extra 非空)
    - 枚举值新增                (mismatched 中 reason 含 "value mismatch" 且 expected/actual 都是基本类型字符串)
    - optional 字段消失         (missing 中字段名不在 meta.required 列表里)

退出码:
  0 - 仅 COMPATIBLE 或无变更
  2 - 存在 BREAKING
  (异常静默 exit 0, 避免误阻断 CI)

CLI:
  python tools/replayer/schema_alert.py --input <diff.json> [--output <alert.md>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def classify_diff(diff: dict, required_fields: list[str] | None = None) -> dict:
    """对单个 diff 做分类。返回 {breaking: [...], compatible: [...], endpoint: str}."""
    required_fields = required_fields or []
    breaking: list[dict] = []
    compatible: list[dict] = []

    endpoint = diff.get("endpoint") or diff.get("name") or "<unknown>"

    if diff.get("status_match") is False:
        breaking.append({
            "kind": "status_code_change",
            "detail": f"snapshot={diff.get('snapshot_status')} actual={diff.get('actual_status')}",
        })

    for path in diff.get("missing", []) or []:
        leaf = path.rsplit(".", 1)[-1].split("[")[0]
        if leaf in required_fields or path in required_fields:
            breaking.append({"kind": "required_field_removed", "path": path})
        else:
            # 默认按 BREAKING 处理(字段删除一般是破坏性的);只有显式标 optional 才降级
            breaking.append({"kind": "field_removed", "path": path})

    for m in diff.get("mismatched", []) or []:
        reason = (m.get("reason") or "").lower()
        expected = str(m.get("expected", ""))
        actual = str(m.get("actual", ""))
        if "type mismatch" in reason:
            # 嵌套层级变化:expected/actual 是 dict/list 标记
            if expected in ("dict", "list") or actual in ("dict", "list"):
                breaking.append({
                    "kind": "nested_structure_change",
                    "path": m.get("path"),
                    "detail": reason,
                })
            else:
                breaking.append({
                    "kind": "type_change",
                    "path": m.get("path"),
                    "detail": reason,
                })
        elif "value mismatch" in reason:
            # 枚举值新增 / 业务值变化 -> COMPATIBLE(留给业务确认)
            compatible.append({
                "kind": "value_change",
                "path": m.get("path"),
                "expected": expected[:80],
                "actual": actual[:80],
            })
        else:
            # 未知 reason 保守判 COMPATIBLE,不阻断 CI
            compatible.append({
                "kind": "unknown_mismatch",
                "path": m.get("path"),
                "detail": reason or "(no reason)",
            })

    for path in diff.get("extra", []) or []:
        compatible.append({"kind": "field_added", "path": path})

    return {
        "endpoint": endpoint,
        "breaking": breaking,
        "compatible": compatible,
    }


def render_markdown(reports: list[dict]) -> str:
    lines: list[str] = []
    lines.append("# Schema Alert Report\n")
    total_breaking = sum(len(r["breaking"]) for r in reports)
    total_compatible = sum(len(r["compatible"]) for r in reports)
    lines.append(f"- endpoints scanned: {len(reports)}")
    lines.append(f"- BREAKING items: {total_breaking}")
    lines.append(f"- COMPATIBLE items: {total_compatible}\n")

    if total_breaking:
        lines.append("## BREAKING\n")
        for r in reports:
            if not r["breaking"]:
                continue
            lines.append(f"### {r['endpoint']}\n")
            for item in r["breaking"]:
                kind = item.get("kind", "?")
                path = item.get("path", "")
                detail = item.get("detail", "")
                lines.append(f"- **{kind}** `{path}` {detail}".rstrip())
            lines.append("")
        lines.append("### 建议处理\n")
        lines.append("- 字段删除 / 类型变化 / 嵌套层级变化 → 先与业务方确认是否故意下线")
        lines.append("- 若是上游 release 的非兼容变更 → 立即更新 adapter.yaml + fixtures + schema.json")
        lines.append("- 若是临时抖动 → 加入 known-failures.md 并补 retry/降级路径\n")

    if total_compatible:
        lines.append("## COMPATIBLE\n")
        for r in reports:
            if not r["compatible"]:
                continue
            lines.append(f"### {r['endpoint']}\n")
            for item in r["compatible"]:
                kind = item.get("kind", "?")
                path = item.get("path", "")
                if kind == "value_change":
                    lines.append(
                        f"- **{kind}** `{path}` expected=`{item.get('expected','')}` actual=`{item.get('actual','')}`"
                    )
                else:
                    detail = item.get("detail", "")
                    lines.append(f"- **{kind}** `{path}` {detail}".rstrip())
            lines.append("")
        lines.append("### 建议处理\n")
        lines.append("- 字段新增 / 枚举值新增 → 评估是否要在 schema.json 扩充字段定义")
        lines.append("- 不阻断 CI,但建议在下一次迭代里同步到 adapter\n")

    if not total_breaking and not total_compatible:
        lines.append("No schema changes detected.\n")

    return "\n".join(lines)


def load_input(path: Path) -> list[dict]:
    """支持单 diff 对象或 diff 列表。"""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        # 如果是 {endpoints: [...]} 包装,展开
        if "endpoints" in raw and isinstance(raw["endpoints"], list):
            return raw["endpoints"]
        return [raw]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify snapshot_diff results into BREAKING vs COMPATIBLE",
    )
    parser.add_argument("--input", required=True, help="snapshot_diff JSON file")
    parser.add_argument("--output", default=None, help="markdown report path")
    parser.add_argument(
        "--required-field",
        action="append",
        default=[],
        help="field name treated as required (can be passed multiple times)",
    )
    args = parser.parse_args()

    try:
        diffs = load_input(Path(args.input))
    except Exception as exc:
        # 异常静默:避免误阻断 CI
        print(f"[schema_alert] failed to load input: {exc}", file=sys.stderr)
        return 0

    reports = [classify_diff(d, args.required_field) for d in diffs]

    total_breaking = sum(len(r["breaking"]) for r in reports)
    total_compatible = sum(len(r["compatible"]) for r in reports)

    if args.output:
        try:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(render_markdown(reports), encoding="utf-8")
        except Exception as exc:
            print(f"[schema_alert] failed to write report: {exc}", file=sys.stderr)

    if total_breaking:
        print(
            f"[schema_alert] BREAKING={total_breaking} COMPATIBLE={total_compatible}",
            file=sys.stderr,
        )
        for r in reports:
            for item in r["breaking"]:
                print(
                    f"  [BREAKING] {r['endpoint']}: {item.get('kind')} {item.get('path','')} {item.get('detail','')}".rstrip(),
                    file=sys.stderr,
                )
        print(
            "  Suggested: confirm with upstream; update adapter.yaml + fixtures + schema.json",
            file=sys.stderr,
        )
        return 2

    print(f"[schema_alert] OK  BREAKING=0  COMPATIBLE={total_compatible}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        # 顶层兜底:任何未捕获异常都不阻断 CI
        print(f"[schema_alert] unexpected error: {exc}", file=sys.stderr)
        sys.exit(0)
