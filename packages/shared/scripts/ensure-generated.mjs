// Writes an empty stub src/generated/api.d.ts when no schema has been generated yet,
// so the package (and consumers importing "@neuroai/shared/api") type-check before `generate`.
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const out = resolve(root, "src/generated/api.d.ts");

const STUB = `// STUB — no OpenAPI schema generated yet. Run: make gen-types (API must be running)
export interface paths {}
export interface webhooks {}
export interface components {
  schemas: {};
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {}
`;

if (!existsSync(out)) {
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, STUB);
  console.log(`[shared] wrote stub ${out}`);
}
