"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { cn } from "@/lib/utils";

import { type LandingKey, lt } from "../i18n";
import { btnAmber, container } from "../styles";
import { LandingLogo } from "./LandingLogo";

const links: { href: string; label: LandingKey }[] = [
  { href: "#how", label: "nav.how" },
  { href: "#modules", label: "nav.modules" },
  { href: "#safety", label: "nav.safety" },
  { href: "/status", label: "nav.status" },
];

// Sticky top bar. The only client state on the landing besides HealthBadge: the phone menu toggle.
export function Nav() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-black/5 bg-[#faf9f6]/85 backdrop-blur">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-lg focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:font-semibold focus:text-[#0f766e] focus:ring-2 focus:ring-[#0f766e]"
      >
        {lt("nav.skip")}
      </a>
      <nav aria-label={lt("nav.aria")} className={cn(container, "flex h-16 items-center gap-4")}>
        <Link
          href="/"
          className="flex items-center gap-2.5 rounded-lg text-lg font-semibold tracking-tight text-[#1f2933] outline-none focus-visible:ring-2 focus-visible:ring-[#0f766e]"
        >
          <LandingLogo size="md" />
          {lt("nav.brand")}
        </Link>

        <ul className="ml-auto hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                className="rounded-lg px-3 py-2 text-sm font-medium text-[#1f2933]/80 outline-none hover:bg-black/5 hover:text-[#1f2933] focus-visible:ring-2 focus-visible:ring-[#0f766e]"
              >
                {lt(l.label)}
              </Link>
            </li>
          ))}
        </ul>

        <Link href="/login" className={cn(btnAmber, "hidden min-h-10 px-4 text-sm md:inline-flex")}>
          {lt("nav.cta")}
        </Link>

        <button
          type="button"
          aria-expanded={open}
          aria-controls="landing-mobile-menu"
          aria-label={open ? lt("nav.menu_close") : lt("nav.menu_open")}
          onClick={() => setOpen((v) => !v)}
          className="ml-auto flex size-11 items-center justify-center rounded-xl text-[#1f2933] outline-none hover:bg-black/5 focus-visible:ring-2 focus-visible:ring-[#0f766e] md:hidden"
        >
          {open ? <X aria-hidden className="size-6" /> : <Menu aria-hidden className="size-6" />}
        </button>
      </nav>

      <div
        id="landing-mobile-menu"
        hidden={!open}
        className="border-t border-black/5 bg-[#faf9f6] md:hidden"
      >
        <ul className={cn(container, "flex flex-col gap-1 py-3")}>
          {links.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                onClick={() => setOpen(false)}
                className="block rounded-xl px-3 py-3 text-base font-medium text-[#1f2933] outline-none hover:bg-black/5 focus-visible:ring-2 focus-visible:ring-[#0f766e]"
              >
                {lt(l.label)}
              </Link>
            </li>
          ))}
          <li className="pt-2">
            <Link href="/login" onClick={() => setOpen(false)} className={cn(btnAmber, "w-full")}>
              {lt("nav.cta")}
            </Link>
          </li>
        </ul>
      </div>
    </header>
  );
}
