import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

type Common = {
  emoji?: string;
  icon?: React.ReactNode;
  label: string;
  hint?: string;
  className?: string;
  disabled?: boolean;
};
type Props = Common & ({ href: string; onClick?: never } | { href?: never; onClick: () => void });

// Patient-UI primary action (TZ §8.1): ≥ 96px tall tile — emoji/icon left, label + hint, arrow right.
export function BigButton({ emoji, icon, label, hint, className, disabled, ...rest }: Props) {
  const cls = cn(
    "group bg-primary text-primary-foreground shadow-soft hover:bg-primary-hover focus-visible:ring-ring flex min-h-24 w-full items-center gap-4 rounded-2xl px-5 py-4 text-left text-[1.2em] font-semibold outline-none focus-visible:ring-4 focus-visible:ring-offset-2 active:translate-y-px disabled:opacity-50 aria-disabled:opacity-50",
    className,
  );
  const inner = (
    <>
      {(emoji || icon) && (
        <span
          aria-hidden
          className="flex size-16 shrink-0 items-center justify-center rounded-xl bg-white/15 text-[2em] leading-none"
        >
          {emoji ?? icon}
        </span>
      )}
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="leading-tight">{label}</span>
        {hint && <span className="text-[0.72em] leading-snug font-normal opacity-90">{hint}</span>}
      </span>
      <ArrowRight
        aria-hidden
        className="size-[1.4em] shrink-0 opacity-80 transition-transform group-hover:translate-x-0.5"
      />
    </>
  );
  if ("href" in rest && rest.href) {
    return (
      <Link href={rest.href} className={cls} aria-disabled={disabled}>
        {inner}
      </Link>
    );
  }
  return (
    <button type="button" onClick={rest.onClick} className={cls} disabled={disabled}>
      {inner}
    </button>
  );
}
