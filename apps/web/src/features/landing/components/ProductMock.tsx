import { Activity, BatteryLow, Mic, Phone, Smile } from "lucide-react";

import { RichText } from "@/components/RichText";
import { StatusPill } from "@/components/StatusPill";

import { lt } from "../i18n";
import { shadowSoft } from "../styles";
import { LandingLogo } from "./LandingLogo";

const pills = [
  { Icon: Activity, label: lt("mock.engagement"), value: lt("mock.engagement_value") },
  { Icon: BatteryLow, label: lt("mock.fatigue"), value: lt("mock.fatigue_value") },
  { Icon: Smile, label: lt("mock.mood"), value: lt("mock.mood_value") },
];

// Static mini patient screen (no API): the same shapes the real /p/talk screen uses —
// big mic circle, AI bubble with bold keyword, "AI shunday tushundi" pills (icon + text).
export function ProductMock() {
  return (
    <figure className="relative mx-auto w-full max-w-md">
      <div
        aria-hidden
        className="absolute inset-0 -rotate-2 rounded-3xl bg-white/10 ring-1 ring-white/20"
      />
      <div
        className={`relative flex flex-col gap-4 rounded-3xl bg-white p-5 text-[#1f2933] ring-1 ring-black/5 ${shadowSoft}`}
      >
        <div className="flex items-center justify-between gap-3">
          <span className="flex items-center gap-2 font-semibold">
            <LandingLogo size="sm" />
            <span className="text-sm text-[#6b7280]">{lt("mock.header")}</span>
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#0f766e] px-3 py-1.5 text-sm font-semibold text-white">
            <Phone aria-hidden className="size-4" />
            {lt("mock.help")}
          </span>
        </div>

        <div className="flex flex-col gap-2.5">
          <div className="self-end rounded-2xl rounded-br-md bg-[#faf9f6] px-4 py-2.5 ring-1 ring-black/5">
            <p className="text-xs font-medium text-[#6b7280]">{lt("mock.patient")}</p>
            <p className="text-base">{lt("mock.patient_text")}</p>
          </div>
          <div className="max-w-[92%] self-start rounded-2xl rounded-bl-md bg-teal-50 px-4 py-3">
            <p className="text-xs font-medium text-[#0f766e]">{lt("mock.ai")}</p>
            <RichText text={lt("mock.ai_text")} className="text-lg leading-snug" />
          </div>
        </div>

        <section
          aria-label={lt("mock.state_title")}
          className="rounded-2xl bg-[#faf9f6] px-3 py-2.5 ring-1 ring-black/5"
        >
          <p className="mb-1.5 text-xs font-medium text-[#6b7280]">{lt("mock.state_title")}</p>
          <ul className="flex flex-wrap gap-2">
            {pills.map(({ Icon, label, value }) => (
              <li
                key={label}
                className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-sm ring-1 ring-black/5"
              >
                <Icon aria-hidden className="size-4 text-[#0f766e]" />
                <span className="text-[#6b7280]">{label}:</span>
                <span className="font-semibold">{value}</span>
              </li>
            ))}
          </ul>
        </section>

        <div className="flex flex-col items-center gap-3 pt-1">
          <StatusPill status="idle" className="text-sm" />
          <div
            aria-hidden
            className="flex size-28 items-center justify-center rounded-full bg-[#0f766e] text-white shadow-lg ring-8 ring-teal-50"
          >
            <Mic className="size-12" />
          </div>
          <span className="text-lg font-semibold">{lt("mock.mic")}</span>
        </div>
      </div>
      <figcaption className="sr-only">{lt("mock.caption")}</figcaption>
    </figure>
  );
}
