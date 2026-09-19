"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { createSession, endSession, getTranscript } from "./api";
import type { Session, SessionMode } from "./types";

// Creates a session on mount and ends it on unmount (talk / exercise screens).
export function useSessionLifecycle(patientId: string | null, mode: SessionMode) {
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [attempt, setAttempt] = useState(0);
  const sessionRef = useRef<Session | null>(null);

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    setError(null);
    createSession(patientId, mode)
      .then((s) => {
        if (cancelled) {
          void endSession(s.id).catch(() => undefined);
          return;
        }
        sessionRef.current = s;
        setSession(s);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e);
      });
    return () => {
      cancelled = true;
      const s = sessionRef.current;
      sessionRef.current = null;
      setSession(null);
      if (s) void endSession(s.id).catch(() => undefined);
    };
  }, [patientId, mode, attempt]);

  return { session, error, retry: () => setAttempt((n) => n + 1) };
}

export function useTranscript(sessionId: string | null) {
  return useQuery({
    queryKey: ["sessions", sessionId, "transcript"],
    queryFn: () => getTranscript(sessionId as string),
    enabled: Boolean(sessionId),
  });
}

export function useEndSession() {
  return useMutation({ mutationFn: (id: string) => endSession(id) });
}
