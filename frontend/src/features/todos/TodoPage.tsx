/**
 * Todo Page - Main component for todo management
 *
 * Shows all key patterns INLINE for easy learning by example:
 * - TanStack Query data fetching with filters and pagination
 * - Mutation hooks with cache invalidation
 * - Filter and pagination state management
 * - Form handling with create/update modes
 *
 * This component demonstrates the complete CRUD pattern that can be
 * copied and adapted for other features. All patterns are visible
 * directly in this file rather than hidden behind custom hooks.
 */

import { useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Button } from "../../components/ui/Button";
import type {
  ListTodosApiV1TodosGetParams,
  TodoCreate,
  TodoResponse,
  TodoUpdate,
} from "../../lib/api/generated/api.schemas";
import {
  getListTodosApiV1TodosGetQueryKey,
  useCreateTodoApiV1TodosPost,
  useDeleteTodoApiV1TodosIdDelete,
  useListTodosApiV1TodosGet,
  useUpdateTodoApiV1TodosIdPatch,
} from "../../lib/api/generated/todos/todos";
import { TodoFiltersComponent } from "./components/TodoFilters";
import { TodoForm } from "./components/TodoForm";
import { TodoList } from "./components/TodoList";
import { TodoStats } from "./components/TodoStats";

export function TodoPage() {
  const queryClient = useQueryClient();

  // ============================================
  // PATTERN 1: FILTER STATE MANAGEMENT
  // ============================================
  const [filters, setFilters] = useState({
    search: "",
    completed: null as boolean | null,
    priority: null as string | null,
    sortBy: "created_at",
    sortOrder: "desc" as "asc" | "desc",
  });

  const [pagination, setPagination] = useState({
    offset: 0,
    limit: 50,
  });

  const updateFilters = (newFilters: Partial<typeof filters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
    // Reset to first page when filters change
    setPagination((prev) => ({ ...prev, offset: 0 }));
  };

  const resetFilters = () => {
    setFilters({
      search: "",
      completed: null,
      priority: null,
      sortBy: "created_at",
      sortOrder: "desc",
    });
    setPagination({ offset: 0, limit: 50 });
  };

  // ============================================
  // PATTERN 2: DATA FETCHING WITH TANSTACK QUERY
  // Shows: Query hook usage, params building, caching config
  // ============================================
  const queryParams = useMemo<ListTodosApiV1TodosGetParams>(
    () => ({
      offset: pagination.offset,
      limit: pagination.limit,
      completed: filters.completed,
      priority: filters.priority,
      search: filters.search || null,
      sort_by: filters.sortBy,
      sort_order: filters.sortOrder,
    }),
    [filters, pagination],
  );

  const { data, isLoading, error } = useListTodosApiV1TodosGet(queryParams, {
    query: {
      staleTime: 30000, // 30 seconds
      retry: 1,
    },
  });

  const todos = data?.items || [];
  const total = data?.total || 0;

  // ============================================
  // PATTERN 3: MUTATIONS WITH CACHE INVALIDATION
  // Shows: Mutation hooks, onSuccess callbacks, cache invalidation
  // ============================================
  const createMutation = useCreateTodoApiV1TodosPost({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: getListTodosApiV1TodosGetQueryKey(),
        });
      },
    },
  });

  const updateMutation = useUpdateTodoApiV1TodosIdPatch({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: getListTodosApiV1TodosGetQueryKey(),
        });
      },
    },
  });

  const deleteMutation = useDeleteTodoApiV1TodosIdDelete({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: getListTodosApiV1TodosGetQueryKey(),
        });
      },
    },
  });

  // Mutation helper functions
  const createTodo = (data: TodoCreate) => {
    createMutation.mutate({ data });
  };

  const updateTodo = (id: number, data: TodoUpdate) => {
    updateMutation.mutate({ id, data });
  };

  const deleteTodo = (id: number) => {
    deleteMutation.mutate({ id });
  };

  const toggleComplete = (id: number, completed: boolean) => {
    updateMutation.mutate({ id, data: { completed: !completed } });
  };

  // ============================================
  // PATTERN 4: PAGINATION HELPERS
  // ============================================
  const goToNextPage = () => {
    setPagination((prev) => ({
      ...prev,
      offset: prev.offset + prev.limit,
    }));
  };

  const goToPreviousPage = () => {
    setPagination((prev) => ({
      ...prev,
      offset: Math.max(0, prev.offset - prev.limit),
    }));
  };

  const canGoNext = pagination.offset + pagination.limit < total;
  const canGoPrevious = pagination.offset > 0;

  // ============================================
  // PATTERN 5: FORM STATE MANAGEMENT
  // ============================================
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTodo, setEditingTodo] = useState<TodoResponse | undefined>(undefined);

  const handleOpenCreateForm = () => {
    setEditingTodo(undefined);
    setIsFormOpen(true);
  };

  const handleOpenEditForm = (todo: TodoResponse) => {
    setEditingTodo(todo);
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setEditingTodo(undefined);
  };

  const handleFormSubmit = (data: {
    title: string;
    description?: string;
    priority: "low" | "medium" | "high";
    due_date?: string;
  }) => {
    if (editingTodo) {
      // Update existing todo
      updateTodo(editingTodo.id, {
        title: data.title,
        description: data.description || null,
        priority: data.priority,
        due_date: data.due_date || null,
      });
    } else {
      // Create new todo
      createTodo({
        title: data.title,
        description: data.description,
        priority: data.priority,
        due_date: data.due_date,
      });
    }
  };

  // ============================================
  // UI RENDERING
  // ============================================
  return (
    <div className="min-h-[calc(100vh-4rem)] bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Todo Manager</h1>
              <p className="mt-2 text-gray-600">
                Organize and track your tasks with priority levels and due dates
              </p>
            </div>
            <Button variant="primary" onClick={handleOpenCreateForm}>
              + Add Todo
            </Button>
          </div>
        </div>

        {/* Stats */}
        <TodoStats todos={todos} />

        {/* Filters */}
        <TodoFiltersComponent
          filters={filters}
          onFilterChange={updateFilters}
          onReset={resetFilters}
        />

        {/* Results Info */}
        {!isLoading && (
          <div className="mb-4 text-sm text-gray-600">
            Showing {pagination.offset + 1}-{Math.min(pagination.offset + pagination.limit, total)}{" "}
            of {total} todos
          </div>
        )}

        {/* Todo List - Shows loading, error, and data states inline */}
        <TodoList
          todos={todos}
          isLoading={isLoading}
          error={error ? String(error) : null}
          onToggleComplete={toggleComplete}
          onEdit={handleOpenEditForm}
          onDelete={deleteTodo}
        />

        {/* Pagination */}
        {total > pagination.limit && (
          <div className="mt-6 flex items-center justify-center gap-4">
            <Button variant="secondary" onClick={goToPreviousPage} disabled={!canGoPrevious}>
              Previous
            </Button>
            <span className="text-sm text-gray-600">
              Page {Math.floor(pagination.offset / pagination.limit) + 1} of{" "}
              {Math.ceil(total / pagination.limit)}
            </span>
            <Button variant="secondary" onClick={goToNextPage} disabled={!canGoNext}>
              Next
            </Button>
          </div>
        )}

        {/* Todo Form Modal */}
        <TodoForm
          todo={editingTodo}
          isOpen={isFormOpen}
          onClose={handleCloseForm}
          onSubmit={handleFormSubmit}
          isSubmitting={
            createMutation.isPending || updateMutation.isPending || deleteMutation.isPending
          }
        />
      </div>
    </div>
  );
}
