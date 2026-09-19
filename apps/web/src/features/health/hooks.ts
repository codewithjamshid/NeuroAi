import { useQuery } from "@tanstack/react-query";

import { getHealth, getProvidersHealth } from "./api";

export const healthKeys = {
  health: ["health"] as const,
  providers: ["health", "providers"] as const,
};

export function useHealth(refetchInterval = 15_000) {
  return useQuery({
    queryKey: healthKeys.health,
    queryFn: getHealth,
    refetchInterval,
    retry: false,
  });
}

export function useProvidersHealth(refetchInterval = 15_000) {
  return useQuery({
    queryKey: healthKeys.providers,
    queryFn: getProvidersHealth,
    refetchInterval,
    retry: false,
  });
}
