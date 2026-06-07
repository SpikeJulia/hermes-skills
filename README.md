<div align="center">

**中文** · [English](./README.en.md)

# 🔮 MrTang Skills

#### Mr.Tang 日常在用的一些 Agent Skill，开源在这里

[![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-3-3B82F6?style=for-the-badge)](#-skills)
[![Hermes](https://img.shields.io/badge/Hermes-Agent_Skill-8B5CF6?style=for-the-badge)](https://github.com/SpikeJulia/hermes-config)

![Hermes Agent](https://img.shields.io/badge/Hermes_Agent-Skill-6c5ce7?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude_Code-Compatible-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Compatible-10B981?style=flat-square&logo=openai&logoColor=white)
![OpenCode](https://img.shields.io/badge/OpenCode-Compatible-3B82F6?style=flat-square)

</div>

都是在自己项目里跑通了一段时间，确实省事，才搬出来开源的。没什么花活，就是几个挺实用的东西。

每个 Skill 都是结构化的 `SKILL.md` + `scripts/`，可以单独 clone 走，也可以让 Agent 直接读 GitHub 链接安装。

---

## 📋 目录

| 名字 | 一句话 |
|---|---|
| 🎯 [**hermes-butler-orchestration（管家编排手册）**](#-hermes-butler-orchestration管家编排手册) | 管家调度子代理的操作系统 — 9 角色模板 + 15+ pitfall 库 + 治理宪法 |
| 🔍 [**official-source-research（定向调研）**](#-official-source-research定向调研) | 调研技术/产品时优先从官网/GitHub 官方仓库获取一手资料 |
| 🧠 [**hermes-memory-tool（记忆管理）**](#-hermes-memory-tool记忆管理) | 三层记忆的合并/降级/删除，配浏览器可视化查看器 |

---

## 📦 安装方式

让 Agent 直接读 GitHub 链接自己装：

```
帮我安装这个 skill：https://github.com/SpikeJulia/MrTang-Skills/tree/main/hermes-memory
```

或者手动 clone：

```bash
git clone https://github.com/SpikeJulia/MrTang-Skills.git
cp -r MrTang-Skills/hermes-memory ~/.hermes/skills/
cp -r MrTang-Skills/official-source-research ~/.hermes/skills/research/
```

---

## ✨ Skills

<table>
<tr><td>

### 🎯 hermes-butler-orchestration（管家编排手册）

> *"派子代理干活不是喊一嗓子就完事——得有角色模板、有 dispatch 清单、有 pitfall 库防止踩一样的坑。"*

从 Hermes 官方的 `subagent-driven-development`（v1.1.0，3 文件）**完全重写**为 v2.0.0（56 文件）。不再是"怎么用 delegate_task"的简单说明，而是 **SOUL.md 治理架构的执行手册索引层**——管家调度多个子代理的完整操作系统。

**和官方版的区别**

| | 官方 v1.1.0 | 这个 |
|---|---|---|
| 文件数 | 3 | 56 |
| 角色模板 | 无 | 9 个（implementer/reviewer/researcher/debugger/planner/documenter/数据分析师/tester/安全审查员） |
| Pitfall 库 | 无 | 15+（Vue 响应式、Claude Code、子代理验证、ACP provider 劫持……） |
| 治理模型 | 无 | governance-architecture + governance-model + verification-protocol |
| 管家专属 | 无 | butler-agent + 主人 meta 偏好 + option-framing 纪律 |

**它能做什么**

- 🧩 **9 个角色模板** — 派子代理时注入的角色约束，精准指派不跨领域
- 📋 **dispatch 清单** — 派发前的检查门禁，防止拍脑袋派活
- 🕳️ **15+ pitfall 库** — 踩过的坑文档化，下次不踩
- 🏛️ **五层治理宪法** — 严格遵守层次效力：`SOUL.md（宪法）→ SKILL.md（索引）→ references/（知识）→ templates/（执行）→ scripts/（操作）`。SOUL.md 冲突时最高优先，SKILL.md 含 governance_version 防静默漂移
- 🛡️ **验证协议** — 子代理自测可以、自验收不行；凭据说事，证据不完整 = 未验证

**怎么触发**

Agent 启动时作为 `hermes-butler-orchestration` skill 加载，无需手动触发。

**🌐 跨平台**：Hermes Agent

→ [SKILL.md](./hermes-butler-orchestration/SKILL.md)

</td></tr>
<tr><td>

### 🔍 official-source-research（定向调研）

> *"说'去看看 XXX'的时候，我希望你先去官网，不是看 CSDN。"*

当你说"看看 Supabase"、"调研一下 Windsurf"、"查一下 MiniMax 最新定价"时，自动执行四步调研流：**定位官网/GitHub → 深度阅读一手资料 → 按需深入 → 结构化汇报**，第三方内容仅作交叉验证。

**为什么需要这个**

Agent 拿 CSDN 文章当主要信源、凭 web_search snippet 交差、分不清官方仓库和社区 fork——这些问题一劳永逸解决。

**它能做什么**

- 🥇 官网首页 / 官方 Blog → 🥇 GitHub README/Releases → 🥈 官方文档站 → 🥉 第三方补充
- 结构化输出：官方信息 + 核心功能 + 关键发现 + 补充参考（标注来源）
- 含自检清单，确保每条结论都来自官方渠道

**怎么触发**

```
看看 XXX
去看看 XXX
调研一下 XXX
研究一下 XXX
了解下 XXX
查一下 XXX
```

**🌐 跨平台**：Hermes Agent · Claude Code · Codex · OpenCode

→ [SKILL.md](./official-source-research/SKILL.md)

</td></tr>
<tr><td>

### 🧠 hermes-memory-tool（记忆管理）

> *"Agent 用久了 MEMORY.md 越来越臃肿，fact_store 里还有一堆不知道是啥的东西——干脆开个浏览器直接管。"*

Hermes Agent 的记忆系统分三层（`MEMORY.md` / `USER.md` / `fact_store.db`），本 Skill 把它们按 P0-P3 优先级分级管理，配一个**浏览器可视化查看器**直接增删改。

**为什么需要这个**

Agent 看着过期的记忆和重复的事实，越用越笨。不是模型变笨，是记忆脑腐了。手动改 MEMORY.md 又痛苦——长文件、§ 分隔、容易改错。这个 Skill 给浏览器一个 GUI，三秒钟删一条改一条。

**它能做什么**

- **维护三层记忆的规范** — 合并同类项、按 P0-P3 优先级分层、跨层迁移
- **浏览器可视化查看器** — 端口 8649，直接增/删/改 Markdown 条目，Fact Store 还能改 category 和 tags
- **每次会话健康度评估** — "有新知识要记吗？""有冗余要清吗？"

**怎么触发**

```
整理记忆
记忆健康
记忆合并
降级那条
启动 memory viewer
打开浏览器查看器
sync up my memory
```

**🌐 跨平台**：Hermes Agent · Claude Code · Codex · OpenCode

→ [SKILL.md](./hermes-memory-tool/SKILL.md) · [架构详解](./hermes-memory-tool/references/memory-architecture.md) · [查看器详解](./hermes-memory-tool/references/viewer-architecture.md)

</td></tr>
</table>

---

## 🌟 关于

我是 Mr.Tang，一个为人民服务的普通人，喜欢鼓捣 AI 相关的小玩意儿。

这些 Skill 都是我自己每天在用的，开源出来如果对你有帮助，给个 ⭐ 就行。有问题或建议，欢迎在 Issues / Discussions 里说一声。

---

## 📜 License

[MIT](./LICENSE)
