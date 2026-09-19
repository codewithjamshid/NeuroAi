"use client";

import { LogOut } from "lucide-react";
import Link from "next/link";

import { Button, buttonVariants } from "@/components/ui/button";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

import { useAuth, useLogout } from "../hooks";

export function UserMenu() {
  const { user, hydrated } = useAuth();
  const logout = useLogout();

  if (!hydrated) return null;
  if (!user) {
    return (
      <Link href="/login" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
        {t("auth.login")}
      </Link>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <span className="max-w-[40vw] truncate font-medium">{user.full_name}</span>
      <Button variant="outline" size="sm" onClick={logout} className="gap-1.5">
        <LogOut aria-hidden />
        {t("auth.logout")}
      </Button>
    </div>
  );
}
