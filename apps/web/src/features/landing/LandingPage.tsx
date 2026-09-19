import { Footer } from "./components/Footer";
import { Hero } from "./components/Hero";
import { HowItWorks } from "./components/HowItWorks";
import { Modules } from "./components/Modules";
import { Nav } from "./components/Nav";
import { Problem } from "./components/Problem";
import { Roles } from "./components/Roles";
import { Safety } from "./components/Safety";
import { StateDiagram } from "./components/StateDiagram";
import { Tech } from "./components/Tech";

// Marketing landing at "/" (server component). Section order per the demo brief; the only
// client pieces are the Nav toggle, StatusPill in the mock and HealthBadge in the footer.
export function LandingPage() {
  return (
    <div className="flex min-h-dvh flex-col overflow-x-clip bg-[#faf9f6] text-[#1f2933]">
      <Nav />
      <main id="main" className="flex-1">
        <Hero />
        <Problem />
        <HowItWorks />
        <Modules />
        <StateDiagram />
        <Safety />
        <Roles />
        <Tech />
      </main>
      <Footer />
    </div>
  );
}
