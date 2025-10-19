/**
 * App Component - TanStack Router Application
 *
 * Story 2.5: Task 1.4 - Configure router in main application
 * Migrated from React Router to TanStack Router for file-based routing
 */

import { createRouter, RouterProvider } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";

// Create router instance with route tree
const router = createRouter({ routeTree });

// Register router type for TypeScript
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

function App() {
  return <RouterProvider router={router} />;
}

export default App;
