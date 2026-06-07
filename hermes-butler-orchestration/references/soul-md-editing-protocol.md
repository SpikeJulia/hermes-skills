# SOUL.md Editing Protocol

主人 Mr. Tang 的 SOUL.md 改动需要走一套特殊流程，区别于普通 config 文件。
原因：SOUL.md 在 `~/.hermes/.gitignore` 第 55 行被**故意排除**（人格隐私 + 可移植），
不在 git 仓里；改动一旦失误没有 git 历史兜底，必须靠**流程防御**。

## When to use

- 主人说"升级一下管家铁律" / "改一下 SOUL.md" / "把人设再调一调"
- hermes 升级/迁移后需要恢复本地 SOUL.md 改动
- 跨设备同步 SOUL.md 内容

## Steps

### 1. 改前必查：当前 SOUL.md 实际内容

```python
read_file(path="/home/tangxuan/.hermes/SOUL.md")
```

**不要凭印象写草稿**——这是铁律级错误。草稿基于 SOUL.md 实际内容蒸馏，不是基于
"我以为 SOUL.md 里有什么"。

### 2. 改前必查：当前 skill 实际内容

如果主人提的是工作流/铁律类改动，先查相关 skill 源文：

```python
# 例：主人说"升级管家铁律"
read_file(path="/home/tangxuan/.hermes/skills/software-development/subagent-driven-development/references/butler-agent.md")
```

skill 内容是蒸馏 SOUL.md 改动的**输入源**，不能跳过。

### 3. 写草稿到 /tmp，不直接动 SOUL.md

```python
write_file(
    path="/tmp/soul-md-draft-v1.md",
    content="<草稿>"
)
```

理由：草稿要先给主人过目拍板，再写进真 SOUL.md。/tmp 是 working area。

### 4. 主人拍板后，patch 精准替换（不重写整文件）

```python
patch(
    mode='replace',
    path='/home/tangxuan/.hermes/SOUL.md',
    old_string='<原段落，含足够上下文确保唯一>',
    new_string='<新段落>',
)
```

要点：
- **old_string 必须唯一**（加 3-5 行上下文），否则 patch 报 ambiguous
- **不要 write_file 重写整个 SOUL.md**——会丢其他段落（说话风格、场景反应、2077 习惯）
- patch 工具返回的 diff 要**人工看一眼**确认只动了目标段

### 5. 改后必做：备份 + 验证

```bash
# 备份
cp ~/.hermes/SOUL.md /tmp/SOUL.md.bak.$(date +%Y%m%d-%H%M%S)

# 验证：行数变化 + head/tail 抽查
wc -l ~/.hermes/SOUL.md
head -25 ~/.hermes/SOUL.md  # 确认来历段 + 改后的核心铁律段
```

### 6. 是否入仓：先问主人再决定

主人对 SOUL.md 入仓有 3 种意图，需要拍板（参考 2026-06-04 会话）：

- **A. 本地有就行**（最常见，符合原设计）：不动 git
- **B. SOUL.md 进仓**：先看 .gitignore 第 55 行，移出 SOUL.md；**警告主人公开 repo 暴露**
- **C. SOUL.md 留本地 + CHANGELOG.md 记一笔**：当前 master 分支实际做法

**默认行为**：主人说"得保留"时**先 clarify 哪种含义**，不要直接动手。

## Pitfalls

### ❌ 不要把 skill 内容当 SOUL.md 复述
2026-06-04 翻车：主人问"管家铁律是什么"，我把 dispatch-checklist、role 模板、
3-fix 限制全列出来——这些 80% 来自 skill 不是 SOUL.md。SOUL.md 改版应只蒸馏
"人格级原则"，具体技术细节靠 skill 兜底。

### ❌ 不要用 write_file 重写整个 SOUL.md
SOUL.md 48-59 行承载来人设细节（说话风格、场景反应、2077 习惯、撒娇边界、红线），
write_file 重写会丢这些。**永远用 patch 精准替换。**

### ❌ 不要 commit SOUL.md 到 ~/.hermes git 仓
`.gitignore` 第 55 行排除 SOUL.md 是主人**故意设计**（人格隐私 + 可移植）。
commit 前必须 grep .gitignore 确认排除规则，否则一旦 push 公开 repo 暴露人格。

### ❌ 改前不查就写草稿
基于"我以为 SOUL.md 有什么"写草稿 = 凭印象作答。**先 read_file 实际内容**再蒸馏。

### ❌ SOUL.md 含不可见 unicode 触发 prompt injection 防御（2026-06-04 教训）
**完整内容见 `references/content-file-invisible-unicode-pitfall.md`** —— 该 reference 覆盖：
- 4 种触发字符（U+200D / U+200B / U+200C / U+FEFF）的 UTF-8 字节级检测
- 适用 SOUL.md / MEMORY.md / USER.md / 任何 content file（**不只 SOUL.md**）
- 修复 Strategy 1（拆复合 emoji）/ Strategy 2（strip all）/ Strategy 3（patch 精准）
- 2026-06-04 `🐈‍💨` → `🐈💨` 完整 case study + 诊断流程

**SOUL.md 编辑流程强制项**：改后**必跑** invisible Unicode 检测（脚本见新 reference "Detection" 段）。

## Related

- `butler-agent.md`（references/）— SOUL.md 管家铁律的源 skill，本次改动的"输入"
- `.gitignore` 第 55 行 — 排除 SOUL.md 的规则
- 2026-06-04 会话原文：本次 protocol 提炼来源
