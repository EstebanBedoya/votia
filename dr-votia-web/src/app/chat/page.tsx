/**
 * Chat page — the hero screen. Three-column pixel-art layout over the scenic
 * Andean background: data-collection panel · chat window · Guacamayo character.
 * All transport stays in the child components (useChat / useRadar unchanged).
 */

import { CharacterPanel } from "@/components/CharacterPanel";
import { ChatWindow } from "@/components/ChatWindow";
import { StatsPanel } from "@/components/StatsPanel";
import { TitleBar } from "@/components/TitleBar";

export default function ChatPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-[1200px] flex-col gap-4 p-4 md:p-8 lg:h-dvh lg:max-h-dvh lg:overflow-hidden">
      <TitleBar title="Guacamayo AI" />

      <div className="grid flex-1 grid-cols-1 gap-4 lg:min-h-0 lg:grid-cols-[280px_1fr_240px]">
        {/* Left: real radar data as a collection panel */}
        <div className="order-2 lg:order-1 lg:min-h-0">
          <StatsPanel />
        </div>

        {/* Center: the chat (messages scroll internally on desktop) */}
        <div className="order-1 min-h-[520px] lg:order-2 lg:min-h-0">
          <ChatWindow />
        </div>

        {/* Right: character */}
        <div className="order-3 lg:min-h-0 lg:overflow-y-auto lg:pixel-scroll">
          <CharacterPanel />
        </div>
      </div>
    </main>
  );
}
