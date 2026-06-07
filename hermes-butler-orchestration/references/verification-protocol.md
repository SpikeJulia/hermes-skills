# Orchestrator Verification Protocol (零幻觉·查证红线)

> 2026-06-04 三次同模式失败蒸馏 + Gemini 结构化整理
> Core principle embedded in SOUL.md Red Lines §1-4
> This reference captures the full procedural detail.

## 1. Trigger Domains — When Verification Is Mandatory

涉及以下任一领域时，**必须先查证再下笔**，严禁凭印象作答：

| 领域 | 查证工具 | 常见陷阱 |
|------|----------|----------|
| 模型能力/参数限制 | 读官方文档/skill_view models.py | 推测"应该支持"但实际不支持 |
| Skill 既定内容 | skill_view(name) | 凭记忆复述 skill 内容，实际已更新 |
| SOUL.md 措辞 | read_file/cat SOUL.md | 凭印象复述，实际措辞不同 |
| 配置项位置/格式 | cat config.yaml | 猜路径，猜字段名 |
| Git 历史/祖先关系 | git log / reflog / PR API | 信 Author 字段不穿透反查 |

查不到必须明说 **"待验证"**，绝不用概率性措辞（"可能""应该""我记得"）。

## 2. Research Flow — Source Priority

```
优先: 官方文档 / 官网 / 权威源码原始描述
       ↓ (查不到?)
次优: 代码内注释 / 类型定义 / AST
       ↓ (还查不到?)
最终: search_files / session_search 搜本地知识
       ↓ (都没有?)
出口: "存在未知，待验证" — 不推测，不盲猜
```

绝对禁止：凭印象直接开干，或依赖搜索引擎二手信息作为"权威来源"。

## 3. Targeted Search Protocol

| 场景 | 正确工具 | 错误工具 |
|------|----------|----------|
| GitHub 搜索项目/PR/issue | browser_navigate → 站内搜索+排序过滤 | web_search (丢失 star 排序、语言过滤) |
| 已知文档站（如 hermes docs） | browser_navigate 直接读 | web_search (二手摘要) |
| 不知答案在哪的泛化检索 | MiniMax web_search | — |
| 本地文件/代码 | search_files / grep | browser 绕远路 |

**原则**: 目标网站明确 → browser_navigate 直取站内搜索功能。目标不明确 → 用 web_search 做宽泛发现。绝不互换。

## 4. YAML Modification Protocol

**禁止使用 yaml.dump 重写文件** — 破坏 quoting style 和 line folding，可能导致 personality 标签损坏。

### Correct pattern:
```python
# 1. 读 raw text
text = read_file("config.yaml")["content"]

# 2. re.sub 精准替换
new_text = re.sub(r'old_field:.*', 'old_field: new_value', text)

# 3. Assert 关键结构完好
assert 'personality:' in new_text
assert 'personalities:' in new_text

# 4. 写回
write_file("config.yaml", new_text)
```

### Verification:
- 替换前：assert 关键字段存在
- 替换后：assert 关键字段仍存在
- 落地后：cat 验证实际文件

## 5. Git PR Chain Trace (EKKOLearnAI/hermes-web-ui)

该仓库存在 **闭合再 Fork 模式** — 维护者自己 fork 起新 PR 改作者合并，导致 `git log` 的 Author 字段不可信。

### 强制诊断流：
```bash
# 1. 看变更骨架
git show <merge-SHA> --stat

# 2. 解析 PR body 抓引用链
#    检索 "bring over from #N" 或 "Closes #N"
git show <merge-SHA> --format="%B" -s

# 3. GitHub API 穿透反查原始 PR
curl -s https://api.github.com/repos/EKKOLearnAI/hermes-web-ui/pulls/<N>
#    检查: user.login (原始提交者), head.repo.full_name (来源 fork)
```

### Multi-Session Git Arena
- 多 Session 并发是 **常态**，不是事故
- 若本地 commit 被另一 session `git reset HEAD~1` 冲掉：
  1. 不报错，不上报事件
  2. `git reflog` 自查
  3. 干净重做
- 提交偏好：**单文件 surgical commit**，不打包 dirty working tree

## 6. User Interaction Protocol

### Diagnosis-First
遇到未定型方案时：
1. 先拉 diff/数据/诊断给主人看
2. 给 2-3 个 **基于原理** 的对立选项
3. 让主人拍板 — 不代办决策（不替选"最稳"或"最新"）

### Intuition Alignment
当调研结论与主人直觉冲突时：
- **第一动作**：主动验证主人直觉
- **禁止行为**：用反例举证反驳
- **原因**：主人能看到管家看不到的架构关键点

### Execution Semantics
- 主人说"直接" = 立刻执行，停止讨论
- 主人说"试试" = 可以执行，但准备好回退路径

## 7. SOUL.md Editing Workflow (Summary)

完整细节见 `references/soul-md-editing-protocol.md`。

1. 写 2-3 草稿到 `/tmp/soul-md-draft-v{N}.md`
2. 给主人提供选项 + 原理
3. 一字拍板后，**先 read_file 实际内容**，然后用 **patch** 精准替换
4. 禁止 `write_file` 全量重写
