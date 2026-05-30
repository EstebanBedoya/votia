"use client";

/**
 * Chat state + transport. Talks to the same-origin BFF (/api/chat). The session
 * cookie is httponly and same-origin, so the browser sends/receives it on its own
 * (`credentials: "include"`) — no manual session handling here.
 */

import { useCallback, useState } from "react";

import type { Candidato, Source, Tema, Tipo } from "@/lib/types";

export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  role: ChatRole;
  content: string;
  /** Sources backing an assistant message. */
  fuentes?: Source[];
}

/** Optional retrieval filters mirrored from ChatRequest. */
export interface AskOptions {
  candidato?: Candidato;
  tema?: Tema;
  tipo?: Tipo;
  k?: number;
}

export interface UseChat {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  ask: (pregunta: string, opts?: AskOptions) => Promise<void>;
  reset: () => void;
}

export function useChat(): UseChat {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = useCallback(
    async (pregunta: string, opts: AskOptions = {}) => {
      const text = pregunta.trim();
      if (!text || loading) return;

      setError(null);
      setLoading(true);
      setMessages((prev) => [...prev, { role: "user", content: text }]);

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "content-type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ pregunta: text, ...opts }),
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data?.error ?? `Request failed (${res.status})`);
        }
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.respuesta, fuentes: data.fuentes },
        ]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unexpected error");
      } finally {
        setLoading(false);
      }
    },
    [loading],
  );

  const reset = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, ask, reset };
}
