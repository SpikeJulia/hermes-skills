#!/usr/bin/env python3
"""
Hermes Memory Viewer Server v2
Real-time memory management via browser with edit + direct delete.
"""

import json
import os
import sqlite3
import http.server
import urllib.parse
from pathlib import Path
from socketserver import ThreadingMixIn

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
MEMORIES_DIR = HERMES_HOME / "memories"
MEMORY_FILE = MEMORIES_DIR / "MEMORY.md"
USER_FILE = MEMORIES_DIR / "USER.md"
FACT_DB = HERMES_HOME / "memory_store.db"
PORT = 8649


# ── SQLite WAL mode (avoid lock contention) ────────────────────

def _init_db():
    """Enable WAL mode and set busy timeout on the fact DB."""
    conn = sqlite3.connect(str(FACT_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.close()

try:
    _init_db()
except Exception:
    pass  # DB might not exist yet, ok


# ── Data Loaders / Savers ─────────────────────────────────────

def load_md(filepath: Path) -> list[dict]:
    if not filepath.exists():
        return []
    text = filepath.read_text(encoding="utf-8")
    parts = [p.strip() for p in text.split("§") if p.strip()]
    return [{"content": p} for p in parts]


def save_md(filepath: Path, entries: list[dict]):
    text = "\n§\n".join(e["content"] for e in entries)
    filepath.write_text(text, encoding="utf-8")


def load_facts() -> list[dict]:
    if not FACT_DB.exists():
        return []
    conn = sqlite3.connect(str(FACT_DB))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT fact_id, content, category, tags, trust_score, created_at "
        "FROM facts ORDER BY fact_id"
    ).fetchall()
    conn.close()
    return [{
        "fact_id": r["fact_id"],
        "content": r["content"],
        "category": r["category"],
        "tags": (r["tags"] or "").split(",") if r["tags"] else [],
        "trust_score": r["trust_score"],
    } for r in rows]


def update_fact(fact_id: int, content: str, category: str = None, tags: str = None):
    """Update an existing fact's content/category/tags."""
    conn = sqlite3.connect(str(FACT_DB))
    if category is not None and tags is not None:
        conn.execute(
            "UPDATE facts SET content=?, category=?, tags=? WHERE fact_id=?",
            (content, category, tags, fact_id),
        )
    elif category is not None:
        conn.execute(
            "UPDATE facts SET content=?, category=? WHERE fact_id=?",
            (content, category, fact_id),
        )
    else:
        conn.execute("UPDATE facts SET content=? WHERE fact_id=?", (content, fact_id))
    conn.commit()
    conn.close()


def delete_fact(fact_id: int):
    conn = sqlite3.connect(str(FACT_DB))
    conn.execute("DELETE FROM facts WHERE fact_id=?", (fact_id,))
    conn.execute("DELETE FROM fact_entities WHERE fact_id=?", (fact_id,))
    conn.commit()
    conn.close()


# ── HTTP Handler ──────────────────────────────────────────────

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _text(self, text, status=200, content_type="text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/data":
            memory = load_md(MEMORY_FILE)
            profile = load_md(USER_FILE)
            facts = load_facts()
            self._json({
                "memory": [
                    {"idx": f"M{i+1}", "content": e["content"]}
                    for i, e in enumerate(memory)
                ],
                "profile": [
                    {"idx": f"P{i+1}", "content": e["content"]}
                    for i, e in enumerate(profile)
                ],
                "facts": [
                    {
                        "idx": f"F{i+1}", "fact_id": e["fact_id"],
                        "content": e["content"],
                        "category": e["category"],
                        "tags": e["tags"],
                        "trust_score": e["trust_score"],
                    }
                    for i, e in enumerate(facts)
                ],
                "stats": {
                    "memory": len(memory),
                    "profile": len(profile),
                    "facts": len(facts),
                }
            })

        elif path == "/":
            self._text(HTML)
        else:
            self._text("Not Found", 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        except Exception as e:
            return self._json({"ok": False, "error": f"bad json: {e}"}, 400)

        # ── DELETE ───────────────────────────
        if path == "/api/delete":
            section = body.get("section")
            idx = body.get("idx")
            fact_id = body.get("fact_id")
            try:
                if section == "memory":
                    entries = load_md(MEMORY_FILE)
                    n = int(idx[1:]) - 1
                    if 0 <= n < len(entries):
                        entries.pop(n)
                        save_md(MEMORY_FILE, entries)
                elif section == "profile":
                    entries = load_md(USER_FILE)
                    n = int(idx[1:]) - 1
                    if 0 <= n < len(entries):
                        entries.pop(n)
                        save_md(USER_FILE, entries)
                elif section == "factstore" and fact_id:
                    delete_fact(int(fact_id))
                self._json({"ok": True})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)

        # ── UPDATE ───────────────────────────
        elif path == "/api/update":
            section = body.get("section")
            idx = body.get("idx")
            fact_id = body.get("fact_id")
            new_content = body.get("content", "").strip()
            new_category = body.get("category")
            new_tags = body.get("tags")
            if not new_content:
                return self._json({"ok": False, "error": "内容不能为空"}, 400)
            try:
                if section == "memory":
                    entries = load_md(MEMORY_FILE)
                    n = int(idx[1:]) - 1
                    if 0 <= n < len(entries):
                        entries[n]["content"] = new_content
                        save_md(MEMORY_FILE, entries)
                elif section == "profile":
                    entries = load_md(USER_FILE)
                    n = int(idx[1:]) - 1
                    if 0 <= n < len(entries):
                        entries[n]["content"] = new_content
                        save_md(USER_FILE, entries)
                elif section == "factstore" and fact_id:
                    tags_str = ",".join(new_tags) if isinstance(new_tags, list) else new_tags
                    update_fact(int(fact_id), new_content, new_category, tags_str)
                self._json({"ok": True})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)

        # ── CREATE ───────────────────────────
        elif path == "/api/create":
            section = body.get("section")
            content = body.get("content", "").strip()
            category = body.get("category", "general")
            tags = body.get("tags", [])
            if not content:
                return self._json({"ok": False, "error": "内容不能为空"}, 400)
            try:
                if section == "memory":
                    entries = load_md(MEMORY_FILE)
                    entries.append({"content": content})
                    save_md(MEMORY_FILE, entries)
                elif section == "profile":
                    entries = load_md(USER_FILE)
                    entries.append({"content": content})
                    save_md(USER_FILE, entries)
                elif section == "factstore":
                    conn = sqlite3.connect(str(FACT_DB))
                    tags_str = ",".join(tags) if isinstance(tags, list) else tags
                    conn.execute(
                        "INSERT INTO facts (content, category, tags, trust_score, created_at) "
                        "VALUES (?, ?, ?, 0.5, datetime('now'))",
                        (content, category, tags_str),
                    )
                    conn.commit()
                    conn.close()
                self._json({"ok": True})
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)

        else:
            self._text("Not Found", 404)


# ── HTML ──────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hermes 记忆系统</title>
<style>
  :root {
    --bg: #0f1117; --card: #181b24; --card-hover: #1e2230;
    --border: #2a2e3a; --text: #e2e4eb; --text-dim: #8b8fa3;
    --accent: #6c5ce7; --accent-glow: rgba(108,92,231,0.15);
    --danger: #e74c3c; --danger-bg: rgba(231,76,60,0.1);
    --green: #00b894; --yellow: #fdcb6e;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: var(--bg); color: var(--text); padding: 40px 20px 100px;
  }
  .container { max-width: 880px; margin: 0 auto; }
  .header { text-align: center; margin-bottom: 40px; padding-bottom: 30px; border-bottom: 1px solid var(--border); }
  .header h1 { font-size: 28px; background: linear-gradient(135deg,var(--accent),#a29bfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }
  .header .stats { color: var(--text-dim); font-size: 14px; display: flex; justify-content: center; gap: 24px; flex-wrap: wrap; }
  .header .stats span { background: var(--card); padding: 4px 14px; border-radius: 12px; border: 1px solid var(--border); }
  .header .stats .num { color: var(--accent); font-weight: 600; }
  .header .desc { color: var(--text-dim); font-size: 13px; margin-top: 12px; }

  .section { margin-bottom: 32px; }
  .section-title { font-size: 16px; font-weight: 600; margin-bottom: 12px; padding: 8px 16px; background: var(--card); border-radius: 8px; border-left: 3px solid var(--accent); display: flex; align-items: center; gap: 10px; }
  .section-title .badge { font-size: 11px; padding: 2px 10px; border-radius: 10px; background: var(--accent-glow); color: var(--accent); font-weight: 500; }
  .section-title .add-btn { margin-left: auto; background: var(--accent-glow); border: 1px solid var(--accent); color: var(--accent); padding: 4px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; font-weight: 500; }
  .section-title .add-btn:hover { background: var(--accent); color: #fff; }

  .msg { text-align: center; padding: 40px; color: var(--text-dim); }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 6px; overflow: hidden; transition: all 0.15s; }
  .card:hover { border-color: #3a3f55; }
  .card-header { display: flex; align-items: center; padding: 12px 16px; gap: 12px; }
  .card-header .idx { font-size: 11px; color: var(--text-dim); background: var(--bg); padding: 2px 8px; border-radius: 6px; min-width: 32px; text-align: center; font-family: monospace; }
  .card-header .title { flex: 1; font-size: 14px; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: text; }
  .card-header .actions { display: flex; gap: 6px; flex-shrink: 0; }
  .card-header .btn { background: none; border: 1px solid var(--border); color: var(--text-dim); width: 28px; height: 28px; border-radius: 6px; cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center; transition: all 0.15s; }
  .card-header .btn:hover { background: var(--card-hover); color: var(--text); }
  .card-header .btn-edit:hover { background: rgba(108,92,231,0.15); border-color: var(--accent); color: var(--accent); }
  .card-header .btn-delete:hover { background: var(--danger-bg); border-color: var(--danger); color: var(--danger); }

  .card-body { max-height: 0; overflow: hidden; transition: max-height 0.25s, padding 0.2s; padding: 0 16px; }
  .card-body.open { max-height: 800px; padding: 0 16px 14px; }
  .card-body .content { font-size: 13px; line-height: 1.7; color: var(--text-dim); padding: 12px; background: var(--bg); border-radius: 8px; border: 1px solid var(--border); white-space: pre-wrap; word-break: break-word; font-family: monospace; font-size: 12px; }
  .card-body .meta { display: flex; gap: 8px; margin-top: 8px; font-size: 11px; color: var(--text-dim); flex-wrap: wrap; }
  .card-body .meta .tag { background: var(--accent-glow); color: #a29bfe; padding: 2px 8px; border-radius: 4px; }

  /* Edit mode */
  .edit-area { display: none; flex-direction: column; gap: 8px; }
  .card.editing .edit-area { display: flex; }
  .card.editing .display-area { display: none; }
  .edit-area textarea { width: 100%; min-height: 120px; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-family: monospace; font-size: 12px; line-height: 1.6; resize: vertical; }
  .edit-area textarea:focus { outline: none; border-color: var(--accent); }
  .edit-area .edit-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .edit-area .edit-row label { font-size: 12px; color: var(--text-dim); }
  .edit-area .edit-row input, .edit-area .edit-row select { background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 6px 10px; font-size: 12px; font-family: inherit; }
  .edit-area .edit-row input:focus, .edit-area .edit-row select:focus { outline: none; border-color: var(--accent); }
  .edit-area .edit-row .tag-input { flex: 1; min-width: 150px; }
  .edit-actions { display: flex; gap: 8px; justify-content: flex-end; }
  .edit-actions button { padding: 6px 16px; border-radius: 6px; border: 1px solid var(--border); background: none; color: var(--text-dim); cursor: pointer; font-size: 13px; transition: all 0.15s; }
  .edit-actions .btn-save { background: var(--accent); color: #fff; border-color: var(--accent); }
  .edit-actions .btn-save:hover { opacity: 0.85; }
  .edit-actions .btn-cancel:hover { background: var(--card-hover); color: var(--text); }

  /* Add form */
  .add-form { display: none; background: var(--card); border: 1px dashed var(--border); border-radius: 10px; padding: 16px; margin-bottom: 12px; }
  .add-form.open { display: block; }
  .add-form textarea { width: 100%; min-height: 100px; background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 8px; padding: 12px; font-family: monospace; font-size: 12px; resize: vertical; }
  .add-form textarea:focus { outline: none; border-color: var(--accent); }
  .add-form .form-row { display: flex; gap: 8px; align-items: center; margin-top: 10px; flex-wrap: wrap; }
  .add-form .form-row label { font-size: 12px; color: var(--text-dim); }
  .add-form .form-row select, .add-form .form-row input { background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 6px; padding: 6px 10px; font-size: 12px; }
  .add-form .form-row .tag-input { flex: 1; min-width: 150px; }
  .add-form .form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 10px; }
  .add-form .form-actions button { padding: 6px 16px; border-radius: 6px; border: 1px solid var(--border); background: none; color: var(--text-dim); cursor: pointer; font-size: 13px; }
  .add-form .form-actions .btn-save { background: var(--accent); color: #fff; border-color: var(--accent); }

  .toast { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); background: var(--green); color: #fff; padding: 10px 24px; border-radius: 10px; font-size: 14px; opacity: 0; transition: opacity 0.3s; pointer-events: none; z-index: 100; }
  .toast.show { opacity: 1; }
  .toast.error { background: var(--danger); }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🔮 Hermes 记忆系统</h1>
    <div class="stats" id="stats"></div>
    <div class="desc">点击 ✕ 立即删除 · 点击 ✏️ 编辑 · 点击 + 新增 · 改动自动保存</div>
  </div>
  <div id="app"><div class="msg">加载中...</div></div>
</div>
<div class="toast" id="toast"></div>

<script>
let data = null;

async function load() {
  try {
    const res = await fetch('/api/data', { cache: 'no-store' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    data = await res.json();
    render();
  } catch(e) {
    document.getElementById('app').innerHTML = `
      <div class="msg" style="padding:60px 20px;">
        <div style="font-size:48px;margin-bottom:16px;">❌</div>
        <div style="font-size:18px;margin-bottom:12px;">无法连接到记忆服务器</div>
        <div style="font-size:13px;line-height:1.8;margin-bottom:16px;">
          错误信息：<code style="background:var(--card);padding:2px 8px;border-radius:4px;">${esc(String(e.message))}</code>
        </div>
        <div style="font-size:13px;line-height:1.8;text-align:left;background:var(--card);padding:16px;border-radius:8px;border:1px solid var(--border);">
          <strong>排查步骤：</strong><br>
          1. 确认 WSL 内的服务器正在运行：<br>
             <code style="color:var(--accent);">python3 /home/tangxuan/tools/memory_viewer_server.py</code><br><br>
          2. 浏览器地址栏核对：<br>
             <code style="color:var(--accent);">http://localhost:8649</code><br>
             （或 WSL IP: <code style="color:var(--accent);">http://192.168.41.3:8649</code>）<br><br>
          3. 按 F12 打开开发者工具，看 Console/Network 标签的具体报错<br><br>
          4. 硬刷新：<code style="color:var(--accent);">Ctrl+Shift+R</code> (清缓存)
        </div>
      </div>`;
  }
}

function render() {
  const app = document.getElementById('app');
  const stats = document.getElementById('stats');
  if (!data || !data.stats) { app.innerHTML = '<div class="msg">数据为空</div>'; return; }
  const s = data.stats;
  stats.innerHTML = `
    <span>Memory <span class="num">${s.memory}</span> 条</span>
    <span>Profile <span class="num">${s.profile}</span> 条</span>
    <span>Fact Store <span class="num">${s.facts}</span> 条</span>
  `;
  let html = '';
  html += sectionHtml('memory', '🧠 Memory', '始终注入 · ${s}条'.replace('${s}', s.memory), s.memory, 'memory');
  html += sectionHtml('profile', '👤 User Profile', '用户画像 · ${s}条'.replace('${s}', s.profile), s.profile, 'profile');
  html += sectionHtml('factstore', '🗄️ Fact Store', '结构化记忆 · ${s}条'.replace('${s}', s.facts), s.facts, 'factstore');
  app.innerHTML = html;
}

function sectionHtml(section, title, badge, count, id) {
  // Backend keys: memory, profile, facts. Frontend IDs: memory, profile, factstore.
  const keyMap = { memory: 'memory', profile: 'profile', factstore: 'facts' };
  const items = data[keyMap[section]] || [];
  let html = `<div class="section">
    <div class="section-title">${title} <span class="badge">${badge}</span>
      <button class="add-btn" onclick="toggleAdd('${id}')">+ 新增</button>
    </div>
    <div class="add-form" id="add-${id}">
      <textarea id="add-text-${id}" placeholder="内容..."></textarea>
      <div class="form-row" id="add-extra-${id}">${section==='factstore' ? `
        <label>分类:</label>
        <select id="add-cat-${id}">
          <option value="user_pref">user_pref</option>
          <option value="project">project</option>
          <option value="tool" selected>tool</option>
          <option value="general">general</option>
        </select>
        <label>tags:</label>
        <input class="tag-input" id="add-tags-${id}" placeholder="comma,separated,tags">
      ` : ''}</div>
      <div class="form-actions">
        <button onclick="toggleAdd('${id}')">取消</button>
        <button class="btn-save" onclick="createEntry('${id}')">保存</button>
      </div>
    </div>
  `;
  items.forEach((e, i) => {
    html += cardHtml(section, e, e.idx, e.fact_id, e.tags, e.trust_score, e.category);
  });
  html += `</div>`;
  return html;
}

function cardHtml(section, entry, idx, factId, tags, trust, category) {
  const content = entry.content;
  const tagHtml = (tags||[]).filter(Boolean).map(t => `<span class="tag">${esc(t)}</span>`).join('');
  const metaHtml = (tagHtml || trust || (section==='factstore' && category))
    ? `<div class="meta">${section==='factstore' && category ? `<span class="tag">${esc(category)}</span>` : ''}${tagHtml}${trust ? `<span class="tag">trust: ${trust}</span>` : ''}</div>` : '';
  const factAttr = factId ? ` data-factid="${factId}"` : '';
  const extraInputs = section==='factstore' ? `
    <div class="edit-row">
      <label>分类:</label>
      <select id="edit-cat-${idx}">
        <option value="user_pref" ${category==='user_pref'?'selected':''}>user_pref</option>
        <option value="project" ${category==='project'?'selected':''}>project</option>
        <option value="tool" ${category==='tool'?'selected':''}>tool</option>
        <option value="general" ${category==='general'?'selected':''}>general</option>
      </select>
      <label>tags:</label>
      <input class="tag-input" id="edit-tags-${idx}" value="${(tags||[]).join(',')}" placeholder="comma,separated">
    </div>
  ` : '';
  return `
    <div class="card" data-section="${section}" data-idx="${idx}"${factAttr}>
      <div class="card-header">
        <span class="idx">${idx}</span>
        <span class="title" onclick="expand(this, event)">${esc(content.slice(0, 50))}</span>
        <div class="actions">
          <button class="btn btn-edit" onclick="editEntry(this)" title="编辑">✏️</button>
          <button class="btn btn-delete" onclick="del(this)" title="删除">✕</button>
        </div>
      </div>
      <div class="card-body open">
        <div class="display-area">
          <div class="content">${esc(content)}</div>
          ${metaHtml}
        </div>
        <div class="edit-area">
          <textarea id="edit-text-${idx}">${esc(content)}</textarea>
          ${extraInputs}
          <div class="edit-actions">
            <button class="btn-cancel" onclick="cancelEdit(this)">取消</button>
            <button class="btn-save" onclick="saveEdit('${section}', '${idx}'${factId?', '+factId:''})">保存</button>
          </div>
        </div>
      </div>
    </div>`;
}

function esc(s) {
  const div = document.createElement('div');
  div.textContent = s == null ? '' : s;
  return div.innerHTML;
}

function expand(btn, event) {
  event.stopPropagation();
  const body = btn.closest('.card').querySelector('.card-body');
  body.classList.toggle('open');
}

async function del(btn) {
  const card = btn.closest('.card');
  const section = card.dataset.section;
  const idx = card.dataset.idx;
  const factId = card.dataset.factid;
  const title = card.querySelector('.title').textContent;

  if (!confirm(`确定删除 ${idx}?\n\n${title.slice(0,80)}${title.length>80?'…':''}`)) return;

  try {
    const res = await fetch('/api/delete', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ section, idx, fact_id: factId ? parseInt(factId) : null })
    });
    const result = await res.json();
    if (result.ok) {
      card.style.transition = 'all 0.3s';
      card.style.opacity = '0.3';
      card.style.transform = 'translateX(20px)';
      toast('✅ 已删除 ' + idx);
      setTimeout(load, 600);
    } else {
      toast('❌ 删除失败: ' + result.error, true);
    }
  } catch(e) {
    toast('❌ 请求失败', true);
  }
}

function editEntry(btn) {
  const card = btn.closest('.card');
  card.classList.add('editing');
  const ta = card.querySelector('textarea');
  if (ta) { ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); }
}

function cancelEdit(btn) {
  const card = btn.closest('.card');
  card.classList.remove('editing');
}

async function saveEdit(section, idx, factId) {
  const newContent = document.getElementById('edit-text-' + idx).value.trim();
  if (!newContent) { toast('❌ 内容不能为空', true); return; }
  const body = { section, idx, content: newContent };
  if (factId !== undefined) {
    body.fact_id = parseInt(factId);
    const catEl = document.getElementById('edit-cat-' + idx);
    const tagsEl = document.getElementById('edit-tags-' + idx);
    if (catEl) body.category = catEl.value;
    if (tagsEl) body.tags = tagsEl.value;
  }
  try {
    const res = await fetch('/api/update', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const result = await res.json();
    if (result.ok) {
      toast('✅ 已保存 ' + idx);
      setTimeout(load, 400);
    } else {
      toast('❌ 保存失败: ' + result.error, true);
    }
  } catch(e) {
    toast('❌ 请求失败', true);
  }
}

function toggleAdd(section) {
  const form = document.getElementById('add-' + section);
  if (form) {
    form.classList.toggle('open');
    if (form.classList.contains('open')) {
      const ta = document.getElementById('add-text-' + section);
      if (ta) ta.focus();
    }
  }
}

async function createEntry(section) {
  const content = document.getElementById('add-text-' + section).value.trim();
  if (!content) { toast('❌ 内容不能为空', true); return; }
  const body = { section, content };
  if (section === 'factstore') {
    const catEl = document.getElementById('add-cat-' + section);
    const tagsEl = document.getElementById('add-tags-' + section);
    if (catEl) body.category = catEl.value;
    if (tagsEl) body.tags = tagsEl.value;
  }
  try {
    const res = await fetch('/api/create', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const result = await res.json();
    if (result.ok) {
      toast('✅ 已新增');
      document.getElementById('add-text-' + section).value = '';
      if (section === 'factstore') {
        const tagsEl = document.getElementById('add-tags-' + section);
        if (tagsEl) tagsEl.value = '';
      }
      toggleAdd(section);
      setTimeout(load, 400);
    } else {
      toast('❌ 新增失败: ' + result.error, true);
    }
  } catch(e) {
    toast('❌ 请求失败', true);
  }
}

function toast(msg, isError) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.toggle('error', !!isError);
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 2200);
}

load();
</script>
</body>
</html>
"""

# ── Main ──────────────────────────────────────────────────────

class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in separate threads."""

if __name__ == "__main__":
    server = ThreadedHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"\n  🎯 Hermes Memory Viewer v2")
    print(f"  ┌──────────────────────────────────────────────┐")
    print(f"  │  http://localhost:{PORT}                        │")
    print(f"  │                                               │")
    print(f"  │  ✏️  Edit · ✕ Delete · + Add · all live       │")
    print(f"  │  Press Ctrl+C to stop                         │")
    print(f"  └──────────────────────────────────────────────┘\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  👋 Server stopped.")
        server.server_close()
