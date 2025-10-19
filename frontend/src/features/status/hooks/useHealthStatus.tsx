/**
 * Custom hook for fetching and managing health status data
 *
 * Encapsulates the logic for polling health endpoints with auto-refresh
 * and provides formatted data for the status page components.
 */

import {
  useHealthCheckApiV1HealthGet,
  useHealthCheckDbApiV1HealthDbGet,
} from "../../../lib/api/generated/health/health";

export interface HealthStatus {
  app: {
    status: string;
    isLoading: boolean;
    error: string | null;
  };
  database: {
    status: string;
    connection: string;
    error: string | null;
    isLoading: boolean;
    httpError: boolean;
  };
  lastUpdated: Date;
}

export function useHealthStatus() {
  const {
    data: appHealthData,
    isLoading: appLoading,
    error: appError,
    dataUpdatedAt: appUpdatedAt,
  } = useHealthCheckApiV1HealthGet({
    query: {
      refetchInterval: 1500, // 1.5 seconds
      refetchIntervalInBackground: true,
      staleTime: 0,
      retry: 1,
    },
  });

  const {
    data: dbHealthData,
    isLoading: dbLoading,
    error: dbError,
    dataUpdatedAt: dbUpdatedAt,
  } = useHealthCheckDbApiV1HealthDbGet({
    query: {
      refetchInterval: 1500, // 1.5 seconds
      refetchIntervalInBackground: true,
      staleTime: 0,
      retry: 1,
    },
  });

  // Use the most recent data update timestamp from either query
  const lastUpdatedTimestamp = Math.max(appUpdatedAt, dbUpdatedAt);

  const healthStatus: HealthStatus = {
    app: {
      status: appHealthData?.status || "unknown",
      isLoading: appLoading,
      error: appError ? String(appError) : null,
    },
    database: {
      status: dbHealthData?.status || "unknown",
      connection: dbHealthData?.database || "unknown",
      error: dbHealthData?.error || null,
      isLoading: dbLoading,
      httpError: !!dbError,
    },
    lastUpdated: new Date(lastUpdatedTimestamp),
  };

  return healthStatus;
}
