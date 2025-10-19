/**
 * Todo filters component
 *
 * Provides UI controls for filtering, searching, and sorting todos.
 * Includes search input, priority filter, completion filter, and sort controls.
 */

import { useEffect, useId, useState } from "react";
import { Button } from "../../../components/ui/Button";
import type { TodoFilters } from "../hooks/useTodos";

interface TodoFiltersProps {
  filters: TodoFilters;
  onFilterChange: (filters: Partial<TodoFilters>) => void;
  onReset: () => void;
}

export function TodoFiltersComponent({ filters, onFilterChange, onReset }: TodoFiltersProps) {
  // Generate unique IDs for form controls
  const searchId = useId();
  const priorityId = useId();
  const completedId = useId();
  const sortId = useId();

  // Local state for debounced search
  const [searchInput, setSearchInput] = useState(filters.search);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onFilterChange({ search: searchInput });
    }, 300);

    return () => clearTimeout(timer);
  }, [searchInput, onFilterChange]);

  return (
    <div className="bg-white shadow rounded-lg p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        <Button size="sm" variant="ghost" onClick={onReset} className="text-sm font-medium">
          Reset Filters
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Search Input */}
        <div>
          <label htmlFor={searchId} className="block text-sm font-medium text-gray-700 mb-1">
            Search
          </label>
          <input
            type="text"
            id={searchId}
            placeholder="Search todos..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Priority Filter */}
        <div>
          <label htmlFor={priorityId} className="block text-sm font-medium text-gray-700 mb-1">
            Priority
          </label>
          <select
            id={priorityId}
            value={filters.priority || ""}
            onChange={(e) => onFilterChange({ priority: e.target.value || null })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>

        {/* Completion Filter */}
        <div>
          <label htmlFor={completedId} className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            id={completedId}
            value={filters.completed === null ? "" : String(filters.completed)}
            onChange={(e) => {
              const value = e.target.value;
              onFilterChange({
                completed: value === "" ? null : value === "true",
              });
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Tasks</option>
            <option value="false">Active</option>
            <option value="true">Completed</option>
          </select>
        </div>

        {/* Sort Controls */}
        <div>
          <label htmlFor={sortId} className="block text-sm font-medium text-gray-700 mb-1">
            Sort By
          </label>
          <div className="flex gap-2">
            <select
              id={sortId}
              value={filters.sortBy}
              onChange={(e) => onFilterChange({ sortBy: e.target.value })}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="created_at">Created Date</option>
              <option value="due_date">Due Date</option>
              <option value="priority">Priority</option>
              <option value="title">Title</option>
            </select>
            <button
              type="button"
              onClick={() =>
                onFilterChange({
                  sortOrder: filters.sortOrder === "asc" ? "desc" : "asc",
                })
              }
              className="px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              title={filters.sortOrder === "asc" ? "Ascending" : "Descending"}
            >
              {filters.sortOrder === "asc" ? "↑" : "↓"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
