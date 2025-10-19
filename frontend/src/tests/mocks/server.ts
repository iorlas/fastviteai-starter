import { setupServer } from "msw/node";
import { handlers } from "./handlers";

/**
 * MSW Server for Node.js Test Environment
 *
 * This server is used in test files to intercept HTTP requests
 * and return mock responses defined in handlers.ts
 *
 * Usage in tests:
 * - Server is automatically started before all tests (see setup.ts)
 * - Server is automatically reset after each test
 * - Server is automatically closed after all tests
 */

export const server = setupServer(...handlers);
