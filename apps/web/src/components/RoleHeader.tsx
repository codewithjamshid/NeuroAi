import Link from "next/link";

import { UserMenu } from "@/features/auth/components/UserMenu";
import { t } from "@/lib/i18n";

export function RoleHeader({ role, home }: { role: string; home: string }) {
  return (
    <header className="flex items-center justify-between gap-3 border-b px-4 py-3">
      <div className="flex items-center gap-3">
        <Link href={home} className="font-semibold text-teal-800 dark:text-teal-300">
          {t("app.name")}
        </Link>
        <span className="text-muted-foreground">{role}</span>
      </div>
      <UserMenu />
    </header>
  );
}
