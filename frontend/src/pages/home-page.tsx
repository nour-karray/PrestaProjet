import { useCallback, useEffect, useState } from "react";

type HealthState = "loading" | "available" | "unavailable";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8080";

export default function Home() {
  const [healthState, setHealthState] = useState<HealthState>("loading");

  const checkBackend = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/health`, { cache: "no-store" });
      const payload: unknown = await response.json();
      const isHealthy =
        response.ok &&
        typeof payload === "object" &&
        payload !== null &&
        "status" in payload &&
        payload.status === "ok";

      setHealthState(isHealthy ? "available" : "unavailable");
    } catch {
      setHealthState("unavailable");
    }
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void checkBackend();
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [checkBackend]);

  const retryBackendCheck = () => {
    setHealthState("loading");
    void checkBackend();
  };

  const status = {
    loading: {
      label: "Vérification en cours…",
      detail: "Connexion au service backend.",
      color: "bg-blue-50 text-blue-700 border-blue-200",
      dot: "bg-blue-500 animate-pulse",
    },
    available: {
      label: "Backend disponible",
      detail: "Le frontend communique correctement avec l’API.",
      color: "bg-green-50 text-green-800 border-green-200",
      dot: "bg-green-500",
    },
    unavailable: {
      label: "Backend indisponible",
      detail: "Vérifiez que le service Spring Boot est démarré sur le port 8080.",
      color: "bg-red-50 text-red-800 border-red-200",
      dot: "bg-red-500",
    },
  }[healthState];

  return (
    <main className="min-h-screen p-6 md:p-10">
      <div className="mx-auto grid min-h-[calc(100vh-5rem)] max-w-6xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl md:grid-cols-[18rem_1fr]">
        <aside className="bg-[var(--navy)] p-7 text-white">
          <div className="flex items-center gap-3 text-lg font-bold">
            <span className="grid size-10 place-items-center rounded-xl bg-white/10 text-xl">
              ◇
            </span>
            <span>
              Gestion
              <br />
              Formations
            </span>
          </div>
          <p className="mt-10 text-sm leading-6 text-blue-100">
            Initialisation technique de la plateforme de gestion des formations
            professionnelles.
          </p>
          <div className="mt-8 rounded-xl border border-white/10 bg-white/5 p-4 text-sm">
            <p className="font-semibold">Lot 1</p>
            <p className="mt-1 text-blue-100">Socle frontend et backend</p>
          </div>
        </aside>

        <section className="flex items-center p-7 md:p-14">
          <div className="w-full max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--primary)]">
              Gestion Formations
            </p>
            <h1 className="mt-3 text-3xl font-bold tracking-tight md:text-5xl">
              Le socle de l’application est prêt.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-slate-600">
              Cette page contrôle en temps réel la disponibilité de l’API Spring Boot.
            </p>

            <div className={`mt-9 rounded-xl border p-5 ${status.color}`} role="status">
              <div className="flex items-start gap-3">
                <span className={`mt-1.5 size-2.5 rounded-full ${status.dot}`} />
                <div>
                  <p className="font-semibold">{status.label}</p>
                  <p className="mt-1 text-sm opacity-80">{status.detail}</p>
                </div>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={retryBackendCheck}
                disabled={healthState === "loading"}
                className="rounded-lg bg-[var(--primary)] px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-wait disabled:opacity-60"
              >
                Vérifier à nouveau
              </button>
              <code className="rounded-lg bg-slate-100 px-4 py-3 text-xs text-slate-600">
                GET {apiUrl}/health
              </code>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
