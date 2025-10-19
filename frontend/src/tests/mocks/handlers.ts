import { HttpResponse, http } from "msw";

/**
 * MSW Request Handlers
 *
 * Define API mocks for testing. These handlers intercept HTTP requests
 * and return mock responses.
 *
 * For Node.js environment (vitest), we need to use absolute URLs or
 * match patterns that work with the test environment. Since apiClient
 * uses a baseURL of "/api", we need to ensure handlers match the
 * actual request URLs that will be made.
 *
 * Story 2.3: Auth endpoint handlers for frontend testing
 */

// MSW in Node requires absolute URLs or wildcard patterns
// We use wildcard (*) to match any hostname + the path
export const handlers = [
  // Example: Health check endpoint
  http.get("*/api/health", () => {
    return HttpResponse.json({
      status: "ok",
      timestamp: new Date().toISOString(),
    });
  }),

  // Example: Error response
  http.get("*/api/error", () => {
    return HttpResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }),
];
