/**
 * Generic priority badge component for displaying priority indicators
 *
 * Reusable component that can be used throughout the application
 * to display priority levels with color-coded visual indicators.
 */

interface PriorityBadgeProps {
  priority: "low" | "medium" | "high";
}

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  const variantStyles = {
    low: "bg-green-100 text-green-800 border-green-600",
    medium: "bg-amber-100 text-amber-800 border-amber-600",
    high: "bg-red-100 text-red-800 border-red-600",
  };

  const dotStyles = {
    low: "bg-green-600",
    medium: "bg-amber-600",
    high: "bg-red-600",
  };

  const labels = {
    low: "Low",
    medium: "Medium",
    high: "High",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold ${variantStyles[priority]}`}
    >
      <span className={`mr-2 h-2 w-2 rounded-full ${dotStyles[priority]}`} />
      {labels[priority]}
    </span>
  );
}
