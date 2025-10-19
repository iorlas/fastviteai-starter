/**
 * Todo form validation schemas
 *
 * Zod schemas for todo form validation. Exported for reuse across
 * create and edit forms, tests, and other components that need validation.
 *
 * @example
 * ```tsx
 * import { todoFormSchema, type TodoFormData } from './schemas/todo.schema';
 *
 * const form = useForm<TodoFormData>({
 *   resolver: zodResolver(todoFormSchema),
 * });
 * ```
 */

import { z } from "zod";

/**
 * Schema for todo form data validation
 *
 * Validates:
 * - title: Required, 1-200 characters
 * - description: Optional string
 * - priority: Must be "low", "medium", or "high"
 * - due_date: Optional datetime string (from datetime-local input)
 */
export const todoFormSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title must be 200 characters or less"),
  description: z.string().optional(),
  priority: z.enum(["low", "medium", "high"]),
  due_date: z.string().optional(),
});

/**
 * Inferred TypeScript type from todoFormSchema
 *
 * Use this type for form data in components and hooks.
 */
export type TodoFormData = z.infer<typeof todoFormSchema>;
