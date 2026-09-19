import { Ban, CircleCheck, Lock } from "lucide-react";

import { type LandingKey, lt } from "../i18n";
import { Section } from "./Section";

const groups: { title: LandingKey; items: LandingKey[]; Icon: typeof Ban }[] = [
  {
    title: "safety.not.title",
    items: ["safety.not.1", "safety.not.2", "safety.not.3"],
    Icon: Ban,
  },
  {
    title: "safety.does.title",
    items: ["safety.does.1", "safety.does.2", "safety.does.3"],
    Icon: CircleCheck,
  },
  {
    title: "safety.data.title",
    items: ["safety.data.1", "safety.data.2", "safety.data.3", "safety.data.4"],
    Icon: Lock,
  },
];

// TZ §1.4 hard constraints + §6.2 escalation + §11.3 data answers, as one dark positioning band.
export function Safety() {
  return (
    <Section
      id="safety"
      tone="dark"
      eyebrow={lt("safety.eyebrow")}
      title={lt("safety.title")}
      subtitle={lt("safety.subtitle")}
    >
      <div className="grid gap-4 md:grid-cols-3">
        {groups.map(({ title, items, Icon }) => (
          <div key={title} className="rounded-2xl bg-white/8 p-6 ring-1 ring-white/15">
            <h3 className="flex items-center gap-2 text-lg font-semibold">
              <Icon aria-hidden className="size-5 text-teal-200" />
              {lt(title)}
            </h3>
            <ul className="mt-4 flex flex-col gap-3 text-base leading-relaxed text-teal-50/90">
              {items.map((k) => (
                <li key={k} className="flex gap-3">
                  <Icon aria-hidden className="mt-1 size-4 shrink-0 text-teal-200/80" />
                  <span>{lt(k)}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Section>
  );
}
