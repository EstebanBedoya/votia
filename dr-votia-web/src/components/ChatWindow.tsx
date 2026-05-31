"use client";

/**
 * Central chat window — the hero of the design. Owns the conversation via useChat
 * (unchanged transport), renders bubbles, quick-reply chips, the candidate filter
 * and the sunken input with a tactile "ENVIAR" button.
 */

import { useEffect, useRef, useState } from "react";
import Image from "next/image";

import { ChatBubble } from "@/components/ChatBubble";
import { PixelButton } from "@/components/PixelButton";
import { PixelIcon } from "@/components/PixelIcon";
import { QuickReplyChip } from "@/components/QuickReplyChip";
import { useChat } from "@/hooks/useChat";
import { artUrl } from "@/lib/assets";
import { CANDIDATOS } from "@/lib/constants";
import type { Candidato } from "@/lib/types";

const SUGGESTIONS = [
  "¿Qué propone Fajardo en seguridad?",
  "Compará las propuestas de salud",
  "¿Cuál es el plan económico de Claudia López?",
  "Hablame de anticorrupción",
];

export function ChatWindow() {
  const { messages, loading, error, ask, reset } = useChat();
  const [input, setInput] = useState("");
  const [candidato, setCandidato] = useState<Candidato | "">("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  function send(text: string) {
    void ask(text, candidato ? { candidato } : undefined);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input;
    setInput("");
    send(text);
  }

  return (
    <section className="pixel-window flex h-full flex-col">
      {/* Window header */}
      <header className="flex items-center justify-between gap-3 border-b-4 border-coffee bg-surface-high px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 border-2 border-coffee bg-emerald" />
          <span className="font-display text-sm font-bold text-secondary">
            Guacamayo AI
          </span>
        </div>
        <div className="flex items-center gap-2">
          <select
            aria-label="Filtrar por candidato"
            value={candidato}
            onChange={(e) => setCandidato(e.target.value as Candidato | "")}
            className="pixel-input px-2 py-1 font-mono text-xs"
          >
            <option value="">Todos</option>
            {CANDIDATOS.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={reset}
            disabled={loading}
            aria-label="Limpiar conversación"
            className="inline-flex items-center gap-1 border-2 border-coffee bg-surface-low px-2 py-1 pixel-label transition-colors hover:bg-tertiary-container disabled:opacity-50"
          >
            <PixelIcon name="trash" size={14} /> Limpiar
          </button>
        </div>
      </header>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4 pixel-scroll"
      >
        {messages.length === 0 && !loading && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <Image
              src={artUrl("guacamayo.png")}
              alt="Guacamayo"
              width={120}
              height={160}
              className="pixelated w-20 drop-shadow-[4px_4px_0_rgba(0,0,0,0.25)]"
            />
            <p className="font-display text-base font-bold text-secondary">
              ¡Hola! Soy Guacamayo
            </p>
            <p className="max-w-sm text-sm text-on-surface-variant">
              Preguntame sobre las propuestas electorales de Colombia 2026.
            </p>
          </div>
        )}

        {messages.map((m, i) => (
          <ChatBubble key={i} message={m} />
        ))}

        {loading && (
          <div className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 animate-pulse border-2 border-coffee bg-gold" />
            <span className="pixel-label">Pensando…</span>
          </div>
        )}
        {error && (
          <p
            role="alert"
            className="border-[3px] border-coffee bg-error-container px-3 py-2 font-mono text-xs text-error"
          >
            Error: {error}
          </p>
        )}
      </div>

      {/* Quick replies */}
      {messages.length === 0 && (
        <div className="flex flex-wrap gap-2 border-t-4 border-coffee bg-surface-high px-4 py-3">
          {SUGGESTIONS.map((s) => (
            <QuickReplyChip key={s} text={s} onPick={send} disabled={loading} />
          ))}
        </div>
      )}

      {/* Input bar */}
      <form
        onSubmit={onSubmit}
        className="flex items-center gap-3 border-t-4 border-coffee bg-surface-container p-4"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe tu mensaje…"
          disabled={loading}
          className="pixel-input flex-1 px-3 py-2.5 text-sm"
        />
        <PixelButton
          type="submit"
          disabled={loading || !input.trim()}
          className="inline-flex items-center gap-2"
        >
          <PixelIcon name="send" size={16} /> Enviar
        </PixelButton>
      </form>
    </section>
  );
}
