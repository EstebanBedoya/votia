/**
 * Renders the assistant's markdown answers, themed to "Tierra Pixelada".
 * GFM enabled (tables, lists, strikethrough). Links open in a new tab.
 */

import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

const components: Components = {
  p: ({ children }) => <p className="my-2 first:mt-0 last:mb-0 leading-relaxed">{children}</p>,
  strong: ({ children }) => <strong className="font-bold text-coffee">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="font-medium text-secondary underline decoration-2 underline-offset-2 hover:text-tertiary"
    >
      {children}
    </a>
  ),
  ul: ({ children }) => <ul className="my-2 ml-4 list-disc space-y-1 marker:text-tertiary">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 ml-4 list-decimal space-y-1 marker:text-secondary">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  h1: ({ children }) => (
    <h3 className="font-display mb-1 mt-3 text-base font-bold uppercase text-secondary first:mt-0">{children}</h3>
  ),
  h2: ({ children }) => (
    <h4 className="font-display mb-1 mt-3 text-sm font-bold uppercase text-secondary first:mt-0">{children}</h4>
  ),
  h3: ({ children }) => (
    <h5 className="mb-1 mt-2 text-sm font-bold text-coffee first:mt-0">{children}</h5>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-4 border-gold bg-surface-low px-3 py-1.5 italic">{children}</blockquote>
  ),
  code: ({ className, children }) => {
    const isBlock = (className ?? "").includes("language-");
    if (isBlock) {
      return (
        <code className="block overflow-x-auto whitespace-pre border-2 border-coffee bg-surface-low p-2 font-mono text-[12px]">
          {children}
        </code>
      );
    }
    return (
      <code className="border border-coffee bg-surface-low px-1 font-mono text-[13px] text-tertiary">
        {children}
      </code>
    );
  },
  pre: ({ children }) => <pre className="my-2">{children}</pre>,
  hr: () => <hr className="my-3 border-t-2 border-dashed border-outline-variant" />,
  table: ({ children }) => (
    <div className="my-2 overflow-x-auto">
      <table className="w-full border-2 border-coffee text-sm">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-coffee bg-surface-high px-2 py-1 text-left font-mono text-xs uppercase">{children}</th>
  ),
  td: ({ children }) => <td className="border border-outline-variant px-2 py-1">{children}</td>,
};

export function Markdown({ children }: { children: string }) {
  return (
    <div className="text-[15px]">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {children}
      </ReactMarkdown>
    </div>
  );
}
