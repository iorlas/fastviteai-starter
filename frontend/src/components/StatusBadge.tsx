/**
 * Generic status badge component for displaying status indicators
 *
 * Reusable component that can be used throughout the application
 * to display status with color-coded visual indicators.
 */

interface StatusBadgeProps {
  variant: "success" | "error" | "warning" | "info";
  label: string;
}

export function StatusBadge({ variant, label }: StatusBadgeProps) {
  const variantStyles = {
    success: "bg-green-100 text-green-800 border-green-600",
    error: "bg-red-100 text-red-800 border-red-600",
    warning: "bg-yellow-100 text-yellow-800 border-yellow-600",
    info: "bg-blue-100 text-blue-800 border-blue-600",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold ${variantStyles[variant]}`}
    >
      <span
        className={`mr-2 h-2 w-2 rounded-full ${variant === "success" ? "bg-green-600" : variant === "error" ? "bg-red-600" : variant === "warning" ? "bg-yellow-600" : "bg-blue-600"}`}
      />
      {label}
    </span>
  );
}
