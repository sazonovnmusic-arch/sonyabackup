# Roundness and profile avatar rules for AI Workspace UI

This reference captures the visual styling rules that stabilized after several iterations for this user's AI Workspace.

## Core principle: strong rounding, but avatars stay squarish

The UI is compact, dark, and friendly. Rounded corners are used almost everywhere, but profile/agent avatars keep a squarish silhouette so they read as distinct from circular user avatars.

## Color tokens

```css
:root {
  --bg: #0a0a0a;
  --surface: #111111;
  --surface-2: #171717;
  --surface-3: #1f1f1f;
  --border: #252525;
  --border-2: #303030;
  --text: #f0f0f0;
  --text-dim: #808080;
  --accent: #0ea5e9;
  --danger: #ef4444;
}
```

## Rounding scale

| Element | Radius token | Approximate px | Notes |
|---------|--------------|----------------|-------|
| Buttons, inputs, cards | `rounded-lg` / `rounded-xl` | 8–12 px | Default for interactive surfaces. |
| Message bubbles | `rounded-3xl` with one tail corner less rounded | ~24 px + `rounded-br-md` / `rounded-bl-md` | ChatGPT-style bubbles with a sharp tail corner. |
| Small utility buttons | `rounded-md` | 6 px | Sidebar toggles, close buttons. |
| Modals / drawers | `var(--radius-lg)` / `var(--radius-xl)` | 12–16 px | Consistent with theme. |
| Profile avatars | `rounded-md` / `rounded-xl` | 6–12 px | **Not circular.** Keep square-ish with soft rounding. |

Avoid pixel/arcade/retro styles unless explicitly requested. If the user says "слишком аркадный", "убери пиксельный", or "верни минималистичный", revert to the clean dark system above.

## Profile avatar implementation

The top-left generic "AI" badge and the welcome-screen icon should both show the **selected profile's initials**, not a generic AI logo.

### Sidebar avatar strip

```jsx
<button
  className="w-10 h-10 border flex items-center justify-center text-xs font-medium transition overflow-hidden rounded-xl"
  style={{ borderColor: isActive ? 'var(--accent)' : 'var(--border)' }}
>
  {p.has_avatar ? (
    <img src={`${API}/profiles/${p.name}/avatar`} alt={p.name} className="w-full h-full object-cover" />
  ) : (
    p.name.slice(0, 2).toUpperCase()
  )}
</button>
```

### Welcome screen avatar

When no session is selected, replace the generic "AI" icon with the selected profile's initials or avatar:

```jsx
<div className="w-10 h-10 mb-6 flex items-center justify-center border border-[var(--accent)] bg-[var(--surface-2)] text-[var(--accent)] text-sm font-medium rounded-xl overflow-hidden">
  {selected?.has_avatar ? (
    <img src={`${API}/profiles/${selected.name}/avatar`} alt={selected.name} className="w-full h-full object-cover" />
  ) : (
    selected?.name?.slice(0, 2).toUpperCase() || '?'
  )}
</div>
<h2 className="text-xl text-[var(--text)] mb-2">
  {selected ? `На связи ${selected.name}, чем могу помочь?` : 'Выберите агента'}
</h2>
```

When the user later supplies PNG icons, swap the initials for the image without changing the container shape.

## Common mistakes

1. **Circular avatars.** Do not use `rounded-full` for profile avatars unless the user explicitly asks. The settled style is square-ish with soft rounding.
2. **Generic AI logo in the welcome screen.** The logo area should identify the selected agent, not the product.
3. **Too little rounding on cards/buttons.** If the UI feels harsh, increase radius to `rounded-xl`/`rounded-2xl` before adding shadows or colors.
4. **Pixel/retro styling by default.** Only apply after explicit request; revert quickly if rejected.
