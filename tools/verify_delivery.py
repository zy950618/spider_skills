"""verify_delivery.py: 完成度 5 维自验工具

声明"完成"前 Claude 主动跑。规则源 99-SKILLS治理/08-完成度自评.md。

返回 exit_code: 0 = 通过(或仅跳 1 维) / 2 = 跳 ≥2 维,不许声明完成
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_REPO_ROOT = SCRIPT_DIR.parent
SITE_MEMORY_DIR = "站点经验库"

# 与 08-完成度自评.md 一致的窗口:近 1h
RECENT_WINDOW_SEC = 3600
# 集成层 mtime 容差:transcript mtime - 7200 秒之后算"任务期间"
INTEGRATION_MTIME_TOLERANCE_SEC = 7200

# Regression 关键词
REGRESSION_MARKERS = (
    "score_skills",
    "ci_gate",
    "pytest",
    "测试通过",
    "test pass",
)

# Honesty 关键词(在 transcript 文本末尾 3000 字符内扫)
HONESTY_MARKERS = (
    "没验证",
    "未验证",
    "not verified",
    "未在干净环境",
    "blockers",
    "局限",
)


# ---------------------------------------------------------------------------
# transcript 定位与解析
# ---------------------------------------------------------------------------

def find_latest_transcript() -> Path | None:
    """从 ~/.claude/projects/ 找最近 mtime 的 .jsonl"""
    base = Path.home() / ".claude" / "projects"
    if not base.exists():
        return None
    candidates: list[Path] = []
    for p in base.rglob("*.jsonl"):
        try:
            candidates.append(p)
        except Exception:
            continue
    if not candidates:
        return None
    try:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    except Exception:
        return None


def load_transcript(path: Path | None) -> list[dict]:
    if path is None or not path.exists():
        return []
    events: list[dict] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return events
    return events


def event_ts(ev: dict) -> float | None:
    """从一条 transcript 事件里取 unix 时间戳(秒)"""
    ts = ev.get("timestamp") or ev.get("ts")
    if not ts:
        return None
    if isinstance(ts, (int, float)):
        # 毫秒兜底
        return float(ts) / 1000.0 if ts > 10_000_000_000 else float(ts)
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            return None
    return None


def iter_content_blocks(events: list[dict]):
    """遍历 (event_ts, block) 元组,只产出 dict 类型的 content block"""
    for ev in events:
        ts = event_ts(ev)
        msg = ev.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict):
                    yield ts, c, ev


def extract_text(events: list[dict]) -> str:
    """抽 transcript 全文(text / tool_use input / tool_result content)"""
    parts: list[str] = []
    for _, c, _ev in iter_content_blocks(events):
        t = c.get("type")
        if t == "text":
            parts.append(str(c.get("text", "")))
        elif t == "tool_use":
            ti = c.get("input")
            if isinstance(ti, dict):
                for v in ti.values():
                    if isinstance(v, str):
                        parts.append(v)
        elif t == "tool_result":
            r = c.get("content")
            if isinstance(r, str):
                parts.append(r)
            elif isinstance(r, list):
                for rr in r:
                    if isinstance(rr, dict) and rr.get("type") == "text":
                        parts.append(str(rr.get("text", "")))
    return "\n".join(parts)


def transcript_mtime(path: Path | None) -> float:
    """transcript 文件 mtime;找不到就用 now"""
    if path is not None:
        try:
            return path.stat().st_mtime
        except Exception:
            pass
    return time.time()


# ---------------------------------------------------------------------------
# 5 维检查
# ---------------------------------------------------------------------------

def check_code(events: list[dict], now: float, blockers: list[str]) -> int:
    """1. Code: 近 1h 有成功的 bash tool_use(对应 tool_result 不是 is_error)"""
    # 第一遍:收集近 1h 的 bash tool_use_id
    bash_ids: set[str] = set()
    for ts, c, _ev in iter_content_blocks(events):
        if ts is not None and (now - ts) > RECENT_WINDOW_SEC:
            continue
        if c.get("type") != "tool_use":
            continue
        name = (c.get("name") or "").lower()
        if name in ("bash",):
            tid = c.get("id")
            if isinstance(tid, str):
                bash_ids.add(tid)
    if not bash_ids:
        blockers.append("Code: 近 1h transcript 内未发现 bash tool_use 调用")
        return 0
    # 第二遍:看对应 tool_result 是否非错误
    succeeded = False
    for _ts, c, _ev in iter_content_blocks(events):
        if c.get("type") != "tool_result":
            continue
        tid = c.get("tool_use_id")
        if tid not in bash_ids:
            continue
        if c.get("is_error") is True:
            continue
        succeeded = True
        break
    if not succeeded:
        blockers.append("Code: 近 1h bash tool_use 都没成功的 tool_result")
        return 0
    return 1


def check_docs(events: list[dict], now: float, blockers: list[str]) -> int:
    """2. Docs: 近 1h 有 Read tool_use 且 path 以 .md 结尾"""
    for ts, c, _ev in iter_content_blocks(events):
        if ts is not None and (now - ts) > RECENT_WINDOW_SEC:
            continue
        if c.get("type") != "tool_use":
            continue
        name = (c.get("name") or "").lower()
        if name != "read":
            continue
        ti = c.get("input")
        if not isinstance(ti, dict):
            continue
        # 兼容 file_path / path
        path = ti.get("file_path") or ti.get("path") or ""
        if isinstance(path, str) and path.lower().endswith(".md"):
            return 1
    blockers.append("Docs: 近 1h 内未发现 Read 任何 .md 文件")
    return 0


def check_integration(
    domain: str,
    repo_root: Path,
    transcript_mt: float,
    blockers: list[str],
) -> int:
    """3. Integration: 若 domain != none,看 site memory 关键文件 mtime"""
    if domain == "none":
        return 1
    site_dir = repo_root / SITE_MEMORY_DIR / domain
    if not site_dir.exists():
        blockers.append(
            f"Integration: {SITE_MEMORY_DIR}/{domain}/ 目录不存在(还未从 _templates/ 复制?)"
        )
        return 0
    threshold = transcript_mt - INTEGRATION_MTIME_TOLERANCE_SEC
    candidates = ("test-log-lessons.md", "known-failures.md")
    updated: list[str] = []
    for name in candidates:
        f = site_dir / name
        try:
            mt = f.stat().st_mtime
        except FileNotFoundError:
            continue
        except Exception:
            continue
        if mt >= threshold:
            updated.append(name)
    if updated:
        return 1
    blockers.append(
        f"Integration: {SITE_MEMORY_DIR}/{domain}/test-log-lessons.md 或 known-failures.md "
        f"在本次任务期间无 mtime 更新"
    )
    return 0


def check_regression(text: str, blockers: list[str]) -> int:
    """4. Regression: transcript 全文里出现回归检查关键词"""
    lower = text.lower()
    for kw in REGRESSION_MARKERS:
        if kw.lower() in lower:
            return 1
    blockers.append(
        "Regression: transcript 未出现 score_skills / ci_gate / pytest / 测试通过 等回归动作"
    )
    return 0


def check_honesty(text: str, blockers: list[str]) -> int:
    """5. Honesty: transcript 末尾 3000 字符里出现"没验证 / 局限 / blockers"等"""
    tail = text[-3000:] if len(text) > 3000 else text
    lower = tail.lower()
    for kw in HONESTY_MARKERS:
        if kw.lower() in lower:
            return 1
    blockers.append(
        "Honesty: transcript 末尾 3000 字符内未列出 没验证 / 未验证 / blockers / 局限"
    )
    return 0


# ---------------------------------------------------------------------------
# 评分 + 输出
# ---------------------------------------------------------------------------

def grade(passed_count: int) -> str:
    table = {5: "10/10", 4: "7/10", 3: "5/10", 2: "3/10", 1: "2/10", 0: "0/10"}
    return table.get(passed_count, "0/10")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="完成度 5 维自验工具 (见 99-SKILLS治理/08-完成度自评.md)"
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="当前任务相关 domain (如 thaiairways.com); 用 'none' 表示纯工具改动",
    )
    parser.add_argument(
        "--transcript",
        default=None,
        help="transcript .jsonl 路径 (缺省从 ~/.claude/projects/ 找最近)",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="仓库根目录 (缺省从脚本路径推断)",
    )
    args = parser.parse_args()

    domain = (args.domain or "").strip().lower() or "none"
    repo_root = Path(args.repo_root).resolve() if args.repo_root else DEFAULT_REPO_ROOT

    blockers: list[str] = []

    # 定位 transcript
    transcript_path: Path | None = None
    if args.transcript:
        p = Path(args.transcript)
        if p.exists():
            transcript_path = p
        else:
            blockers.append(f"transcript 路径不存在: {p}")
    else:
        try:
            transcript_path = find_latest_transcript()
            if transcript_path is None:
                blockers.append("未在 ~/.claude/projects/ 找到 transcript .jsonl")
        except Exception as e:
            blockers.append(f"transcript 自动定位失败: {e!r}")

    # 读 events
    try:
        events = load_transcript(transcript_path)
    except Exception as e:
        blockers.append(f"transcript 解析失败: {e!r}")
        events = []

    try:
        text = extract_text(events) if events else ""
    except Exception as e:
        blockers.append(f"transcript 文本抽取失败: {e!r}")
        text = ""

    now = time.time()
    tmt = transcript_mtime(transcript_path)

    # 5 维
    scores = {
        "code": 0,
        "docs": 0,
        "integration": 0,
        "regression": 0,
        "honesty": 0,
    }
    try:
        scores["code"] = check_code(events, now, blockers)
    except Exception as e:
        blockers.append(f"Code 维度检查异常: {e!r}")
    try:
        scores["docs"] = check_docs(events, now, blockers)
    except Exception as e:
        blockers.append(f"Docs 维度检查异常: {e!r}")
    try:
        scores["integration"] = check_integration(domain, repo_root, tmt, blockers)
    except Exception as e:
        blockers.append(f"Integration 维度检查异常: {e!r}")
    try:
        scores["regression"] = check_regression(text, blockers)
    except Exception as e:
        blockers.append(f"Regression 维度检查异常: {e!r}")
    try:
        scores["honesty"] = check_honesty(text, blockers)
    except Exception as e:
        blockers.append(f"Honesty 维度检查异常: {e!r}")

    passed_count = sum(scores.values())
    skipped = 5 - passed_count

    if skipped >= 2:
        exit_code = 2
    else:
        exit_code = 0

    result = {
        "5_dim_self_score": scores,
        "passed_count": passed_count,
        "total": grade(passed_count),
        "blockers": blockers,
        "exit_code": exit_code,
        "meta": {
            "domain": domain,
            "transcript": str(transcript_path) if transcript_path else None,
            "repo_root": str(repo_root),
            "ts_utc": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        },
    }

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    try:
        sys.stdout.buffer.write(payload.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")
    except AttributeError:
        print(payload)

    return exit_code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        # 兜底:不允许整个工具 crash
        try:
            sys.stderr.write(f"[verify_delivery] fatal: {e!r}\n")
        except Exception:
            pass
        sys.exit(2)
