// DEMO_SCOPE "API kontrakt — Auth" (hand-written; not the generated OpenAPI types).
export type Role = "patient" | "caregiver" | "clinician" | "admin";

export type AuthUser = {
  id: string;
  role: Role;
  full_name: string;
  email?: string;
  locale?: string;
  patient_id?: string | null;
};

export type LoginRequest = { email: string; password: string };
export type LoginResponse = { access: string; refresh: string; user: AuthUser };
export type RefreshResponse = { access: string; refresh: string };
export type MeResponse = AuthUser;
