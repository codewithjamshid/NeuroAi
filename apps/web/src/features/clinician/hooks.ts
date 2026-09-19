"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createMedication,
  createProtocol,
  generateReport,
  getProtocol,
  listClinicianPatients,
  listMedications,
  listPatientSessions,
  listProtocolTemplates,
  listReports,
} from "./api";
import type { MedicationCreate } from "./types";

export const clinicianKeys = {
  patients: ["clinician", "patients"] as const,
  sessions: (id: string) => ["clinician", "patients", id, "sessions"] as const,
  templates: ["protocol-templates"] as const,
  protocol: (id: string) => ["patients", id, "protocol"] as const,
  medications: (id: string) => ["patients", id, "medications"] as const,
  reports: (id: string) => ["patients", id, "reports"] as const,
};

export const useClinicianPatients = () =>
  useQuery({ queryKey: clinicianKeys.patients, queryFn: listClinicianPatients });

export const usePatientSessions = (patientId: string | null, limit = 20) =>
  useQuery({
    queryKey: [...clinicianKeys.sessions(patientId ?? ""), limit],
    queryFn: () => listPatientSessions(patientId as string, limit),
    enabled: Boolean(patientId),
  });

export const useProtocolTemplates = () =>
  useQuery({
    queryKey: clinicianKeys.templates,
    queryFn: listProtocolTemplates,
    staleTime: 60_000,
  });

export const useProtocol = (patientId: string | null) =>
  useQuery({
    queryKey: clinicianKeys.protocol(patientId ?? ""),
    queryFn: () => getProtocol(patientId as string),
    enabled: Boolean(patientId),
  });

export function useCreateProtocol(patientId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { template_key?: string; title?: string }) =>
      createProtocol(patientId as string, body),
    onSuccess: () => {
      if (patientId) {
        void qc.invalidateQueries({ queryKey: clinicianKeys.protocol(patientId) });
        void qc.invalidateQueries({ queryKey: ["patients", patientId, "today"] });
      }
    },
  });
}

export const useMedications = (patientId: string | null) =>
  useQuery({
    queryKey: clinicianKeys.medications(patientId ?? ""),
    queryFn: () => listMedications(patientId as string),
    enabled: Boolean(patientId),
  });

export function useCreateMedication(patientId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: MedicationCreate) => createMedication(patientId as string, body),
    onSuccess: () => {
      if (patientId) void qc.invalidateQueries({ queryKey: clinicianKeys.medications(patientId) });
    },
  });
}

export const useReports = (patientId: string | null) =>
  useQuery({
    queryKey: clinicianKeys.reports(patientId ?? ""),
    queryFn: () => listReports(patientId as string),
    enabled: Boolean(patientId),
  });

export function useGenerateReport(patientId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (period: string) => generateReport(patientId as string, period),
    onSuccess: () => {
      if (patientId) void qc.invalidateQueries({ queryKey: clinicianKeys.reports(patientId) });
    },
  });
}
