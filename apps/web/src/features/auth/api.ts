import { apiFetch, apiJson } from "@/lib/api";

import type { LoginRequest, LoginResponse, MeResponse, RefreshResponse } from "./types";

export function login(body: LoginRequest): Promise<LoginResponse> {
  return apiJson<LoginResponse>("/auth/login", "POST", body, { auth: false });
}

export function refresh(refreshToken: string): Promise<RefreshResponse> {
  return apiJson<RefreshResponse>(
    "/auth/refresh",
    "POST",
    { refresh: refreshToken },
    { auth: false },
  );
}

export function getMe(): Promise<MeResponse> {
  return apiFetch<MeResponse>("/me");
}
