import { createFileRoute } from "@tanstack/react-router";
import { TodoPage } from "../features/todos/TodoPage";

export const Route = createFileRoute("/todos")({
  component: TodoPage,
  // Note: TodoList component handles loading/error states internally
  // No need for route-level pendingComponent
});
