import uz from "@/i18n/uz.json";

export type I18nKey = keyof typeof uz;

type Vars = Record<string, string | number | null | undefined>;

// Single locale for now (TZ §3: uz-Latn primary; ru is P2 → ru.json later).
// `{name}` placeholders are replaced from `vars`.
export function t(key: I18nKey, vars?: Vars): string {
  const s: string = uz[key];
  if (!vars) return s;
  return s.replace(/\{(\w+)\}/g, (m, k: string) => {
    const v = vars[k];
    return v === undefined || v === null ? m : String(v);
  });
}

// Runtime-checked lookup for keys built dynamically (e.g. `mood.${n}`); falls back to the raw key.
export function tk(key: string, vars?: Vars): string {
  if (key in uz) return t(key as I18nKey, vars);
  return key;
}
