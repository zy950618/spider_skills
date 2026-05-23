"""聚合一个 domain 下所有 snapshot 的 diff 结果,出 markdown 报告 + 更新 trend.json。

依赖 snapshot_diff.py。

用法:
  python tools/replayer/consistency_report.py --domain thaiairways.com

输出:
  - 站点经验库/<domain>/fixtures/reports/<YYYY-MM-DD>-replay.md
  - 站点经验库/<domain>/fixtures/reports/trend.json
  - stdout: 摘要 (供 CI 决定是否开 issue)
  - 退出码: 一致率 >= --threshold 返回 0,否则返回 3
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_ROOT = REPO_ROOT / "站点经验库"
sys.path.insert(0, str(REPO_ROOT / "tools" / "replayer"))

from snapshot_diff import diff_snapshot
from field_rules import load_meta


def render_report(domain: str, results: list[dict], overall: dict) -> str:
    date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# 一致性重放报告 — {domain}",
        "",
        f"- 生成时间: {date}",
        f"- snapshots 总数: {overall['total']}",
        f"- 重放成功: {overall['replayed']}",
        f"- 结构通过: {overall['structure_ok']} / {overall['replayed']}",
        f"- empty snapshot (不进分母): {overall.get('empty_snapshot_count', 0)}",
        f"- **整体一致率: {overall['consistency_rate']:.2%}**" +
            (" (NO_DATA: 所有 snapshot 都是空,无法计算)" if overall['status'] == 'NO_DATA' else ""),
        f"- 状态: {overall['status']}",
        "",
        "## 单 endpoint 明细",
        "",
        "| Endpoint | Status | Fields | Matched | Mismatch | Missing | Extra | Rate |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        if r.get("empty_snapshot"):
            status = "SKIP"
        elif r["structure_ok"] and r["consistency_rate"] >= 0.95:
            status = "PASS"
        elif r["consistency_rate"] >= 0.80:
            status = "WARN"
        else:
            status = "FAIL"
        status_str = f"{r.get('snapshot_status', '-')}→{r.get('actual_status', '-')}"
        rate_str = "EMPTY" if r.get("empty_snapshot") else f"{r['consistency_rate']:.1%}"
        lines.append(
            f"| `{r['endpoint']}` | {status_str} | {r['total_fields']} | {r['matched']} "
            f"| {len(r['mismatched'])} | {len(r['missing'])} | {len(r['extra'])} "
            f"| {rate_str} [{status}] |"
        )

    fails = [r for r in results if not r.get("empty_snapshot") and (not r["structure_ok"] or r["consistency_rate"] < 0.95)]
    if fails:
        lines.append("")
        lines.append("## 失败 / 警告详情")
        for r in fails:
            lines.append("")
            lines.append(f"### `{r['endpoint']}` — 一致率 {r['consistency_rate']:.1%}")
            if not r["status_match"]:
                lines.append(
                    f"- **HTTP status 不匹配**: snapshot={r['snapshot_status']} actual={r['actual_status']}"
                )
            if r["missing"]:
                lines.append(f"- 缺失字段 ({len(r['missing'])}): `{', '.join(r['missing'][:5])}`"
                             f"{'...' if len(r['missing']) > 5 else ''}")
            if r["extra"]:
                lines.append(f"- 多余字段 ({len(r['extra'])}): `{', '.join(r['extra'][:5])}`"
                             f"{'...' if len(r['extra']) > 5 else ''}")
            if r["mismatched"]:
                lines.append(f"- 字段值不一致 ({len(r['mismatched'])}):")
                for m in r["mismatched"][:5]:
                    lines.append(f"  - `{m['path']}`: {m['reason']}")
                    lines.append(f"    - expected: `{m['expected']}`")
                    lines.append(f"    - actual:   `{m['actual']}`")

    empties = [r for r in results if r.get("empty_snapshot")]
    if empties:
        lines.append("")
        lines.append("## empty snapshot (录制时没拿到 body, 跳过比对)")
        for r in empties[:10]:
            lines.append(f"- `{r['endpoint']}` (actual extra fields: {len(r['extra'])})")
        if len(empties) > 10:
            lines.append(f"- ... 共 {len(empties)} 个")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("脚本: `tools/replayer/consistency_report.py`")
    return "\n".join(lines) + "\n"


def update_trend(trend_file: Path, overall: dict) -> None:
    trend = {"entries": []}
    if trend_file.exists():
        try:
            trend = json.loads(trend_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    if "entries" not in trend:
        trend["entries"] = []
    trend["entries"].append({
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "consistency_rate": overall["consistency_rate"],
        "total": overall["total"],
        "replayed": overall["replayed"],
        "structure_ok": overall["structure_ok"],
        "status": overall["status"],
    })
    if len(trend["entries"]) > 200:
        trend["entries"] = trend["entries"][-200:]
    trend_file.write_text(json.dumps(trend, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="聚合 diff 出 markdown 报告 + trend.json")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--threshold", type=float, default=0.90,
                        help="一致率阈值, 低于此值退出码 3 (CI 用)")
    args = parser.parse_args()

    fix_dir = SITE_ROOT / args.domain / "fixtures"
    snap_dir = fix_dir / "snapshots"
    actual_dir = fix_dir / "actual"
    reports_dir = fix_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not snap_dir.is_dir():
        print(f"ERROR: {snap_dir} not found", file=sys.stderr)
        return 1
    if not actual_dir.is_dir():
        print(f"ERROR: {actual_dir} not found. 先跑 snapshot_replay.py", file=sys.stderr)
        return 1

    req_files = sorted(snap_dir.glob("*.req.json"))
    results: list[dict] = []
    total_matched = 0
    total_compared = 0
    replayed = 0
    structure_ok_count = 0
    empty_count = 0

    for req_file in req_files:
        prefix = req_file.stem[:-4]
        resp_file = snap_dir / f"{prefix}.resp.json"
        actual_file = actual_dir / f"{prefix}.actual.json"
        meta_file = snap_dir / f"{prefix}.meta.yaml"

        if not actual_file.exists():
            results.append({
                "endpoint": prefix,
                "skipped": True,
                "snapshot_status": "-", "actual_status": "-",
                "total_fields": 0, "matched": 0,
                "mismatched": [], "missing": [], "extra": [],
                "structure_ok": False, "consistency_rate": 0.0,
                "status_match": False, "empty_snapshot": False,
            })
            continue

        try:
            snap = json.loads(resp_file.read_text(encoding="utf-8"))
            act = json.loads(actual_file.read_text(encoding="utf-8"))
            meta = load_meta(meta_file) if meta_file.exists() else {}
        except Exception as e:
            print(f"  parse fail {prefix}: {e}")
            continue

        d = diff_snapshot(snap, act, meta)
        d["endpoint"] = prefix
        results.append(d)
        replayed += 1

        # empty_snapshot 不进一致率分母 (snapshot 录制时没拿到 body)
        if d.get("empty_snapshot"):
            empty_count += 1
            continue

        total_matched += d["matched"]
        total_compared += d["total_fields"]
        if d["structure_ok"]:
            structure_ok_count += 1

    overall_rate = total_matched / total_compared if total_compared else 0.0
    if total_compared == 0:
        status_label = "NO_DATA"
    elif overall_rate >= args.threshold:
        status_label = "PASS"
    elif overall_rate >= 0.80:
        status_label = "WARN"
    else:
        status_label = "FAIL"

    overall = {
        "total": len(req_files),
        "replayed": replayed,
        "structure_ok": structure_ok_count,
        "empty_snapshot_count": empty_count,
        "consistency_rate": round(overall_rate, 4),
        "status": status_label,
    }

    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    report_file = reports_dir / f"{date_str}-replay.md"
    report_file.write_text(render_report(args.domain, results, overall), encoding="utf-8")
    update_trend(reports_dir / "trend.json", overall)

    print(f"\n=== {args.domain} ===")
    print(f"replayed: {replayed}/{len(req_files)}")
    print(f"structure_ok: {structure_ok_count}/{replayed}")
    print(f"consistency_rate: {overall_rate:.2%}  [{status_label}]")
    print(f"report: {report_file}")

    return 0 if overall_rate >= args.threshold else 3


if __name__ == "__main__":
    sys.exit(main())
