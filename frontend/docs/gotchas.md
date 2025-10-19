# Frontend Gotchas

Common pitfalls and best practices for the React frontend. Keep this list compact for quick reference.

---

## 1. Forms: Transform Empty Datetime Strings
Convert empty datetime strings to `undefined` before sending to API. HTML forms send `""`, but API expects `null`.
**See:** `src/features/todos/components/TodoForm.tsx:76`

---

## 2. Forms: Extract Validation Schemas
Always extract Zod schemas to `features/[feature]/schemas/[entity].schema.ts` for reusability and testing.
**See:** `src/features/todos/schemas/todo.schema.ts`

---

## 3. Buttons: Use Button Component
Never write inline button styles. Use `<Button>` component with variants (`primary`, `secondary`, `danger`, `ghost`).
**See:** `src/components/ui/Button.tsx`

---

## 4. TanStack Query: Show Patterns Inline
Don't hide query/mutation logic behind custom hooks. Show the patterns directly in the page component for learning by example.
**See:** `src/features/todos/TodoPage.tsx` - all query and mutation logic is visible

---

## 5. Loading/Error States: Keep Inline in Components
Show loading skeletons and error states directly in list components (not abstracted). LLMs learn best from visible patterns.
**See:** `src/features/todos/components/TodoList.tsx:29-66` - inline loading/error patterns

---

## 6. Class Names: Use cn() Utility
When merging Tailwind classes (especially in components with className prop), use `cn()` to resolve conflicts.
**See:** `src/lib/cn.ts`, `src/components/ui/Button.tsx:96`

---

**Last Updated:** 2025-10-19
