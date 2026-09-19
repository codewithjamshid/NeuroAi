"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { speakUz, stopSpeaking as stopAudio, warmUz } from "@/features/audio/useAudioPlayer";
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

// Instructions via Navoiy (POST /tts, cached), browser speechSynthesis only as the last resort.
// Each call cancels the previous utterance (shared player state), so instructions never stack.
export function speak(text: string) {
  void speakUz(text);
}

export function stopSpeaking() {
  stopAudio();
}

// Pre-synthesize the instruction phrases so the first one plays without the worker's cold delay.
export function warmInstructions(texts: string[]) {
  warmUz(texts);
}
