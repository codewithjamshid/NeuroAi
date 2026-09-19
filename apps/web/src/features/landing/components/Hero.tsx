import { ArrowRight, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

import { lt } from "../i18n";
import { btnAmber, btnGhostWhite, container } from "../styles";
import { ProductMock } from "./ProductMock";

// Teal gradient hero (#0f766e → #134e4a), white text, product mock on the right.
export function Hero() {
  return (
    <section
      aria-labelledby="hero-title"
      className="relative overflow-hidden bg-gradient-to-br from-[#0f766e] to-[#134e4a] text-white"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -top-32 -right-32 size-[28rem] rounded-full bg-white/10 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-40 -left-24 size-[24rem] rounded-full bg-teal-300/10 blur-3xl"
      />

      <div
        className={cn(
          container,
          "relative grid items-center gap-12 py-16 sm:py-24 lg:grid-cols-[1.1fr_0.9fr] lg:gap-16",
        )}
      >
        <div className="motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-4 max-w-2xl motion-safe:duration-700">
          <p className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm font-medium text-teal-50 ring-1 ring-white/20">
            {lt("hero.eyebrow")}
          </p>
          <h1
            id="hero-title"
            className="mt-5 text-4xl leading-[1.08] font-semibold tracking-tight text-balance sm:text-5xl lg:text-6xl"
          >
            {lt("hero.title")}
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-relaxed text-teal-50/90 sm:text-xl">
            {lt("hero.subtitle")}
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/login" className={btnAmber}>
              {lt("hero.cta_primary")}
              <ArrowRight aria-hidden className="size-5" />
            </Link>
            <Link href="#how" className={btnGhostWhite}>
              {lt("hero.cta_secondary")}
            </Link>
          </div>
          <p className="mt-6 flex items-start gap-2 text-sm text-teal-50/80">
            <ShieldCheck aria-hidden className="mt-0.5 size-4 shrink-0" />
            {lt("hero.note")}
          </p>
        </div>

        <div className="motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-6 motion-safe:fill-mode-both motion-safe:delay-150 motion-safe:duration-700">
          <ProductMock />
        </div>
      </div>
    </section>
  );
}
