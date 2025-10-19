/**
 * Health Status Route
 *
 * Public route accessible at /health
 * Displays real-time system status for backend services
 */

import { createFileRoute } from "@tanstack/react-router";
import { StatusPage } from "../features/status/StatusPage";

export const Route = createFileRoute("/health")({
  component: StatusPage,
});
