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

---

## backfill_from_site_memory.py

从 `站点经验库/<domain>/` 反推真实任务下限，写进指定 Skill 的 `metrics/real-task-summary.md`。

任务下限 = `## Failure:` 计数 + `## Pattern:` / `## Lesson:` 计数 + change-log 表格版本行数。

### 用法

```bash
# dry-run (默认)
python tools/backfill_from_site_memory.py \
    --domain thaiairways.com \
    --skill-metrics "1-业务流程层/website-314-api-delivery/metrics/real-task-summary.md"

# 真正写入
python tools/backfill_from_site_memory.py \
    --domain thaiairways.com \
    --skill-metrics "1-业务流程层/website-314-api-delivery/metrics/real-task-summary.md" \
    --apply

# 多 domain 累加
python tools/backfill_from_site_memory.py \
    --domain thaiairways.com --domain vietjetair.com \
    --skill-metrics "..." --apply

# 覆盖已写入的反推段
python tools/backfill_from_site_memory.py ... --apply --rewrite
```

### 行为

1. 用区段标记 `<!-- backfill-from-site-memory:start -->` / `:end` 包裹反推段
2. 默认追加；已存在反推段时跳过，加 `--rewrite` 才覆盖
3. 写入的数字会被 `score_skills.py` 检测为真实数据，撤销 v0.3.4 metrics 占位虚高

### 何时跑

每次新建 / 更新 `站点经验库/<domain>/` 后跑一次，让该 domain 真实参与的 Skill metrics 反映真实任务下限。

---

## scaffold_evals.py

给指定 Skill 生成 `evals/*.yaml` + `agents/openai.yaml` 骨架。骨架用 `TODO:` 占位 prompt 和 criteria，需要后续手动或交 agent 填真实内容。

### 用法

```bash
# 单个 Skill
python tools/scaffold_evals.py --skill 2-JS逆向工具层/find-crypto-entry

# 批量
python tools/scaffold_evals.py \
    --skill 2-JS逆向工具层/find-crypto-entry \
    --skill 2-JS逆向工具层/ast-deobfuscate \
    --skill 3-移动逆向工具层/rev-frida

# 覆盖已有骨架
python tools/scaffold_evals.py --skill ... --force
```

### 行为

1. 读 SKILL.md frontmatter 提取 `name` 和 `description`
2. 写 `agents/openai.yaml`（不存在时）
3. 写 `evals/001-positive-placeholder.yaml`（expect_skill: true）
4. 写 `evals/002-negative-placeholder.yaml`（expect_skill: false）
5. 写 `evals/003-regression-placeholder.yaml`（expect_skill: true）
6. 默认不覆盖已存在的文件

### 何时跑

新增工具层 Skill 时跑一次生成骨架，然后用 agent 填真实 case 内容，避免长期保留 TODO 占位。

---

## post_task_reminder.py / append_drift_history.py

Stop hook 与 CI 周更 drift snapshot 的脚本。详见 `99-SKILLS治理/05-当前评分与回测结果.md` 的 v0.3.4 章节。
