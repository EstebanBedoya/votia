/** Tactile pixel-art button. Solid bottom plane; "presses" 4px down on click. */

import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger";

const VARIANT: Record<Variant, string> = {
  primary: "",
  secondary: "pixel-btn-secondary",
  danger: "pixel-btn-danger",
};

export interface PixelButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export function PixelButton({
  variant = "primary",
  className = "",
  children,
  ...rest
}: PixelButtonProps) {
  return (
    <button
      className={`pixel-btn ${VARIANT[variant]} px-5 py-2 text-sm ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
