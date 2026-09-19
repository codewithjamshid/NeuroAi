import { ArrowRight, HeartHandshake, Stethoscope, User } from "lucide-react";
import Link from "next/link";

import { type LandingKey, lt } from "../i18n";
import { btnOutlineTeal, card, iconTile } from "../styles";
import { Section } from "./Section";

const roles: { title: LandingKey; text: LandingKey; Icon: typeof User }[] = [
  { title: "roles.1.title", text: "roles.1.text", Icon: User },
  { title: "roles.2.title", text: "roles.2.text", Icon: HeartHandshake },
  { title: "roles.3.title", text: "roles.3.text", Icon: Stethoscope },
];

// TZ §1.3 roles. Every card links to /login (demo accounts live there), never straight to /p|/c|/d.
export function Roles() {
  return (
    <Section
      id="roles"
      eyebrow={lt("roles.eyebrow")}
      title={lt("roles.title")}
      subtitle={lt("roles.subtitle")}
    >
      <ul className="grid gap-4 md:grid-cols-3">
        {roles.map(({ title, text, Icon }) => (
          <li key={title} className={`${card} flex flex-col`}>
            <div className={iconTile}>
              <Icon aria-hidden className="size-6" />
            </div>
            <h3 className="mt-4 text-2xl font-semibold tracking-tight text-[#1f2933]">
              {lt(title)}
            </h3>
            <p className="mt-2 flex-1 text-base leading-relaxed text-[#6b7280]">{lt(text)}</p>
            <Link href="/login" className={`${btnOutlineTeal} mt-6`}>
              {lt("roles.cta")}
              <ArrowRight aria-hidden className="size-5" />
            </Link>
          </li>
        ))}
      </ul>
    </Section>
  );
}
