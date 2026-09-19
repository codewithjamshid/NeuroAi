import { create } from "zustand";

// Pattern placeholder for global client state (TZ §9.3: session, state, audio stores follow).
export type Hand = "left" | "right";

type UiState = {
  hand: Hand;
  setHand: (hand: Hand) => void;
};

export const useUiStore = create<UiState>((set) => ({
  hand: "right",
  setHand: (hand) => set({ hand }),
}));
