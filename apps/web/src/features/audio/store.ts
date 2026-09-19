import { create } from "zustand";

import type { AudioErrorCode, AudioStatus } from "./types";

type AudioState = {
  status: AudioStatus;
  error: AudioErrorCode | null;
  setStatus: (status: AudioStatus) => void;
  setError: (error: AudioErrorCode | null) => void;
};

export const useAudioStore = create<AudioState>((set) => ({
  status: "idle",
  error: null,
  setStatus: (status) => set({ status }),
  setError: (error) => set({ error }),
}));
