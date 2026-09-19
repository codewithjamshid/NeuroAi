import { apiFetch, apiJson } from "@/lib/api";

import type {
  Dashboard,
  Interpretation,
  MoodTrendPoint,
  Patient,
  PatientCreate,
  RedFlag,
  RedFlagStatus,
  TodayResponse,
} from "./types";

export const listPatients = () => apiFetch<Patient[]>("/patients");
export const getPatient = (id: string) => apiFetch<Patient>(`/patients/${id}`);
export const createPatient = (body: PatientCreate) => apiJson<Patient>("/patients", "POST", body);
export const getToday = (patientId: string) =>
  apiFetch<TodayResponse>(`/patients/${patientId}/today`);
export const postMood = (patientId: string, self_score: number) =>
  apiJson<unknown>(`/patients/${patientId}/mood`, "POST", { self_score });
export const getMoodTrend = (patientId: string, days = 14) =>
  apiFetch<MoodTrendPoint[]>(`/patients/${patientId}/mood/trend?days=${days}`);
export const getDashboard = (patientId: string) =>
  apiFetch<Dashboard>(`/patients/${patientId}/dashboard`);
export const getRedFlags = (patientId: string, status?: RedFlagStatus) =>
  apiFetch<RedFlag[]>(`/patients/${patientId}/red-flags${status ? `?status=${status}` : ""}`);
export const patchRedFlag = (id: string, body: { status: RedFlagStatus; note?: string }) =>
  apiJson<RedFlag>(`/red-flags/${id}`, "PATCH", body);
export const getInterpretations = (patientId: string, limit = 10) =>
  apiFetch<Interpretation[]>(`/patients/${patientId}/interpretations?limit=${limit}`);
