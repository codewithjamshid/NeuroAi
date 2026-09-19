import {
  Activity,
  AudioLines,
  Bot,
  Database,
  ScanFace,
  Send,
  Server,
  Timer,
  Volume2,
} from "lucide-react";
import Link from "next/link";

import { type LandingKey, lt } from "../i18n";
import { Section } from "./Section";

const chips: { label: LandingKey; Icon: typeof Bot }[] = [
  { label: "tech.1", Icon: AudioLines },
  { label: "tech.2", Icon: Volume2 },
  { label: "tech.3", Icon: ScanFace },
  { label: "tech.4", Icon: Bot },
  { label: "tech.5", Icon: Server },
  { label: "tech.6", Icon: Database },
  { label: "tech.7", Icon: Send },
];

// TZ §4.2–4.4: stack as compact chips; "≤ 5 s" is the §1.5 voice-turn target.
export function Tech() {
  return (
    <Section id="tech" tone="white" eyebrow={lt("tech.eyebrow")} title={lt("tech.title")}>
      <ul className="flex flex-wrap gap-3">
        {chips.map(({ label, Icon }) => (
          <li
            key={label}
            className="inline-flex items-center gap-2 rounded-full border border-teal-200 bg-[#faf9f6] px-4 py-2.5 text-sm font-medium text-[#1f2933]"
          >
            <Icon aria-hidden className="size-4 text-[#0f766e]" />
            {lt(label)}
          </li>
        ))}
      </ul>
      <div className="mt-8 flex flex-col gap-4 rounded-2xl bg-[#faf9f6] px-5 py-4 ring-1 ring-black/5 sm:flex-row sm:items-center sm:justify-between">
        <p className="flex items-start gap-3 text-base text-[#1f2933]">
          <Timer aria-hidden className="mt-0.5 size-5 shrink-0 text-[#0f766e]" />
          {lt("tech.note")}
        </p>
        <Link
          href="/status"
          className="inline-flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-[#0f766e] outline-none hover:bg-teal-50 focus-visible:ring-2 focus-visible:ring-[#0f766e]"
        >
          <Activity aria-hidden className="size-4" />
          {lt("tech.status_link")}
        </Link>
      </div>
    </Section>
  );
}
