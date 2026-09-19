import type { ApiError as ApiErrorBody } from "@neuroai/shared";

import { readAuthToken, resetAuth } from "@/features/auth/store";
import { env } from "@/lib/env";
import { t } from "@/lib/i18n";

export const DEFAULT_TIMEOUT_MS = 5000;
// STT + LLM + TTS round trip (TZ §3 target ≤ 5 s, worst case with fallbacks much longer).
export const AI_TIMEOUT_MS = 45_000;

// TZ §4.6: errors come back as {"error": {"code", "message"}} — type shared with the API package
export type { ApiErrorBody };

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, message: string, status = 0) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

export function isApiErrorBody(value: unknown): value is ApiErrorBody {
  if (typeof value !== "object" || value === null || !("error" in value)) return false;
  const err = (value as { error: unknown }).error;
  return (
    typeof err === "object" &&
    err !== null &&
    typeof (err as { code?: unknown }).code === "string" &&
    typeof (err as { message?: unknown }).message === "string"
  );
}

export function apiUrl(path: string): string {
  const base = env.apiUrl.replace(/\/+$/, "");
  return `${base}/${path.replace(/^\/+/, "")}`;
}

// `/media/tts/x.wav` is mounted at the API origin root (and under /api/v1) — resolve against the origin.
export function mediaUrl(path: string): string {
  if (/^https?:\/\//.test(path)) return path;
  try {
    return `${new URL(env.apiUrl).origin}/${path.replace(/^\/+/, "")}`;
  } catch {
    return path;
  }
}

export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  if (e instanceof Error && e.message) return e.message;
  return t("error.request_failed");
}

export type ApiFetchInit = RequestInit & { timeoutMs?: number; auth?: boolean };

function handleUnauthorized() {
  resetAuth();
  if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
    window.location.assign("/login");
  }
}

export async function apiFetch<T>(path: string, init: ApiFetchInit = {}): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, headers, auth = true, ...rest } = init;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const reqHeaders = new Headers(headers);
  if (!reqHeaders.has("Accept")) reqHeaders.set("Accept", "application/json");
  const token = auth ? readAuthToken() : null;
  if (token && !reqHeaders.has("Authorization")) {
    reqHeaders.set("Authorization", `Bearer ${token}`);
  }

  try {
    const res = await fetch(apiUrl(path), {
      ...rest,
      headers: reqHeaders,
      signal: controller.signal,
    });
    const body: unknown = res.status === 204 ? null : await res.json().catch(() => null);
    if (!res.ok) {
      // Only an expired/invalid session bounces to /login — a failed login attempt itself must not.
      if (res.status === 401 && token) handleUnauthorized();
      if (isApiErrorBody(body)) throw new ApiError(body.error.code, body.error.message, res.status);
      throw new ApiError(`http_${res.status}`, t("error.request_failed"), res.status);
    }
    return body as T;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new ApiError("timeout", t("error.timeout"));
    }
    throw new ApiError("network_error", t("error.network"));
  } finally {
    clearTimeout(timer);
  }
}

export function apiJson<T>(
  path: string,
  method: "POST" | "PATCH" | "PUT" | "DELETE",
  body?: unknown,
  init: ApiFetchInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (body !== undefined) headers.set("Content-Type", "application/json");
  return apiFetch<T>(path, {
    ...init,
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

// Multipart (audio blobs): the browser sets the boundary header itself.
export function apiFetchForm<T>(path: string, form: FormData, init: ApiFetchInit = {}): Promise<T> {
  return apiFetch<T>(path, { timeoutMs: AI_TIMEOUT_MS, ...init, method: "POST", body: form });
}
