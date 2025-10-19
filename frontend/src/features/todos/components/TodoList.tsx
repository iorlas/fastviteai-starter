/**
 * Todo list component
 *
 * Renders a grid of TodoItem components with loading skeleton,
 * error state, and empty state handling.
 */

import type { TodoResponse } from "../../../lib/api/generated/api.schemas";
import { TodoItem } from "./TodoItem";

interface TodoListProps {
  todos: TodoResponse[];
  isLoading: boolean;
  error: string | null;
  onToggleComplete: (id: number, completed: boolean) => void;
  onEdit: (todo: TodoResponse) => void;
  onDelete: (id: number) => void;
}

export function TodoList({
  todos,
  isLoading,
  error,
  onToggleComplete,
  onEdit,
  onDelete,
}: TodoListProps) {
  // Loading state
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <div
            key={`skeleton-${
              // biome-ignore lint/suspicious/noArrayIndexKey: skeleton items don't have stable IDs
              i
            }`}
            className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm animate-pulse"
          >
            <div className="flex items-start gap-3">
              <div className="h-5 w-5 bg-gray-200 rounded mt-1" />
              <div className="flex-1 space-y-3">
                <div className="h-6 bg-gray-200 rounded w-3/4" />
                <div className="h-4 bg-gray-200 rounded w-full" />
                <div className="h-4 bg-gray-200 rounded w-2/3" />
                <div className="flex gap-2">
                  <div className="h-8 bg-gray-200 rounded w-16" />
                  <div className="h-8 bg-gray-200 rounded w-16" />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <div className="text-red-600 font-semibold mb-2">Error Loading Todos</div>
        <p className="text-red-700 text-sm">{error}</p>
      </div>
    );
  }

  // Empty state
  if (todos.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
        <div className="text-gray-400 mb-4">
          <svg
            className="mx-auto h-12 w-12"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <title>No todos icon</title>
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No todos found</h3>
        <p className="text-gray-600">
          Get started by creating your first todo or adjust your filters.
        </p>
      </div>
    );
  }

  // Todo list
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {todos.map((todo) => (
        <TodoItem
          key={todo.id}
          todo={todo}
          onToggleComplete={onToggleComplete}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
