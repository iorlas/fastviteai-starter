/**
 * Root Route - Base layout for all routes
 *
 * Story 2.5: Task 1.3 - File-based routing structure
 * Provides QueryClientProvider, Navigation, and Outlet for all child routes
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRootRoute, Outlet } from "@tanstack/react-router";
import { Navigation } from "../components/Navigation";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      retry: 1,
    },
  },
});

export const Route = createRootRoute({
  component: RootComponent,
});

function RootComponent() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <Outlet />
      </div>
    </QueryClientProvider>
  );
}
