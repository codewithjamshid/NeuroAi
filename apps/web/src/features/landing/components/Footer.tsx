import Link from "next/link";

import { HealthBadge } from "@/features/health/components/HealthBadge";
import { cn } from "@/lib/utils";

import { lt } from "../i18n";
import { container } from "../styles";
import { LandingLogo } from "./LandingLogo";

const linkCls =
  "rounded-lg px-1 py-0.5 text-sm font-medium text-[#1f2933] underline-offset-4 outline-none hover:underline focus-visible:ring-2 focus-visible:ring-[#0f766e]";

// Event line, the positioning disclaimer, links and the live API badge (the only network call).
export function Footer() {
  return (
    <footer aria-label={lt("footer.aria")} className="border-t border-black/5 bg-[#faf9f6]">
      <div className={cn(container, "grid gap-8 py-12 md:grid-cols-[1.2fr_1.4fr_auto]")}>
        <div>
          <p className="flex items-center gap-2.5 text-lg font-semibold tracking-tight text-[#1f2933]">
            <LandingLogo size="md" />
            {lt("nav.brand")}
          </p>
          <p className="mt-2 text-sm text-[#6b7280]">{lt("footer.event")}</p>
        </div>

        <p className="max-w-prose text-sm leading-relaxed text-[#6b7280]">
          {lt("footer.disclaimer")}
        </p>

        <div className="flex flex-col items-start gap-3">
          <nav aria-label={lt("footer.links")} className="flex items-center gap-4">
            <Link href="/status" className={linkCls}>
              {lt("footer.status")}
            </Link>
            <Link href="/login" className={linkCls}>
              {lt("footer.login")}
            </Link>
          </nav>
          <HealthBadge />
        </div>
      </div>
    </footer>
  );
}
