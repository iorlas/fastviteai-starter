/**
 * Shared utility functions
 *
 * Common utilities used across the application. Extract functions here
 * when they're used in multiple components.
 */

/**
 * Format a date string or Date object into a localized string
 *
 * @param dateString - ISO date string, Date object, or null
 * @param options - Intl.DateTimeFormat options for custom formatting
 * @returns Formatted date string or null if input is null
 *
 * @example
 * ```tsx
 * formatDate("2024-01-15T10:30:00Z")
 * // => "Jan 15, 2024, 10:30 AM"
 *
 * formatDate(todo.created_at, { dateStyle: "short" })
 * // => "1/15/24"
 *
 * formatDate(null)
 * // => null
 * ```
 */
export function formatDate(
  dateString: string | Date | null,
  options?: Intl.DateTimeFormatOptions,
): string | null {
  if (!dateString) return null;

  const date = typeof dateString === "string" ? new Date(dateString) : dateString;

  const defaultOptions: Intl.DateTimeFormatOptions = {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  };

  return date.toLocaleDateString("en-US", options || defaultOptions);
}
