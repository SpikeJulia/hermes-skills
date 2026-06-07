---
name: terminal-cwd-persistence-pitfall
description: terminal tool 的 cwd **不持久** — 每次 terminal() 调用都从 $HOME 重新开始，cd 不会跨调用保留。导致 git/Hermes 命令在错误目录报 "fatal: not a git repository"。本 reference 涵盖 3 套解决方案 + 常见错误模式。
---

# Terminal cwd 不持久 — 反复踩坑必读

## 核心规则

`terminal()` 工具的 `workdir` 参数**只在单次调用内有效**。`cd X && command` 在同一条命令里能用，但**新开 terminal() 调用 cwd 又回到 $HOME**（默认）。

```
❌ 错: terminal 1 跑 `cd ~/.hermes && git status`，terminal 2 跑 `git status` → 报 "not a git repository"
✅ 对: terminal 1 跑 `cd ~/.hermes && git status`，terminal 2 跑 `cd ~/.hermes && git status`（每条都重 cd）
✅ 对: terminal 1 跑 `git -C ~/.hermes status`（指定 -C）
✅ 对: terminal 1 跑 `git status`，但带 workdir="/home/tangxuan/.hermes" 参数
```

## 3 套解决方案

### 方案 A: `workdir` 参数（**最稳**）

```python
terminal(
    command="git status",
    workdir="/home/tangxuan/.hermes",  # ← 关键
)
```

**适用**: 单条命令，路径固定。**不适用**: 长 && 链需要切多个目录。

### 方案 B: 同条命令 `cd ... && ...` 包裹

```bash
cd /home/tangxuan/.hermes && git add SOUL.md && git commit -m "..."
```

**适用**: 复杂命令链。**不适用**: 多条独立 terminal 调用（每条都得重 cd）。

### 方案 C: `git -C` / `cd 内置` 标志

```bash
git -C /home/tangxuan/.hermes status
git -C /home/tangxuan/.hermes log --oneline -5
```

**适用**: 单 git 命令。**不适用**: 任意 shell 命令（很多命令没 -C）。

## 3 个最常见错误模式（2026-06-04 实战）

### 错误 1: 假设 `cd` 跨调用持久

```bash
# terminal call 1
cd /home/tangxuan/.hermes  # ← 假设切换生效
git status                  # ← 实际跑在 ~/.hermes 没问题
# terminal call 2（不同 terminal()）
git status                  # ← ❌ "fatal: not a git repository"
```

**原因**: 每次 `terminal()` 调用是独立 shell session，cwd 不保留。
**正解**: 每条 terminal 命令都显式切目录或用 workdir。

### 错误 2: `&&` 链在某步失败但没看到

```bash
cd /path/that/does/not/exist && git add SOUL.md
# ↑ cd 失败 → git add 也不跑（因 &&）
# 但只看 output 容易误以为 git add 跑了
```

**正解**: cd 后用 `pwd` 验证一下，或 `cd ... || exit 1`。

### 错误 3: 相对路径在错误 cwd 下静默

```bash
# 假设在 /home/tangxuan/.hermes 跑
cat CHANGELOG.md.bak.*       # ← 在 /home/tangxuan 跑就找不到
echo "log" >> ../log.txt     # ← 路径相对 /home/tangxuan
```

**正解**: 涉及相对路径时**必用 `workdir=`** 或 `cd ... &&` 同条包裹。

## 4 个相关 pitfall

### Pitfall 1: 在 ~/.hermes 跑的 git 命令 vs 别的项目

~/.hermes 是 git 仓（`hermes-config`），但 `hermes-web-ui` 是另一仓。**不能在 ~/.hermes 下 git log hermes-web-ui 路径**——会报 "not a git repository" 或查到错的 history。

**正解**: hermes-web-ui 命令用 `workdir="/home/tangxuan/.hermes-web-ui/src"`。

### Pitfall 2: `hermes-agent` 子目录

`~/.hermes/hermes-agent/` 又是独立 venv。venv 激活命令 `source .venv/bin/activate` **仅当 cwd 在 hermes-agent 才有效**。

**正解**: 
```bash
cd /home/tangxuan/.hermes/hermes-agent && source .venv/bin/activate && python3 -c "..."
```

### Pitfall 3: `bash -c '...'` vs `bash -c 'cd X && ...'`

```bash
# 错: bash -c 'cd X && cmd' 在新 subshell 跑，cwd 跟外面不共享
bash -c 'cd /foo && git status'   # 外部 cwd 仍是 $HOME
git status                         # 报 not a git repo

# 对: 不用 bash -c，直接写
cd /foo && git status              # 同条命令内有效
```

### Pitfall 4: `git -C` 在 bash 链里要小心引号

```bash
git -C "/path with spaces/repo" status  # ✅
git -C /path\ with\ spaces/repo status  # ✅ shell escape
git -C "/path with spaces/repo" log -1   # ✅
```

## 验证清单（每次跑完 terminal 命令后 5 秒检查）

- [ ] 输出说 "not a git repository" / "No such file" → cwd 错了
- [ ] 用 `pwd && git rev-parse --show-toplevel` 在末尾验 cwd
- [ ] 长 && 链用 `&& echo OK` 结尾，确认跑完
- [ ] 跨 terminal() 调用时**每条都显式切目录**
- [ ] 涉及相对路径时**必用 workdir**

## Related

- `references/git-commit-staging-verification.md` — 3 步 commit gate（cwd 错会污染 stat）
- `references/sibling-multisession-share/` — multi-session 共享 `~/.hermes/` 的 cwd 隔离
- SKILL.md Pitfalls 段："凭印象作答是铁律级错误" — cwd 错了还在脑补命令会跑对 = 凭印象

## 触发场景

跑 terminal 命令报 "fatal: not a git repository" / "No such file or directory" / "Permission denied" 时立即看本 reference。
