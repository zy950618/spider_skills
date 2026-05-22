"""Stop hook: 任务结束时检测是否需要沉淀提醒。

读 stdin 的 hook payload,扫 transcript 提取 domain。
如果对话涉及网站逆向但没看到沉淀动作,把提示写到 stderr 并以退出码 2 退出,
让 Claude 接到反馈、酌情提醒用户补沉淀步骤。

设计原则:异常静默(任何失败都退出码 0),不影响主任务。
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DOMAIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"([a-z0-9][a-z0-9-]{0,62}\.(?:com|net|org|cn|co|io|ai|jp|hk|tw|sg|kr|vn|th|my|id|uk|de|fr|au))",
    re.IGNORECASE,
)

EXCLUDE_DOMAINS = {
    "github.com", "githubusercontent.com", "raw.githubusercontent.com",
    "anthropic.com", "claude.com", "claude.ai",
    "google.com", "googleapis.com", "googleusercontent.com",
    "npmjs.com", "yarnpkg.com",
    "stackoverflow.com", "stackexchange.com",
    "mozilla.org", "developer.mozilla.org",
    "python.org", "pypi.org", "pythonhosted.org",
    "nodejs.org",
    "openai.com",
    "microsoft.com", "msdn.com", "live.com",
    "wikipedia.org",
    "example.com", "example.org", "example.net",
    "localhost",
}

PERSIST_MARKERS = (
    "sync_site_memory.py",
    "score_skills.py",
    "skills-evaluation-governance",
    "known-failures.md",
    "test-log-lessons.md",
    "site-memory.md",
    "站点经验库",
    "site memory",
)

REVERSE_MARKERS = (
    "逆向", "reverse", "crawler", "crawl",
    "接口还原", "接口实现", "纯接口", "签名", "加密参数",
    "sign", "token", "x-sign", "authkey", "x-d-token",
    "waf", "imperva", "reese84", "84盾", "incapsula", "akamai",
    "find-crypto-entry", "ast-deobfuscate", "env-patch",
    "frida", "apk", "ipa", "dex", "il2cpp",
    "314", "adapter.yaml",
)

SITE_MEMORY_DIR = "站点经验库"


def load_transcript(path: str) -> list[dict]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    events: list[dict] = []
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def extract_text(events: list[dict]) -> str:
    parts: list[str] = []
    for ev in events:
        msg = ev.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for c in content:
                if not isinstance(c, dict):
                    continue
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


def extract_domains(text: str) -> set[str]:
    found: set[str] = set()
    for m in DOMAIN_RE.finditer(text):
        d = m.group(1).lower()
        parts = d.split(".")
        if len(parts) < 2:
            continue
        main = ".".join(parts[-2:])
        if main in EXCLUDE_DOMAINS:
            continue
        if any(ch.isdigit() for ch in parts[-2]) and len(parts[-2]) < 4:
            continue
        found.add(main)
    return found


def has_any(text: str, markers) -> bool:
    lower = text.lower()
    return any(k.lower() in lower for k in markers)


def list_site_memory_dirs(repo_root: Path) -> set[str]:
    site = repo_root / SITE_MEMORY_DIR
    if not site.exists():
        return set()
    return {
        d.name.lower()
        for d in site.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    if payload.get("stop_hook_active"):
        return 0

    transcript_path = payload.get("transcript_path", "")
    cwd = payload.get("cwd") or os.getcwd()
    repo_root = Path(cwd)

    try:
        events = load_transcript(transcript_path)
    except Exception:
        return 0
    if not events:
        return 0

    try:
        text = extract_text(events)
    except Exception:
        return 0

    if not has_any(text, REVERSE_MARKERS):
        return 0

    try:
        domains = extract_domains(text)
    except Exception:
        return 0
    if not domains:
        return 0

    persisted = has_any(text, PERSIST_MARKERS)
    existing = list_site_memory_dirs(repo_root)
    new_domains = {d for d in domains if d not in existing}

    if not new_domains and persisted:
        return 0

    lines = ["[my_reverse_skill] 任务结束沉淀提醒:"]
    if new_domains:
        lines.append(
            "  - 检测到未沉淀的 domain: " + ", ".join(sorted(new_domains))
        )
        lines.append(
            f"    建议先从 `{SITE_MEMORY_DIR}/_templates/` 复制 7 文件模板到对应 domain 目录"
        )
    if not persisted:
        lines.append("  - 对话中未见沉淀动作,请考虑:")
        lines.append("    1) 写 `站点经验库/<domain>/known-failures.md` 失败模式")
        lines.append("    2) 写 `站点经验库/<domain>/test-log-lessons.md` 测试教训")
        lines.append("    3) 写 `站点经验库/<domain>/change-log.md` 变更记录")
        lines.append("    4) 跑 `python tools/sync_site_memory.py --project <P> --domain <D> --apply`")
        lines.append("    5) 调用 `skills-evaluation-governance` 给本次用到的 skill 打分")
    lines.append("  详见 `99-SKILLS治理/06-网页逆向标准规划.md` 阶段 E。")

    print("\n".join(lines), file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
