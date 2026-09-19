import {
  Activity,
  ArrowDown,
  ArrowRight,
  AudioLines,
  BatteryLow,
  Bot,
  HeartPulse,
  Mic,
  ScanFace,
  Sigma,
  Smile,
} from "lucide-react";

import { type LandingKey, lt } from "../i18n";
import { card, shadowSoft } from "../styles";
import { Section } from "./Section";

const inputs: { label: LandingKey; hint: LandingKey; Icon: typeof Mic }[] = [
  { label: "state.in.1", hint: "state.in.1.hint", Icon: Mic },
  { label: "state.in.2", hint: "state.in.2.hint", Icon: ScanFace },
  { label: "state.in.3", hint: "state.in.3.hint", Icon: AudioLines },
];

const core: { label: LandingKey; Icon: typeof Activity }[] = [
  { label: "state.core.1", Icon: Activity },
  { label: "state.core.2", Icon: BatteryLow },
  { label: "state.core.3", Icon: Smile },
  { label: "state.core.4", Icon: HeartPulse },
];

const outputs: LandingKey[] = ["state.out.1", "state.out.2", "state.out.3"];

function Arrow() {
  return (
    <div aria-hidden className="flex items-center justify-center text-[#0f766e]/60">
      <ArrowRight className="hidden size-8 lg:block" />
      <ArrowDown className="size-8 lg:hidden" />
    </div>
  );
}

// TZ §5.4: three sources → PatientState (4 indicators) → §5.5 behaviour rules. Arrows flip to
// vertical on phones. Purely presentational; the real panel is features/sessions/StatePanel.
export function StateDiagram() {
  return (
    <Section
      id="state"
      tone="white"
      eyebrow={lt("state.eyebrow")}
      title={lt("state.title")}
      subtitle={lt("state.subtitle")}
    >
      <div className="grid items-center gap-4 lg:grid-cols-[1fr_auto_1.15fr_auto_1fr] lg:gap-6">
        <ul className="grid gap-3" aria-label={lt("state.inputs")}>
          {inputs.map(({ label, hint, Icon }) => (
            <li
              key={label}
              className="flex items-center gap-3 rounded-2xl bg-[#faf9f6] px-4 py-3 ring-1 ring-black/5"
            >
              <Icon aria-hidden className="size-6 shrink-0 text-[#0f766e]" />
              <div>
                <p className="font-semibold text-[#1f2933]">{lt(label)}</p>
                <p className="text-sm text-[#6b7280]">{lt(hint)}</p>
              </div>
            </li>
          ))}
        </ul>

        <Arrow />

        <div
          className={`rounded-2xl bg-gradient-to-br from-[#0f766e] to-[#134e4a] p-6 text-white ${shadowSoft}`}
        >
          <p className="font-mono text-sm font-semibold tracking-wide text-teal-100 uppercase">
            {lt("state.core")}
          </p>
          <ul className="mt-4 grid grid-cols-2 gap-2">
            {core.map(({ label, Icon }) => (
              <li
                key={label}
                className="flex items-center gap-2 rounded-xl bg-white/10 px-3 py-2.5 font-medium ring-1 ring-white/15"
              >
                <Icon aria-hidden className="size-5" />
                {lt(label)}
              </li>
            ))}
          </ul>
        </div>

        <Arrow />

        <div className={card}>
          <p className="flex items-center gap-2 font-semibold text-[#1f2933]">
            <Bot aria-hidden className="size-5 text-[#0f766e]" />
            {lt("state.out")}
          </p>
          <ul className="mt-3 flex flex-col gap-2 text-sm leading-relaxed text-[#6b7280]">
            {outputs.map((k) => (
              <li key={k} className="border-l-2 border-teal-200 pl-3">
                {lt(k)}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <p className="mt-8 flex items-start gap-3 rounded-2xl bg-amber-50 px-5 py-4 text-base text-[#1f2933] ring-1 ring-amber-200">
        <Sigma aria-hidden className="mt-0.5 size-5 shrink-0 text-[#d97706]" />
        {lt("state.note")}
      </p>
    </Section>
  );
}
