import uz from "./landing.uz.json";

export type LandingKey = keyof typeof uz;

// Landing-only copy. Kept apart from src/i18n/uz.json so the marketing text never ships in the
// role bundles and the shared dictionary stays app-only (CLAUDE.md: no hardcoded UI text).
export function lt(key: LandingKey): string {
  return uz[key];
}
