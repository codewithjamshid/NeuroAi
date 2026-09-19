import {
  ChartLine,
  HeartHandshake,
  Languages,
  MessageCircleHeart,
  Mic,
  ScanFace,
  ShieldAlert,
} from "lucide-react";

import { type LandingKey, lt } from "../i18n";
import { card, iconTile } from "../styles";
import { Section } from "./Section";

const modules: { title: LandingKey; text: LandingKey; Icon: typeof Mic }[] = [
  { title: "modules.1.title", text: "modules.1.text", Icon: MessageCircleHeart },
  { title: "modules.2.title", text: "modules.2.text", Icon: Languages },
  { title: "modules.3.title", text: "modules.3.text", Icon: Mic },
  { title: "modules.4.title", text: "modules.4.text", Icon: ScanFace },
  { title: "modules.5.title", text: "modules.5.text", Icon: ShieldAlert },
  { title: "modules.6.title", text: "modules.6.text", Icon: ChartLine },
  { title: "modules.7.title", text: "modules.7.text", Icon: HeartHandshake },
];

// TZ §2 M1–M8 as a grid; numbers (40 needs, 120 items, 6 categories, 14 days) come from the TZ.
export function Modules() {
  return (
    <Section
      id="modules"
      eyebrow={lt("modules.eyebrow")}
      title={lt("modules.title")}
      subtitle={lt("modules.subtitle")}
    >
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {modules.map(({ title, text, Icon }) => (
          <li
            key={title}
            className={`${card} transition-transform motion-safe:hover:-translate-y-0.5`}
          >
            <div className="flex items-center gap-3">
              <div className={iconTile}>
                <Icon aria-hidden className="size-6" />
              </div>
              <h3 className="text-lg font-semibold tracking-tight text-[#1f2933]">{lt(title)}</h3>
            </div>
            <p className="mt-3 text-base leading-relaxed text-[#6b7280]">{lt(text)}</p>
          </li>
        ))}
      </ul>
    </Section>
  );
}
