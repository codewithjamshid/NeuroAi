"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { apiJson, mediaUrl } from "@/lib/api";

import { useAudioStore } from "./store";

// Navoiy first, browser voice last. Text without a tts_url → POST /tts (server keeps a sha1 wav
// cache) → play the wav; speechSynthesis reads the text only when the API has no audio or fails.
// One utterance at a time: every speak/stop supersedes whatever is playing or still being fetched.

const TTS_TIMEOUT_MS = 15_000; // worker ≈ 2–3.5 s cold; the cloud fallback is slower
const TTS_MAX_CHARS = 600; // TTSIn.text max_length

type TTSOut = { tts_url: string | null; provider: string };
type Outcome = "ended" | "failed" | "cancelled";
type SpeakHooks = { onFetch?: () => void; onStart?: () => void; onEnd?: () => void };

// text → tts_url; in-flight promises are cached too, so a burst of one phrase makes one request.
const urlCache = new Map<string, Promise<string | null>>();
let current: { el: HTMLAudioElement; cancel: () => void } | null = null;
let generation = 0; // bumped by every speak/stop: the newest call wins, stale ones exit quietly

function cleanText(text: string | null | undefined): string {
  let s = (text ?? "").replace(/\*\*/g, "").trim();
  if (s.length > TTS_MAX_CHARS) {
    const cut = s.lastIndexOf(" ", TTS_MAX_CHARS);
    s = s.slice(0, cut > 0 ? cut : TTS_MAX_CHARS);
  }
  return s;
}

function requestTtsUrl(text: string): Promise<string | null> {
  const hit = urlCache.get(text);
  if (hit) return hit;
  const pending = apiJson<TTSOut>("/tts", "POST", { text }, { timeoutMs: TTS_TIMEOUT_MS })
    .then((r) => r.tts_url || null)
    .catch(() => null)
    .then((url) => {
      if (!url) urlCache.delete(text); // no audio / error: not cached, the next call retries
      return url;
    });
  urlCache.set(text, pending);
  return pending;
}

function stopCurrent() {
  const c = current;
  current = null;
  if (c) {
    c.el.onended = null;
    c.el.onerror = null;
    c.el.pause();
    c.el.src = "";
    c.cancel();
  }
  if (typeof speechSynthesis !== "undefined") {
    try {
      speechSynthesis.cancel();
    } catch {
      // speech is optional
    }
  }
}

function playUrl(url: string): Promise<Outcome> {
  return new Promise((resolve) => {
    if (typeof Audio === "undefined") {
      resolve("failed");
      return;
    }
    const el = new Audio(mediaUrl(url));
    let settled = false;
    const settle = (outcome: Outcome) => {
      if (settled) return;
      settled = true;
      if (current?.el === el) current = null;
      resolve(outcome);
    };
    current = { el, cancel: () => settle("cancelled") };
    el.onended = () => settle("ended");
    el.onerror = () => settle("failed");
    el.play().catch(() => settle("failed"));
  });
}

// Last resort: no Uzbek voice ships with browsers; Turkish reads Latin Uzbek acceptably.
function speakBrowser(text: string): Promise<void> {
  return new Promise((resolve) => {
    if (typeof speechSynthesis === "undefined") {
      resolve();
      return;
    }
    try {
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "uz-UZ";
      u.rate = 0.85;
      const voice = speechSynthesis
        .getVoices()
        .find(
          (v) => v.lang.toLowerCase().startsWith("uz") || v.lang.toLowerCase().startsWith("tr"),
        );
      if (voice) u.voice = voice;
      u.onend = () => resolve();
      u.onerror = () => resolve();
      speechSynthesis.speak(u);
    } catch {
      resolve();
    }
  });
}

async function speakCore(
  url: string | null | undefined,
  text: string | null | undefined,
  hooks: SpeakHooks = {},
): Promise<void> {
  const my = ++generation;
  stopCurrent();
  const clean = cleanText(text);
  let target = url || null;
  if (!target && clean) {
    hooks.onFetch?.();
    target = await requestTtsUrl(clean);
    if (my !== generation) return; // superseded while waiting for the API
  }
  if (target) {
    hooks.onStart?.();
    const outcome = await playUrl(target);
    if (outcome === "cancelled" || my !== generation) return;
    if (outcome === "ended") {
      hooks.onEnd?.();
      return;
    }
    // "failed" (unreachable wav, autoplay blocked): fall through to the browser voice
  }
  if (clean) {
    hooks.onStart?.();
    await speakBrowser(clean);
    if (my !== generation) return;
  }
  hooks.onEnd?.();
}

// Non-hook callers (face-exercise instructions): same cache, same fallback, cancels the previous.
export function speakUz(text: string): Promise<void> {
  return speakCore(null, text);
}

export function stopSpeaking(): void {
  generation += 1;
  stopCurrent();
}

// Pre-synthesize phrases (sequentially, in the background) so the first playback is not delayed.
export function warmUz(texts: string[]): void {
  void (async () => {
    for (const text of texts) {
      const clean = cleanText(text);
      if (clean) await requestTtsUrl(clean);
    }
  })();
}

export function useAudioPlayer() {
  const [playing, setPlaying] = useState(false);
  const setStatus = useAudioStore((s) => s.setStatus);

  const hooks = useMemo<SpeakHooks>(
    () => ({
      onFetch: () => setStatus("thinking"),
      onStart: () => {
        setPlaying(true);
        setStatus("speaking");
      },
      onEnd: () => {
        setPlaying(false);
        setStatus("idle");
      },
    }),
    [setStatus],
  );

  const stop = useCallback(() => {
    stopSpeaking();
    hooks.onEnd?.();
  }, [hooks]);

  // play(url, fallbackText): the wav when given; otherwise fallbackText via /tts, then the browser.
  const play = useCallback(
    (url: string | null | undefined, fallbackText?: string): Promise<void> =>
      speakCore(url, fallbackText, hooks),
    [hooks],
  );

  const speakText = useCallback(
    (text: string): Promise<void> => speakCore(null, text, hooks),
    [hooks],
  );

  useEffect(() => stop, [stop]);

  return { play, speakText, stop, playing };
}
