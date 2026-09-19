"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { useAuthHydration } from "@/features/auth/hooks";

function AuthHydration() {
  useAuthHydration();
  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  // one client per browser session; created lazily so SSR never shares state across requests
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          // networkMode "always": the API is on localhost — never pause queries when the laptop
          // reports itself offline (demo without wifi).
          queries: {
            staleTime: 5_000,
            retry: 1,
            refetchOnWindowFocus: false,
            networkMode: "always",
          },
          mutations: { networkMode: "always" },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthHydration />
      {children}
    </QueryClientProvider>
  );
}
