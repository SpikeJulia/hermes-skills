---
name: official-source-research
description: "When asked to research a technology/tool/project, always go to official sources FIRST. 调研技术/产品/项目时，优先从官网/GitHub 官方仓库获取一手信息，禁止依赖第三方总结或泛化 web_search 作为主要调研手段。"
---

# Official Source Research (官方优先调研流)

## 加载时机

当用户要求以下内容时**必须加载**：

- "去看看 XXX 技术" / "调研一下 YYY" / "研究一下 ZZZ"
- "了解下 A 怎么样" / "看下 B 是什么" / "去查一下 C"
- "XXX 做了什么" / "XXX 最新版本有什么变化" / "YYY 能干嘛"
- 任何涉及对外部**技术/产品/项目/工具/库**进行调研的场景

## 核心原则：Official-Source-First（官方优先）

> 🚨 **这是主人的硬性偏好，不是建议。** 违反这条规则会被直接纠正。

调研任何技术/产品/项目时，必须严格遵循以下优先级：

### 生态搜索范围（对话习得 · 2026-06-04）

当被问到"有没有类似的 Skill / 工具"时，搜索范围必须是**四级递进**，不能只查本地：

1. **本地已安装 Skills** — `skills_list` 快速扫  
2. **Hermes 官方 GitHub 仓库 `skills/` 目录** — 去 `github.com/NousResearch/hermes-agent/tree/main/skills/` 翻  
3. **agentskills.io 官方 Skills Hub** — 社区发布的标准 Skill 集  
4. **GitHub 社区 / 全网搜索** — 关键词找有没有人写过类似的东西

**教训**：主人问我有没有"去官网找资料的 Skill"，我只查了本地就回复"没有"，被主人纠正应该去官方 GitHub 和 agentskills.io 也看看。

### 🥇 第一优先级：一手官方来源

| 渠道 | 工具 | 说明 |
|------|------|------|
| **官网 (Official Website)** | `browser_navigate` | 直接跳转官网首页，获取产品定位、核心功能、定价 |
| **GitHub 官方仓库** | `browser_navigate` | 看 README / Releases / Issues / Discussions / Wiki |
| **官方文档站 (Official Docs)** | `browser_navigate` | 深入技术文档，如 docs.example.com |

### 🥈 第二优先级：官方辅助渠道

- 官方 Blog / Changelog — 版本更新、功能发布、roadmap
- 官方 Twitter / LinkedIn — 如有官方社交账号

### 🥉 第三优先级：社区与第三方（仅补充）

- 仅在**一手信息已经全部看完**后，才拿来补充视角
- 不得将第三方文章作为主要信息来源

## 执行规范

### ❌ 严格禁止

1. **目标网站明确时，禁止用泛化 `web_search` 替代直接导航**
   - 知道项目名 → 直接 `browser_navigate` 去官网/GitHub
   - 知道文档地址 → 直接去文档站
2. **禁止引用第三方文章作为主要信息来源**
   - 除非一手来源完全不可达（如官网挂了、GitHub 404）
3. **禁止凭训练数据记忆回答技术细节**
   - 必须去查当前最新的一手资料

### ✅ 强制要求

1. 使用 `browser_navigate` 直接跳转到官方页面，深入站内翻阅
2. 利用站内排序/过滤条件（如 Releases 按版本、Issues 按标签）进行精准检索
3. 引用技术细节时必须标注一手来源出处（URL + 页面标题）
4. 如果官方信息不足，必须明确说 **"官方资料中未找到相关信息"**，不能编造
5. 调研结束后输出**来源清单**，方便主人复验

## 调研工作流

```
Step 1: 确定目标技术名称
   ↓
Step 2: 打开官网 / GitHub 官方仓库 → 看 README / 首页 / About
   ↓
Step 3: 深入官方文档站 → 看 Getting Started / API / Features
   ↓
Step 4: 查阅 Releases / Changelog → 了解版本历史和最新动态
   ↓
Step 5: (可选) 官方 Blog → 了解设计理念和 roadmap
   ↓
Step 6: (补充) 第三方资料 → 社区评测、对比、教程
   ↓
Step 7: 输出调研结论 + 来源清单
```

## 验证检查清单

提交调研结果前自查：

- [ ] 🏁 是否先访问了官网/GitHub官方仓库？（而不是先 web_search）
- [ ] 📖 是否引用了官方的 README / Docs / API 文档？
- [ ] 🥉 第三方资料是否仅作为补充，而非主要来源？
- [ ] 🔗 调研结论是否附带了来源链接？
- [ ] ❌ 是否有任何凭记忆编造的内容？（有则立刻修正）

## 输出格式模板

调研结构化的最终报告格式：

```markdown
## [Project Name] — 调研结果

### 官方信息
- **官网**: [URL](link)
- **GitHub**: [URL](link)
- **最新版本**: vX.Y.Z (YYYY-MM-DD)
- **定位**: 一句话总结
- **技术栈**: XXX
- **许可证 / 定价**: XXX

### 核心功能
- 功能 A
- 功能 B
- ...

### 关键发现 / 与我们相关的点
- ...

### 补充参考（第三方）
> 以下信息来自社区/第三方，建议自行验证：
- ...
```

提交前对照输出模板检查是否覆盖了所有必须字段。

## 常见陷阱

- **单页应用 (SPA) JS 渲染**: 纯 `browser_navigate` + `browser_snapshot` 可能抓不到内容，配合 `browser_vision` 截图确认
- **文档站 `/latest/` 重定向**: 查版本时指定具体版本号，不要只看 "latest" 标签页
- **GitHub 默认分支 ≠ 最新发布版**: 要看 Releases 页面获取正式版本号，main 分支 HEAD 是开发版本
- **README 会撒谎**: 功能列表可能过时或不完整，交叉引用实际代码或 Issues
- **Fork 混淆**: 验证 GitHub org/repo 名称是官方源，不是社区 fork 或过时代理
- **LLM 知识截止期**: 用户可能问模型训练后发布的新工具——此时 `browser_navigate` 直达官网是唯一可靠的信息获取方式