"use client";

import { cn } from "@/lib/utils";

// Board cell (TZ §8.2 /p/board): ≥ 64px, emoji + label, keyboard focusable.
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
        "bg-card focus-visible:ring-ring flex min-h-24 min-w-16 flex-col items-center justify-center gap-1 rounded-xl border-2 px-2 py-3 text-center font-medium outline-none hover:bg-teal-50 focus-visible:ring-4 disabled:opacity-50 dark:hover:bg-teal-950",
        selected && "border-teal-700 bg-teal-50 dark:bg-teal-950",
        className,
      )}
    >
      <span aria-hidden className="text-[1.8em] leading-none">
        {emoji ?? "▫️"}
      </span>
      <span className="text-[0.9em] leading-tight">{label}</span>
    </button>
  );
}
