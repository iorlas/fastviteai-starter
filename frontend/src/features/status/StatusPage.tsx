/**
 * System Status Page
 *
 * Displays real-time health status of backend services including
 * application health and database connectivity. Auto-refreshes
 * every 1.5 seconds to provide live monitoring.
 */

import { useId } from "react";
import { StatusCard } from "./components/StatusCard";
import { StatusOverview } from "./components/StatusOverview";
import { useHealthStatus } from "./hooks/useHealthStatus";

export function StatusPage() {
  const healthStatus = useHealthStatus();
  const infoIconTitleId = useId();

  const isAppHealthy = healthStatus.app.status === "healthy" && !healthStatus.app.error;
  const isDatabaseHealthy =
    healthStatus.database.status === "healthy" &&
    healthStatus.database.connection === "connected" &&
    !healthStatus.database.error &&
    !healthStatus.database.httpError;

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">System Status</h1>
          <p className="mt-2 text-gray-600">
            Real-time monitoring of backend services and infrastructure
          </p>
        </div>

        <StatusOverview lastUpdated={healthStatus.lastUpdated} />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <StatusCard
            title="Application"
            status={healthStatus.app.status}
            isHealthy={isAppHealthy}
            isLoading={healthStatus.app.isLoading}
            error={healthStatus.app.error}
          />

          <StatusCard
            title="Database"
            status={healthStatus.database.status}
            isHealthy={isDatabaseHealthy}
            isLoading={healthStatus.database.isLoading}
            error={
              healthStatus.database.httpError
                ? "Unable to connect to health check endpoint"
                : healthStatus.database.error
            }
            additionalInfo={healthStatus.database.connection}
          />
        </div>

        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-blue-400"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-labelledby={infoIconTitleId}
              >
                <title id={infoIconTitleId}>Information</title>
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">About this page</h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  This page displays the real-time health status of backend services. Data is
                  automatically refreshed every 1.5 seconds. A green status indicates the service is
                  operational, while a red status indicates an issue that requires attention.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
