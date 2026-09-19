import Link from "next/link";

import { t } from "@/lib/i18n";

export function RoleHeader({ role }: { role: string }) {
  return (
    <header className="flex items-center justify-between gap-3 border-b px-4 py-3">
      <Link href="/" className="font-semibold text-teal-800 dark:text-teal-300">
        {t("app.name")}
      </Link>
      <span className="text-muted-foreground">{role}</span>
    </header>
  );
}
