/**
 * Test component to validate Orval-generated TanStack Query hooks
 *
 * This component demonstrates:
 * - Using generated useHealthCheckApiV1HealthGet hook
 * - TypeScript type safety from generated types
 * - TanStack Query integration
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useHealthCheckApiV1HealthGet } from "../lib/api/generated/health/health";

const queryClient = new QueryClient();

function HealthCheckComponent() {
  const { data, isLoading, error } = useHealthCheckApiV1HealthGet();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {String(error)}</div>;

  return (
    <div>
      <h1>Health Check</h1>
      <p>Status: {data?.status}</p>
    </div>
  );
}

export function HealthCheckTest() {
  return (
    <QueryClientProvider client={queryClient}>
      <HealthCheckComponent />
    </QueryClientProvider>
  );
}
