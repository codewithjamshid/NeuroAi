"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import { getCaregiverToday, getTips, telegramLink, telegramStatus } from "./api";

export const useCaregiverToday = (patientId: string | null) =>
  useQuery({
    queryKey: ["caregiver", patientId, "today"],
    queryFn: () => getCaregiverToday(patientId as string),
    enabled: Boolean(patientId),
    refetchInterval: 15_000,
  });

export const useTips = (patientId: string | null) =>
  useQuery({
    queryKey: ["caregiver", patientId, "tips"],
    queryFn: () => getTips(patientId as string),
    enabled: Boolean(patientId),
    staleTime: 5 * 60_000,
  });

export const useTelegramStatus = (refetchInterval?: number) =>
  useQuery({ queryKey: ["telegram", "status"], queryFn: telegramStatus, refetchInterval });

export const useTelegramLink = () => useMutation({ mutationFn: telegramLink });
