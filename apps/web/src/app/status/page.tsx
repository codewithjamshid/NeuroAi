import type { Metadata } from "next";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { StatusPanel } from "@/features/health/components/StatusPanel";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("status.title") };

// TZ §8.2: public page (no auth) — demo shows provider status live.
export default function StatusPage() {
  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{t("status.title")}</h1>
          <p className="text-muted-foreground">{t("status.subtitle")}</p>
        </div>
        <Link href="/" className={buttonVariants({ variant: "outline" })}>
          {t("nav.home")}
        </Link>
      </header>
      <StatusPanel />
    </main>
  );
}
