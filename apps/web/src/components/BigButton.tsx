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

// Patient-UI primary action (TZ §8.1): ≥ 96px tall, icon/emoji + text, never color-only.
export function BigButton({ emoji, icon, label, hint, className, disabled, ...rest }: Props) {
  const cls = cn(
    "bg-primary text-primary-foreground focus-visible:ring-ring flex min-h-24 w-full items-center gap-4 rounded-2xl px-5 py-4 text-left text-[1.2em] font-semibold shadow-sm outline-none focus-visible:ring-4 active:translate-y-px disabled:opacity-50",
    className,
  );
  const inner = (
    <>
      {emoji && (
        <span aria-hidden className="text-[2em] leading-none">
          {emoji}
        </span>
      )}
      {icon}
      <span className="flex flex-col">
        <span>{label}</span>
        {hint && <span className="text-[0.75em] font-normal opacity-90">{hint}</span>}
      </span>
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
