---
name: patch-tool-markdown-bold-pitfall
description: Hermes `patch` 工具对 Markdown 加粗 `**text**` 处理有 bug — `old_string` 包含 `**...**` 时，patch 后的 new_string 可能丢失开/闭 `**`，或被部分删除。涉及改 SOUL.md / config.yaml 注释 / CHANGELOG.md 段标题等加粗段时必读。
---

# patch 工具 Markdown 加粗转义 Bug

## 核心规则

Hermes `patch` 工具在处理 `old_string` 含 `**...**`（Markdown 加粗）时，**`new_string` 中的 `**` 可能被吞掉**（开/闭的星号对消失，或整个 `**...**` 段被截断）。

**必做**: 改完 `**...**` 段后**立即 read_file 验证** `**...**` 是否完整（开闭成对）。

## 触发场景

- 改 `SOUL.md` 的 `**核心铁律**` / `**红线**` / `**Update survival pitfall:**` 等加粗段
- 改 `CHANGELOG.md` 的 `**提交 xxx**` 段
- 改 `config.yaml` 注释里的加粗字段名
- 改 skill SKILL.md 段标题加粗

## 3 个症状模式

### 症状 1: 闭 `**` 丢失

```markdown
# 改前（old_string）
**Update survival pitfall:** ... To survive updates:

# 改后（new_string）
### ⚠️ 凭印象作答是铁律级错误

# 实际写入（patch 工具输出）
### ⚠️ 凭印象作答是铁律级错误
# ↑ 看起来对，但 read_file 时发现 line 之前 "Update survival pitfall" 整段还在（duplicate block）
```

**根因**: patch 的模糊匹配命中了"相似但不唯一"的 old_string，导致替换只替换了部分内容。

### 症状 2: 开 `**` 丢失

```markdown
# 改前
**YAML 字段操作铁律：** 用 `re.sub`...

# 改后
**YAML 字段操作铁律：** 用 `re.sub` 在 raw text 上做精准替换...

# 实际写入
YAML 字段操作铁律：**用 `re.sub` 在 raw text 上做精准替换...
# ↑ 开 ** 丢了
```

### 症状 3: 整段加粗 `**...**` 被吞

```markdown
# 改前
Some text **重点强调**.

# 改后
Some text 重点强调（更多文字）.

# 实际写入
Some text 重点强调（更多文字）.
# ↑ 整对 ** 被吞
```

## 4 个防御步骤

### 步骤 1: patch 前 cat 原文件（先验证 unique match）

```bash
# 改前先 grep 看 old_string 在文件里是否唯一
grep -c "Update survival pitfall" ~/.hermes/skills/.../SKILL.md
# 期望: 1 (唯一)
# 若 > 1 → old_string 不够长，加更多上下文
```

### 步骤 2: patch 用足够上下文

```python
# ❌ 短 old_string（不唯一）
patch(old_string="Update survival pitfall", new_string="...")

# ✅ 长 old_string（含上下文行）
patch(old_string="**Update survival pitfall:** `hermes update` pulls...\n\n完整改 SOUL.md 的流程见...", new_string="### ⚠️ 凭印象作答是铁律级错误\n\n完整改 SOUL.md 的流程见...")
```

### 步骤 3: patch 完**立即 read_file 验证**

```python
# patch 完成后
read_file(path, offset=<改的行附近>, limit=5)
# 视觉确认 **...** 开闭成对
```

### 步骤 4: 用 git diff 终极验证

```bash
git diff <file> | grep -E '^[+-]\*\*' 
# 看 + 行和 - 行的 ** 是否成对变化
```

## 替代方案：直接 sed / write_file

如果 patch 反复失败（多次 patch 同一段），**改用 write_file** 重写整文件：

```python
# 1. 先 read_file 拿完整内容
content = read_file(path)

# 2. Python str.replace() 做精确替换
new_content = content.replace("**Update survival pitfall:** ...", "### ⚠️ 凭印象作答...")

# 3. write_file 写回（先备份）
import shutil
shutil.copy(path, "/tmp/<file>.bak.<ts>")
write_file(path, new_content)

# 4. diff 验证
import subprocess
print(subprocess.run(["diff", "/tmp/<file>.bak.<ts>", path], capture_output=True).text)
```

## 4 个 case study（2026-06-04 实战）

### Case 1: SOUL.md 升级（patch 成功）

- old_string: SOUL.md 第 7-10 行 3 段（无加粗）
- new_string: 派活前/派活时/派活后 + 3 红线（新加粗）
- 结果: 成功（因 old_string 无 `**`）

### Case 2: SKILL.md sibling 复制粘贴修复（patch 多次）

- 第 1 次 patch: 删重复段 — 成功
- 第 2 次 patch: 删 `**Update survival pitfall:**` 整段 — 失败（new_string 里 `### ⚠️` 段没出现，整段被吞）
- 第 3 次 patch: 重新写 new_string with 足够上下文 — 成功

**教训**: sibling 留的"加粗段"特别脆弱，patch 时必须用 line 全文作为 old_string，不能只 match 标题。

### Case 3: CHANGELOG.md 多文件 sed 追加（OK）

- 用 `cat >> CHANGELOG.md << EOF` heredoc 追加 — 成功（因为新加的内容是新增，不涉及改旧加粗段）

**教训**: append-only 不会触发 patch bug；问题主要在改既有加粗段时。

### Case 4: config.yaml xiao-tang 段清理（用 Python 不用 patch）

- 用 `lines[22:107] = []` 切片删除 — 成功
- 原因: 大段删除（85 行）不适合 patch 模糊匹配，直接 Python 处理更稳

## Related

- `references/soul-md-editing-protocol.md` — SOUL.md 改版流程（涉及 `**核心铁律**` 段编辑）
- `references/terminal-cwd-persistence-pitfall.md` — patch 前的 grep 验证在哪个 cwd 跑
- SKILL.md Pitfalls 段："凭印象作答是铁律级错误" — patch 失败后靠脑补"应该改对了" = 凭印象

## 触发场景

`patch` 工具改含 `**...**` 段后**没立即 read_file 验证** → 几乎必中招。
