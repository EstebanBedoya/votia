/**
 * A single chat message as a pixel-art bubble: rectangular, coffee border, with
 * an 8px triangular tail. User bubbles sit right (gold), Guacamayo left (parchment).
 */

import { Markdown } from "@/components/Markdown";
import { Sources } from "@/components/Sources";
import type { ChatMessage as Message } from "@/hooks/useChat";

export function ChatBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const who = isUser ? "VOS" : "GUACAMAYO";

  return (
    <div className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}>
      <span className="pixel-label mb-1 px-1 text-on-surface-variant">{who}</span>
      <div
        data-role={message.role}
        className={`relative max-w-[85%] border-[3px] border-coffee px-4 py-3 pixel-shadow ${
          isUser
            ? "bubble-tail-right bg-primary-container text-on-primary-container"
            : "bubble-tail-left bg-surface-lowest text-on-surface"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap break-words text-[15px] leading-relaxed">
            {message.content}
          </p>
        ) : (
          <div className="break-words">
            <Markdown>{message.content}</Markdown>
          </div>
        )}
        {message.fuentes && message.fuentes.length > 0 && (
          <Sources fuentes={message.fuentes} />
        )}
      </div>
    </div>
  );
}
