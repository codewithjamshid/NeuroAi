"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { mediaUrl } from "@/lib/api";

import { useAudioStore } from "./store";

// TTS chain ends with "browser" (DEMO_SCOPE): no tts_url → speechSynthesis.
export function useAudioPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const setStatus = useAudioStore((s) => s.setStatus);

  const finish = useCallback(() => {
    setPlaying(false);
    setStatus("idle");
  }, [setStatus]);

  const stop = useCallback(() => {
    const a = audioRef.current;
    if (a) {
      a.pause();
      a.src = "";
      audioRef.current = null;
    }
    if (typeof speechSynthesis !== "undefined") speechSynthesis.cancel();
    finish();
  }, [finish]);

  const speakText = useCallback(
    (text: string): Promise<void> =>
      new Promise((resolve) => {
        if (typeof speechSynthesis === "undefined" || !text.trim()) {
          finish();
          resolve();
          return;
        }
        speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text.replace(/\*\*/g, ""));
        u.lang = "uz-UZ";
        u.rate = 0.85;
        const voice = speechSynthesis
          .getVoices()
          .find(
            (v) => v.lang.toLowerCase().startsWith("uz") || v.lang.toLowerCase().startsWith("tr"),
          );
        if (voice) u.voice = voice;
        u.onend = () => {
          finish();
          resolve();
        };
        u.onerror = () => {
          finish();
          resolve();
        };
        setPlaying(true);
        setStatus("speaking");
        speechSynthesis.speak(u);
      }),
    [finish, setStatus],
  );

  // play(url, fallbackText): autoplay the wav; on null/failure fall back to speechSynthesis.
  const play = useCallback(
    async (url: string | null | undefined, fallbackText?: string): Promise<void> => {
      stop();
      if (!url) {
        if (fallbackText) await speakText(fallbackText);
        return;
      }
      await new Promise<void>((resolve) => {
        const a = new Audio(mediaUrl(url));
        audioRef.current = a;
        let settled = false;
        const done = () => {
          if (settled) return;
          settled = true;
          finish();
          resolve();
        };
        const fallback = () => {
          if (settled) return;
          settled = true;
          audioRef.current = null;
          if (fallbackText) void speakText(fallbackText).then(resolve);
          else {
            finish();
            resolve();
          }
        };
        a.onended = done;
        a.onerror = fallback;
        setPlaying(true);
        setStatus("speaking");
        a.play().catch(fallback);
      });
    },
    [finish, setStatus, speakText, stop],
  );

  useEffect(() => stop, [stop]);

  return { play, speakText, stop, playing };
}
