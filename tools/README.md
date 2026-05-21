# tools/ — 仓库辅助脚本

## sync_site_memory.py

把项目 memory 中的 `type: project` / `type: feedback` 条目同步到 `站点经验库/<domain>/` 的 7 个标准文件。

### 用法

```bash
# dry-run（默认，只预览）
python tools/sync_site_memory.py \
    --project E:/flight-cwl/flight-cwl-vj-baggage \
    --domain vietjetair.com

# 真正写入
python tools/sync_site_memory.py \
    --project E:/flight-cwl/flight-cwl-vj-baggage \
    --domain vietjetair.com \
    --apply

# 同时同步 feedback 类（默认只同步 project 类）
python tools/sync_site_memory.py \
    --project E:/flight-cwl/flight-cwl-vj-baggage \
    --domain vietjetair.com \
    --apply --include-feedback
```

### 行为

1. 扫 `<project>/memory/*.md` 和 `~/.claude/projects/<sanitized>/memory/*.md` 两处
2. 跳过 `MEMORY.md` 索引文件
3. 根据 frontmatter 的 `type` 过滤
4. 根据内容关键词归类到 `known-failures.md` / `route-decisions.md` / `market-matrix.md` 等
5. 站点目录不存在时从 `站点经验库/_templates/` 复制 7 文件模板
6. 追加写入（不覆盖），每条加 `<!-- synced from: ... -->` 注释方便溯源

### 何时跑

任务结束、做总结时手动跑一次。**不建议接 Stop hook 自动跑**（会污染无关项目）。
