# 07-iitb-baap-agent: Code Review and Optimization Notes

Scope reviewed: `bharatbricksiitb/07-iitb-baap-agent`

---

## Findings (ordered by impact)

### 1) High: "Ephemeral mode" still attempts DB writes

In `chat` route, the code indicates that when DB is unavailable it should run in ephemeral mode (no persistence). However, the user-message path still calls `saveMessages` unconditionally.

- **Risk**: If DB is down/disabled, normal chat sends can fail instead of degrading gracefully.
- **File**: `e2e-chatbot-app-next/server/src/routes/chat.ts`

```ts
// If message is provided, add it to the list and save it
// If not (continuation/regeneration), just use previous messages
let uiMessages: ChatMessage[];
if (message) {
  uiMessages = [...previousMessages, message];
  await saveMessages({
    messages: [
      {
        chatId: id,
        id: message.id,
        role: 'user',
        parts: message.parts,
        attachments: [],
        createdAt: new Date(),
        traceId: null,
      },
    ],
  });
}
```

---

### 2) Medium: Tool prefetch strategy is expensive on every turn

Backend always prefetches both vector search and Genie, then injects both outputs into context every request.

- **Risk**: Avoidable latency and token cost on many turns, especially follow-ups and low-information queries.
- **File**: `agent_server/agent.py`

```py
await asyncio.gather(
    call_tool("vs", vs_tool, {"query": user_query}),
    call_tool("genie", genie_tool, {"query": user_query}),
)
```

---

### 3) Medium: Scroll state is derived from duplicate hooks

`useScrollToBottom()` is instantiated in multiple components, but only one instance is actually bound to the message container.

- **Risk**: Inconsistent "scroll to bottom" UX and hard-to-debug state divergence.
- **Files**:
  - `client/src/components/messages.tsx`
  - `client/src/components/multimodal-input.tsx`
  - `client/src/hooks/use-scroll-to-bottom.tsx`

```tsx
const { isAtBottom, scrollToBottom } = useScrollToBottom();
```

---

### 4) Low: Tool cache TTL behavior is misleading

`_CACHE_TTL_SECONDS` is set, but cache reuse condition effectively keeps tools forever once MCP tools are present.

- **Risk**: Stale tool registry/names, confusion for maintainers.
- **File**: `agent_server/agent.py`

---

## UI/UX improvement opportunities

- Add explicit sign-in call-to-action on unauthenticated screen (instead of passive message).
- Show a visible "ephemeral mode" indicator when DB is unavailable so users understand chat history/feedback behavior.
- Improve recovery affordances in chat error states (retry where safe, clearer error messaging).
- Consider reducing duplicate scroll-to-bottom controls or wiring both controls to the same state source.

---

## Performance improvement opportunities

- Gate prefetching by intent/type of user turn instead of always calling both tools.
- Truncate or summarize tool outputs before injecting to prompt context.
- Add server-side max cap for `/api/history?limit=` to avoid expensive accidental requests.
- Reduce verbose logging in hot paths; keep structured logs at warning/error in production.

---

## Code clarity and effectiveness opportunities

- Align comments with actual behavior (ephemeral and caching comments currently overstate guarantees).
- Centralize scroll management into one hook instance/provider shared by both message pane and input controls.
- Add defensive DB-availability guards around persistence calls to match intended fallback behavior.
- Standardize error handling patterns across routes (`ChatSDKError` vs generic 500 responses).

---

## Suggested execution order

1. Fix ephemeral mode write guards in `chat.ts` (highest correctness impact).
2. Refactor prefetch policy in `agent.py` to avoid unconditional dual-tool calls.
3. Consolidate scroll-state ownership across `messages` and `multimodal-input`.
4. Clean up cache TTL semantics and comments in `agent.py`.
5. Apply UX polish and logging cleanup.

---

## Assumptions

- Assumed `@chat-template/db` may throw or fail in DB-disabled states unless guarded.
- Review focused on primary source paths and excluded generated build artifacts.
