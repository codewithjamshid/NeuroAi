/**
 * OpenAPI types of apps/api (`paths`, `components`, `operations`).
 * `scripts/ensure-generated.mjs` writes an empty stub when nothing has been generated yet;
 * `make gen-types` (repo root, API running) replaces it with the real schema.
 */
export type * from "./generated/api";
