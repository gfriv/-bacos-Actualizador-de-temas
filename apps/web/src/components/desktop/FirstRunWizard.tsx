"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { CheckCircle2, Cpu, HardDrive, Laptop, Loader2, Server, WandSparkles } from "lucide-react";
import { AIProviderSetup } from "@/components/ai/AIProviderSetup";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type HardwareProfile = Awaited<ReturnType<NonNullable<Window["abacosDesktop"]>["detectHardware"]>>;
type ModelRecommendation = Awaited<
  ReturnType<NonNullable<Window["abacosDesktop"]>["recommendModels"]>
>[number];
type OllamaStatus = Awaited<ReturnType<NonNullable<Window["abacosDesktop"]>["detectOllama"]>>;

export function FirstRunWizard() {
  const [isDesktop, setIsDesktop] = useState(false);
  const [completed, setCompleted] = useState(true);
  const [step, setStep] = useState(0);
  const [hardware, setHardware] = useState<HardwareProfile | null>(null);
  const [recommendations, setRecommendations] = useState<ModelRecommendation[]>([]);
  const [ollama, setOllama] = useState<OllamaStatus | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  useEffect(() => {
    const desktop = window.abacosDesktop;
    if (!desktop) return;
    setIsDesktop(true);
    void desktop.getConfig().then((config) => {
      setCompleted(Boolean(config.firstRun?.completed));
    });
  }, []);

  if (!isDesktop || completed) return null;

  async function runLocalDiagnostic() {
    const desktop = window.abacosDesktop;
    if (!desktop) return;
    setLoading("diagnostic");
    try {
      const detected = await desktop.detectHardware();
      setHardware(detected);
      setRecommendations(await desktop.recommendModels(detected));
      setOllama(await desktop.detectOllama());
      setStep(2);
    } finally {
      setLoading(null);
    }
  }

  async function finishWizard(aiMode: "api" | "local") {
    const desktop = window.abacosDesktop;
    if (!desktop) return;
    await desktop.setConfig({
      firstRun: {
        completed: true,
        aiMode,
        providerId: aiMode === "local" ? "ollama" : "api"
      }
    });
    setCompleted(true);
  }

  return (
    <Card className="border-abacos-red/25 bg-white/92 shadow-soft">
      <CardHeader className="space-y-2">
        <div className="flex items-center gap-2">
          <Badge className="bg-abacos-red text-white">Escritorio</Badge>
          <Badge variant="outline">Primer arranque</Badge>
        </div>
        <CardTitle>Configura Ábacos IA en este ordenador</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {step === 0 ? (
          <>
            <p className="text-sm leading-6 text-abacos-gray">
              Esta versión local arranca el backend en este equipo y permite elegir entre API propia
              o IA local con Ollama. La revisión docente sigue siendo obligatoria antes de consolidar.
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              <ModeButton
                icon={<Server className="h-5 w-5" />}
                title="Usar mi propia API"
                description="Mayor calidad y modelos gestionados por proveedor. Requiere clave API."
                onClick={() => setStep(1)}
              />
              <ModeButton
                icon={<Laptop className="h-5 w-5" />}
                title="Usar IA local"
                description="Más privacidad operativa. Depende de RAM, CPU/GPU y espacio disponible."
                onClick={runLocalDiagnostic}
                loading={loading === "diagnostic"}
              />
            </div>
          </>
        ) : null}

        {step === 1 ? (
          <div className="space-y-4">
            <AIProviderSetup compact />
            <p className="text-xs leading-5 text-abacos-gray">
              En modo API, los fragmentos necesarios pueden enviarse al proveedor seleccionado. No
              uses documentos reales sin base legal, contrato y revisión RGPD.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setStep(0)}>
                Volver
              </Button>
              <Button onClick={() => finishWizard("api")}>Empezar</Button>
            </div>
          </div>
        ) : null}

        {step === 2 ? (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <Metric icon={<Cpu className="h-4 w-4" />} label="RAM" value={`${hardware?.totalRamGB ?? "-"} GB`} />
              <Metric icon={<WandSparkles className="h-4 w-4" />} label="GPU" value={hardware?.gpuModel ?? "No detectada"} />
              <Metric icon={<HardDrive className="h-4 w-4" />} label="Disco" value={`${hardware?.diskFreeGB ?? "-"} GB libres`} />
            </div>
            <div className="rounded-md border border-border bg-abacos-light p-3 text-sm">
              <div className="flex items-center gap-2 font-semibold text-abacos-black">
                <CheckCircle2 className={cn("h-4 w-4", ollama?.running ? "text-abacos-green" : "text-abacos-yellow")} />
                Ollama: {ollama?.running ? "disponible" : "no disponible"}
              </div>
              {ollama?.error ? <p className="mt-1 text-xs text-abacos-gray">{ollama.error}</p> : null}
            </div>
            <div className="space-y-2">
              <p className="text-sm font-semibold text-abacos-black">Modelos recomendados</p>
              {recommendations.slice(0, 4).map((item) => (
                <div key={item.modelName} className="rounded-md border border-border bg-white p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-semibold">{item.displayName}</span>
                    <Badge variant={item.suitability === "not_recommended" ? "outline" : "default"}>
                      {item.suitability}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs leading-5 text-abacos-gray">{item.reason}</p>
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setStep(0)}>
                Volver
              </Button>
              <Button onClick={() => finishWizard("local")}>Empezar</Button>
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function ModeButton({
  icon,
  title,
  description,
  loading,
  onClick
}: {
  icon: ReactNode;
  title: string;
  description: string;
  loading?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-md border border-border bg-white p-4 text-left transition hover:-translate-y-0.5 hover:border-abacos-red/40 hover:shadow-soft"
    >
      <span className="mb-3 grid h-10 w-10 place-items-center rounded-md bg-abacos-red-soft text-abacos-red-dark">
        {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : icon}
      </span>
      <span className="block font-semibold text-abacos-black">{title}</span>
      <span className="mt-1 block text-sm leading-5 text-abacos-gray">{description}</span>
    </button>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-white p-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase text-abacos-gray">
        {icon}
        {label}
      </div>
      <p className="mt-2 truncate text-sm font-semibold text-abacos-black">{value}</p>
    </div>
  );
}
