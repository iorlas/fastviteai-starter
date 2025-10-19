import { describe, expect, it } from "vitest";
import { apiClient } from "../lib/api/client";

describe("MSW API Mocking", () => {
  it("intercepts health check API call", async () => {
    const response = await apiClient.get("/health");

    expect(response.status).toBe(200);
    expect(response.data).toEqual({
      status: "ok",
      timestamp: expect.any(String),
    });
  });

  it("handles error responses from MSW", async () => {
    await expect(apiClient.get("/error")).rejects.toThrow();
  });
});
