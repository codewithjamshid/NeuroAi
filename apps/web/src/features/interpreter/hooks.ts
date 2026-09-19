"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getBoard, interpreterConfirm, interpreterGuess } from "./api";

export function useBoard(patientId: string | null) {
  return useQuery({
    queryKey: ["interpreter", "board", patientId],
    queryFn: () => getBoard(patientId as string),
    enabled: Boolean(patientId),
    staleTime: 60_000,
  });
}

export function useGuess(patientId: string | null) {
  return useMutation({
    mutationFn: (input: { audio: Blob } | { text: string }) =>
      interpreterGuess(patientId as string, input),
  });
}

export function useConfirm(patientId: string | null) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: interpreterConfirm,
    onSuccess: () => {
      if (patientId) {
        void qc.invalidateQueries({ queryKey: ["patients", patientId, "interpretations"] });
      }
    },
  });
}
