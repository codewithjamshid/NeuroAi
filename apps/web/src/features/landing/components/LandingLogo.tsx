import { LogoMark, type LogoSize } from "@/components/LogoMark";

// Landing adapter over the shared brand mark so the nav, footer and product mock draw the same
// "N" as the role headers and login. Kept as the single import point for src/components here.
export function LandingLogo({
  size = "md",
  tone = "brand",
  className,
}: {
  size?: LogoSize;
  tone?: "brand" | "light";
  className?: string;
}) {
  return <LogoMark size={size} tone={tone} className={className} />;
}
