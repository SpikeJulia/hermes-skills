# Hermes 记忆系统 — 存储架构参考

> 当 SKILL.md 不够用时，加载这份。它记录**数据住在哪、什么格式、什么 schema**，是迁移/合并/调试时的速查表。

---

## 三层存储一览

| 层 | 物理位置 | 格式 | 工具 | 何时加载 |
|---|---|---|---|---|
| **L1 Memory** | `~/.hermes/memories/MEMORY.md` | 纯文本，`§` 分隔条目 | `memory(action)` | 每条消息自动 |
| **L1 User Profile** | `~/.hermes/memories/USER.md` | 纯文本，`§` 分隔条目 | `memory(target=user)` | 每条消息自动 |
| **L2 Fact Store** | `~/.hermes/memory_store.db` | SQLite（含 FTS5 全文索引） | `fact_store(action=*)` | 主动查询 |
| **L3 Skills** | `~/.hermes/skills/<name>/SKILL.md` | YAML frontmatter + Markdown | `skill_view(name)` | 触发词/手动 |

---

## L1 文件格式（MEMORY.md / USER.md）

```markdown
第一条内容
§
第二条内容
§
第三条内容
```

- **分隔符**：section sign `§`（不是 `|`、不是空行）
- **空白处理**：split 后每段 `.strip()`，空段自动忽略
- **没有标题、没有 metadata、没有 timestamp**——纯内容条目
- **顺序就是渲染顺序**

### 容量与字符限制
- 单个 entry 按 **字符数**（不是 token）限制
- MEMORY.md + USER.md 一起注入到每条 system prompt，受总字符预算限制
- 实测安全区：单文件 ≤ 4,000 chars，合并后 ≤ 6,000 chars

---

## L2 SQLite Schema

```sql
-- 核心事实表
CREATE TABLE facts (
    fact_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    content      TEXT    NOT NULL,
    category     TEXT    DEFAULT 'general',  -- user_pref | project | tool | general
    tags         TEXT    DEFAULT '',          -- comma-separated
    trust_score  REAL    DEFAULT 0.5,
    retrieval_count INTEGER DEFAULT 0,
    created_at   TEXT    DEFAULT (datetime('now')),
    updated_at   TEXT
);

-- 实体表（用于关系推理）
CREATE TABLE entities (...);

-- 事实-实体关联表
CREATE TABLE fact_entities (fact_id, entity_id);

-- FTS5 全文索引
CREATE VIRTUAL TABLE facts_fts USING fts5(
    content, category, tags,
    content='facts', content_rowid='fact_id'
);
```

### Category 取值
- `user_pref` — 用户偏好
- `project` — 项目配置
- `tool` — 工具/技术细节
- `general` — 通用知识

### Tags
- 用逗号分隔的纯字符串：`"hermes,config,git"`
- 不要带空格、特殊字符
- 检索时按 substring 匹配，不是精确分词

### 重要操作注意事项

**多进程并发读写 → 必开 WAL 模式：**
```python
conn = sqlite3.connect(str(FACT_DB))
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=5000")
```

不开 WAL 会出现"database is locked"假死，原因：Hermes 主进程可能同时持有连接。

**FTS5 触发器：**
`facts_fts` 通过 trigger 同步，**直接 `DELETE FROM facts` 不会触发 FTS 重建**。如果做批量清理，要手动：
```sql
INSERT INTO facts_fts(facts_fts) VALUES('rebuild');
```

---

## 字段命名约定（避坑）

后端 API 返回的 JSON：
```json
{ "memory": [...], "profile": [...], "facts": [...], "stats": {...} }
```

前端 section ID 通常用 `memory` / `profile` / **`factstore`**（带 store 后缀，更语义化）。

**这个错我已经踩过一次了**——任何自定义查看器/工具，要在前端做 `keyMap` 映射：
```js
const keyMap = { memory: 'memory', profile: 'profile', factstore: 'facts' };
const items = data[keyMap[section]] || [];
```

不要假设后端字段名匹配 section ID。

---

## 容量监控阈值

| 指标 | 绿灯 | 橙灯（该合并/清理） | 红灯（紧急） |
|---|---|---|---|
| MEMORY.md | < 3,000 chars | 3,000-5,000 | > 5,000 |
| USER.md | < 1,000 chars | 1,000-1,500 | > 1,500 |
| Fact Store | < 30 条 | 30-60 条 | > 60 条 |
| `retrieval_count = 0` 占比 | < 30% | 30-60% | > 60% |

**统计命令：**
```bash
wc -c ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md

sqlite3 ~/.hermes/memory_store.db \
  "SELECT COUNT(*), SUM(retrieval_count) FROM facts"

sqlite3 ~/.hermes/memory_store.db \
  "SELECT COUNT(*) FROM facts WHERE retrieval_count = 0"
```

---

## 相关陷阱

- **❌ 不要用 `paragraph.text = "..."` 编辑 MEMORY.md 风格的纯文本**（这是 python-docx 的坑，别串台）
- **❌ 不要假设 hermes 主进程没在用 DB**——任何直接读写 `memory_store.db` 的脚本都要 WAL + 短事务
- **❌ 不要把"待确认"的事实写进 Memory**——Memory 是 high-confidence 区，新事实先去 Fact Store 验证
- **✅ Fact Store 改 category 不会重建 FTS**——如果改了 category 想让搜索命中，删除后重插
- **✅ Memory 条目合并后要重读**——合并是 destructive 的，先 backup：`cp MEMORY.md MEMORY.md.bak`
