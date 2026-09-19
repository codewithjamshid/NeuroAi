import type { Metadata } from "next";
import Link from "next/link";

import { LogoMark } from "@/components/LogoMark";
import { LoginForm } from "@/features/auth/components/LoginForm";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("auth.login") };

export default function LoginPage() {
  return (
    <main className="flex min-h-dvh flex-col">
      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center gap-8 px-4 py-10 md:px-6">
        <header className="flex flex-col items-center gap-3 text-center">
          <Link
            href="/"
            className="focus-visible:ring-ring rounded-2xl outline-none focus-visible:ring-4"
            aria-label={t("app.name")}
          >
            <LogoMark size="xl" className="shadow-soft rounded-2xl" />
          </Link>
          <div className="flex flex-col gap-1">
            <h1 className="text-3xl">{t("app.name")}</h1>
            <p className="text-muted-foreground">{t("app.tagline")}</p>
          </div>
        </header>
        <LoginForm />
        <footer className="text-muted-foreground mx-auto max-w-prose text-center text-sm">
          {t("app.disclaimer")}
        </footer>
      </div>
    </main>
  );
}
