# Frontend (React + TypeScript + Vite)

Modern React frontend built with TypeScript, Vite, and TanStack ecosystem.

## Commands

**See [Makefile](Makefile) for all available commands.** Run `make` or `make help` to see the full list.

Quick reference:
- `make install` - Install dependencies
- `make dev` - Start development server
- `make check` - Format and lint with auto-fix
- `make test` - Run tests with coverage

**Note**: Both `make <command>` and `pnpm <command>` work. The Makefile wraps pnpm scripts for documentation and discoverability.

## Technology Stack

### Core
- **Framework**: [React 19](https://react.dev/) - UI library
- **Build Tool**: [Vite](https://vite.dev/) - Fast build tool and dev server
- **Language**: [TypeScript](https://www.typescriptlang.org/) - Type-safe JavaScript
- **Package Manager**: [pnpm](https://pnpm.io/) - Fast, disk space efficient package manager

### Routing & Data Fetching
- **Routing**: [TanStack Router](https://tanstack.com/router) - Type-safe routing with file-based routes
- **Data Fetching**: [TanStack Query](https://tanstack.com/query) - Async state management
- **API Client**: [Axios](https://axios-http.com/) - HTTP client
- **Code Generation**: [Orval](https://orval.dev/) - Generate TypeScript/TanStack Query hooks from OpenAPI

### Forms & Validation
- **Forms**: [React Hook Form](https://react-hook-form.com/) - Performant, flexible forms
- **Validation**: [Zod](https://zod.dev/) - TypeScript-first schema validation

### Styling
- **CSS Framework**: [Tailwind CSS v4](https://tailwindcss.com/) - Utility-first CSS

### Development Tools
- **Linting/Formatting**: [Biome](https://biomejs.dev/) - Fast linter and formatter (replaces ESLint + Prettier)
- **Testing**: [Vitest](https://vitest.dev/) - Vite-native test runner
- **Testing Library**: [@testing-library/react](https://testing-library.com/react) - User-centric testing utilities
- **API Mocking**: [MSW](https://mswjs.io/) - Mock Service Worker for API mocking

## Architecture: Feature-Based Components

Feature-based folder organization for scalability. Components are organized by domain rather than by type.

```
src/
├── lib/
│   └── api/          # API client, Axios config, generated types (Orval)
├── features/         # Domain-specific components (e.g., auth/, todos/)
├── components/       # Shared UI components (generic, reusable)
├── routes/           # TanStack Router route definitions
└── tests/
    ├── setup.ts      # Vitest and Testing Library config
    └── mocks/        # MSW (Mock Service Worker) API mocks
```

### Directory Guidelines

- **lib/api/**: API client configuration and generated types from OpenAPI
- **features/**: Domain-specific logic organized by feature (e.g., `auth/`, `dashboard/`)
- **components/**: Generic, reusable UI components (e.g., Button, Input, Modal)
- **routes/**: File-based routing with TanStack Router
- **tests/**: Testing infrastructure including MSW mocks and test utilities

### Example Feature Structure

```
features/
└── todos/
    ├── components/       # Feature-specific components
    │   ├── TodoList.tsx
    │   └── TodoItem.tsx
    ├── hooks/            # Feature-specific hooks
    │   └── useTodos.tsx
    ├── api/              # Feature-specific API calls (uses generated client)
    │   └── todos.ts
    └── types/            # Feature-specific types
        └── todo.ts
```

## Setup

### Prerequisites

- Node.js 22+
- pnpm 9+

### Installation

```bash
# Install dependencies
make install

# Or manually
pnpm install
```

### Configuration

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Environment variables:

- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

All environment variables must be prefixed with `VITE_` to be exposed to the client.

### Development

```bash
# Start development server
make dev

# Or manually
pnpm dev

# Server runs at http://localhost:5173
```

## API Client Generation

Uses Orval to generate TypeScript + TanStack Query hooks from FastAPI OpenAPI spec.

### Generate API Client

```bash
# Make sure backend is running (http://localhost:8000)
make codegen

# Or manually
pnpm codegen
```

This reads from `http://localhost:8000/openapi.json` (or `VITE_API_URL`) and generates:
- TypeScript types
- TanStack Query hooks (useQuery, useMutation)
- Axios HTTP client

Output: `src/lib/api/generated/`

### Configuration

See `orval.config.ts` for code generation settings.

**Run `make codegen` after any backend API changes.**

## Routing

Uses TanStack Router with file-based routing.

### Route Files

Routes are defined in `src/routes/`:

```
routes/
├── __root.tsx        # Root layout
├── index.tsx         # / route
└── about.tsx         # /about route
```

### Route Definition Example

```tsx
// routes/about.tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/about')({
  component: AboutComponent,
})

function AboutComponent() {
  return <div>About page</div>
}
```

See [TanStack Router docs](https://tanstack.com/router/latest/docs/framework/react/guide/file-based-routing) for more.

## State Management

Uses TanStack Query for server state. Generated API hooks automatically handle:
- Data fetching
- Caching
- Revalidation
- Loading/error states

```tsx
// Example using generated hook
import { useGetTodos } from '@/lib/api/generated'

function TodoList() {
  const { data, isLoading, error } = useGetTodos()

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return <ul>{data?.map(todo => <li key={todo.id}>{todo.title}</li>)}</ul>
}
```

## Forms

Uses React Hook Form + Zod for type-safe forms with validation.

```tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

type FormData = z.infer<typeof schema>

function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = (data: FormData) => {
    console.log(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <span>{errors.email.message}</span>}
      {/* ... */}
    </form>
  )
}
```

### Handling Optional Fields

**IMPORTANT**: When working with optional datetime, numeric, or UUID fields that map to FastAPI/Pydantic, empty form inputs return empty strings (`""`), but the backend expects `null` or a valid value.

**Solution**: Transform empty strings to `undefined` before submitting:

```tsx
const onSubmit = (data: FormData) => {
  const transformed = {
    ...data,
    due_date: data.due_date || undefined,  // Empty string -> undefined
    priority_level: data.priority_level || undefined,
  }
  createMutation.mutate(transformed)
}
```

**See**: [Frontend Gotchas](docs/gotchas.md) for this and other common pitfalls.

## Testing

### Run Tests

```bash
make test

# Or manually
pnpm test

# Always includes coverage (see package.json)
```

### Test Organization

- **Component tests**: Co-located with components (`*.test.tsx`)
- **Integration tests**: `src/tests/integration/`
- **Test utilities**: `src/tests/setup.ts`
- **API mocks**: `src/tests/mocks/` (MSW handlers)

### Writing Tests

```tsx
// Example component test
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { TodoList } from './TodoList'

describe('TodoList', () => {
  it('renders todo items', () => {
    render(<TodoList />)
    expect(screen.getByText('Buy milk')).toBeInTheDocument()
  })
})
```

### API Mocking with MSW

MSW intercepts HTTP requests at the network level, allowing you to test components that fetch data.

```tsx
// src/tests/mocks/handlers.ts
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/v1/todos', () => {
    return HttpResponse.json([
      { id: 1, title: 'Buy milk', completed: false },
    ])
  }),
]
```

## Build

### Production Build

```bash
make build

# Or manually
pnpm build
```

Output: `dist/` directory

### Preview Production Build

```bash
make preview

# Or manually
pnpm preview
```

## Code Quality

### Format and Lint

```bash
make check

# Runs: biome check src/ --write
# (format + lint with auto-fix)
```

Configuration in `biome.json`.

### Pre-commit Hooks

Pre-commit hooks automatically run quality checks before commits. See [root README](../README.md#pre-commit-hooks) for setup.

## Configuration Files

- **biome.json**: Linting and formatting rules
- **tsconfig.json**: Base TypeScript configuration
- **tsconfig.app.json**: App-specific TypeScript config
- **tsconfig.node.json**: Node/build script TypeScript config
- **vite.config.ts**: Vite build configuration
- **vitest.config.ts**: Vitest test configuration
- **orval.config.ts**: API code generation configuration

## Related Documentation

- [Backend Documentation](../backend/README.md) - FastAPI backend
- [Root README](../README.md) - Project overview and quick start
- [CLAUDE.md](../CLAUDE.md) - AI assistant guide
- [Frontend Gotchas](docs/gotchas.md) - Common frontend pitfalls and best practices (IMPORTANT: read before implementing features)
- [Makefile](Makefile) - All available commands
