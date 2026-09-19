"use client";

import { LogIn, ShieldAlert } from "lucide-react";
import Link from "next/link";

import { LoadingCard } from "@/components/ErrorCard";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useAuth } from "../hooks";
import { homeForRole } from "../store";
import type { Role } from "../types";

// Client-side guard for /p, /c, /d layouts: never crashes, shows a "Kirish kerak" card instead.
export function RoleGuard({ roles, children }: { roles: Role[]; children: React.ReactNode }) {
  const { user, hydrated, isAuthed } = useAuth();

  if (!hydrated) {
    return <LoadingCard text={t("auth.checking")} className="mt-2 bg-transparent" />;
  }

  if (!isAuthed || !user) {
    return (
      <Card className="shadow-soft mx-auto mt-6 w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[1.2em]">
            <span className="bg-accent text-accent-foreground inline-flex size-[2em] shrink-0 items-center justify-center rounded-full">
              <LogIn aria-hidden className="size-[1.1em]" />
            </span>
            {t("auth.required.title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p>{t("auth.required.text")}</p>
          <Link
            href="/login"
            className={cn(
              buttonVariants({ size: "lg" }),
              "hover:bg-primary-hover min-h-16 text-[1em]",
            )}
          >
            {t("auth.login")}
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (!roles.includes(user.role)) {
    return (
      <Card className="shadow-soft mx-auto mt-6 w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[1.2em]">
            <span className="inline-flex size-[2em] shrink-0 items-center justify-center rounded-full bg-amber-50 text-amber-800">
              <ShieldAlert aria-hidden className="size-[1.1em]" />
            </span>
            {t("auth.forbidden.title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p>{t("auth.forbidden.text")}</p>
          <Link
            href={homeForRole(user.role)}
            className={cn(
              buttonVariants({ size: "lg" }),
              "hover:bg-primary-hover min-h-16 text-[1em]",
            )}
          >
            {t("auth.go_home")}
          </Link>
        </CardContent>
      </Card>
    );
  }

  return <>{children}</>;
}
