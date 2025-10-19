/**
 * Button component with variant support
 *
 * Reusable button component with multiple visual variants and sizes.
 * Handles disabled states, loading states, and full width option.
 *
 * @example
 * ```tsx
 * // Primary action button
 * <Button variant="primary" onClick={handleSave}>
 *   Save
 * </Button>
 *
 * // Danger action with confirmation
 * <Button variant="danger" size="sm" onClick={handleDelete}>
 *   Delete
 * </Button>
 *
 * // Ghost button for secondary actions
 * <Button variant="ghost" onClick={handleEdit}>
 *   Edit
 * </Button>
 * ```
 */

import type { ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Visual variant of the button
   * - primary: Blue background, white text (default)
   * - secondary: White background, gray border
   * - danger: Red background, white text
   * - ghost: Transparent background, colored text
   */
  variant?: ButtonVariant;

  /**
   * Size of the button
   * - sm: Compact padding (px-3 py-1)
   * - md: Standard padding (px-4 py-2) (default)
   * - lg: Large padding (px-6 py-3)
   */
  size?: ButtonSize;

  /**
   * Make button full width
   */
  fullWidth?: boolean;

  /**
   * Show loading state (disables button and shows loading text)
   */
  isLoading?: boolean;
}

/**
 * Button component with configurable variants and sizes
 */
export function Button({
  variant = "primary",
  size = "md",
  fullWidth = false,
  isLoading = false,
  className = "",
  disabled,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  const baseStyles =
    "font-medium rounded-md shadow-sm focus:outline-none focus:ring-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed";

  const variantStyles: Record<ButtonVariant, string> = {
    primary:
      "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 border border-transparent",
    secondary: "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-blue-500",
    danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 border border-transparent",
    ghost:
      "bg-blue-50 text-blue-600 hover:bg-blue-100 focus:ring-blue-500 border border-transparent",
  };

  const sizeStyles: Record<ButtonSize, string> = {
    sm: "px-3 py-1 text-sm",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <button
      type={type}
      className={cn(
        baseStyles,
        variantStyles[variant],
        sizeStyles[size],
        fullWidth && "w-full",
        className,
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? "Loading..." : children}
    </button>
  );
}
