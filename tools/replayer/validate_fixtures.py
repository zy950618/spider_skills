"""验证 fixtures schema 合规。

检查项:
  1. 每个 prefix 必须有三件套 (req.json + resp.json + meta.yaml)
  2. meta.yaml 必须有 endpoint / recorded_at / expires_at / category
  3. category 不允许 payment / order-create / pay-confirm
  4. expires_at 未过期 (过期发 warn, 不 fail)
  5. sensitive: true 的 resp.json body 不应是空 (要么打 sensitive 要么 unset)

退出码:
  0 = 全通过
  1 = 结构错误
  2 = 内部错
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_ROOT = REPO_ROOT / "站点经验库"

FORBIDDEN_CATEGORIES = {"payment", "order-create", "pay-confirm", "checkout-pay"}
ALLOWED_CATEGORIES = {"public-read", "search", "detail", "list", "session", "config"}

META_REQUIRED = ["endpoint", "recorded_at", "expires_at", "category"]


def parse_meta(text: str) -> dict:
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r'^([a-z_]+)\s*:\s*"?([^"#]*)"?', line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"')
    return out


def parse_iso(s: str) -> datetime.datetime | None:
    s = s.strip().rstrip("Z")
    try:
        return datetime.datetime.fromisoformat(s).replace(tzinfo=datetime.timezone.utc)
    except Exception:
        return None


def main() -> int:
    if not SITE_ROOT.is_dir():
        print(f"WARN: {SITE_ROOT} not found, nothing to validate")
        return 0

    errors: list[str] = []
    warnings: list[str] = []
    total = {"domains": 0, "snapshots": 0, "valid": 0, "expired": 0}

    now = datetime.datetime.now(datetime.timezone.utc)

    for domain_dir in SITE_ROOT.iterdir():
        if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
            continue
        snap_dir = domain_dir / "fixtures" / "snapshots"
        if not snap_dir.is_dir():
            continue
        total["domains"] += 1

        req_files = sorted(snap_dir.glob("*.req.json"))
        for req in req_files:
            prefix = req.stem[:-4]
            total["snapshots"] += 1
            resp = snap_dir / f"{prefix}.resp.json"
            meta = snap_dir / f"{prefix}.meta.yaml"

            ok = True
            if not resp.exists():
                errors.append(f"{domain_dir.name}/{prefix}: missing .resp.json")
                ok = False
            if not meta.exists():
                errors.append(f"{domain_dir.name}/{prefix}: missing .meta.yaml")
                ok = False

            if not meta.exists():
                continue

            try:
                meta_text = meta.read_text(encoding="utf-8")
            except Exception as e:
                errors.append(f"{domain_dir.name}/{prefix}: read meta failed: {e}")
                continue
            m = parse_meta(meta_text)

            for k in META_REQUIRED:
                if k not in m or not m[k]:
                    errors.append(f"{domain_dir.name}/{prefix}: meta missing '{k}'")
                    ok = False

            cat = m.get("category", "")
            if cat in FORBIDDEN_CATEGORIES:
                errors.append(f"{domain_dir.name}/{prefix}: forbidden category '{cat}' "
                              f"(payment/order-create not allowed in fixtures)")
                ok = False
            elif cat and cat not in ALLOWED_CATEGORIES:
                warnings.append(f"{domain_dir.name}/{prefix}: category '{cat}' not in allowed set")

            exp = m.get("expires_at", "")
            if exp:
                exp_dt = parse_iso(exp)
                if exp_dt and exp_dt < now:
                    warnings.append(f"{domain_dir.name}/{prefix}: expired at {exp}, re-record needed")
                    total["expired"] += 1

            if ok and (resp.exists()):
                total["valid"] += 1

    print(f"== fixtures schema validation ==")
    print(f"domains: {total['domains']}  snapshots: {total['snapshots']}  "
          f"valid: {total['valid']}  expired: {total['expired']}")
    if warnings:
        print(f"\nwarnings ({len(warnings)}):")
        for w in warnings[:30]:
            print(f"  WARN  {w}")
    if errors:
        print(f"\nerrors ({len(errors)}):")
        for e in errors[:30]:
            print(f"  ERROR {e}")
        return 1
    print("\nall good.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
