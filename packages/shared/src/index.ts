/**
 * @neuroai/shared — hand-written cross-app types.
 *
 * The OpenAPI-generated types live in `./generated/api.d.ts` (gitignored) and are exposed via
 * `@neuroai/shared/api` — run `make gen-types` (repo root) with the API up.
 * This entry never imports the generated file, so it compiles before the first generate.
 */

/** GET /api/v1/health */
export type HealthResponse = {
  status: "ok";
  version: string;
  env?: string;
};

/** Error envelope for every non-2xx API response (TZ §4.6). */
export type ApiError = {
  error: {
    code: string;
    message: string;
  };
};

/** AI worker GET /health (apps/ai_worker, TZ §4.7). */
export type WorkerModelStatus = "loaded" | "disabled" | "error";
export type WorkerHealthResponse = {
  models: Record<"stt" | "tts" | "voice_emotion" | "medllm", WorkerModelStatus>;
  gpu: { name: string; mem_used_mb: number } | null;
  version: string;
};
