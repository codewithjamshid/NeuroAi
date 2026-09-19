"use client";

import { LogIn, LogOut } from "lucide-react";
import Link from "next/link";

import { Button, buttonVariants } from "@/components/ui/button";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useAuth, useLogout } from "../hooks";

function initialsOf(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase() ?? "")
    .join("");
}

export function UserMenu() {
  const { user, hydrated } = useAuth();
  const logout = useLogout();

  if (!hydrated) return null;
  if (!user) {
    return (
      <Link
        href="/login"
        className={cn(buttonVariants({ variant: "outline", size: "sm" }), "gap-1.5")}
      >
        <LogIn aria-hidden />
        {t("auth.login")}
      </Link>
    );
  }
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <span className="flex min-w-0 items-center gap-2">
        <span
          aria-hidden
          className="bg-primary/10 text-primary-deep inline-flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold"
        >
          {initialsOf(user.full_name)}
        </span>
        <span className="hidden max-w-[28vw] truncate font-medium sm:inline">{user.full_name}</span>
      </span>
      <Button variant="outline" size="sm" onClick={logout} className="gap-1.5">
        <LogOut aria-hidden />
        {t("auth.logout")}
      </Button>
    </div>
  );
}
