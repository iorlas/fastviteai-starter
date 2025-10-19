/**
 * Landing Page Route
 *
 * Story 2.5: Task 2.1 - Public landing page route
 * Public route accessible without authentication
 */

import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  component: IndexPage,
});

function IndexPage() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-12">
      <div className="w-full max-w-md space-y-8 text-center">
        <div>
          <h1 className="text-4xl font-bold text-gray-900">Welcome to Boilerplate App</h1>
          <p className="mt-4 text-lg text-gray-600">
            A modern, full-stack boilerplate application built with FastAPI and React
          </p>
        </div>

        <div className="flex flex-col space-y-4"></div>

        <div className="text-sm text-gray-500">
          <p>Demo Credentials:</p>
          <p className="font-mono">demo@example.com / demo1234</p>
        </div>
      </div>
    </div>
  );
}
