// NEXT_PUBLIC_* values are inlined at build time; keep literal property access.
export const env = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1",
  faceFps: Number(process.env.NEXT_PUBLIC_FACE_FPS ?? "15"),
  emergencyNumber: process.env.NEXT_PUBLIC_EMERGENCY_NUMBER ?? "103",
} as const;
