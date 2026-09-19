import type { Metadata } from "next";
import Link from "next/link";

import { LoginForm } from "@/features/auth/components/LoginForm";
import { t } from "@/lib/i18n";

export const metadata: Metadata = { title: t("auth.login") };

export default function LoginPage() {
  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-2xl flex-col gap-6 px-4 py-10">
      <header className="flex flex-col gap-1">
        <Link href="/" className="text-3xl font-semibold text-teal-800 dark:text-teal-300">
          {t("app.name")}
        </Link>
        <p className="text-muted-foreground">{t("app.tagline")}</p>
      </header>
      <LoginForm />
      <footer className="text-muted-foreground mt-auto text-sm">{t("app.disclaimer")}</footer>
    </main>
  );
}
