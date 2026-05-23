"""字段豁免与容忍度规则。snapshot_diff 用本模块决定字段差异是否算失败。

两类规则:
  VOLATILE_FIELDS: 字段名集合。默认全局豁免(任何字段名在这里就跳过对比),
                   meta.yaml 的 volatile_fields 追加进来。
  TOLERANCE_RULES: 命名规则字典。meta.yaml 的 tolerance 引用规则名。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


VOLATILE_FIELDS: set[str] = {
    "sessionid", "session_id", "sess", "sessid",
    "requestid", "request_id", "rid", "req_id",
    "uuid", "guid", "id",
    "timestamp", "ts", "time", "now", "date", "datetime", "createdat", "created_at",
    "updatedat", "updated_at", "modifiedat", "modified_at",
    "token", "jwt", "csrf", "nonce", "csrftoken", "csrf_token",
    "traceid", "trace_id", "spanid", "span_id", "x_trace_id",
    "etag", "x_request_id", "x_amzn_requestid", "x_cache",
    "cookie", "set_cookie",
    "expires", "expiresin", "expires_in",
}


def _percent(threshold: float) -> Callable[[Any, Any], bool]:
    def cmp(old: Any, new: Any) -> bool:
        try:
            o, n = float(old), float(new)
        except (TypeError, ValueError):
            return False
        if o == 0:
            return n == 0
        return abs(o - n) / abs(o) < threshold
    return cmp


def _int_diff(max_diff: int) -> Callable[[Any, Any], bool]:
    def cmp(old: Any, new: Any) -> bool:
        try:
            return abs(int(old) - int(new)) <= max_diff
        except (TypeError, ValueError):
            return False
    return cmp


def _list_len_percent(threshold: float) -> Callable[[Any, Any], bool]:
    def cmp(old: Any, new: Any) -> bool:
        if not isinstance(old, list) or not isinstance(new, list):
            return False
        a, b = len(old), len(new)
        denom = max(a, 1)
        return abs(a - b) / denom < threshold
    return cmp


TOLERANCE_RULES: dict[str, Callable[[Any, Any], bool]] = {
    "exact": lambda a, b: a == b,
    "percent_5": _percent(0.05),
    "percent_10": _percent(0.10),
    "percent_20": _percent(0.20),
    "int_diff_5": _int_diff(5),
    "int_diff_20": _int_diff(20),
    "list_len_10pct": _list_len_percent(0.10),
    "list_len_20pct": _list_len_percent(0.20),
    "list_len_50pct": _list_len_percent(0.50),
    "ignore": lambda a, b: True,
}


def normalize_field_name(name: str) -> str:
    return name.lower().replace("-", "_").replace(" ", "_")


def is_volatile(field_name: str, extra_volatile: set[str] | None = None) -> bool:
    n = normalize_field_name(field_name)
    if n in VOLATILE_FIELDS:
        return True
    if extra_volatile and n in {normalize_field_name(x) for x in extra_volatile}:
        return True
    return False


def load_meta(path: Path) -> dict:
    if yaml is None:
        return {}
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def get_extra_volatile(meta: dict) -> set[str]:
    raw = meta.get("volatile_fields") or []
    return set(raw) if isinstance(raw, list) else set()


def get_tolerance_map(meta: dict) -> dict[str, str]:
    raw = meta.get("tolerance") or {}
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items() if v in TOLERANCE_RULES}


def match_tolerance_path(field_path: str, tolerance_map: dict[str, str]) -> str | None:
    """字段路径(如 'data.flights[].price')匹配 tolerance_map 中的 key。

    支持简化通配:
      - 精确匹配
      - 列表项匹配 (data.flights[].price 匹配 data.flights[0].price)
    """
    if field_path in tolerance_map:
        return tolerance_map[field_path]
    normalized = _normalize_list_index(field_path)
    if normalized in tolerance_map:
        return tolerance_map[normalized]
    return None


def _normalize_list_index(path: str) -> str:
    import re
    return re.sub(r"\[\d+\]", "[]", path)


def compare_value(old: Any, new: Any, tolerance_name: str | None) -> bool:
    if tolerance_name and tolerance_name in TOLERANCE_RULES:
        return TOLERANCE_RULES[tolerance_name](old, new)
    return old == new
