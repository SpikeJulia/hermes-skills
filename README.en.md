<div align="center">

[中文](./README.md) · **English**

# 🔮 Hermes Skills

#### Some Hermes Agent Skills Mr.Tang uses daily, open-sourced here

[![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-1-3B82F6?style=for-the-badge)](#-skills)
[![Hermes](https://img.shields.io/badge/Hermes-Agent_Skill-8B5CF6?style=for-the-badge)](https://github.com/SpikeJulia/hermes-config)

![Hermes Agent](https://img.shields.io/badge/Hermes_Agent-Skill-6c5ce7?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude_Code-Compatible-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Compatible-10B981?style=flat-square&logo=openai&logoColor=white)
![OpenCode](https://img.shields.io/badge/OpenCode-Compatible-3B82F6?style=flat-square)

</div>

These Skills have been battle-tested in my own projects. Nothing fancy, just useful stuff.

Each Skill is a structured `SKILL.md` + `scripts/` package. Clone it, or let your Agent install it from the GitHub link directly.

---

## 📋 Table of Contents

| Name | One-liner |
|---|---|
| 🧠 [**hermes-memory (Memory Management)**](#-hermes-memory-memory-management) | Three-layer memory housekeeping + browser viewer |

---

## 📦 Installation

Ask your Agent:

```
Install this skill: https://github.com/SpikeJulia/hermes-skills/tree/main/hermes-memory
```

Or clone manually:

```bash
git clone https://github.com/SpikeJulia/hermes-skills.git
cp -r hermes-skills/hermes-memory ~/.hermes/skills/
```

---

## ✨ Skills

<table>
<tr><td>

### 🧠 hermes-memory (Memory Management)

> *"After a while, MEMORY.md bloats and fact_store accumulates mysteries. Why not just open a browser and clean it up?"*

Hermes Agent has a three-layer memory system (`MEMORY.md` / `USER.md` / `fact_store.db`). This Skill manages them by P0–P3 priority and ships a **browser-based visual viewer** for instant CRUD.

**Why it matters**

Outdated memories and duplicate facts make the Agent dumber over time. Not the model — the memory rots. Hand-editing MEMORY.md is painful: long file, `§` delimiter, easy to break. This Skill gives you a GUI. Three seconds per delete, three seconds per edit.

**What it does**

- **Three-layer memory governance** — merge duplicates, classify by P0–P3, migrate between layers
- **Browser visual viewer** on port 8649 — add/edit/delete Markdown entries, edit category and tags for Fact Store
- **Per-session health check** — remind the butler to capture new knowledge and prune redundancies

**How to trigger**

```
tidy up memory
memory health check
merge those facts
open memory viewer
launch the viewer
sync up my memory
```

**🌐 Cross-platform**: Hermes Agent · Claude Code · Codex · OpenCode

→ [SKILL.md](./hermes-memory/SKILL.md) · [Architecture](./hermes-memory/references/memory-architecture.md) · [Viewer Details](./hermes-memory/references/viewer-architecture.md)

</td></tr>
</table>

---

## 🌟 About

I'm Mr.Tang, a regular person serving the people, who likes tinkering with AI.

These Skills are what I actually use every day. If they help you, a ⭐ is appreciated. Issues / Discussions are always welcome.

---

## 📜 License

[MIT](./LICENSE)
