/**
 * Utility for merging Tailwind CSS class names
 *
 * Combines clsx (for conditional classes) and tailwind-merge (for resolving conflicts).
 * Use this to merge className props and avoid Tailwind class conflicts.
 *
 * @example
 * ```tsx
 * // Basic usage
 * cn("px-2 py-1", "px-4") // => "py-1 px-4" (px-4 wins)
 *
 * // Conditional classes
 * cn("text-base", { "font-bold": isActive }) // => "text-base font-bold" or "text-base"
 *
 * // Component with className prop
 * function Button({ className, ...props }: ButtonProps) {
 *   return (
 *     <button className={cn("px-4 py-2 rounded", className)} {...props} />
 *   );
 * }
 *
 * <Button className="bg-blue-500" /> // => "px-4 py-2 rounded bg-blue-500"
 * ```
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge class names with Tailwind CSS conflict resolution
 *
 * Accepts any number of class values (strings, objects, arrays) and returns
 * a single string with conflicts resolved (later classes win).
 *
 * @param inputs - Class names to merge (strings, objects, arrays, etc.)
 * @returns Merged class name string with conflicts resolved
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
