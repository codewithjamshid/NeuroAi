import { cn } from "@/lib/utils";

import { container, eyebrow as eyebrowCls, h2, lead } from "../styles";

type Tone = "page" | "white" | "dark";

const tones: Record<Tone, string> = {
  page: "bg-[#faf9f6]",
  white: "bg-white",
  dark: "bg-[#134e4a] text-white",
};

// Landing section shell: anchor id (offset for the sticky nav), eyebrow + h2 + lead, container.
export function Section({
  id,
  eyebrow,
  title,
  subtitle,
  tone = "page",
  className,
  children,
}: {
  id: string;
  eyebrow: string;
  title: string;
  subtitle?: string;
  tone?: Tone;
  className?: string;
  children: React.ReactNode;
}) {
  const dark = tone === "dark";
  return (
    <section
      id={id}
      aria-labelledby={`${id}-title`}
      className={cn("scroll-mt-20 py-16 sm:py-24", tones[tone], className)}
    >
      <div className={container}>
        <header className="mb-10 max-w-2xl sm:mb-14">
          <p className={cn(eyebrowCls, dark && "text-teal-200")}>{eyebrow}</p>
          <h2 id={`${id}-title`} className={cn("mt-2", h2, dark && "text-white")}>
            {title}
          </h2>
          {subtitle && <p className={cn("mt-3", lead, dark && "text-teal-50/80")}>{subtitle}</p>}
        </header>
        {children}
      </div>
    </section>
  );
}
