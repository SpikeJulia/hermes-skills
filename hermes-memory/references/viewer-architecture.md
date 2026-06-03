# Hermes 记忆查看器 — 架构参考

> 单文件 Python HTTP 服务 + 嵌入式 HTML 的设计参考。包含已踩过的坑和修法。

---

## 整体设计

```
~/.hermes/skills/hermes-memory/scripts/memory_viewer_server.py
├─ 后端：Python http.server (单文件, ~700 行)
│   ├─ ThreadingMixIn (并发请求)
│   ├─ SQLite WAL 模式
│   └─ 4 个 API: GET /api/data · POST /api/delete · POST /api/update · POST /api/create
└─ 前端：嵌入式 HTML (r"""...""")
    ├─ Vanilla JS (无框架)
    ├─ 4 按钮: ✏️ 编辑 · ✕ 删除 (带确认) · + 新增 · 标题展开
    └─ Tailwind 风格的内联 CSS
```

**为什么单文件？** Agent 写、自己维护的内部工具，加打包/构建链是 over-engineering。单文件 = clone 即跑、修改一处生效、grep 容易。

---

## 启动方式

```bash
python3 ~/.hermes/skills/hermes-memory/scripts/memory_viewer_server.py
# → http://localhost:8649
```

**端口选择原则：**
- 紧挨着已有的 user-facing 端口（hermes-web-ui 用 8648 → 8649 邻居）
- 避免常见端口（3000/8000/8080 容易被抢）
- 确认是用户**还没用过的高位端口**，降低冲突概率

---

## 已踩过的 4 个坑（必看）

### 坑 1：单线程死锁
**症状：** 页面 HTML 200 但 `/api/data` 卡死 → JS 报 "连接失败"
**根因：** `http.server.HTTPServer` 单线程，浏览器同时请求 HTML + API，第二个请求要排队；SQLite 读阻塞了其他读
**修法：**
```python
from socketserver import ThreadingMixIn
class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in separate threads."""
```

### 坑 2：SQLite lock
**症状：** 多个客户端同时读报 "database is locked"
**根因：** 默认 rollback journal 模式，写锁独占
**修法：**
```python
conn.execute("PRAGMA journal_mode=WAL")     # Write-Ahead Logging
conn.execute("PRAGMA busy_timeout=5000")    # 5s 自动重试
```

### 坑 3：前后端 key 名不匹配
**症状：** JS 报 "Cannot read properties of undefined (reading 'forEach')"
**根因：** 后端返 `{facts: [...]}`，前端找 `data['factstore']` → undefined
**修法：** 前端做映射表 + 兜底：
```js
const keyMap = { memory: 'memory', profile: 'profile', factstore: 'facts' };
const items = data[keyMap[section]] || [];
```

### 坑 4：process 卡死无法 kill
**症状：** `pkill` / `kill PID` 都不响应
**根因：** 进程在某个 SQLite 操作上死锁，signal 排队中
**修法：** `pkill -9 -f memory_viewer_server` 强杀，或先 `ps -ef | grep memory` 找 PID

---

## 用户体验设计原则

| 原则 | 实现 |
|---|---|
| **点 ✕ 就删** | 不要做"标记 + 复制 + 粘贴"的多步流程。Agent 是辅助执行，不是审批人 |
| **删前确认** | `confirm()` 弹窗 + 内容预览，避免误删 |
| **删后反馈** | 视觉动画（淡出/位移）+ toast 提示，让人知道操作生效了 |
| **直改直存** | 改完点保存立即写文件，不做"暂存"区 |
| **失败可见** | 错误信息显示在页面，不要只 console.log |
| **空检查** | `data && data.stats` 才渲染；空数据/网络错都给明确文案 |

---

## API 规范

```
GET  /api/data
     → { memory: [], profile: [], facts: [], stats: {memory, profile, facts} }

POST /api/delete
     { section: "memory"|"profile"|"factstore", idx: "M1", fact_id?: number }
     → { ok: true } | { ok: false, error: string }

POST /api/update
     { section, idx, content, fact_id?, category?, tags? }
     → { ok: true } | { ok: false, error: string }

POST /api/create
     { section, content, category?, tags? }  (factstore 支持 category/tags)
     → { ok: true } | { ok: false, error: string }
```

**idx 约定：** `M1`/`M2`/... 是渲染顺序的 1-based 索引；删除/编辑时 `int(idx[1:]) - 1` 转为 0-based。

**fact_id 是 SQLite 主键**，全局唯一；idx 是当前显示索引，可能因为删除而漂移。

---

## 何时该用/不该用这个查看器

✅ **适合：**
- 用户说"删掉 X 条目"、"整理记忆"
- 一次性浏览三层数据
- 调试"为什么这条记忆没生效"
- 批量删除/合并前的预览

❌ **不适合：**
- 合并/降级/跨层迁移——告诉 Agent "把 X 和 Y 合并" 更快
- 复杂查询（按时间/按 trust_score 排序）——直接 SQL
- 大于 100 条的事实库——分页/搜索 UI 缺失

---

## 后续可扩展点（不要现在就做）

- [ ] 搜索框（按 content 模糊匹配）
- [ ] 跨层迁移（把 Memory 条目搬到 Fact Store）
- [ ] Trust score 调整（每条 fact 上面有个滑块）
- [ ] 撤销最近 10 次操作（操作日志）
- [ ] Dark/light 主题切换

做这些的前提：用户明确要求。**不要主动 over-engineer。**
