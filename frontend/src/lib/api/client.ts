/**
 * API Client Configuration
 *
 * Axios instance with basic error handling for the frontend.
 * - Configures base URL from environment variable (VITE_API_URL)
 * - Response interceptor: Logs common HTTP errors
 */

import axios, { type AxiosError, type AxiosResponse } from "axios";

// API base URL from environment variable, defaults to /api (proxied in vite.config.ts)
const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

/**
 * Axios instance with default configuration
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30 second timeout
});

/**
 * Custom instance for Orval-generated API clients
 * This wrapper adapts apiClient to the signature expected by Orval
 */
export const customInstance = async <T>(
  config: Parameters<typeof apiClient.request>[0],
): Promise<T> => {
  const response = await apiClient.request<T>(config);
  return response.data;
};

/**
 * Response interceptor: Handle common error responses
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Pass through successful responses
    return response;
  },
  (error: AxiosError) => {
    // Handle common errors
    if (error.response?.status === 500) {
      console.error("Server error:", error.response.data);
    }

    if (error.response?.status === 404) {
      console.warn("Resource not found:", error.config?.url);
    }

    if (error.response?.status === 403) {
      console.warn("Forbidden - insufficient permissions:", error.response.status);
    }

    // Network errors (no response received)
    if (!error.response) {
      console.error("Network error - no response received:", error.message);
    }

    return Promise.reject(error);
  },
);
