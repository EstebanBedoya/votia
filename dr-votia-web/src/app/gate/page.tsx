"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { PixelButton } from "@/components/PixelButton";
import { PixelPanel } from "@/components/PixelPanel";

export default function GatePage() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await fetch("/api/gate", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ code }),
      });

      if (res.ok) {
        router.replace("/");
      } else {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "Código incorrecto.");
      }
    } catch {
      setError("No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-surface p-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="mb-6 text-center">
          <p className="font-display text-3xl font-bold text-coffee">🦜</p>
          <h1 className="font-display text-xl font-bold text-coffee">Dr. votIA</h1>
          <p className="mt-1 font-body text-sm text-on-surface-variant">
            Ingresá el código de acceso para continuar.
          </p>
        </div>

        <PixelPanel>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1">
              <label
                htmlFor="access-code"
                className="font-display text-xs font-bold uppercase tracking-wide text-secondary"
              >
                Código
              </label>
              <input
                id="access-code"
                type="password"
                autoComplete="off"
                autoFocus
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="••••••••"
                className="w-full border-4 border-coffee bg-surface-lowest px-3 py-2 font-mono text-sm text-coffee outline-none placeholder:text-outline-variant focus:border-secondary"
              />
            </div>

            {error && (
              <p className="border-4 border-error bg-error-container px-3 py-2 font-body text-sm text-error">
                {error}
              </p>
            )}

            <PixelButton type="submit" disabled={loading || !code.trim()} className="w-full">
              {loading ? "Verificando…" : "Entrar"}
            </PixelButton>
          </form>
        </PixelPanel>
      </div>
    </main>
  );
}
