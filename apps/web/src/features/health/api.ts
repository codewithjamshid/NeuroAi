import { apiFetch } from "@/lib/api";

export type HealthResponse = { status: string } & Record<string, unknown>;

// apps/api app/modules/health/schemas.py (ProvidersHealth); every field optional so the UI
// keeps working if the providers builder ships a different shape.
export type ProviderStatus = {
  name: string;
  status?: string | null;
  configured?: boolean | null;
  circuit?: string | null;
  latency_ms?: number | null;
};

export type ChainName = "llm" | "stt" | "tts" | "voice_emotion";

export type ProvidersHealthResponse = Partial<Record<ChainName, ProviderStatus[]>> & {
  worker?: { mode?: string; url?: string; status?: string; latency_ms?: number | null } | null;
} & Record<string, unknown>;

export function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health", { auth: false });
}

export function getProvidersHealth(): Promise<ProvidersHealthResponse> {
  return apiFetch<ProvidersHealthResponse>("/health/providers", { auth: false });
}
