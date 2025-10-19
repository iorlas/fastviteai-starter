/**
 * Main Entry Point
 *
 * Story 2.5: Task 1.4 - TanStack Router integration
 * QueryClientProvider now handled in __root.tsx route
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
