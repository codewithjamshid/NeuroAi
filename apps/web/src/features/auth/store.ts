import { create } from "zustand";
import { persist, type PersistStorage, type StorageValue } from "zustand/middleware";

import type { AuthUser, Role } from "./types";

export const AUTH_STORAGE_KEY = "neuroai.auth";

type Persisted = { access: string | null; refresh: string | null; user: AuthUser | null };

type AuthState = Persisted & {
  hydrated: boolean;
  setAuth: (auth: { access: string; refresh: string; user: AuthUser }) => void;
  setUser: (user: AuthUser) => void;
  clear: () => void;
  setHydrated: (v: boolean) => void;
};

// Stored as a flat {access, refresh, user} object (DEMO_SCOPE), not zustand's {state, version} wrapper.
const flatStorage: PersistStorage<Persisted> = {
  getItem: (name) => {
    try {
      const raw = localStorage.getItem(name);
      if (!raw) return null;
      const parsed = JSON.parse(raw) as Partial<Persisted>;
      return {
        state: {
          access: parsed.access ?? null,
          refresh: parsed.refresh ?? null,
          user: parsed.user ?? null,
        },
        version: 0,
      };
    } catch {
      return null;
    }
  },
  setItem: (name, value: StorageValue<Persisted>) => {
    try {
      localStorage.setItem(name, JSON.stringify(value.state));
    } catch {
      /* private mode / quota — auth just won't persist */
    }
  },
  removeItem: (name) => {
    try {
      localStorage.removeItem(name);
    } catch {
      /* ignore */
    }
  },
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      access: null,
      refresh: null,
      user: null,
      hydrated: false,
      setAuth: ({ access, refresh, user }) => set({ access, refresh, user }),
      setUser: (user) => set({ user }),
      clear: () => set({ access: null, refresh: null, user: null }),
      setHydrated: (hydrated) => set({ hydrated }),
    }),
    {
      name: AUTH_STORAGE_KEY,
      storage: flatStorage,
      partialize: (s) => ({ access: s.access, refresh: s.refresh, user: s.user }),
      // Hydrate from an effect (Providers) so SSR markup and the first client render match.
      skipHydration: true,
      onRehydrateStorage: () => (state) => state?.setHydrated(true),
    },
  ),
);

export function readAuthToken(): string | null {
  return useAuthStore.getState().access;
}

export function resetAuth(): void {
  useAuthStore.getState().clear();
}

export function homeForRole(role: Role | undefined | null): string {
  switch (role) {
    case "patient":
      return "/p";
    case "caregiver":
      return "/c";
    case "clinician":
    case "admin":
      return "/d";
    default:
      return "/login";
  }
}
