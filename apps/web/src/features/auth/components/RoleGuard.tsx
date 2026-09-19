"use client";

import { CircleDashed, LogIn, ShieldAlert } from "lucide-react";
import Link from "next/link";

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
    return (
      <div className="text-muted-foreground flex items-center gap-2 p-6">
        <CircleDashed aria-hidden className="size-5 animate-spin" />
        {t("auth.checking")}
      </div>
    );
  }

  if (!isAuthed || !user) {
    return (
      <Card className="mx-auto mt-6 w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[1.2em]">
            <LogIn aria-hidden className="size-[1.2em]" />
            {t("auth.required.title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p>{t("auth.required.text")}</p>
          <Link href="/login" className={cn(buttonVariants({ size: "lg" }), "min-h-16 text-[1em]")}>
            {t("auth.login")}
          </Link>
        </CardContent>
      </Card>
    );
  }

  if (!roles.includes(user.role)) {
    return (
      <Card className="mx-auto mt-6 w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[1.2em]">
            <ShieldAlert aria-hidden className="size-[1.2em]" />
            {t("auth.forbidden.title")}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p>{t("auth.forbidden.text")}</p>
          <Link
            href={homeForRole(user.role)}
            className={cn(buttonVariants({ size: "lg" }), "min-h-16 text-[1em]")}
          >
            {t("auth.go_home")}
          </Link>
        </CardContent>
      </Card>
    );
  }

  return <>{children}</>;
}
