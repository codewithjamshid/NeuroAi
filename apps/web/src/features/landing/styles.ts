// Landing design tokens as class strings (design direction: teal #0f766e / hover #115e59,
// page #faf9f6, ink #1f2933, muted #6b7280, amber #d97706 for CTAs only, radius 16px, soft shadow).
// Kept local so the landing does not depend on globals.css edits made by the app design pass.

export const container = "mx-auto w-full max-w-6xl px-4 sm:px-6";

export const shadowSoft = "shadow-[0_1px_2px_rgba(0,0,0,0.05),0_8px_24px_rgba(15,118,110,0.08)]";

export const card = `rounded-2xl bg-white p-6 ring-1 ring-black/5 ${shadowSoft}`;

export const iconTile =
  "flex size-12 shrink-0 items-center justify-center rounded-xl bg-teal-50 text-[#0f766e]";

const btnBase =
  "inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl px-6 text-base font-semibold transition-colors outline-none focus-visible:ring-4 active:translate-y-px";

export const btnAmber = `${btnBase} bg-[#d97706] text-white shadow-md hover:bg-[#b45309] focus-visible:ring-amber-300/60`;

export const btnTeal = `${btnBase} bg-[#0f766e] text-white hover:bg-[#115e59] focus-visible:ring-teal-300/60`;

export const btnOutlineTeal = `${btnBase} border border-[#0f766e]/40 bg-white text-[#0f766e] hover:bg-teal-50 focus-visible:ring-teal-300/60`;

export const btnGhostWhite = `${btnBase} border border-white/40 bg-white/10 text-white hover:bg-white/20 focus-visible:ring-white/40`;

export const eyebrow = "text-sm font-semibold tracking-wide text-[#0f766e] uppercase";

export const h2 = "text-3xl font-semibold tracking-tight text-[#1f2933] sm:text-4xl";

export const lead = "text-lg text-[#6b7280]";
