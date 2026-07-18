import { create } from "zustand";
import type { AIMessage } from "@/types/finance";

export type ChatStatus = "idle" | "submitted" | "streaming" | "error";

interface AIState {
  messages: AIMessage[];
  status: ChatStatus;
  contextSummary: string;
  /** Client-only alias reverse map. Never sent to the server. */
  piiMap: Record<string, string>;
  errorMessage: string | null;
}

interface AIActions {
  appendMessage: (m: AIMessage) => void;
  setStatus: (s: ChatStatus) => void;
  setError: (msg: string | null) => void;
  setContextSummary: (s: string) => void;
  mergePii: (aliases: Record<string, string>) => void;
  clearChat: () => void;
}

/** Hard cap on messages sent to the model per turn. */
export const MESSAGE_WINDOW = 20;

export const useAIStore = create<AIState & AIActions>((set) => ({
  messages: [],
  status: "idle",
  contextSummary: "",
  piiMap: {},
  errorMessage: null,
  appendMessage: (m) => set((s) => ({ messages: [...s.messages, m].slice(-200) })),
  setStatus: (status) => set({ status }),
  setError: (errorMessage) => set({ errorMessage }),
  setContextSummary: (contextSummary) => set({ contextSummary }),
  mergePii: (aliases) => set((s) => ({ piiMap: { ...s.piiMap, ...aliases } })),
  clearChat: () =>
    set({
      messages: [],
      status: "idle",
      contextSummary: "",
      piiMap: {},
      errorMessage: null,
    }),
}));
