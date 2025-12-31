import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { runsApi, RunResponse } from "@/api/runs";

interface UseRunPollingOptions {
  spaceId: string;
  runId: string | null;
  enabled?: boolean;
  interval?: number;
}

export function useRunPolling({
  spaceId,
  runId,
  enabled = true,
  interval = 2000,
}: UseRunPollingOptions) {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const query = useQuery<RunResponse>({
    queryKey: ["runs", spaceId, runId],
    queryFn: () => runsApi.get(spaceId, runId!),
    enabled: enabled && !!runId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === "running") {
        return interval;
      }
      return false;
    },
  });

  useEffect(() => {
    if (query.data?.status === "running") {
      intervalRef.current = setInterval(() => {
        query.refetch();
      }, interval);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [query.data?.status, interval, query]);

  return query;
}

