/**
 * Status card component for displaying health check information
 *
 * Shows the status of a specific service (app or database) with
 * visual indicators and error messages when applicable.
 */

import { StatusBadge } from "../../../components/StatusBadge";

interface StatusCardProps {
  title: string;
  status: string;
  isHealthy: boolean;
  isLoading: boolean;
  error?: string | null;
  additionalInfo?: string;
}

export function StatusCard({
  title,
  status,
  isHealthy,
  isLoading,
  error,
  additionalInfo,
}: StatusCardProps) {
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
        {isLoading ? (
          <span className="text-sm text-gray-500">Loading...</span>
        ) : (
          <StatusBadge
            variant={isHealthy ? "success" : "error"}
            label={isHealthy ? "Operational" : "Degraded"}
          />
        )}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Status:</span>
          <span className="text-sm font-medium text-gray-900 capitalize">{status}</span>
        </div>

        {additionalInfo && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Connection:</span>
            <span className="text-sm font-medium text-gray-900 capitalize">{additionalInfo}</span>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">
              <span className="font-semibold">Error: </span>
              {error}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
