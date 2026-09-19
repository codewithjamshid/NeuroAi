"use client";

import { cn } from "@/lib/utils";

// Board cell (TZ §8.2 /p/board): ≥ 72px tile, 40px emoji + label, keyboard focusable.
export function Pictogram({
  emoji,
  label,
  onClick,
  selected,
  disabled,
  className,
}: {
  emoji?: string | null;
  label: string;
  onClick: () => void;
  selected?: boolean;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={selected}
      className={cn(
        "bg-card shadow-soft hover:border-primary hover:bg-accent focus-visible:ring-ring flex min-h-[92px] min-w-16 flex-col items-center justify-center gap-1.5 rounded-2xl border-2 px-2 py-3 text-center font-medium outline-none focus-visible:ring-4 active:translate-y-px disabled:opacity-50",
        selected && "border-primary bg-accent",
        className,
      )}
    >
      <span aria-hidden className="text-[40px] leading-none">
        {emoji ?? "▫️"}
      </span>
      <span className="text-[0.8em] leading-tight">{label}</span>
    </button>
  );
}
