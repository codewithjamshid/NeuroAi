import { BellRing, Ear, ListChecks } from "lucide-react";

import { type LandingKey, lt } from "../i18n";
import { shadowSoft } from "../styles";
import { Section } from "./Section";

const steps: { title: LandingKey; text: LandingKey; Icon: typeof Ear }[] = [
  { title: "how.1.title", text: "how.1.text", Icon: Ear },
  { title: "how.2.title", text: "how.2.text", Icon: ListChecks },
  { title: "how.3.title", text: "how.3.text", Icon: BellRing },
];

// "Tushunadi / Bajartiridi / Xabar beradi" — the positioning line as three numbered steps.
export function HowItWorks() {
  return (
    <Section
      id="how"
      tone="white"
      eyebrow={lt("how.eyebrow")}
      title={lt("how.title")}
      subtitle={lt("how.subtitle")}
    >
      <ol className="grid gap-4 md:grid-cols-3">
        {steps.map(({ title, text, Icon }, i) => (
          <li key={title} className={`relative rounded-2xl bg-[#faf9f6] p-6 ${shadowSoft}`}>
            <div className="flex items-center justify-between">
              <span className="flex size-12 items-center justify-center rounded-2xl bg-[#0f766e] text-white">
                <Icon aria-hidden className="size-6" />
              </span>
              <span
                aria-hidden
                className="text-4xl font-semibold tracking-tight text-[#0f766e]/20 tabular-nums"
              >
                0{i + 1}
              </span>
            </div>
            <h3 className="mt-5 text-2xl font-semibold tracking-tight text-[#1f2933]">
              {lt(title)}
            </h3>
            <p className="mt-2 text-base leading-relaxed text-[#6b7280]">{lt(text)}</p>
          </li>
        ))}
      </ol>
    </Section>
  );
}
