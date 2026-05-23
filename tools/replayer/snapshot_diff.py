"""比较单个 snapshot 的预期响应与实际响应,产 diff 报告与一致率。

输入:
  - snapshot resp.json (预期)
  - actual resp.json   (重放产物)
  - meta.yaml          (本接口的豁免与容忍度规则)

输出:
  dict {
    "total_fields": int,
    "matched": int,
    "mismatched": list[{"path", "expected", "actual", "reason"}],
    "missing": list[str],
    "extra": list[str],
    "structure_ok": bool,
    "consistency_rate": float,
    "status_match": bool,
  }
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools" / "replayer"))

from field_rules import (
    compare_value,
    get_extra_volatile,
    get_tolerance_map,
    is_volatile,
    load_meta,
    match_tolerance_path,
)


def walk_fields(obj: object, prefix: str = "") -> list[tuple[str, object]]:
    out: list[tuple[str, object]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                out.append((path, type(v).__name__))
                out.extend(walk_fields(v, path))
            else:
                out.append((path, v))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            path = f"{prefix}[{i}]"
            if isinstance(v, (dict, list)):
                out.append((path, type(v).__name__))
                out.extend(walk_fields(v, path))
            else:
                out.append((path, v))
    return out


def get_field(obj: object, path: str) -> tuple[bool, object]:
    """按 dot/[i] 路径取值。返回 (found, value)。"""
    if not path:
        return True, obj
    cur = obj
    i = 0
    n = len(path)
    token = ""
    while i < n:
        ch = path[i]
        if ch == ".":
            if token:
                if not isinstance(cur, dict) or token not in cur:
                    return False, None
                cur = cur[token]
                token = ""
            i += 1
        elif ch == "[":
            if token:
                if not isinstance(cur, dict) or token not in cur:
                    return False, None
                cur = cur[token]
                token = ""
            j = path.index("]", i)
            idx = int(path[i + 1 : j])
            if not isinstance(cur, list) or idx >= len(cur):
                return False, None
            cur = cur[idx]
            i = j + 1
        else:
            token += ch
            i += 1
    if token:
        if not isinstance(cur, dict) or token not in cur:
            return False, None
        cur = cur[token]
    return True, cur


def diff_snapshot(snapshot_resp: dict, actual_resp: dict, meta: dict) -> dict:
    extra_vol = get_extra_volatile(meta)
    tol_map = get_tolerance_map(meta)

    snap_status = snapshot_resp.get("status")
    actual_status = actual_resp.get("status")
    status_match = snap_status == actual_status

    snap_body = snapshot_resp.get("body")
    actual_body = actual_resp.get("body")

    snap_paths = {p: v for p, v in walk_fields(snap_body)}
    actual_paths = {p: v for p, v in walk_fields(actual_body)}

    matched = 0
    mismatched: list[dict] = []
    missing: list[str] = []
    extra: list[str] = []
    structure_ok = True

    for path, expected in snap_paths.items():
        leaf_name = path.split(".")[-1].split("[")[0]
        if is_volatile(leaf_name, extra_vol):
            continue

        if path not in actual_paths:
            missing.append(path)
            structure_ok = False
            continue

        actual_val = actual_paths[path]
        if type(expected).__name__ != type(actual_val).__name__:
            mismatched.append({
                "path": path,
                "expected": str(expected)[:80],
                "actual": str(actual_val)[:80],
                "reason": f"type mismatch ({type(expected).__name__} vs {type(actual_val).__name__})",
            })
            structure_ok = False
            continue

        if isinstance(expected, str) and expected in ("dict", "list"):
            matched += 1
            continue

        tol_name = match_tolerance_path(path, tol_map)
        if compare_value(expected, actual_val, tol_name):
            matched += 1
        else:
            mismatched.append({
                "path": path,
                "expected": str(expected)[:80],
                "actual": str(actual_val)[:80],
                "reason": f"value mismatch (tolerance={tol_name or 'exact'})",
            })

    for path in actual_paths:
        leaf_name = path.split(".")[-1].split("[")[0]
        if is_volatile(leaf_name, extra_vol):
            continue
        if path not in snap_paths:
            extra.append(path)

    total_compared = matched + len(mismatched) + len(missing)
    if total_compared == 0:
        # snapshot 没有任何可比字段 (空 body / 录制失败 / 二进制响应)
        # 不能算 100% PASS, 应该明示无数据
        rate = 0.0
        empty_snapshot = True
    else:
        rate = matched / total_compared
        empty_snapshot = False

    return {
        "status_match": status_match,
        "snapshot_status": snap_status,
        "actual_status": actual_status,
        "total_fields": total_compared,
        "matched": matched,
        "mismatched": mismatched,
        "missing": missing,
        "extra": extra,
        "structure_ok": structure_ok and status_match and not empty_snapshot,
        "consistency_rate": round(rate, 4),
        "empty_snapshot": empty_snapshot,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="diff snapshot vs actual response")
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--actual", required=True)
    parser.add_argument("--meta", default=None)
    parser.add_argument("--json", action="store_true", help="output as JSON")
    args = parser.parse_args()

    snap = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    act = json.loads(Path(args.actual).read_text(encoding="utf-8"))
    meta = load_meta(Path(args.meta)) if args.meta else {}

    result = diff_snapshot(snap, act, meta)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status: snapshot={result['snapshot_status']} actual={result['actual_status']}"
              f"  match={result['status_match']}")
        print(f"fields: matched={result['matched']}  mismatched={len(result['mismatched'])}"
              f"  missing={len(result['missing'])}  extra={len(result['extra'])}")
        print(f"structure_ok: {result['structure_ok']}")
        print(f"consistency_rate: {result['consistency_rate']:.2%}")
        if result["mismatched"]:
            print("\nMismatched:")
            for m in result["mismatched"][:20]:
                print(f"  {m['path']}: {m['reason']}")
                print(f"    expected: {m['expected']}")
                print(f"    actual:   {m['actual']}")
        if result["missing"]:
            print(f"\nMissing in actual: {result['missing'][:10]}")
        if result["extra"]:
            print(f"Extra in actual:   {result['extra'][:10]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
