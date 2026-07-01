Никита (Nikita) — работает с CPA лендингами и настройкой AI моделей. Предпочитает русский разговорный стиль, женскую персону, Gemini 3 Flash для экономии токенов. Кодинг делегирует, самостоятельное удаление файлов запрещено. Ожидает автономного решения задач: 'сам найди, попробуй подключить сам' с полными разрешениями без лишних вопросов.
§
Hermes model preferences: default = kimi-k2.6:cloud (ollama-cloud); coding = deepseek-v3.2; instamodel uses kimi-k2.6:cloud.
§
Hermes cron jobs are stored per profile at ~/.hermes/profiles/<profile>/cron/jobs.json. Bridge/UI should read these files directly to list jobs across all profiles; `hermes cron list` only sees the active profile.
§
User builds AI Workspace (~/ai-workspace) and expects autonomous implementation of features without asking permission. When adding UI features, preserve existing layout and provide complete end-to-end Bridge+UI changes.
§
AI Workspace UI: ChatGPT-style dark chat. User bubble gray, agent on clean bg. Markdown headings/lists/tables/code. Word-by-word typewriter. 16×16 copy icon below messages. Fira Code + atom-one-dark highlight. Older session bubbles to top on send with slide animation.
§
CPA/form rule: preserve original CSS classes; add functional classes space-separated only. Never remove formFb__inputs, ss, pp, formFb__btn. Deliver index.html + JS.