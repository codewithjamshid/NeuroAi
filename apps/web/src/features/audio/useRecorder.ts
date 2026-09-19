"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { useAudioStore } from "./store";
import type { AudioErrorCode, RecorderState } from "./types";

// DEMO_SCOPE: MediaRecorder webm/opus, energy VAD — 1.2 s silence → stop, hard stop 15 s.
export const SILENCE_MS = 1200;
export const MAX_MS = 15_000;
const TICK_MS = 50;
const CALIBRATION_TICKS = 6; // first 300 ms estimate the noise floor

const MIME_CANDIDATES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/ogg;codecs=opus",
];

export function pickMimeType(): string {
  if (typeof MediaRecorder === "undefined") return "";
  return MIME_CANDIDATES.find((m) => MediaRecorder.isTypeSupported(m)) ?? "";
}

export function audioFileName(blob: Blob): string {
  if (blob.type.includes("mp4")) return "audio.mp4";
  if (blob.type.includes("ogg")) return "audio.ogg";
  return "audio.webm";
}

function mapMicError(e: unknown): AudioErrorCode {
  const name = e instanceof DOMException ? e.name : "";
  if (name === "NotAllowedError" || name === "SecurityError" || name === "PermissionDeniedError") {
    return "mic_denied";
  }
  if (
    name === "NotFoundError" ||
    name === "DevicesNotFoundError" ||
    name === "OverconstrainedError"
  ) {
    return "no_mic";
  }
  return "not_supported";
}

export type Recorder = {
  state: RecorderState;
  error: AudioErrorCode | null;
  level: number; // 0..1 live RMS (for the mic animation)
  supported: boolean;
  start: () => Promise<Blob | null>;
  stop: () => void;
};

export function useRecorder(opts?: { silenceMs?: number; maxMs?: number }): Recorder {
  const silenceMs = opts?.silenceMs ?? SILENCE_MS;
  const maxMs = opts?.maxMs ?? MAX_MS;
  const [state, setState] = useState<RecorderState>("idle");
  const [error, setError] = useState<AudioErrorCode | null>(null);
  const [level, setLevel] = useState(0);
  const setAudioStatus = useAudioStore((s) => s.setStatus);
  const setAudioError = useAudioStore((s) => s.setError);

  const recRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const timerRef = useRef<number | null>(null);

  const cleanup = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    streamRef.current?.getTracks().forEach((tr) => tr.stop());
    streamRef.current = null;
    void ctxRef.current?.close().catch(() => undefined);
    ctxRef.current = null;
    recRef.current = null;
    setLevel(0);
  }, []);

  const stop = useCallback(() => {
    const rec = recRef.current;
    if (rec && rec.state !== "inactive") rec.stop();
  }, []);

  const supported =
    typeof window !== "undefined" &&
    typeof MediaRecorder !== "undefined" &&
    Boolean(navigator.mediaDevices?.getUserMedia);

  const start = useCallback((): Promise<Blob | null> => {
    return new Promise<Blob | null>((resolve) => {
      void (async () => {
        if (recRef.current) {
          resolve(null);
          return;
        }
        if (!supported) {
          setError("not_supported");
          setAudioError("not_supported");
          resolve(null);
          return;
        }
        let stream: MediaStream;
        try {
          stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        } catch (e) {
          const code = mapMicError(e);
          setError(code);
          setAudioError(code);
          resolve(null);
          return;
        }
        setError(null);
        setAudioError(null);
        streamRef.current = stream;

        const mimeType = pickMimeType();
        const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
        recRef.current = rec;
        const chunks: Blob[] = [];
        rec.ondataavailable = (ev) => {
          if (ev.data.size > 0) chunks.push(ev.data);
        };
        rec.onstop = () => {
          const blob = new Blob(chunks, { type: rec.mimeType || mimeType || "audio/webm" });
          cleanup();
          setState("processing");
          resolve(blob);
        };

        // Energy VAD via AnalyserNode.
        let analyser: AnalyserNode | null = null;
        let buf: Float32Array<ArrayBuffer> | null = null;
        try {
          const ctx = new AudioContext();
          ctxRef.current = ctx;
          const src = ctx.createMediaStreamSource(stream);
          analyser = ctx.createAnalyser();
          analyser.fftSize = 1024;
          src.connect(analyser);
          buf = new Float32Array(analyser.fftSize);
        } catch {
          analyser = null; // no VAD → hard stop only
        }

        const startedAt = performance.now();
        let lastVoiceAt = startedAt;
        let speechStarted = false;
        let ticks = 0;
        let floor = 0;

        timerRef.current = window.setInterval(() => {
          const now = performance.now();
          if (now - startedAt >= maxMs) {
            stop();
            return;
          }
          if (!analyser || !buf) return;
          analyser.getFloatTimeDomainData(buf);
          let sum = 0;
          for (let i = 0; i < buf.length; i++) sum += buf[i] * buf[i];
          const rms = Math.sqrt(sum / buf.length);
          setLevel(Math.min(1, rms * 8));
          ticks += 1;
          if (ticks <= CALIBRATION_TICKS) {
            floor = Math.max(floor, rms);
            return;
          }
          const threshold = Math.max(0.015, floor * 2.5);
          if (rms > threshold) {
            speechStarted = true;
            lastVoiceAt = now;
          } else if (speechStarted && now - lastVoiceAt >= silenceMs) {
            stop();
          }
        }, TICK_MS);

        rec.start(250);
        setState("listening");
        setAudioStatus("listening");
      })();
    });
  }, [cleanup, maxMs, setAudioError, setAudioStatus, silenceMs, stop, supported]);

  // Back to idle once the caller has consumed the blob (they set "thinking"/"speaking" themselves).
  useEffect(() => {
    if (state === "processing") {
      const id = window.setTimeout(() => setState("idle"), 0);
      return () => window.clearTimeout(id);
    }
  }, [state]);

  useEffect(() => cleanup, [cleanup]);

  return { state, error, level, supported, start, stop };
}
