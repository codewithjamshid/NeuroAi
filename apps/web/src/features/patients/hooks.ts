"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/features/auth/hooks";

import {
  createPatient,
  getDashboard,
  getInterpretations,
  getMoodTrend,
  getPatient,
  getRedFlags,
  getToday,
  listPatients,
  patchRedFlag,
  postMood,
} from "./api";
import type { PatientCreate, RedFlagStatus } from "./types";

export const patientKeys = {
  list: ["patients"] as const,
  one: (id: string) => ["patients", id] as const,
  today: (id: string) => ["patients", id, "today"] as const,
  mood: (id: string) => ["patients", id, "mood"] as const,
  dashboard: (id: string) => ["patients", id, "dashboard"] as const,
  flags: (id: string, status?: string) => ["patients", id, "red-flags", status ?? "all"] as const,
  interpretations: (id: string, limit: number) =>
    ["patients", id, "interpretations", limit] as const,
};

export function usePatients(enabled = true) {
  return useQuery({ queryKey: patientKeys.list, queryFn: listPatients, enabled });
}

// The patient the current user acts for: own account → user.patient_id; caregiver → primary
// patient (login gives it) or the first linked patient from GET /patients.
export function usePatientId(): { patientId: string | null; isPending: boolean; error: unknown } {
  const { user, hydrated } = useAuth();
  const fromUser = user?.patient_id ?? null;
  const needList = hydrated && Boolean(user) && !fromUser;
  const list = usePatients(needList);
  if (fromUser) return { patientId: fromUser, isPending: false, error: null };
  if (!needList) return { patientId: null, isPending: !hydrated, error: null };
  return {
    patientId: list.data?.[0]?.id ?? null,
    isPending: list.isPending,
    error: list.error,
  };
}

export function usePatient(id: string | null) {
  return useQuery({
    queryKey: patientKeys.one(id ?? ""),
    queryFn: () => getPatient(id as string),
    enabled: Boolean(id),
  });
}

export function useToday(patientId: string | null) {
  return useQuery({
    queryKey: patientKeys.today(patientId ?? ""),
    queryFn: () => getToday(patientId as string),
    enabled: Boolean(patientId),
  });
}

export function useMoodMutation(patientId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (score: number) => postMood(patientId as string, score),
    onSuccess: () => {
      if (patientId) void qc.invalidateQueries({ queryKey: patientKeys.today(patientId) });
    },
  });
}

export function useMoodTrend(patientId: string | null, days = 14) {
  return useQuery({
    queryKey: [...patientKeys.mood(patientId ?? ""), days],
    queryFn: () => getMoodTrend(patientId as string, days),
    enabled: Boolean(patientId),
  });
}

export function useDashboard(patientId: string | null) {
  return useQuery({
    queryKey: patientKeys.dashboard(patientId ?? ""),
    queryFn: () => getDashboard(patientId as string),
    enabled: Boolean(patientId),
  });
}

export function useRedFlags(patientId: string | null, status?: RedFlagStatus) {
  return useQuery({
    queryKey: patientKeys.flags(patientId ?? "", status),
    queryFn: () => getRedFlags(patientId as string, status),
    enabled: Boolean(patientId),
  });
}

export function useRedFlagMutation(patientId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (v: { id: string; status: RedFlagStatus; note?: string }) =>
      patchRedFlag(v.id, { status: v.status, note: v.note }),
    onSuccess: () => {
      if (patientId) {
        void qc.invalidateQueries({ queryKey: ["patients", patientId, "red-flags"] });
        void qc.invalidateQueries({ queryKey: patientKeys.dashboard(patientId) });
      }
      void qc.invalidateQueries({ queryKey: ["clinician", "patients"] });
    },
  });
}

export function useInterpretations(patientId: string | null, limit = 10, refetchInterval?: number) {
  return useQuery({
    queryKey: patientKeys.interpretations(patientId ?? "", limit),
    queryFn: () => getInterpretations(patientId as string, limit),
    enabled: Boolean(patientId),
    refetchInterval,
  });
}

export function useCreatePatient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PatientCreate) => createPatient(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: patientKeys.list });
      void qc.invalidateQueries({ queryKey: ["clinician", "patients"] });
    },
  });
}
