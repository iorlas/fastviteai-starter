/**
 * Todo statistics component
 *
 * Displays summary statistics about todos including total count,
 * completed count, active count, and overdue count.
 */

import type { TodoResponse } from "../../../lib/api/generated/api.schemas";

interface TodoStatsProps {
  todos: TodoResponse[];
}

export function TodoStats({ todos }: TodoStatsProps) {
  const now = new Date();

  const stats = {
    total: todos.length,
    completed: todos.filter((todo) => todo.completed).length,
    active: todos.filter((todo) => !todo.completed).length,
    overdue: todos.filter(
      (todo) => !todo.completed && todo.due_date && new Date(todo.due_date) < now,
    ).length,
  };

  const statCards = [
    { label: "Total", value: stats.total, color: "bg-blue-50 border-blue-200 text-blue-800" },
    {
      label: "Completed",
      value: stats.completed,
      color: "bg-green-50 border-green-200 text-green-800",
    },
    {
      label: "Active",
      value: stats.active,
      color: "bg-amber-50 border-amber-200 text-amber-800",
    },
    { label: "Overdue", value: stats.overdue, color: "bg-red-50 border-red-200 text-red-800" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {statCards.map((stat) => (
        <div key={stat.label} className={`${stat.color} border rounded-lg p-4`}>
          <div className="text-2xl font-bold mb-1">{stat.value}</div>
          <div className="text-sm font-medium">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}
