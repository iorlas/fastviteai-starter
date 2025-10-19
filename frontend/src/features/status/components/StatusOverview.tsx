/**
 * Status overview component showing last update time and refresh indicator
 *
 * Displays a timestamp of the last health check update and provides
 * visual feedback that the page is auto-refreshing.
 */

import { useEffect, useState } from "react";

interface StatusOverviewProps {
  lastUpdated: Date;
}

export function StatusOverview({ lastUpdated }: StatusOverviewProps) {
  const [timeAgo, setTimeAgo] = useState("just now");

  useEffect(() => {
    const updateTimeAgo = () => {
      const seconds = Math.floor((Date.now() - lastUpdated.getTime()) / 1000);

      if (seconds < 3) {
        setTimeAgo("just now");
      } else if (seconds < 60) {
        setTimeAgo(`${seconds}s ago`);
      } else {
        const minutes = Math.floor(seconds / 60);
        setTimeAgo(`${minutes}m ago`);
      }
    };

    updateTimeAgo();
    const interval = setInterval(updateTimeAgo, 1000);

    return () => clearInterval(interval);
  }, [lastUpdated]);

  return (
    <div className="mb-8 flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-600">
          Last updated: <span className="font-medium text-gray-900">{timeAgo}</span>
        </p>
        <p className="text-xs text-gray-500 mt-1">Auto-refreshing every 1.5 seconds</p>
      </div>
      <div className="flex items-center space-x-2">
        <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
        <span className="text-xs text-gray-600">Live</span>
      </div>
    </div>
  );
}
