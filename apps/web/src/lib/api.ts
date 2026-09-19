import type { ApiError as ApiErrorBody } from "@neuroai/shared";

import { env } from "@/lib/env";
import { t } from "@/lib/i18n";

export const DEFAULT_TIMEOUT_MS = 5000;

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

export type ApiFetchInit = RequestInit & { timeoutMs?: number };

export async function apiFetch<T>(path: string, init: ApiFetchInit = {}): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, headers, ...rest } = init;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const reqHeaders = new Headers(headers);
  if (!reqHeaders.has("Accept")) reqHeaders.set("Accept", "application/json");

  try {
    const res = await fetch(apiUrl(path), {
      ...rest,
      headers: reqHeaders,
      signal: controller.signal,
    });
    const body: unknown = res.status === 204 ? null : await res.json().catch(() => null);
    if (!res.ok) {
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
