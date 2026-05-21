#!/usr/bin/env python3
"""
sync_site_memory.py — 把项目 memory 中的 project 类条目同步到 站点经验库/<domain>/

用法:
  # dry-run（默认）：只输出建议，不写文件
  python tools/sync_site_memory.py \\
      --project E:/flight-cwl/flight-cwl-vj-baggage \\
      --domain vietjetair.com

  # 真正写入
  python tools/sync_site_memory.py \\
      --project E:/flight-cwl/flight-cwl-vj-baggage \\
      --domain vietjetair.com \\
      --apply

行为:
  1. 扫描 <project>/.claude/projects/<sanitized>/memory/*.md
  2. 提取所有 frontmatter type=project 或 type=feedback 的 memory
  3. 按内容关键词归类到目标站点经验库的 7 个文件之一
  4. dry-run: 输出 "建议附加到 known-failures.md" 这种提示
  5. --apply: 真实附加到目标文件末尾，加时间戳 + 来源注释

设计原则:
  - 只追加，不覆盖（避免破坏用户手工编辑过的内容）
  - 每次写入加 <!-- synced from: <path> at <ts> --> 注释，方便溯源
  - 站点目录不存在时从 _templates/ 复制 7 文件模板
"""

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

# Windows console 默认 cp936，中文输出会乱码。强制 stdout 用 UTF-8。
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR_ROOT = REPO_ROOT / "站点经验库"
TEMPLATES_DIR = SITE_DIR_ROOT / "_templates"

# 站点经验库的 7 个标准文件 + 归类关键词
TARGET_FILES = {
    "known-failures.md": ["失败", "错误", "拒绝", "403", "400", "blocked", "fail", "reject", "拦截"],
    "route-decisions.md": ["路由", "分支", "网关", "/payment", "/checkout", "route", "branch", "endpoint"],
    "market-matrix.md": ["市场", "货币", "language", "locale", "currency", "market", "VN", "TH"],
    "test-log-lessons.md": ["测试", "复盘", "lesson", "test", "调试", "验证"],
    "site-memory.md": [],  # 兜底
    "eval-backlog.md": ["eval", "评测", "回测", "用例"],
    "change-log.md": ["变更", "升级", "版本", "change", "version"],
}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


def parse_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    body = m.group(2)
    fm = {}
    for line in raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body


def categorize(text, fm):
    """根据 frontmatter + 内容关键词决定归类到哪个文件"""
    haystack = (fm.get("description", "") + " " + text).lower()
    name = fm.get("name", "").lower()
    haystack = haystack + " " + name

    best = "site-memory.md"
    best_hits = 0
    for fname, keywords in TARGET_FILES.items():
        if not keywords:
            continue
        hits = sum(1 for kw in keywords if kw.lower() in haystack)
        if hits > best_hits:
            best = fname
            best_hits = hits
    return best


def find_memory_files(project_path):
    """在项目目录下找 memory/*.md"""
    project = Path(project_path).resolve()
    # 兼容两种结构：项目根/memory  和  C:\Users\<user>\.claude\projects\<sanitized>\memory
    candidates = []
    direct = project / "memory"
    if direct.is_dir():
        candidates.extend(direct.glob("*.md"))

    # 也扫 ~/.claude/projects/<*>/memory
    home = Path.home()
    proj_root = home / ".claude" / "projects"
    if proj_root.is_dir():
        # 把项目路径变成 sanitized name（windows 风格 E--xxx-yyy）
        sanitized = str(project).replace(":", "-").replace("\\", "-").replace("/", "-")
        # 试匹配以 sanitized 为前缀的目录
        for d in proj_root.iterdir():
            if d.is_dir() and sanitized.lower().replace("--", "-") in d.name.lower().replace("--", "-"):
                mem_dir = d / "memory"
                if mem_dir.is_dir():
                    candidates.extend(mem_dir.glob("*.md"))

    # 去重
    seen = set()
    result = []
    for p in candidates:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        if rp.name.upper() == "MEMORY.MD":
            continue  # 跳过索引文件
        result.append(rp)
    return result


def ensure_site_dir(domain, apply):
    target = SITE_DIR_ROOT / domain
    if target.exists():
        return target
    if not apply:
        print(f"[dry-run] 会从 _templates/ 创建 {target}/")
        return target
    if not TEMPLATES_DIR.exists():
        print(f"WARN: 模板目录不存在 {TEMPLATES_DIR}, 仅创建空目录")
        target.mkdir(parents=True, exist_ok=True)
        return target
    import shutil
    shutil.copytree(TEMPLATES_DIR, target)
    print(f"[apply] 已从模板创建 {target}/")
    return target


def append_to_file(target_file, source_file, fm, body, apply):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    block = f"""
<!-- synced from: {source_file} at {ts} -->
### {fm.get('name', source_file.name)}

> **type**: {fm.get('type', 'unknown')}  •  **description**: {fm.get('description', '')}

{body.strip()}

"""
    if not apply:
        print(f"[dry-run] 会追加到 {target_file.name}  (来源: {source_file.name})")
        return
    target_file.parent.mkdir(parents=True, exist_ok=True)
    with open(target_file, "a", encoding="utf-8") as f:
        f.write(block)
    print(f"[apply] {source_file.name} -> {target_file.name}")


def main():
    parser = argparse.ArgumentParser(description="同步 project memory 到站点经验库")
    parser.add_argument("--project", required=True, help="项目根目录路径")
    parser.add_argument("--domain", required=True, help="站点域名（如 vietjetair.com）")
    parser.add_argument("--apply", action="store_true", help="真实写入文件，默认 dry-run")
    parser.add_argument("--include-feedback", action="store_true",
                        help="把 type=feedback 的 memory 也同步（默认只同步 type=project）")
    args = parser.parse_args()

    memory_files = find_memory_files(args.project)
    if not memory_files:
        print(f"未找到 memory 文件 (项目: {args.project})")
        print(f"已检查: {args.project}/memory  和  ~/.claude/projects/<sanitized>/memory")
        sys.exit(1)

    print(f"\n发现 {len(memory_files)} 个 memory 文件:\n")
    for p in memory_files:
        print(f"  {p}")

    site_dir = ensure_site_dir(args.domain, args.apply)
    print(f"\n目标站点目录: {site_dir}\n")

    accepted_types = {"project"}
    if args.include_feedback:
        accepted_types.add("feedback")

    matched = 0
    for mf in memory_files:
        try:
            text = mf.read_text(encoding="utf-8")
        except Exception as e:
            print(f"WARN: 读 {mf} 失败: {e}")
            continue
        fm, body = parse_frontmatter(text)
        if fm.get("type", "").strip() not in accepted_types:
            continue
        matched += 1
        target_name = categorize(body, fm)
        target_path = site_dir / target_name
        append_to_file(target_path, mf, fm, body, args.apply)

    print(f"\n共匹配 {matched} 个 memory，{'已写入' if args.apply else '建议预览（dry-run）'}")
    if not args.apply:
        print("加 --apply 参数真实写入。")


if __name__ == "__main__":
    main()
