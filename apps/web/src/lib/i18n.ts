import uz from "@/i18n/uz.json";

export type I18nKey = keyof typeof uz;

// Single locale for now (TZ §3: uz-Latn primary; ru is P2 → ru.json later).
export function t(key: I18nKey): string {
  return uz[key];
}
