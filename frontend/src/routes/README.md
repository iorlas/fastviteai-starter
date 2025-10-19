# Routes Directory

This directory contains TanStack Router route definitions for file-based routing.

## Structure

Routes will be organized following TanStack Router conventions:
- Each file represents a route
- Nested directories represent nested routes
- Special files for layouts and error boundaries

## Example

```
routes/
├── __root.tsx       # Root layout
├── index.tsx        # / route
├── login.tsx        # /login route
├── signup.tsx       # /signup route
└── todos/
    ├── index.tsx    # /todos route
    └── $id.tsx      # /todos/:id route
```

## Documentation

See TanStack Router documentation: https://tanstack.com/router/latest
