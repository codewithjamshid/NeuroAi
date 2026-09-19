import { HelpButton } from "@/components/HelpButton";
import { RoleHeader } from "@/components/RoleHeader";
import { RoleGuard } from "@/features/auth/components/RoleGuard";
import { t } from "@/lib/i18n";

// TZ §3 accessibility: font ≥ 22px, controls ≥ 64px, high contrast (see .patient-ui in globals.css).
export default function PatientLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="patient-ui flex min-h-dvh flex-col">
      <RoleHeader role={t("role.patient")} home="/p" tone="patient" />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-6 pb-32 md:px-6 md:py-8">
        <RoleGuard roles={["patient", "caregiver", "clinician", "admin"]}>{children}</RoleGuard>
      </main>
      <HelpButton />
    </div>
  );
}
