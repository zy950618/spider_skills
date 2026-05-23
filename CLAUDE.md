# my_reverse_skill — Claude 工作指南

逆向工程 SKILLS 总库。进入本仓库工作时,请先按下面规则行动,**不要直接跳进 reverse-js-crawler 写代码**。

---

## 首要入口(强制)

收到"网页逆向 XXX 网站"、"实现 XXX 站点纯接口"、"把 XXX 接入 314"、"破解 XXX 的 sign/token"、"做一下 XXX 的爬虫"类请求时:

**第一步:读 `99-SKILLS治理/06-网页逆向标准规划.md`,按五阶段输出规划再开干。**

规划格式固定:

```
目标:<URL + 业务目标>
分类:<纯HTTP / JS加密 / 补环境 / WAF / 接口化沉淀 / 314服务化>
难度评估:<低/中/高> + 关键不确定点 3 个
阶段化计划:
  1. 侦察    skill: <name>    产出: <什么>
  2. 入口    skill: <name>    产出: <什么>
  3. 还原    skill: <name>    产出: <什么>
  4. 复现    skill: <name>    产出: <什么>
  5. 沉淀    skill: <name>    产出: <什么>
站点经验库检查:<是否已有 站点经验库/<domain>/,已有则先读完 known-failures.md>
WAF 预判:<是否存在 reese84/incapsula/akamai/cloudflare 痕迹>
风险与红线:<是否涉及真实扣款 / 是否涉及登录态 / 是否需要授权>
```

输出后等用户确认或修正,再进入执行。

---

## 仓库分层速查

| 层 | 目录 | 角色 |
|---|---|---|
| 1 | `1-业务流程层/` | 顶层入口(5 个 skill),按需求调度 2/3/5 层 |
| 2 | `2-JS逆向工具层/` | Web/JS 原子工具(4 个) |
| 3 | `3-移动逆向工具层/` | Android/iOS/Native 工具(7 个) |
| 4 | `4-通用规范层/` | 行为守则(karpathy-guidelines) |
| 5 | `5-沉淀工具层/` | 接口稳定后的标准化(site-api-adapter) |
| 99 | `99-SKILLS治理/` | 生命周期/分类/评分/漂移/准入 |
| - | `站点经验库/` | 站点案例(按 domain/market/locale 拆分) |
| - | `tools/` | 仓库辅助脚本(`sync_site_memory.py`、`ci_gate.py`、`post_task_reminder.py`) |

完整入口见 `00-SKILLS索引.md`,标准入口与目录详解见 `README.md`。

---

## 站点经验库使用约定(强制)

任何 domain 相关任务,**先查 `站点经验库/<domain>/known-failures.md`**:

- 已知失败模式 → 不要重复踩
- 已知路由决策 → 不要重新调研
- 已知 market/locale 矩阵 → 不要重新枚举

新 domain 没有目录时,从 `站点经验库/_templates/` 复制 7 文件模板再开始。

---

## 任务结束的强制沉淀(5 步)

任务结束**强制**走以下五步,否则不算完成:

1. 写 `站点经验库/<domain>/known-failures.md`(失败模式:symptom / stage / market / currency / status / marker / root cause / correct handling)
2. 写 `站点经验库/<domain>/test-log-lessons.md`(这次测试学到什么)
3. 写 `站点经验库/<domain>/change-log.md`(变更记录)
4. 接口已稳定 → 调用 `5-沉淀工具层/site-api-adapter` 产出 adapter.yaml / schema.json
5. 调用 `skills-evaluation-governance`:给本次用到的 skill 打分,新失败模式补 eval

详见 `99-SKILLS治理/06-网页逆向标准规划.md` 第 2 节阶段 E。

---

## 任务结束的进化 6 问

1. 有没有新触发词? → 更新对应 skill 的 description
2. 有没有新失败类型? → `known-failures.md` + 新增 eval
3. 有没有新分类规则? → `99-SKILLS治理/02-新网站接入分类.md` 加行
4. 有没有新加解密或反爬模式? → `references/` 新增章节
5. 有没有应该加入 eval 的场景? → `evals/`
6. 需不需要升版本号? → 看 `99-SKILLS治理/03-测试评分漂移.md`

---

## memory 同步

任务结束需要同步项目 memory 到站点经验库时:

```bash
python tools/sync_site_memory.py --project <项目路径> --domain <domain> --apply
```

dry-run 见 `tools/README.md`。**不要接 Stop hook 自动跑,会污染无关项目**。

---

## 红线

- 真实扣款一律不在自动化测试环境跑,除非用户**明示**授权
- 不把一次失败硬编码成只适配一个站点的规则
- 不用"评分高"代替真实任务成功
- 不把编码代理规则混入逆向 Skill(代码纪律走 `4-通用规范层/karpathy-guidelines`)
- 不把所有经验塞进一个超长 SKILL.md

---

## 完成前自评铁律

声明"完成 / done / 交付 / 收尾"前,必须跑:

```bash
python tools/verify_delivery.py --domain <当前任务的 domain,或 none>
```

exit_code != 0 时,**不许向用户输出"完成"**。需先补完 blockers 列表中的项,重跑直到 exit 0。

规则源:`99-SKILLS治理/08-完成度自评.md` 的 5 维(Code/Docs/Integration/Regression/Honesty)。

verify_delivery.py 是二级 quality gate;Stop hook 的 `post_task_reminder.py` 是三级(任务结束自动检查)。两者互补。

---

## 自动提醒机制

`.claude/settings.json` 注册了 Stop hook(`tools/post_task_reminder.py`)。
Claude 完成响应时,脚本会扫 transcript:

- 若检测到本次涉及业务 domain
- 且对话中未出现 `sync_site_memory.py` / `score_skills.py` / `skills-evaluation-governance` / `站点经验库` 等沉淀标记
- 则输出 reminder 给 Claude

reminder 是软提示,不阻断流程。脚本异常时静默退出,不影响主任务。

### 触发范围(重要)

Stop hook 由**项目级** `.claude/settings.json` 注册,**只在 Claude Code 的 cwd 是本仓库或其子目录时生效**:

- ✓ 在 `E:/SKILLS/my_reverse_skill/` 内任何子目录工作时,hook 自动触发
- ✗ 在外部项目(如 `C:/Users/Administrator`、`flight-cwl-vj-baggage`)中工作时,**hook 不会触发**

跨项目场景下,任务结束请手动核对 06 规划的 5 步沉淀,或在 Claude 中说"按 my_reverse_skill 的 5 步沉淀核对一遍"。

跨项目自动触发需要在 `~/.claude/settings.json` 用户级配置中加 Stop hook 指向本仓库脚本绝对路径,会污染所有项目,**默认不开启,按需手动配**。

### 校准数据

hook 每次触发会写一条记录到 `tools/.reminder-stats.jsonl`(在 `.gitignore` 中,不入 git)。累积 2 周后用于校准 `EXCLUDE_DOMAINS` / `REVERSE_MARKERS` / `PERSIST_MARKERS` 词表。

### 跨平台 python 命令

hook 命令默认 `python`。Windows 上若 `python` 不在 PATH(只装了 Microsoft Store 版可能叫 `py`),把 `.claude/settings.json` 中的 `"python"` 改为 `"py"`。
