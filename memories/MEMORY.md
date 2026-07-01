Прагматичен. Сначала простой вариант, потом сложный.
§
Interface: prefers Telegram over CLI for all tasks incl. coding. Lazy skill loading. Gateway self-preservation: never restart my own gateway from inside — always give command to user or delegate to another bot.
§
YouTube @sostv3 (149K), ниша: обзоры мультфильмов/фильмов. Telegram: t.me/sazonovcpa.
§
5 профилей Hermes: default, coding, youtube, traffic, instamodel. instamodel — Instagram/SMM. Перезапущен 24.06 из-за флуд-контроля.
§
Hermes конфиги — сам меняет через hermes config set, советуется.
§
Критичное правило взаимодействия: пользователь запрещает самостоятельно вносить изменения в систему, конфиги, профили или процессы без явной команды. Если он говорит «посмотри», «глянь», «проверь», «проанализируй» — я должен только отчитаться и предложить варианты решения, но НЕ выполнять никаких действий (не чинить, не менять, не перезапускать, не ломать). Исправления и фиксы — только после прямой команды типа «исправь», «почини», «сделай».
§
Gmail rule: смотреть почту — можно без подтверждения. Отправлять/удалять/архивировать — только после прямой команды «отправь» / «удали» с предварительным показом черновика.
§
instamodel — Instagram Story Generator v6: /root/insta_story_v6.py делает 9:16 Stories с 2 плашками (white+red, 520×90px). Запуск: python3 /root/insta_story_v6.py input.jpg output.png. Шрифты в /root/insta_fonts/. Ограничения: rounded_rectangle даёт разную ширину, tilt ломает размеры, эмодзи не рендерятся. Провайдеры img2img не рабочие (FAL баланс 0, Replicate/OpenAI токены 401).
§
Duplicate `hermes gateway run` processes cause persistent "typing" status in Telegram even when idle. If user reports constant typing indicator, check for multiple gateway PIDs with `ps aux | grep hermes` — kill duplicates leaving one alive, or restart via systemd.
§
Gonzo proxy доступен. 3 варианта:
1) HTTP 62.169.20.75:1000 login:GonzoNvv5Rfv_c_us_s_acc69)7(_ttl_6h pass:RqFaYSd6 (US, TTL 6h)
2) HTTP pool.gonzoproxy.com:1000 login:GonzoNvv5Rfv_c_fi_s_acc142(_ttl_240h pass:RqFaYSd6 (Finland, TTL 240h)
3) HTTP 45.14.112.25:24295 login:ZmdkDRao pass:9BH7ZtXCxI4w