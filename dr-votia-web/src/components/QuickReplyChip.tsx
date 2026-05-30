/** Suggested prompt chip. Clicking it fires the question through the chat. */

export interface QuickReplyChipProps {
  text: string;
  onPick: (text: string) => void;
  disabled?: boolean;
}

export function QuickReplyChip({ text, onPick, disabled }: QuickReplyChipProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onPick(text)}
      className="pixel-chip px-3 py-1.5 text-left normal-case hover:brightness-105 disabled:opacity-50"
    >
      {text}
    </button>
  );
}
