"use client";

import { MicOff } from "lucide-react";

import type { AudioErrorCode } from "@/features/audio/types";
import { t } from "@/lib/i18n";

// getUserMedia failures in plain Uzbek (TZ §3: error states in simple language).
export function MicErrorNotice({ error }: { error: AudioErrorCode | null }) {
  if (!error) return null;
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-2xl border-2 border-amber-600 bg-amber-50 px-4 py-3 text-amber-950"
    >
      <MicOff aria-hidden className="mt-1 size-[1.4em] shrink-0" />
      <span>{t(`audio.error.${error}`)}</span>
    </div>
  );
}
