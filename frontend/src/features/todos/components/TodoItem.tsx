/**
 * Todo item card component
 *
 * Displays individual todo with title, description, priority badge,
 * due date, completion checkbox, and action buttons (edit, delete).
 */

import { useState } from "react";
import { PriorityBadge } from "../../../components/PriorityBadge";
import { Button } from "../../../components/ui/Button";
import type { TodoResponse } from "../../../lib/api/generated/api.schemas";
import { formatDate } from "../../../lib/utils";

interface TodoItemProps {
  todo: TodoResponse;
  onToggleComplete: (id: number, completed: boolean) => void;
  onEdit: (todo: TodoResponse) => void;
  onDelete: (id: number) => void;
}

export function TodoItem({ todo, onToggleComplete, onEdit, onDelete }: TodoItemProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const isOverdue = !todo.completed && todo.due_date && new Date(todo.due_date) < new Date();

  const handleDelete = () => {
    onDelete(todo.id);
    setShowDeleteConfirm(false);
  };

  return (
    <div
      className={`bg-white border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow ${
        isOverdue ? "border-red-300 bg-red-50" : "border-gray-200"
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        <input
          type="checkbox"
          checked={todo.completed}
          onChange={() => onToggleComplete(todo.id, todo.completed)}
          className="mt-1 h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
        />

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3
              className={`text-lg font-semibold ${
                todo.completed ? "line-through text-gray-400" : "text-gray-900"
              }`}
            >
              {todo.title}
            </h3>
            <PriorityBadge priority={todo.priority} />
          </div>

          {todo.description && (
            <p className={`text-sm mb-2 ${todo.completed ? "text-gray-400" : "text-gray-600"}`}>
              {todo.description.length > 150
                ? `${todo.description.slice(0, 150)}...`
                : todo.description}
            </p>
          )}

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mb-3">
            {todo.due_date && (
              <span className={isOverdue ? "text-red-600 font-semibold" : ""}>
                Due: {formatDate(todo.due_date)}
                {isOverdue && " (Overdue)"}
              </span>
            )}
            <span>Created: {formatDate(todo.created_at)}</span>
          </div>

          {/* Actions */}
          {!showDeleteConfirm ? (
            <div className="flex gap-2">
              <Button size="sm" variant="ghost" onClick={() => onEdit(todo)}>
                Edit
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowDeleteConfirm(true)}
                className="text-red-600 bg-red-50 hover:bg-red-100"
              >
                Delete
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">Delete this todo?</span>
              <Button size="sm" variant="danger" onClick={handleDelete}>
                Confirm
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setShowDeleteConfirm(false)}
                className="bg-gray-100 text-gray-600 hover:bg-gray-200"
              >
                Cancel
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
