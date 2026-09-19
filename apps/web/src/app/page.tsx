import { Activity, HeartHandshake, Stethoscope, User } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { HealthBadge } from "@/features/health/components/HealthBadge";
import { type I18nKey, t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const roles: { href: string; title: I18nKey; desc: I18nKey; Icon: typeof User }[] = [
  { href: "/p", title: "role.patient", desc: "role.patient.desc", Icon: User },
  { href: "/c", title: "role.caregiver", desc: "role.caregiver.desc", Icon: HeartHandshake },
  { href: "/d", title: "role.clinician", desc: "role.clinician.desc", Icon: Stethoscope },
];

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-4xl flex-col gap-10 px-4 py-10">
      <header className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-4xl font-semibold tracking-tight text-teal-800 dark:text-teal-300">
            {t("app.name")}
          </h1>
          <div className="flex items-center gap-2">
            <HealthBadge />
            <Link href="/login" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
              {t("auth.login")}
            </Link>
            <Link
              href="/status"
              className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "gap-1.5")}
            >
              <Activity aria-hidden />
              {t("nav.status")}
            </Link>
          </div>
        </div>
        <p className="text-muted-foreground text-xl">{t("app.tagline")}</p>
      </header>

      <section className="grid gap-4 sm:grid-cols-3">
        {roles.map(({ href, title, desc, Icon }) => (
          <Link
            key={href}
            href={href}
            className="group rounded-xl outline-none focus-visible:ring-3"
          >
            <Card className="group-hover:bg-muted/60 h-full transition-colors">
              <CardHeader>
                <Icon aria-hidden className="mb-2 size-10 text-teal-700 dark:text-teal-300" />
                <CardTitle className="text-2xl">{t(title)}</CardTitle>
                <CardDescription className="text-base">{t(desc)}</CardDescription>
              </CardHeader>
              <CardContent>
                <span className={cn(buttonVariants({ size: "lg" }), "min-h-12 w-full text-base")}>
                  {t("role.open")}
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </section>

      <footer className="text-muted-foreground mt-auto text-sm">{t("app.disclaimer")}</footer>
    </main>
  );
}
