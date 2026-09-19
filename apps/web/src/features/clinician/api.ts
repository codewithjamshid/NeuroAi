import { AI_TIMEOUT_MS, apiFetch, apiJson } from "@/lib/api";

import type {
  ClinicianPatientRow,
  ClinicianSessionRow,
  Medication,
  MedicationCreate,
  Protocol,
  ProtocolTemplate,
  Report,
} from "./types";

export const listClinicianPatients = () => apiFetch<ClinicianPatientRow[]>("/clinician/patients");
export const listPatientSessions = (patientId: string, limit = 20) =>
  apiFetch<ClinicianSessionRow[]>(`/clinician/patients/${patientId}/sessions?limit=${limit}`);

export const listProtocolTemplates = () => apiFetch<ProtocolTemplate[]>("/protocol-templates");
export const getProtocol = (patientId: string) =>
  apiFetch<Protocol | null>(`/patients/${patientId}/protocol`);
export const createProtocol = (
  patientId: string,
  body: { template_key?: string; title?: string; items?: unknown[] },
) => apiJson<Protocol>(`/patients/${patientId}/protocol`, "POST", body);

export const listMedications = (patientId: string) =>
  apiFetch<Medication[]>(`/patients/${patientId}/medications`);
export const createMedication = (patientId: string, body: MedicationCreate) =>
  apiJson<Medication>(`/patients/${patientId}/medications`, "POST", body);

export const listReports = (patientId: string) =>
  apiFetch<Report[]>(`/patients/${patientId}/reports`);
export const generateReport = (patientId: string, period = "7d") =>
  apiJson<Report>(`/patients/${patientId}/reports/generate?period=${period}`, "POST", undefined, {
    timeoutMs: 90_000,
  });

export { AI_TIMEOUT_MS };
