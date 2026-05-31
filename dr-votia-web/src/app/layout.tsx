import type { Metadata } from "next";
import type { CSSProperties, ReactNode } from "react";
import { Space_Grotesk, Hanken_Grotesk, JetBrains_Mono } from "next/font/google";

import { artUrl } from "@/lib/assets";

import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "700"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const hankenGrotesk = Hanken_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-hanken-grotesk",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["500", "700"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Dr. votIA — Guacamayo AI",
  description: "Análisis empírico de propuestas electorales — Colombia 2026",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="es"
      className={`${spaceGrotesk.variable} ${hankenGrotesk.variable} ${jetbrainsMono.variable}`}
      style={
        {
          "--art-clouds": `url(${artUrl("clouds.png")})`,
          "--art-mountains": `url(${artUrl("mountains.png")})`,
        } as CSSProperties
      }
    >
      <body>{children}</body>
    </html>
  );
}
