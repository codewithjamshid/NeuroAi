import Link from "next/link";

import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export type LogoSize = "sm" | "md" | "lg" | "xl";

const PX: Record<LogoSize, number> = { sm: 24, md: 32, lg: 44, xl: 64 };

// Brand mark: rounded teal square with a white "N" (inline SVG, offline-safe, no font dependency).
// `tone="light"` draws a white square with a teal "N" for use on the teal hero gradient.
export function LogoMark({
  size = "md",
  tone = "brand",
  className,
  title,
}: {
  size?: LogoSize;
  tone?: "brand" | "light";
  className?: string;
  title?: string;
}) {
  const px = PX[size];
  const bg = tone === "light" ? "#ffffff" : "var(--primary, #0f766e)";
  const fg = tone === "light" ? "var(--primary, #0f766e)" : "#ffffff";
  return (
    <svg
      width={px}
      height={px}
      viewBox="0 0 32 32"
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
      className={cn("shrink-0", className)}
    >
      <rect width="32" height="32" rx="8" fill={bg} />
      <path
        d="M10 23V9l12 14V9"
        fill="none"
        stroke={fg}
        strokeWidth="3.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// Mark + wordmark, optionally linked. Used by RoleHeader, login and (if it wishes) the landing page.
export function LogoLockup({
  size = "md",
  href,
  tone = "brand",
  className,
}: {
  size?: LogoSize;
  href?: string;
  tone?: "brand" | "light";
  className?: string;
}) {
  const textCls =
    size === "sm"
      ? "text-base"
      : size === "md"
        ? "text-lg"
        : size === "lg"
          ? "text-2xl"
          : "text-3xl";
  const inner = (
    <>
      <LogoMark size={size} tone={tone} />
      <span
        className={cn(
          "font-semibold tracking-tight",
          textCls,
          tone === "light" ? "text-white" : "text-primary-deep",
        )}
      >
        {t("app.name")}
      </span>
    </>
  );
  const cls = cn("inline-flex items-center gap-2.5 rounded-lg outline-none", className);
  if (href) {
    return (
      <Link href={href} className={cls} aria-label={t("app.name")}>
        {inner}
      </Link>
    );
  }
  return <span className={cls}>{inner}</span>;
}
