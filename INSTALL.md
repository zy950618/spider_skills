# INSTALL — 安装指南

> 一站式安装。从零到能用大约 5-10 分钟,加上 CloakBrowser 二进制下载额外 3-5 分钟。
>
> 别的入口:[USAGE](./USAGE.md) 使用 · [TRIGGERS](./TRIGGERS.md) 触发词速查

---

## 前置

| 依赖 | 版本 | 用途 |
|---|---|---|
| **git** | 任意 | clone 仓库 |
| **Python** | 3.11+ | 跑 tools/ 下的脚本 + 评分 |
| **Claude Code** | 最新 | 加载 Skills,运行 hooks |
| **管理员权限**(Windows) | - | 创建 junction 软链(普通 mklink 不需要) |

可选(只在用对应功能时装):

| 依赖 | 用途 |
|---|---|
| **cloakbrowser** | 录 fixtures(反爬严的站点);否则用 Chrome DevTools 导 HAR 也行 |
| **pyyaml** | 部分脚本(评分本身不强依赖,但解析 meta.yaml 更准) |

---

## 完整步骤

### Step 1: clone 仓库

```bash
git clone <repo-url> ~/SKILLS/my_reverse_skill
cd ~/SKILLS/my_reverse_skill
```

Windows:

```powershell
git clone <repo-url> E:\SKILLS\my_reverse_skill
cd E:\SKILLS\my_reverse_skill
```

### Step 2: 软链 18 个 Skill 到 ~/.claude/skills/

Claude Code 默认从 `~/.claude/skills/` 加载 Skill,本仓库分层放在子目录里,需要软链回去。

#### Windows (PowerShell)

> 必须用管理员权限运行 PowerShell,否则 New-Item Junction 会失败。

```powershell
# 业务流程层 (5 个)
foreach ($n in @('website-314-api-delivery','mobile-app-reverse-delivery','reverse-js-crawler','imperva-waf-reese84','skills-evaluation-governance')) {
  New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\$n" -Target "E:\SKILLS\my_reverse_skill\1-业务流程层\$n" -Force
}
# JS 工具层 (4 个)
foreach ($n in @('find-crypto-entry','ast-deobfuscate','env-patch','ai-reverse-skill-creator')) {
  New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\$n" -Target "E:\SKILLS\my_reverse_skill\2-JS逆向工具层\$n" -Force
}
# 移动逆向层 (7 个)
foreach ($n in @('rev-frida','rev-idapython','rev-dex-dumper','rev-u3d-dump','rev-struct','rev-symbol','rev-unicorn-debug')) {
  New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\$n" -Target "E:\SKILLS\my_reverse_skill\3-移动逆向工具层\$n" -Force
}
# 通用规范 + 沉淀工具
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\karpathy-guidelines" -Target "E:\SKILLS\my_reverse_skill\4-通用规范层\karpathy-guidelines" -Force
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\site-api-adapter" -Target "E:\SKILLS\my_reverse_skill\5-沉淀工具层\site-api-adapter" -Force
```

#### macOS / Linux

```bash
REPO="$HOME/SKILLS/my_reverse_skill"   # 改成你本地实际路径
DST="$HOME/.claude/skills"
mkdir -p "$DST"

for n in website-314-api-delivery mobile-app-reverse-delivery reverse-js-crawler imperva-waf-reese84 skills-evaluation-governance; do
  ln -snf "$REPO/1-业务流程层/$n" "$DST/$n"
done
for n in find-crypto-entry ast-deobfuscate env-patch ai-reverse-skill-creator; do
  ln -snf "$REPO/2-JS逆向工具层/$n" "$DST/$n"
done
for n in rev-frida rev-idapython rev-dex-dumper rev-u3d-dump rev-struct rev-symbol rev-unicorn-debug; do
  ln -snf "$REPO/3-移动逆向工具层/$n" "$DST/$n"
done
ln -snf "$REPO/4-通用规范层/karpathy-guidelines" "$DST/karpathy-guidelines"
ln -snf "$REPO/5-沉淀工具层/site-api-adapter" "$DST/site-api-adapter"
```

### Step 3: (可选) 装 CloakBrowser 录 fixtures

只有要做一致性验证 fixtures 录制时才需要。**反爬不严的站点可以跳过这步,用 Chrome DevTools 导 HAR 即可**(见 [07 一致性验证规约 Step 1B](./99-SKILLS治理/07-一致性验证规约.md))。

```bash
pip install cloakbrowser
python -m cloakbrowser install   # 下载浏览器二进制,3-5 分钟
python -m cloakbrowser info      # 验证装好
```

可选装 pyyaml(让评分脚本更准地解析 meta.yaml):

```bash
pip install pyyaml
```

### Step 4: 装 hooks

本仓库默认在项目级 `.claude/settings.json` 注册了 Stop hook(任务结束扫 transcript 提醒沉淀)。

**项目级** (默认,推荐) — 已经装好,无需操作。只在 cwd 在本仓库内时触发,不污染其他项目。

**跨项目级** (可选,有副作用) — 在外部项目工作时也想触发提醒,把下面这段加到 `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"E:/SKILLS/my_reverse_skill/tools/post_task_reminder.py\""
          }
        ]
      }
    ]
  }
}
```

> 副作用:**所有项目的 Stop 事件都会跑这个 hook**。脚本异常时退出码 0 静默,不影响主任务,但还是会多一次 fork。
>
> Windows 上 `python` 不在 PATH 时改成 `py`。

### Step 5: 验证安装

#### Unix / macOS / Git Bash

```bash
# 1. 检查 Skills 软链
ls ~/.claude/skills/ | grep -E '(rev-|website-|reverse-js|imperva|find-crypto|ast-|env-patch|karpathy|site-api|ai-reverse|skills-evaluation|mobile-app)'
# 应该看到 18 个

# 2. 跑评分(应该不报错)
cd ~/SKILLS/my_reverse_skill   # 或 E:\SKILLS\my_reverse_skill
python "1-业务流程层/skills-evaluation-governance/scripts/score_skills.py" "1-业务流程层"
# 应该输出 JSON,1 层 5 个 Skill 的 v0.3.6 分数 (overall.total ≈ 65)

# 3. 跑 fixtures 验证(空仓库,应该 PASS)
python tools/replayer/validate_fixtures.py
# 应该输出: domains: 0  snapshots: 0  ... all good.

# 4. 重启 Claude Code, 在仓库目录内打开
# 输入 "/" 应该能看到所有 Skill
# 输入 "逆向" 等关键词时, Claude 会自动加载触发的 Skill
```

#### Windows PowerShell

```powershell
# 1. 检查 Skills 软链 (期望 18 个)
(Get-ChildItem "$env:USERPROFILE\.claude\skills" -Directory).Count

# 2. 跑评分
cd E:\SKILLS\my_reverse_skill
python "1-业务流程层/skills-evaluation-governance/scripts/score_skills.py" "1-业务流程层"

# 3. 跑 fixtures 验证
python tools\replayer\validate_fixtures.py

# 4. 重启 Claude Code
```

#### Windows cmd

```cmd
:: 1. 检查 Skills 软链
dir "%USERPROFILE%\.claude\skills" /B | find /C /V ""

:: 2. 跑评分
cd /d E:\SKILLS\my_reverse_skill
python "1-业务流程层\skills-evaluation-governance\scripts\score_skills.py" "1-业务流程层"

:: 3. 跑 fixtures 验证
python tools\replayer\validate_fixtures.py
```

---

## 升级

```bash
cd ~/SKILLS/my_reverse_skill
git pull
# 软链指向本仓库目录,git pull 后自动生效。Skills 内容已更新。
```

---

## 卸载

```bash
# Windows (PowerShell)
foreach ($n in @('website-314-api-delivery','reverse-js-crawler','imperva-waf-reese84','mobile-app-reverse-delivery','skills-evaluation-governance','find-crypto-entry','ast-deobfuscate','env-patch','ai-reverse-skill-creator','rev-frida','rev-idapython','rev-dex-dumper','rev-u3d-dump','rev-struct','rev-symbol','rev-unicorn-debug','karpathy-guidelines','site-api-adapter')) {
  Remove-Item "$env:USERPROFILE\.claude\skills\$n" -Force -ErrorAction SilentlyContinue
}

# macOS / Linux
for n in $(ls ~/.claude/skills/); do
  [ -L "$HOME/.claude/skills/$n" ] && rm "$HOME/.claude/skills/$n"
done
```

仓库目录本身可以 `rm -rf ~/SKILLS/my_reverse_skill` 删除。

---

## 常见问题

### Q1: Windows 创建 Junction 报权限错

A: 用**管理员**身份打开 PowerShell。普通用户没权限创建 Junction(虽然 mklink /J 在 cmd 里 Win10+ 可以)。

替代方案:用 mklink /J:

```cmd
mklink /J "%USERPROFILE%\.claude\skills\find-crypto-entry" "E:\SKILLS\my_reverse_skill\2-JS逆向工具层\find-crypto-entry"
```

### Q2: `python` 命令找不到(Windows Store 版 Python)

A: Windows Store 装的 Python 命令叫 `py`,不是 `python`。改 hook 配置:

`.claude/settings.json` 把 `"python \"$CLAUDE_PROJECT_DIR/tools/post_task_reminder.py\""` 改成 `"py \"$CLAUDE_PROJECT_DIR/tools/post_task_reminder.py\""`。

或者重新装 python.org 的版本,勾选 "Add to PATH"。

### Q3: cloakbrowser 装失败

A: 常见原因:
- 国内网络问题 → 设代理 `pip install --proxy http://... cloakbrowser`
- Python 版本 < 3.8 → 升级到 3.11+
- `python -m cloakbrowser install` 下载二进制失败 → 设环境变量代理或重试

跳过 CloakBrowser 也能用 90% 功能 — 一致性验证用 HAR 导入(har_to_fixtures.py)就行。

### Q4: Hook 没触发(任务结束没看到沉淀提醒)

A: 三个原因:
1. cwd 不在仓库内 → 项目级 hook 只在仓库内触发,跨项目要装用户级(Step 4)
2. python 不在 PATH → 见 Q2
3. 对话里没出现"逆向 / sign / crawler / waf"等 marker → hook 只对逆向任务触发,通用问题不打扰

debug:看 `tools/.reminder-stats.jsonl` 是否有新行(每次 hook 触发都会写)。

### Q5: 跑 score_skills.py 报 Windows 中文乱码

A: 仓库 score_skills.py 已经 `sys.stdout.reconfigure(encoding="utf-8")`。如果还乱码,改环境变量:

```cmd
set PYTHONIOENCODING=utf-8
```

或 PowerShell:

```powershell
$env:PYTHONIOENCODING="utf-8"
```

### Q6: 软链装好了但 Claude 看不到 Skill

A: 关闭重开 Claude Code。Skill 加载在启动时扫描 `~/.claude/skills/`,运行中改不生效。

### Q7: 怎么知道某次任务 Claude 用了哪些 Skill

A: 看 Claude 回复里 `Skill(...)` 调用块,或在仓库外跑:

```bash
grep -c "Skill(" ~/.claude/projects/<sanitized-cwd>/conversation.jsonl
```

### Q8: CI 跑不动(GitHub Actions)

A: `.github/workflows/skill-bench.yml` 和 `consistency-replay.yml` 默认配置应该开箱即用。问题排查:
- Repo permissions: Settings → Actions → 给 Actions read+write 权限
- consistency-replay.yml 的 replay-diff job 需要 ADAPTER_BASE_URL secret 或 workflow_dispatch 输入。否则只跑 validate-schema

---

## 验证清单

装完跑一遍:

- [ ] `ls ~/.claude/skills/` 看到 18 个 Skill 软链
- [ ] `python --version` ≥ 3.11
- [ ] `python "1-业务流程层/skills-evaluation-governance/scripts/score_skills.py" "1-业务流程层"` 输出 JSON 不报错
- [ ] `python tools/replayer/validate_fixtures.py` 输出 `all good`
- [ ] `cat .claude/settings.json` 有 Stop hook 配置
- [ ] Claude Code 启动,仓库目录内输入 `/逆向` 能匹配到 Skill
- [ ] (可选) `python -m cloakbrowser info` 显示版本号
