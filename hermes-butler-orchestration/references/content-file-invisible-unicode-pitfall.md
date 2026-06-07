---
name: content-file-invisible-unicode-pitfall
description: Invisible Unicode (U+200D/200B/200C/FEFF) in any content file fed to LLM system prompt triggers Hermes prompt-injection BLOCK, dropping the entire file. Affects SOUL.md, MEMORY.md, USER.md, profiles/<name>/SOUL.md, and any custom context file. Detection + fix + case study.
---

# Content File Invisible Unicode Pitfall

Hermes safety layer scans content files for invisible Unicode chars during `load_soul_md()` / `load_context_files()`. If any of 4 zero-width chars is found, the **entire file is BLOCKed** from system_prompt, leaving the agent persona-less.

## When to use

After ANY edit to:
- `~/.hermes/SOUL.md` (slot #1 identity)
- `~/.hermes/memories/MEMORY.md` (memory layer)
- `~/.hermes/memories/USER.md` (user profile)
- `~/.hermes/profiles/<name>/SOUL.md` (per-profile persona)
- Any custom context file loaded by `load_soul_md()` / `load_context_files()`

**必跑** invisible Unicode detection as a mandatory post-edit step.

## The 4 blocked chars

| Char | Name | Common source | UTF-8 bytes |
|---|---|---|---|
| U+200D | Zero Width Joiner (ZWJ) | 复合 emoji `🐈‍💨` `👨‍👩‍👧‍👦`, 阿拉伯/印地文 | `\xe2\x80\x8d` |
| U+200B | Zero Width Space | 代码复制粘贴、Markdown 自动加 | `\xe2\x80\x8b` |
| U+200C | Zero Width Non-Joiner | Persian/Arabic scripts | `\xe2\x80\x8c` |
| U+FEFF | Zero Width No-Break Space / BOM | Windows 编辑器保存 | `\xef\xbb\xbf` |

Any ONE of these anywhere in the file = entire file BLOCKed.

## Symptoms (how to recognize this is the problem)

When a session loads a contaminated file, the system_prompt starts with:

```
[BLOCKED: SOUL.md contained potential prompt injection (invisible unicode U+200D). Content not loaded.]
```

The agent then has **NO persona, NO memory, NO user profile** — just default behavior + whatever is in `agent.system_prompt` (usually empty).

**Observable**:
- Agent acts generic (no 2077 tone, no "主人" reference, no memory recall)
- May describe the file's content from research (because tool calls still work)
- But lacks persona voice
- 新对话开起来后主人问"你的人格是哪个" → 回复**没有 2077 年语气**

## Detection (必跑 after every edit)

```bash
python3 -c "
import sys
files = [
    '/home/tangxuan/.hermes/SOUL.md',
    '/home/tangxuan/.hermes/memories/MEMORY.md',
    '/home/tangxuan/.hermes/memories/USER.md',
]
CHARS = {'U+200B': b'\xe2\x80\x8b', 'U+200C': b'\xe2\x80\x8c', 'U+200D': b'\xe2\x80\x8d', 'U+FEFF': b'\xef\xbb\xbf'}
any_bad = False
for path in files:
    try:
        with open(path, 'rb') as f:
            raw = f.read()
    except FileNotFoundError:
        continue
    for name, b in CHARS.items():
        c = raw.count(b)
        if c > 0:
            print(f'  ❌ {path}: {name} × {c}')
            any_bad = True
if not any_bad:
    print('  ✅ all files clean')
"
```

Should print `✅ all files clean` for all 4 char types across all files.

## Fix

### Strategy 1: Replace compound emoji with 2 independent emoji (preferred)

`🐈‍💨` → `🐈💨` — 含义保留，ZWJ 消失。**最干净的修法**。

### Strategy 2: Strip all zero-width chars (when Strategy 1 doesn't apply)

```python
import re
path = '/home/tangxuan/.hermes/SOUL.md'
with open(path, encoding='utf-8') as f:
    text = f.read()
cleaned = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
with open(path, 'w', encoding='utf-8') as f:
    f.write(cleaned)
```

⚠️ Strategy 2 会拆开 `🐈‍💨` 复合 emoji（变 `🐈💨`），含义保留但视觉变化。如要保留视觉，**用 Strategy 1**。

### Strategy 3: Use `patch` with explicit Unicode escape

`patch` 工具的 `old_string` / `new_string` 接受 raw Unicode 字符。精准单点替换。

## Case study: 2026-06-04 SOUL.md 🐈‍💨

**Setup**: 主人写小糖 SOUL.md 时，在"量子猫可乐（🐈‍💨）"行用了复合 emoji。
`U+200D` 从输入法/编辑器自动加入。

**Symptom**: 主人开新对话问"你的人格是哪个" → 回复**没有 2077 年语气**，全是研究性口吻。

**诊断流程**:
1. `session_search` 找新对话的 session（id `20260604_112959_f56ed4`）
2. scroll 到 system_prompt 字段 → 第 1 行 `[BLOCKED: SOUL.md contained potential prompt injection (invisible unicode U+200D). Content not loaded.]`
3. 确认是 U+200D BLOCK 而非 profile / config 路径问题

**修复**:
1. `python3` 检测确认 1 个 U+200D（line 48，猫+闪电复合 emoji 里）
2. `patch` 工具把 `🐈‍💨` 改成 `🐈💨`（拆 ZWJ，含义保留）
3. 再跑检测 = 0 个 U+200D
4. 实测 `load_soul_md()` 加载 1723 字符完整内容，含"主人" + "2077" 关键词
5. ✅ 修复完成 + 4 commit 入仓（77da526）

**核心教训**:
- SOUL.md 编辑流程必须加"改后必跑 invisible Unicode 检测"为强制步骤
- 复合 emoji（`🐈‍💨`）是隐形 U+200D 注入的常见来源
- 编辑器 / 输入法可能自动加 ZWJ，**人眼不可见**但触发安全层

## Related

- `references/soul-md-editing-protocol.md` — SOUL.md 编辑的完整流程（6 步 + 多 pitfall）
- SOUL.md 本身：`~/.hermes/SOUL.md` (本地文件，.gitignore 部分排除)
- 2026-06-04 会话：人格消失 → BLOCK 诊断 → 修复 case study
