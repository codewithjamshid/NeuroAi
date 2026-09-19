import { CalendarCheck, EyeOff, MessageSquareText, Users } from "lucide-react";

import { type LandingKey, lt } from "../i18n";
import { card, iconTile } from "../styles";
import { Section } from "./Section";

const cards: { title: LandingKey; text: LandingKey; Icon: typeof Users }[] = [
  { title: "problem.1.title", text: "problem.1.text", Icon: CalendarCheck },
  { title: "problem.2.title", text: "problem.2.text", Icon: Users },
  { title: "problem.3.title", text: "problem.3.text", Icon: MessageSquareText },
  { title: "problem.4.title", text: "problem.4.text", Icon: EyeOff },
];

const facts: { value: LandingKey; label: LandingKey }[] = [
  { value: "problem.fact.1.value", label: "problem.fact.1.label" },
  { value: "problem.fact.2.value", label: "problem.fact.2.label" },
];

// TZ §1.1 (four rows) + §0 (the two ≈1/3 facts). No other numbers.
export function Problem() {
  return (
    <Section
      id="problem"
      eyebrow={lt("problem.eyebrow")}
      title={lt("problem.title")}
      subtitle={lt("problem.subtitle")}
    >
      <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
          {facts.map((f) => (
            <li key={f.value} className={`${card} border-l-4 border-[#0f766e]`}>
              <p className="text-5xl font-semibold tracking-tight text-[#0f766e]">{lt(f.value)}</p>
              <p className="mt-2 text-base text-[#6b7280]">{lt(f.label)}</p>
            </li>
          ))}
        </ul>

        <ul className="grid gap-4 sm:grid-cols-2">
          {cards.map(({ title, text, Icon }) => (
            <li key={title} className={card}>
              <div className={iconTile}>
                <Icon aria-hidden className="size-6" />
              </div>
              <h3 className="mt-4 text-lg font-semibold tracking-tight text-[#1f2933]">
                {lt(title)}
              </h3>
              <p className="mt-2 text-base leading-relaxed text-[#6b7280]">{lt(text)}</p>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}
