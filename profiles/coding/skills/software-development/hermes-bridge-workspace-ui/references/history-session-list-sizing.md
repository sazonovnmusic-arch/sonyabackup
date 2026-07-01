# History session list sizing

Session list blocks in the AI Workspace history drawer are sensitive to proportion. This reference records the iteration that worked.

## Sizes that were tried

| Stage | Padding | Title | Date/meta | Gap | Rounding | Result |
|-------|---------|-------|-----------|-----|----------|--------|
| Initial | `px-3 py-2` | `text-sm` | `text-xs` | `space-y-1.5` | `rounded-md` | Too small (headers hard to read). |
| Large | `px-4 py-3.5` | `text-base` | `text-xs` | `space-y-3` | `rounded-lg` | Too big. |
| Final | `px-3 py-2.5` | `text-sm` | `text-xs` | `space-y-2` | `rounded-md` | Accepted midpoint. |

## Rule of thumb

- When the user says "заголовки в истории больше" / "make history headers bigger", increase the **whole block**, not just the font size.
- When the user says "слишком большие" / "too big", go halfway back.
- Usually 2–3 iterations settle on the final size.

## Recommended starting point

```jsx
<div className="flex-1 overflow-y-auto p-2.5 space-y-2 min-w-0">
  {sessions.map(s => (
    <button
      key={s.id}
      className={cls(
        'w-full text-left px-3 py-2.5 rounded-md transition',
        isActive
          ? 'bg-[var(--accent)]/10 text-[var(--accent)]'
          : 'hover:bg-[var(--surface-2)] text-[var(--text)]'
      )}
    >
      <div className="text-sm font-medium truncate">{s.title}</div>
      <div className="text-xs text-[var(--text-dim)] mt-0.5">
        {dateFmt(s.updated_at)} · {s.message_count} сообщ.
      </div>
    </button>
  ))}
</div>
```

## Notes

- Keep blocks borderless. Only hover/active backgrounds differentiate them.
- The drawer stays open after selecting a session; sizing changes are visible immediately.
- Profile avatars in the sidebar should remain compact and squarish (`rounded-md`), even when history blocks are larger.
