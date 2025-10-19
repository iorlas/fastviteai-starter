/**
 * Orval configuration for generating TypeScript API client from OpenAPI spec
 *
 * This config:
 * - Reads OpenAPI 3.1 spec from backend at /api/v1/openapi.json
 * - Generates TypeScript types and TanStack Query hooks
 * - Outputs to src/lib/api/generated/
 * - Uses Axios as HTTP client
 * - Supports environment variable for OpenAPI spec URL (VITE_API_URL)
 */

import { defineConfig } from "orval";

export default defineConfig({
  api: {
    input: process.env.VITE_API_URL
      ? `${process.env.VITE_API_URL}/openapi.json`
      : "http://localhost:8000/openapi.json",
    output: {
      target: "src/lib/api/generated/api.ts",
      client: "react-query",
      mode: "tags-split",
      override: {
        mutator: {
          path: "src/lib/api/client.ts",
          name: "customInstance",
        },
      },
    },
  },
});
