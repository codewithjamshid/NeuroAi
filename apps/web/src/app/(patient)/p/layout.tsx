import { HelpButton } from "@/components/HelpButton";
import { RoleHeader } from "@/components/RoleHeader";
import { t } from "@/lib/i18n";

// TZ §3 accessibility: font ≥ 22px, controls ≥ 64px, high contrast (see .patient-ui in globals.css).
export default function PatientLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="patient-ui flex min-h-dvh flex-col">
      <RoleHeader role={t("role.patient")} />
      <main className="flex flex-1 flex-col px-4 py-6 pb-28">{children}</main>
      <HelpButton />
    </div>
  );
}
