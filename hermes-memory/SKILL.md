---
name: hermes-memory
description: >
  Hermes 记忆系统管理助手。当用户提到以下任何场景时触发：
  "整理记忆""记忆健康""记忆系统""清理记忆""删除记忆""记忆太乱"
  "记忆合并""降级记忆""升级记忆""跨层迁移""记忆分层""MEMORY.md"
  "USER.md""fact store""memory_store.db""holographic""fact_store"
  "记忆查看器""memory viewer""打开 memory viewer""启动记忆查看器"
  "browser memory""可视化记忆""memory management" 等。
  本 Skill 三件事：(1) 维护 MEMORY.md / USER.md / memory_store.db
  三层记忆的规范（合并、跨层迁移、删除），按 P0-P3 优先级分级；
  (2) 启动 `scripts/memory_viewer_server.py` 启动浏览器可视化查看器，
  支持直删/编辑/新增，端口 8649；(3) 每次会话结束跑一次健康度评估。
  **不要 undertrigger**——用户说"我的记忆乱了""想整理一下 agent 记忆"
  "memory 太多了"时必须加载本 Skill。
version: 1.0.0
author: Mr.Tang
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [memory, fact-store, knowledge-management, viewer, hermes]
    related_skills: []
---

# Hermes 记忆系统管理

> 脚本：`scripts/memory_viewer_server.py`（单文件 Python，含 HTTP 服务 + 嵌入式 HTML）

记忆系统分三层，根据使用频率存放于不同存储：

```
┌──────────────────────────────────────────────────┐
│  Layer 1: MEMORY + USER PROFILE (always-on)       │
│  容量: ~8,000 chars · 每次对话自动注入             │
│  存储: ~/.hermes/memories/MEMORY.md + USER.md      │
│  工具: memory(action)                              │
│  内容: P0/P1 高频事实                              │
├──────────────────────────────────────────────────┤
│  Layer 2: FACT STORE (query-on-demand)             │
│  容量: 无限制(SQLite) · 需主动查询才加载            │
│  存储: ~/.hermes/memory_store.db · FTS5全文搜索     │
│  工具: fact_store(action=search/probe/reason)      │
│  内容: P2 实体知识、跨session参考数据               │
├──────────────────────────────────────────────────┤
│  Layer 3: SKILLS (load-on-demand)                  │
│  容量: 无限制 · 被触发或手动加载才注入              │
│  存储: ~/.hermes/skills/ · SKILL.md + references    │
│  内容: P3 工作流、步骤指南、技术笔记                │
└──────────────────────────────────────────────────┘
```

---

## 优先级体系 (P0-P3)

| 级别 | 频率 | 例子 | 存放位置 |
|---|---|---|---|
| **P0** | 每条消息必用 | `terminal.backend`, proxy 地址, venv 规范 | Memory |
| **P1** | 每会话频繁用 | 模型配置, 搜索策略, 微信网关, git repo | Memory |
| **P2** | 偶尔用/实体相关 | 主人身份/论文, 日报系统, hermes-web-ui 细节 | Fact Store |
| **P3** | 少用/历史参考 | legacy 项目, 调试技巧, python-docx 教训 | Fact Store / Skill |

**谁来决定：**
- 初始由小糖根据使用频率判断
- 运行中通过查看器人工调整
- 数据驱动：Fact Store 的 `retrieval_count` 作为客观依据

---

## 合并规则

**遇到以下情况必须合并，不留冗余：**

1. **同实体合并** — 关于同一个事物/项目的多条条目 → 合并为一条，用要点列举
2. **同拓扑合并** — 同一个配置/问题的不同方面 → 合并
3. **因果链合并** — 问题的原因 + 修复方案 → 合并为一条"坑点+修法"
4. **技能引用合并** — 提到 skill 名称的 → 合并到一条，统一指向 skill 而非重复内容

**合并后格式：**
```
核心一句话。
- 要点1：详细
- 要点2：详细
→ 详情见 skill: xxx
```

---

## 记忆查看器 (Memory Viewer)

**启动：**
```bash
python3 ~/.hermes/skills/hermes-memory/scripts/memory_viewer_server.py
# 浏览器打开 http://localhost:8649
```

**功能：**
- 三按钮操作：✏️ 编辑 · ✕ 删除（带确认）· + 新增
- 数据实时持久化到 MEMORY.md / USER.md / memory_store.db
- 删除带确认弹窗 + 视觉动画
- 编辑支持 Markdown 多行，Fact Store 还能改 category/tags
- ThreadingMixIn + SQLite WAL，并发无忧

**为什么选 8649：**
- hermes-web-ui 用 8648 → 紧挨着避免冲突
- WSL2 自动转发 `localhost:8649` 到 Windows 浏览器

**与对话配合：**
- 简单操作（删除某条）→ 浏览器直接做
- 复杂操作（合并两条/调整优先级/跨层迁移）→ 告诉小糖"把 X 和 Y 合并"

---

## 维护节奏

| 频率 | 动作 | 执行者 |
|---|---|---|
| **每次会话结束** | 健康度评估（新知识要记？冗余要清？） | 小糖 |
| **每周** | 打开查看器扫一遍，标记不再需要的 | 主人 |
| **每月** | 合并同类项、降级/删除低价值条目 | 小糖 |
| **每季度** | Fact Store 清理 retrieval_count=0 且 >30天 | 小糖 |
| **Hermes update 后** | 检查 MEMORY.md 中是否被覆盖的配置 | 小糖 |

---

## 数据流向

```
发现新知识
    │
    ▼
[临时上下文] ← 首次出现，未确认价值
    │ (确认有用，出现2+次)
    ▼
┌───────────── P0/P1 ──────► MEMORY (always-on)
│              │
│              P2 ──────────► Fact Store (query-on-demand)
│              │
│              P3 ──────────► Skill (load-on-demand)
│                             │
│              (workflow定型)  ▼
│                           Skill 固化
│
└── 过期/无用 ──► 删除 (via 查看器)
```

---

## 重要：不记录什么

- ❌ bug 修复过程（具体错在哪、怎么改）
- ❌ 中间调试对话（端口冲突、cache 问题等）
- ❌ 临时会话状态（"现在在做 X"）
- ❌ 重复的事实（已在 Skill/Fact Store/Memory 中存在的）

只记录：
- ✅ 环境事实（端口、路径、配置）
- ✅ 用户偏好（工作流、测试标准、决策模式）
- ✅ 项目细节（架构、约定、坑点）
- ✅ 跨 session 有价值的经验

---

## 技术细节

**后端架构：**
- `http.server.HTTPServer` + `ThreadingMixIn`（多线程）
- SQLite WAL 模式 + busy_timeout=5000（避免锁竞争）
- 三个 API：GET `/api/data` · POST `/api/delete` · POST `/api/update` · POST `/api/create`

**存储位置：**
- `MEMORY.md` / `USER.md`：纯文本，`§` 分隔
- `memory_store.db`：SQLite，包含 `facts` / `entities` / `fact_entities` 表

**端口选择：**
- 8648 是 hermes-web-ui（已有，主人熟）
- 8649 紧挨着，记忆查看器专用
- 避免常用端口冲突（8650/3000 等可能有其他服务）
