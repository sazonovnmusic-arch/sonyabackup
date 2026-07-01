# React Prop/State Mismatch Pitfall

Real bug from AI Workspace session: `setActiveSessionIds is not defined` appeared in every chat.

## Root cause
- `activeSessionIds` and `setActiveSessionIds` were defined in `App`.
- `App` passed `activeSessionIds` to `ChatView`, but not `setActiveSessionIds`.
- Inside `ChatView`, `setActiveSessionIds` was called (in `setActiveSession`, `deleteSession`, etc.), causing runtime ReferenceError and black screen.

## Fix
1. Pass the setter from `App`:
   ```jsx
   <ChatView
     selected={selected}
     activeSessionIds={activeSessionIds}
     setActiveSessionIds={setActiveSessionIds}
     ...
   />
   ```
2. Accept it in `ChatView` signature:
   ```jsx
   function ChatView({ selected, activeSessionIds, setActiveSessionIds, initialHistoryOpen }) {
   ```

## Prevention checklist
- If a child calls a setter, verify the parent passes it.
- If lifting state up, update both the call site and the component signature.
- After build, grep the generated `dist/assets/index-*.js` for the setter name; if only 1 occurrence, it likely isn't being passed.
- On black screen, open browser console before refreshing.
