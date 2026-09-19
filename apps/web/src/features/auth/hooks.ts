"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { getMe, login } from "./api";
import { homeForRole, useAuthStore } from "./store";
import type { LoginRequest } from "./types";

export const authKeys = { me: ["me"] as const };

export function useAuth() {
  const user = useAuthStore((s) => s.user);
  const access = useAuthStore((s) => s.access);
  const hydrated = useAuthStore((s) => s.hydrated);
  return { user, access, hydrated, isAuthed: Boolean(access && user) };
}

// Runs once in Providers: rehydrates the persisted auth after mount (skipHydration).
export function useAuthHydration() {
  useEffect(() => {
    void useAuthStore.persist.rehydrate();
  }, []);
}

export function useLogin() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: LoginRequest) => login(body),
    onSuccess: (data) => {
      setAuth(data);
      qc.clear();
      router.replace(homeForRole(data.user.role));
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const clear = useAuthStore((s) => s.clear);
  const qc = useQueryClient();
  return () => {
    clear();
    qc.clear();
    router.replace("/login");
  };
}

// GET /me — refreshes the cached user (patient_id may be attached after login).
export function useMe(enabled = true) {
  const { isAuthed } = useAuth();
  const setUser = useAuthStore((s) => s.setUser);
  const q = useQuery({
    queryKey: authKeys.me,
    queryFn: getMe,
    enabled: enabled && isAuthed,
    retry: false,
  });
  useEffect(() => {
    if (q.data) setUser(q.data);
  }, [q.data, setUser]);
  return q;
}
