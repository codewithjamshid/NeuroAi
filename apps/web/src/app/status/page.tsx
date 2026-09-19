import { Activity, LogIn } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { LogoLockup } from "@/components/LogoMark";
import { buttonVariants } from "@/components/ui/button";
import { StatusPanel } from "@/features/health/components/StatusPanel";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export const metadata: Metadata = { title: t("status.title") };

// TZ §8.2: public page (no auth) — demo shows provider status live.
export default function StatusPage() {
  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-6 md:px-6 md:py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <LogoLockup href="/" size="md" />
        <nav className="flex items-center gap-2">
          <Link href="/" className={cn(buttonVariants({ variant: "outline" }))}>
            {t("nav.home")}
          </Link>
          <Link href="/login" className={cn(buttonVariants({ variant: "ghost" }), "gap-1.5")}>
            <LogIn aria-hidden />
            {t("auth.login")}
          </Link>
        </nav>
      </div>
      <header className="flex flex-col gap-1">
        <h1 className="flex items-center gap-2.5 text-3xl">
          <span className="bg-accent text-accent-foreground inline-flex size-10 items-center justify-center rounded-xl">
            <Activity aria-hidden className="size-5" />
          </span>
          {t("status.title")}
        </h1>
        <p className="text-muted-foreground flex items-center gap-2">
          <span aria-hidden className="bg-primary inline-block size-2 rounded-full" />
          {t("status.subtitle")}
        </p>
      </header>
      <StatusPanel />
    </main>
  );
}
