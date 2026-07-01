# Multi-Agent Dashboard Sketch Templates

Two ready-made HTML templates for Hermes multi-profile dashboard UIs. Copy-paste and adapt.

---

## Variant A: Teamly-Style ("All-at-once")

Layout: agents sidebar + kanban center + chat bottom panel.

```html
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Команда — Teamly Style</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; }
  .agent-card { transition: all 0.2s; cursor: pointer; }
  .agent-card:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(99,102,241,0.3); }
  .agent-avatar { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; }
  .kanban-col { min-height: 400px; }
  .task-card { transition: all 0.15s; cursor: grab; }
  .task-card:hover { transform: translateX(2px); }
  .chat-bubble { max-width: 80%; }
  .pulse-dot { animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
  .glow { box-shadow: 0 0 20px rgba(99,102,241,0.15); }
</style>
</head>
<body class="h-screen flex flex-col">
<header class="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
  <div class="flex items-center gap-3">
    <div class="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center font-bold text-white">AI</div>
    <h1 class="text-lg font-semibold">Моя AI Команда</h1>
  </div>
  <div class="flex items-center gap-2 text-sm text-slate-400">
    <span class="pulse-dot w-2 h-2 bg-green-400 rounded-full inline-block"></span>
    <span>Все агенты онлайн</span>
  </div>
</header>
<div class="flex-1 flex overflow-hidden">
  <aside class="w-72 bg-slate-800 border-r border-slate-700 p-4 overflow-y-auto">
    <h2 class="text-xs uppercase tracking-wider text-slate-400 mb-4">Агенты (5)</h2>
    <div class="space-y-3">
      <!-- Repeat for each agent -->
      <div class="agent-card bg-slate-700 rounded-xl p-3 flex items-center gap-3 border border-slate-600" onclick="selectAgent('default')">
        <div class="agent-avatar bg-blue-500">🧠</div>
        <div class="flex-1"><div class="font-medium text-sm">Default</div><div class="text-xs text-slate-400">Главный ассистент</div></div>
        <div class="w-2 h-2 bg-green-400 rounded-full"></div>
      </div>
      <!-- ... coding, youtube, traffic, instamodel ... -->
    </div>
    <div class="mt-6 p-3 bg-slate-700/50 rounded-lg border border-slate-600">
      <div class="text-xs text-slate-400 mb-1">Активный агент</div>
      <div id="activeAgent" class="font-semibold text-indigo-400">Default</div>
    </div>
  </aside>
  <main class="flex-1 flex flex-col">
    <div class="flex-1 p-4 overflow-x-auto">
      <div class="flex gap-4 min-w-max">
        <div class="w-80">
          <div class="flex items-center justify-between mb-3"><h3 class="text-sm font-semibold text-slate-300">📝 Todo</h3><span class="text-xs bg-slate-700 px-2 py-1 rounded-full">3</span></div>
          <div class="kanban-col space-y-2">
            <div class="task-card bg-slate-700 p-3 rounded-lg border border-slate-600">
              <div class="text-sm font-medium mb-1">Task name</div>
              <div class="flex items-center gap-2 mt-2"><span class="text-xs bg-red-500/20 text-red-300 px-2 py-0.5 rounded">agent-tag</span></div>
            </div>
          </div>
        </div>
        <!-- In Progress, Done columns... -->
      </div>
    </div>
    <div class="h-72 border-t border-slate-700 bg-slate-800 flex flex-col">
      <div class="px-4 py-2 border-b border-slate-700 flex items-center gap-2"><div class="w-2 h-2 bg-green-400 rounded-full"></div><span class="text-sm font-medium">Чат с <span id="chatAgentName" class="text-indigo-400">Default</span></span></div>
      <div class="flex-1 overflow-y-auto p-4 space-y-3">
        <div class="flex gap-3"><div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-sm flex-shrink-0">🧠</div><div class="chat-bubble bg-slate-700 rounded-xl rounded-tl-sm px-4 py-2 text-sm">Привет!</div></div>
      </div>
      <div class="p-3 border-t border-slate-700 flex gap-2"><input type="text" placeholder="Напишите сообщение..." class="flex-1 bg-slate-900 border border-slate-600 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-indigo-500"><button class="bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-lg text-sm font-medium transition">➤</button></div>
    </div>
  </main>
</div>
<script>function selectAgent(name){ document.getElementById('activeAgent').textContent=name; document.getElementById('chatAgentName').textContent=name; }</script>
</body>
</html>
```

**Stance:** Everything visible at once. Best for monitoring/overview.

---

## Variant B: Dashboard-Style ("Tabbed Focus")

Layout: agents sidebar + tabbed main area (Chat / Tasks / Logs).

```html
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Команда — Dashboard Style</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0e1a; color: #e2e8f0; }
  .agent-row { transition: all 0.2s; cursor: pointer; }
  .agent-row:hover { background: rgba(99,102,241,0.08); }
  .agent-row.active { background: rgba(99,102,241,0.15); border-left: 3px solid #6366f1; }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; }
  .status-dot.online { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
  .chat-area { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
  .msg-user { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); }
  .task-pill { font-size: 10px; padding: 2px 8px; border-radius: 999px; }
</style>
</head>
<body class="h-screen flex flex-col">
<header class="bg-slate-900/80 backdrop-blur border-b border-slate-700 px-6 py-3 flex items-center justify-between">
  <div class="flex items-center gap-3">
    <div class="w-9 h-9 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center font-bold text-white text-sm">AI</div>
    <div><h1 class="text-base font-semibold">Command Center</h1><div class="text-xs text-slate-400">5 агентов активны</div></div>
  </div>
  <div class="flex items-center gap-4">
    <div class="flex -space-x-2">
      <div class="w-8 h-8 rounded-full bg-blue-500 border-2 border-slate-900 flex items-center justify-center text-xs">🧠</div>
      <div class="w-8 h-8 rounded-full bg-purple-500 border-2 border-slate-900 flex items-center justify-center text-xs">💻</div>
      <div class="w-8 h-8 rounded-full bg-red-500 border-2 border-slate-900 flex items-center justify-center text-xs">🎬</div>
      <div class="w-8 h-8 rounded-full bg-orange-500 border-2 border-slate-900 flex items-center justify-center text-xs">📢</div>
      <div class="w-8 h-8 rounded-full bg-pink-500 border-2 border-slate-900 flex items-center justify-center text-xs">📸</div>
    </div>
    <div class="text-xs text-slate-400">Никита</div>
  </div>
</header>
<div class="flex-1 flex overflow-hidden">
  <aside class="w-64 bg-slate-900 border-r border-slate-700 flex flex-col">
    <div class="p-4 border-b border-slate-700">
      <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Агенты</h2>
      <div class="space-y-1">
        <div class="agent-row active flex items-center gap-3 px-3 py-2.5 rounded-lg" onclick="setAgent(this,'default')">
          <div class="w-9 h-9 rounded-full bg-blue-500 flex items-center justify-center text-base">🧠</div>
          <div class="flex-1 min-w-0"><div class="text-sm font-medium truncate">Default</div><div class="text-xs text-slate-500 truncate">Главный ассистент</div></div>
          <div class="status-dot online"></div>
        </div>
        <!-- ... more agents ... -->
      </div>
    </div>
    <div class="p-4 mt-auto">
      <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Статистика</h2>
      <div class="grid grid-cols-2 gap-2">
        <div class="bg-slate-800 rounded-lg p-3 text-center"><div class="text-xl font-bold text-indigo-400">8</div><div class="text-xs text-slate-500">Задач</div></div>
        <div class="bg-slate-800 rounded-lg p-3 text-center"><div class="text-xl font-bold text-green-400">3</div><div class="text-xs text-slate-500">В работе</div></div>
      </div>
    </div>
  </aside>
  <main class="flex-1 flex flex-col chat-area">
    <div class="flex border-b border-slate-700">
      <button class="px-6 py-3 text-sm font-medium text-indigo-400 border-b-2 border-indigo-500" id="tab-chat" onclick="switchTab('chat')">💬 Чат</button>
      <button class="px-6 py-3 text-sm font-medium text-slate-400 hover:text-slate-200" id="tab-kanban" onclick="switchTab('kanban')">📋 Задачи</button>
      <button class="px-6 py-3 text-sm font-medium text-slate-400 hover:text-slate-200" id="tab-logs" onclick="switchTab('logs')">📜 Логи</button>
    </div>
    <!-- Chat panel -->
    <div id="panel-chat" class="flex-1 flex flex-col">
      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-lg shadow-lg">🧠</div>
          <div class="max-w-[70%]"><div class="text-xs text-slate-400 mb-1">Default • сейчас</div><div class="bg-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 text-sm border border-slate-700">Привет, Никита! Готов к работе.</div></div>
        </div>
      </div>
      <div class="p-4 border-t border-slate-700">
        <div class="flex gap-3 items-end bg-slate-800 rounded-xl p-2 border border-slate-600">
          <button class="p-2 text-slate-400 hover:text-slate-200">📎</button>
          <textarea placeholder="Напишите сообщение..." class="flex-1 bg-transparent resize-none outline-none text-sm py-2 max-h-32" rows="1"></textarea>
          <button class="bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-lg text-sm font-medium transition">Отправить</button>
        </div>
      </div>
    </div>
    <!-- Kanban panel (hidden by default) -->
    <div id="panel-kanban" class="flex-1 overflow-y-auto p-4 hidden">...</div>
    <!-- Logs panel -->
    <div id="panel-logs" class="flex-1 overflow-y-auto p-4 hidden">...</div>
  </main>
</div>
<script>
function setAgent(el,name){ document.querySelectorAll('.agent-row').forEach(r=>r.classList.remove('active')); el.classList.add('active'); }
function switchTab(tab){ ['chat','kanban','logs'].forEach(t=>{ document.getElementById('panel-'+t).classList.add('hidden'); document.getElementById('tab-'+t).classList.remove('text-indigo-400','border-b-2','border-indigo-500'); document.getElementById('tab-'+t).classList.add('text-slate-400'); }); document.getElementById('panel-'+tab).classList.remove('hidden'); document.getElementById('tab-'+tab).classList.add('text-indigo-400','border-b-2','border-indigo-500'); document.getElementById('tab-'+tab).classList.remove('text-slate-400'); }
</script>
</body>
</html>
```

**Stance:** Focus per tab. Best for deep work in chat or kanban separately.

---

## Agent Emoji Mapping

| Agent | Emoji | Color | Role |
|-------|-------|-------|------|
| Default | 🧠 | Blue #3b82f6 | Главный ассистент |
| Coding | 💻 | Purple #a855f7 | Код, скрипты |
| YouTube | 🎬 | Red #ef4444 | Контент sostv |
| Traffic | 📢 | Orange #f97316 | TikTok Ads |
| Instamodel | 📸 | Pink #ec4899 | SMM, Stories |

---

## Evaluating SaaS Integrations

When user finds a tool like Teamly, check these before declaring it viable:
1. `https://domain/api` — public API docs?
2. `https://domain/docs` — documentation?
3. Pricing page — custom agents / API access?

If `/api` redirects to login and `/docs` 404s → **closed SaaS, not integrable** with self-hosted agents.
