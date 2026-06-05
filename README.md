<div align="center">

**中文** · [English](./README.en.md)

# 🔮 MrTang Skills

#### Mr.Tang 日常在用的一些 Agent Skill，开源在这里

[![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-2-3B82F6?style=for-the-badge)](#-skills)
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
