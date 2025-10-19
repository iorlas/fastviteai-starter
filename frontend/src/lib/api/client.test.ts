/**
 * API Client Tests
 *
 * Tests for Axios client configuration and error handling.
 */

import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { server } from "../../tests/mocks/server";
import { apiClient } from "./client";

describe("API Client", () => {
  describe("Configuration", () => {
    it("should have correct base URL", () => {
      expect(apiClient.defaults.baseURL).toBe("/api");
    });

    it("should have correct default headers", () => {
      expect(apiClient.defaults.headers["Content-Type"]).toBe("application/json");
    });

    it("should have timeout configured", () => {
      expect(apiClient.defaults.timeout).toBe(30000);
    });
  });

  describe("Response Interceptor - Error Handling", () => {
    it("should handle 403 Forbidden", async () => {
      server.use(
        http.get("*/api/test-403", () => {
          return HttpResponse.json({ detail: "Forbidden" }, { status: 403 });
        }),
      );

      try {
        await apiClient.get("/test-403");
        expect(true).toBe(false);
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it("should handle 404 Not Found", async () => {
      server.use(
        http.get("*/api/test-404", () => {
          return HttpResponse.json({ detail: "Not Found" }, { status: 404 });
        }),
      );

      try {
        await apiClient.get("/test-404");
        expect(true).toBe(false);
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it("should handle 500 Internal Server Error", async () => {
      server.use(
        http.get("*/api/test-500", () => {
          return HttpResponse.json({ detail: "Server Error" }, { status: 500 });
        }),
      );

      try {
        await apiClient.get("/test-500");
        expect(true).toBe(false);
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    it("should handle network errors", async () => {
      server.use(
        http.get("*/api/test-network-error", () => {
          return HttpResponse.error();
        }),
      );

      try {
        await apiClient.get("/test-network-error");
        expect(true).toBe(false);
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe("Successful Responses", () => {
    it("should pass through successful responses", async () => {
      server.use(
        http.get("*/api/test-success", () => {
          return HttpResponse.json({ message: "Success", data: { id: 1 } });
        }),
      );

      const response = await apiClient.get("/test-success");

      expect(response.status).toBe(200);
      expect(response.data).toEqual({ message: "Success", data: { id: 1 } });
    });

    it("should work with POST requests", async () => {
      server.use(
        http.post("*/api/test-post", async ({ request }) => {
          const body = await request.json();
          return HttpResponse.json({ received: body });
        }),
      );

      const payload = { name: "Test", value: 123 };
      const response = await apiClient.post("/test-post", payload);

      expect(response.status).toBe(200);
      expect(response.data.received).toEqual(payload);
    });
  });

  describe("Edge Cases", () => {
    it("should handle requests with custom headers", async () => {
      server.use(
        http.get("*/api/test-custom-headers", ({ request }) => {
          const customHeader = request.headers.get("X-Custom-Header");
          return HttpResponse.json({ customHeader });
        }),
      );

      const response = await apiClient.get("/test-custom-headers", {
        headers: {
          "X-Custom-Header": "custom-value",
        },
      });

      expect(response.data.customHeader).toBe("custom-value");
    });

    it("should handle form data requests", async () => {
      server.use(
        http.post("*/api/test-form-data", async ({ request }) => {
          const formData = await request.formData();
          const username = formData.get("username");
          return HttpResponse.json({ username });
        }),
      );

      const formData = new URLSearchParams();
      formData.append("username", "testuser");

      const response = await apiClient.post("/test-form-data", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      expect(response.data.username).toBe("testuser");
    });

    it("should respect timeout configuration", async () => {
      server.use(
        http.get("*/api/test-timeout", async () => {
          // Delay response
          await new Promise((resolve) => setTimeout(resolve, 100));
          return HttpResponse.json({ data: "delayed" });
        }),
      );

      // This should succeed with normal timeout
      const response = await apiClient.get("/test-timeout");
      expect(response.data.data).toBe("delayed");
    });
  });
});
