#!/usr/bin/env python3
"""
ci_gate.py — 按"层"设阈值，读取 .ci-out/*.json，任何 skill 低于其层阈值则 exit 1。

为什么按层不按统一阈值？
- 业务流程层 (1-) / 沉淀工具层 (5-) 是 package skill，含 SKILL.md + evals + references + agents
  → 高阈值 (70)
- 原子工具层 (2- / 3- / 4-) 是 atom skill，只有 SKILL.md 也可以有效
  → 低阈值 (15)，主要确保 SKILL.md 还在 + frontmatter 完整

这是 v1 baseline。后续随 skill 演化可调高阈值。

用法:
  python tools/ci_gate.py .ci-out
"""

import json
import sys
from pathlib import Path

LAYER_MIN = {
    "1-业务流程层": 70,
    "2-JS逆向工具层": 15,
    "3-移动逆向工具层": 15,
    "4-通用规范层": 15,
    "5-沉淀工具层": 70,
}


def layer_from_filename(name: str) -> str:
    # ".ci-out/1-业务流程层.json"  →  "1-业务流程层"
    return Path(name).stem.replace("_", "/")


def main():
    if len(sys.argv) != 2:
        print("usage: ci_gate.py <ci-out-dir>", file=sys.stderr)
        sys.exit(2)

    out_dir = Path(sys.argv[1])
    if not out_dir.is_dir():
        print(f"ERROR: 目录不存在 {out_dir}", file=sys.stderr)
        sys.exit(2)

    failures = []
    passed = []

    for json_path in sorted(out_dir.glob("*.json")):
        layer = layer_from_filename(json_path.name)
        threshold = LAYER_MIN.get(layer)
        if threshold is None:
            print(f"WARN: 未知层 {layer}, 跳过")
            continue
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        for skill in data.get("skills", []):
            total = skill["scores"]["total"]
            name = skill["skill"]
            if total < threshold:
                failures.append((layer, name, total, threshold, skill.get("gaps", [])))
            else:
                passed.append((layer, name, total, threshold))

    print("=" * 70)
    print(f"Skill Bench CI Gate - layer-aware thresholds")
    print("=" * 70)
    print(f"\n通过 ({len(passed)}):")
    for layer, name, total, threshold in passed:
        print(f"  PASS  {layer:25s} {name:40s} {total:3d} / {threshold}")

    if failures:
        print(f"\n失败 ({len(failures)}):")
        for layer, name, total, threshold, gaps in failures:
            print(f"  FAIL  {layer:25s} {name:40s} {total:3d} / {threshold}")
            for gap in gaps[:3]:
                print(f"        - {gap}")
        print(f"\n{'!' * 70}")
        print(f"CI Gate 失败: {len(failures)} 个 skill 低于其所在层阈值")
        print(f"{'!' * 70}")
        sys.exit(1)

    print(f"\nCI Gate 通过: {len(passed)} 个 skill 全部达标")
    sys.exit(0)


if __name__ == "__main__":
    main()
