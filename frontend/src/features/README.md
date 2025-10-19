# Features Directory

This directory contains feature-based components organized by domain functionality.

## Structure

Each feature should have its own subdirectory containing:
- Feature-specific components
- Feature-specific hooks
- Feature-specific types/interfaces
- Feature-specific tests

## Example

```
features/
├── auth/
│   ├── LoginForm.tsx
│   ├── SignupForm.tsx
│   ├── useAuth.ts
│   └── types.ts
├── todos/
│   ├── TodoList.tsx
│   ├── TodoItem.tsx
│   ├── useTodos.ts
│   └── types.ts
```

##Purpose

Feature-based organization scales better than type-based organization and makes it easier to:
- Find related code
- Extract or refactor features
- Understand feature boundaries
