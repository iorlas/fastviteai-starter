/**
 * Todo form component
 *
 * Modal form for creating and editing todos with React Hook Form
 * and Zod validation. Supports title, description, priority, and due date fields.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useId } from "react";
import { useForm } from "react-hook-form";
import { Button } from "../../../components/ui/Button";
import type { PriorityEnum, TodoResponse } from "../../../lib/api/generated/api.schemas";
import { type TodoFormData, todoFormSchema } from "../schemas/todo.schema";

interface TodoFormProps {
  todo?: TodoResponse;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: TodoFormData) => void;
  isSubmitting?: boolean;
}

export function TodoForm({ todo, isOpen, onClose, onSubmit, isSubmitting }: TodoFormProps) {
  // Generate unique IDs for form controls
  const titleId = useId();
  const descriptionId = useId();
  const priorityId = useId();
  const dueDateId = useId();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TodoFormData>({
    resolver: zodResolver(todoFormSchema),
    defaultValues: {
      title: "",
      description: "",
      priority: "medium" as PriorityEnum,
      due_date: "",
    },
  });

  // Reset form when todo changes or modal opens
  useEffect(() => {
    if (isOpen) {
      if (todo) {
        // Edit mode - populate with existing data
        reset({
          title: todo.title,
          description: todo.description || "",
          priority: todo.priority,
          due_date: todo.due_date ? new Date(todo.due_date).toISOString().slice(0, 16) : "",
        });
      } else {
        // Create mode - reset to defaults
        reset({
          title: "",
          description: "",
          priority: "medium",
          due_date: "",
        });
      }
    }
  }, [todo, isOpen, reset]);

  const handleFormSubmit = (data: TodoFormData) => {
    // Transform empty strings to undefined for optional fields
    // The API expects null (not empty strings) for optional datetime fields
    const transformed = {
      ...data,
      due_date: data.due_date || undefined,
    };
    onSubmit(transformed);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            {todo ? "Edit Todo" : "Create New Todo"}
          </h2>

          <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
            {/* Title Field */}
            <div>
              <label htmlFor={titleId} className="block text-sm font-medium text-gray-700 mb-1">
                Title <span className="text-red-600">*</span>
              </label>
              <input
                type="text"
                id={titleId}
                {...register("title")}
                className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.title ? "border-red-500" : "border-gray-300"
                }`}
                placeholder="Enter todo title"
              />
              {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>}
            </div>

            {/* Description Field */}
            <div>
              <label
                htmlFor={descriptionId}
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Description
              </label>
              <textarea
                id={descriptionId}
                {...register("description")}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter description (optional)"
              />
            </div>

            {/* Priority Field */}
            <div>
              <label htmlFor={priorityId} className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                id={priorityId}
                {...register("priority")}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>

            {/* Due Date Field */}
            <div>
              <label htmlFor={dueDateId} className="block text-sm font-medium text-gray-700 mb-1">
                Due Date
              </label>
              <input
                type="datetime-local"
                id={dueDateId}
                {...register("due_date")}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Form Actions */}
            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="secondary"
                fullWidth
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" fullWidth isLoading={isSubmitting}>
                {todo ? "Update" : "Create"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
