"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { env } from "@/lib/env";

import { clearBaseline, loadBaseline, saveBaseline } from "./baseline";
import { type EngineSnapshot, FaceEngine } from "./engine";
import {
  loadFaceLandmarker,
  mapCameraError,
  openCamera,
  startDetectionLoop,
  stopStream,
} from "./mediapipe";
import type {
  CameraErrorCode,
  FaceBaseline,
  FaceBatchItem,
  FrameMeasure,
  PalsySide,
} from "./types";

export type TrackerStatus = "idle" | "camera" | "model" | "running" | "error";

// Camera → FaceLandmarker loop → FaceEngine; mirrors the engine snapshot into React state per frame.
export function useFaceTracker(opts: {
  palsy: PalsySide;
  baseline: FaceBaseline | null;
  onSecond?: (item: FaceBatchItem) => void;
  onCalibrated?: (frames: FrameMeasure[], blinks: number, ms: number) => void;
}) {
  const engineRef = useRef<FaceEngine | null>(null);
  if (!engineRef.current) engineRef.current = new FaceEngine();
  const engine = engineRef.current;

  const [status, setStatus] = useState<TrackerStatus>("idle");
  const [error, setError] = useState<CameraErrorCode | null>(null);
  const [snap, setSnap] = useState<EngineSnapshot>(() => engine.snapshot());
  const streamRef = useRef<MediaStream | null>(null);
  const stopLoopRef = useRef<(() => void) | null>(null);
  const disposedRef = useRef(false);

  const { palsy, baseline, onSecond, onCalibrated } = opts;
  useEffect(() => {
    engine.palsy = palsy;
    engine.baseline = baseline;
    engine.rest = baseline?.rest ?? null;
  }, [engine, palsy, baseline]);
  useEffect(() => {
    engine.onSecond = onSecond ?? null;
    engine.onCalibrated = onCalibrated ?? null;
  }, [engine, onSecond, onCalibrated]);

  const stop = useCallback(() => {
    stopLoopRef.current?.();
    stopLoopRef.current = null;
    engine.flushSecond();
    stopStream(streamRef.current);
    streamRef.current = null;
    setStatus("idle");
  }, [engine]);

  const start = useCallback(
    async (video: HTMLVideoElement) => {
      setError(null);
      setStatus("camera");
      try {
        const stream = await openCamera();
        if (disposedRef.current) {
          stopStream(stream);
          return;
        }
        streamRef.current = stream;
        video.srcObject = stream;
        await video.play().catch(() => undefined);
        setStatus("model");
        const landmarker = await loadFaceLandmarker();
        if (disposedRef.current) return;
        stopLoopRef.current?.();
        stopLoopRef.current = startDetectionLoop(landmarker, video, env.faceFps, (raw) => {
          engine.handle(raw);
          setSnap(engine.snapshot());
        });
        setStatus("running");
      } catch (e) {
        stopStream(streamRef.current);
        streamRef.current = null;
        setError(mapCameraError(e));
        setStatus("error");
      }
    },
    [engine],
  );

  useEffect(() => {
    disposedRef.current = false;
    return () => {
      disposedRef.current = true;
      stopLoopRef.current?.();
      stopLoopRef.current = null;
      engine.flushSecond();
      stopStream(streamRef.current);
      streamRef.current = null;
    };
  }, [engine]);

  return { status, error, snap, start, stop, engine };
}

export function useFaceBaseline(patientId: string | null) {
  const [baseline, setBaseline] = useState<FaceBaseline | null>(null);
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    if (!patientId) return;
    setBaseline(loadBaseline(patientId));
    setLoaded(true);
  }, [patientId]);
  const save = useCallback((b: FaceBaseline) => {
    saveBaseline(b);
    setBaseline(b);
  }, []);
  const clear = useCallback(() => {
    if (patientId) clearBaseline(patientId);
    setBaseline(null);
  }, [patientId]);
  return { baseline, loaded, save, clear };
}

// Browser TTS fallback for instructions (no server call). Prefers an Uzbek voice, then Turkish
// (reads Latin Uzbek acceptably), else the default voice.
export function speak(text: string) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  try {
    const synth = window.speechSynthesis;
    synth.cancel();
    const u = new SpeechSynthesisUtterance(text);
    const voices = synth.getVoices();
    const pick =
      voices.find((v) => v.lang.toLowerCase().startsWith("uz")) ??
      voices.find((v) => v.lang.toLowerCase().startsWith("tr")) ??
      null;
    if (pick) u.voice = pick;
    u.lang = pick?.lang ?? "uz-UZ";
    u.rate = 0.9;
    synth.speak(u);
  } catch {
    // speech is optional
  }
}

export function stopSpeaking() {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    try {
      window.speechSynthesis.cancel();
    } catch {
      // ignore
    }
  }
}
