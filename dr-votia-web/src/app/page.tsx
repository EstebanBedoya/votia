import Image from "next/image";
import Link from "next/link";

import { PixelButton } from "@/components/PixelButton";

export default function Home() {
  return (
    <main className="grid min-h-screen place-items-center p-4">
      <div className="pixel-window w-full max-w-2xl p-8 text-center md:p-12">
        <Image
          src="/art/guacamayo.png"
          alt="Guacamayo"
          width={248}
          height={330}
          priority
          className="pixelated mx-auto mb-6 w-40 drop-shadow-[4px_4px_0_rgba(0,0,0,0.25)]"
        />

        <h1
          className="font-display text-4xl font-bold text-secondary md:text-5xl"
          style={{ textShadow: "3px 3px 0 var(--color-gold)" }}
        >
          Dr. votIA
        </h1>
        <p className="mx-auto mt-4 max-w-md text-on-surface-variant">
          Análisis empírico de propuestas electorales — Colombia 2026. Guiado por
          Guacamayo, tu asistente cultural pixel-art.
        </p>

        <nav className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Link href="/chat">
            <PixelButton className="px-6 py-3 text-base">Chat con Guacamayo</PixelButton>
          </Link>
          <Link href="/radar">
            <PixelButton variant="secondary" className="px-6 py-3 text-base">
              Radar comparativo
            </PixelButton>
          </Link>
        </nav>
      </div>
    </main>
  );
}
