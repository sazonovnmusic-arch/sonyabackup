# YouTube Channel Analysis — Extraction Recipes

## Browser-based video listing extraction

YouTube's accessibility tree (`browser_snapshot`) does NOT reliably surface video titles or view counts for grid items. Use `browser_console` to inject JS that reads the DOM directly.

### Full extraction (titles + views + URLs)

```javascript
(() => {
  const shorts = [];
  document.querySelectorAll('ytd-rich-item-renderer').forEach(item => {
    const titleEl = item.querySelector('a#video-title-link, a[title]');
    const title = titleEl ? (titleEl.getAttribute('title') || titleEl.textContent?.trim()) : '';
    const href = titleEl?.href || '';
    const allSpans = item.querySelectorAll('span');
    const viewsText = Array.from(allSpans).map(s => s.textContent?.trim())
      .filter(t => t && t.match(/\d+\s*(K|M)\s*views/));
    shorts.push({title, url: href, views: viewsText[0] || ''});
  });
  return JSON.stringify(shorts);
})()
```

### Incremental extraction (after scrolling)

After scrolling down, re-run the same IIFE. Deduplicate by URL. Stop when `total` count stops growing across two consecutive scrolls.

### Popular tab

Click the "Popular" tab (`tab "Popular"`) and re-run extraction. This gives you a pre-sorted ranking without needing to sort yourself.

### Channel metadata

Available directly from `browser_snapshot`:
- Channel name: `heading [level=1]`
- @handle: first `group > StaticText` with `@` prefix
- Subscriber count + video count: next `group > StaticText` pair
- Description: expandable text block (click `...more` button)
- External links (Telegram, website): `link` elements below description

### Community / Posts tab

The Posts tab shows polls with vote counts and comment counts — useful for audience engagement metrics. Available in the snapshot directly.

## IIFE requirement

**Always wrap JS in `(() => { ... })()`**. Top-level `const` declarations persist across `browser_console` calls in the same page session and cause `SyntaxError: Identifier 'X' has already been declared`. An IIFE gives a fresh scope every run.

## Channel profile deliverable template

```
## 📊 Базовая информация
| Параметр | Значение |
|---|---|
| Название | ... |
| Handle | @... |
| Подписчиков | ... |
| Всего видео | ... |
| Формат | Shorts / Long-form / Mixed |
| Ссылки | ... |

## 🎯 Тематика
[franchise/topic breakdown with emoji]

## 📈 Топ-5 по просмотрам
| Видео | Просмотры |
|---|---|
| ... | ... |

## 🤔 Что заметно
[observations: cadence, engagement, gaps, best-performing content types]
```