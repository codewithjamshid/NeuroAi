import { HeartHandshake, Stethoscope, User } from "lucide-react";

import { LogoLockup } from "@/components/LogoMark";
import { UserMenu } from "@/features/auth/components/UserMenu";
import { cn } from "@/lib/utils";

export type RoleTone = "patient" | "caregiver" | "clinician";

// Subtle per-role tint (icon + text, never colour alone).
const TONE: Record<RoleTone, { Icon: typeof User; cls: string }> = {
  patient: { Icon: User, cls: "bg-teal-50 text-teal-900 ring-teal-200" },
  caregiver: { Icon: HeartHandshake, cls: "bg-amber-50 text-amber-900 ring-amber-200" },
  clinician: { Icon: Stethoscope, cls: "bg-indigo-50 text-indigo-900 ring-indigo-200" },
};

function toneFor(home: string): RoleTone {
  if (home.startsWith("/c")) return "caregiver";
  if (home.startsWith("/d")) return "clinician";
  return "patient";
}

export function RoleHeader({ role, home, tone }: { role: string; home: string; tone?: RoleTone }) {
  const { Icon, cls } = TONE[tone ?? toneFor(home)];
  return (
    <header className="bg-background/85 supports-[backdrop-filter]:bg-background/75 sticky top-0 z-40 border-b backdrop-blur">
      <div className="flex items-center justify-between gap-3 px-4 py-2.5 md:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <LogoLockup href={home} size="md" />
          <span
            className={cn(
              // hidden on phones: with the 22px patient font floor the badge collides with the user menu
              "hidden shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ring-1 ring-inset sm:inline-flex",
              cls,
            )}
          >
            <Icon aria-hidden className="size-[1em]" />
            {role}
          </span>
        </div>
        <UserMenu />
      </div>
    </header>
  );
}
