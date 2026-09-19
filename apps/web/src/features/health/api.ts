import { apiFetch } from "@/lib/api";

export type HealthResponse = { status: string } & Record<string, unknown>;

// Shape is finalized in T-04; keep it open so the UI never breaks on new fields.
export type ProvidersHealthResponse = Record<string, unknown>;

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export function getProvidersHealth(): Promise<ProvidersHealthResponse> {
  return apiFetch<ProvidersHealthResponse>("/health/providers");
}
