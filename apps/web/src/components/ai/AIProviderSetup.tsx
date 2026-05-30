"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BrainCircuit,
  CheckCircle2,
  Cpu,
  Download,
  KeyRound,
  Loader2,
  PlugZap,
  RotateCw,
  Server,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import {
  AI_CONFIG_CHANGED_EVENT,
  clearStoredAIConfig,
  describeAIConfig,
  getStoredAIConfig,
  providerLabel,
  setStoredAIConfig,
  type AIProviderConfig,
  type AIProviderId,
  type AIProviderMode,
} from "@/lib/ai/config";
import {
  createAIProvider,
  FALLBACK_AI_PROVIDERS,
  listAIProviderDescriptors,
  pullOllamaModel,
  type AIProviderDescriptor,
  type ModelInfo,
  type ProviderValidationResult,
} from "@/lib/ai/providers";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { HelpTooltip, TooltipProvider } from "@/components/ui/tooltip";

const NO_MODEL = "__no_model__";

export function AIProviderSetup({
  compact = false,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  const [descriptors, setDescriptors] = useState<AIProviderDescriptor[]>(FALLBACK_AI_PROVIDERS);
  const [mode, setMode] = useState<AIProviderMode>("local");
  const [providerId, setProviderId] = useState<AIProviderId>("ollama");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [validation, setValidation] = useState<ProviderValidationResult | null>(null);
  const [loading, setLoading] = useState<"validate" | "models" | "pull" | null>(null);
  const [pullModel, setPullModel] = useState("qwen2.5:7b-instruct");
  const [pullConfirmed, setPullConfirmed] = useState(false);

  useEffect(() => {
    const stored = getStoredAIConfig();
    if (stored) {
      setMode(stored.mode);
      setProviderId(stored.providerId);
      setApiKey(stored.apiKey ?? "");
      setBaseUrl(stored.baseUrl ?? "");
      setModel(stored.model ?? "");
    }
    void listAIProviderDescriptors().then(setDescriptors);
  }, []);

  const providerOptions = useMemo(
    () =>
      descriptors.filter((provider) =>
        mode === "api" ? provider.mode === "api" : provider.mode === "local",
      ),
    [descriptors, mode],
  );

  const descriptor =
    descriptors.find((provider) => provider.id === providerId) ?? providerOptions[0];
  const recommendedModels = useMemo(() => descriptor?.recommendedModels ?? [], [descriptor]);
  const availableModels = useMemo(
    () => (models.length > 0 ? models : recommendedModels),
    [models, recommendedModels],
  );
  const isOllama = providerId === "ollama";
  const requiresApiKey = descriptor?.requiresApiKey ?? false;

  useEffect(() => {
    if (providerOptions.length === 0) return;
    if (!providerOptions.some((provider) => provider.id === providerId)) {
      applyProvider(providerOptions[0]);
    }
  }, [providerId, providerOptions]);

  useEffect(() => {
    if (models.length === 0 && recommendedModels.length > 0) {
      setModels(recommendedModels);
    }
  }, [models.length, recommendedModels]);

  const currentConfig = useMemo<AIProviderConfig>(
    () => ({
      providerId,
      mode,
      apiKey: apiKey.trim() || undefined,
      baseUrl: baseUrl.trim() || undefined,
      model: model.trim() || undefined,
    }),
    [apiKey, baseUrl, mode, model, providerId],
  );

  function applyProvider(provider: AIProviderDescriptor) {
    setProviderId(provider.id);
    setBaseUrl(provider.defaultBaseUrl ?? "");
    setModel(provider.recommendedModels[0]?.id ?? "");
    setModels(provider.recommendedModels);
    setValidation(null);
  }

  function handleModeChange(nextMode: AIProviderMode) {
    setMode(nextMode);
    const nextProvider = descriptors.find((provider) => provider.mode === nextMode);
    if (nextProvider) applyProvider(nextProvider);
  }

  async function handleValidate() {
    if (requiresApiKey && !apiKey.trim()) {
      toast.error("Introduce una API key para validar este proveedor.");
      return;
    }
    setLoading("validate");
    try {
      const provider = createAIProvider(currentConfig, descriptor);
      const result = await provider.validateConnection();
      setValidation(result);
      if (result.models.length > 0) {
        setModels(result.models);
        if (!model.trim()) setModel(result.models[0].id);
      }
      if (result.ok) {
        toast.success("Proveedor de IA validado");
      } else {
        toast.error(result.message);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "No se pudo validar el proveedor.";
      setValidation({ ok: false, providerId, message, models: [] });
      toast.error(message);
    } finally {
      setLoading(null);
    }
  }

  async function handleListModels() {
    setLoading("models");
    try {
      const provider = createAIProvider(currentConfig, descriptor);
      const listedModels = await provider.listModels();
      setModels(listedModels.length > 0 ? listedModels : recommendedModels);
      if (!model.trim()) {
        const firstModel = listedModels[0] ?? recommendedModels[0];
        if (firstModel) setModel(firstModel.id);
      }
      toast.success(
        listedModels.length > 0
          ? "Modelos disponibles actualizados"
          : "Usando modelos recomendados",
      );
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudieron listar modelos.");
    } finally {
      setLoading(null);
    }
  }

  function handleSave() {
    if (requiresApiKey && !apiKey.trim()) {
      toast.error("La clave API es obligatoria para este proveedor.");
      return;
    }
    if (providerId !== "mock" && !model.trim()) {
      toast.error("Elige o escribe un modelo antes de guardar.");
      return;
    }
    setStoredAIConfig(currentConfig);
    toast.success("Configuracion de IA guardada para esta sesion");
  }

  async function handlePullModel() {
    if (!pullConfirmed) {
      toast.error("Confirma explicitamente la descarga del modelo.");
      return;
    }
    setLoading("pull");
    try {
      await pullOllamaModel(pullModel, true);
      toast.success("Descarga de modelo solicitada en Ollama");
      await handleListModels();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo descargar el modelo.");
    } finally {
      setLoading(null);
    }
  }

  return (
    <TooltipProvider delayDuration={150}>
      <Card className={cn("relative overflow-hidden border-abacos-red-soft/80", className)}>
        <div className="absolute inset-x-0 top-0 h-1 bg-[linear-gradient(90deg,#B20D22,#1F5EA8,#4C9A4B,#E6B72E)]" />
        <CardHeader className={compact ? "p-4" : undefined}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-abacos-red-dark">
                Motor de IA
              </p>
              <CardTitle className="mt-1 flex items-center gap-2">
                <BrainCircuit className="h-4 w-4 text-abacos-red" aria-hidden />
                API propia u Ollama local
              </CardTitle>
            </div>
            <HelpTooltip label="La clave se guarda solo en sessionStorage del navegador y viaja al backend en una cabecera efimera para el pipeline. No se persiste en base de datos." />
          </div>
        </CardHeader>
        <CardContent className={cn("grid gap-4", compact ? "p-4 pt-0" : undefined)}>
          <div className="grid grid-cols-2 gap-2 rounded-lg border border-border bg-abacos-light p-1">
            <ModeButton
              active={mode === "api"}
              icon={KeyRound}
              label="API"
              onClick={() => handleModeChange("api")}
            />
            <ModeButton
              active={mode === "local"}
              icon={Cpu}
              label="Local"
              onClick={() => handleModeChange("local")}
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="grid gap-1.5 text-sm font-semibold text-abacos-black">
              Proveedor
              <Select
                value={providerId}
                onValueChange={(value) => {
                  const next = descriptors.find((provider) => provider.id === value);
                  if (next) applyProvider(next);
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {providerOptions.map((provider) => (
                    <SelectItem key={provider.id} value={provider.id}>
                      {provider.displayName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </label>

            <label className="grid gap-1.5 text-sm font-semibold text-abacos-black">
              Modelo
              <Select
                value={model || NO_MODEL}
                onValueChange={(value) => setModel(value === NO_MODEL ? "" : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Elegir modelo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NO_MODEL}>Elegir despues</SelectItem>
                  {availableModels.map((item) => (
                    <SelectItem key={item.id} value={item.id}>
                      {item.displayName || item.id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </label>
          </div>

          {requiresApiKey ? (
            <label className="grid gap-1.5 text-sm font-semibold text-abacos-black">
              API key
              <Input
                type="password"
                autoComplete="off"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="Pega aqui tu clave del proveedor"
              />
            </label>
          ) : null}

          {providerId === "openai_compatible" || isOllama ? (
            <label className="grid gap-1.5 text-sm font-semibold text-abacos-black">
              Endpoint
              <Input
                value={baseUrl}
                onChange={(event) => setBaseUrl(event.target.value)}
                placeholder={
                  isOllama ? "http://localhost:11434" : "https://tu-endpoint-compatible/v1"
                }
              />
            </label>
          ) : null}

          <div className="grid gap-2 sm:grid-cols-[1fr_auto_auto]">
            <Input
              value={model}
              onChange={(event) => setModel(event.target.value)}
              placeholder="Modelo elegido o nombre manual"
              aria-label="Modelo elegido o nombre manual"
            />
            <Button
              type="button"
              variant="outline"
              onClick={handleListModels}
              disabled={loading !== null}
            >
              {loading === "models" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RotateCw className="h-4 w-4" />
              )}
              Modelos
            </Button>
            <Button type="button" onClick={handleValidate} disabled={loading !== null}>
              {loading === "validate" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <PlugZap className="h-4 w-4" />
              )}
              Validar
            </Button>
          </div>

          {validation ? (
            <div
              className={cn(
                "flex items-start gap-2 rounded-lg border p-3 text-sm",
                validation.ok
                  ? "border-green-200 bg-green-50 text-abacos-green"
                  : "border-abacos-red-soft bg-abacos-red-soft text-abacos-red-dark",
              )}
            >
              {validation.ok ? (
                <CheckCircle2 className="mt-0.5 h-4 w-4" />
              ) : (
                <XCircle className="mt-0.5 h-4 w-4" />
              )}
              <p>{validation.message}</p>
            </div>
          ) : null}

          {isOllama ? (
            <div className="grid gap-3 rounded-lg border border-border bg-white p-3 text-sm">
              <div className="flex items-start gap-2">
                <Server className="mt-0.5 h-4 w-4 text-abacos-blue" />
                <p className="text-abacos-gray">
                  Ollama debe estar arrancado en el equipo donde corre el backend. En Vercel no
                  puede acceder al Ollama de tu ordenador; para modo local usa backend local.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {recommendedModels.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className="rounded-full border border-border px-2.5 py-1 text-xs font-semibold text-abacos-gray transition hover:border-abacos-red hover:text-abacos-red-dark"
                    onClick={() => {
                      setPullModel(item.id);
                      setModel(item.id);
                    }}
                  >
                    {item.displayName}
                  </button>
                ))}
              </div>
              <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
                <Input value={pullModel} onChange={(event) => setPullModel(event.target.value)} />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handlePullModel}
                  disabled={loading !== null}
                >
                  {loading === "pull" ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="h-4 w-4" />
                  )}
                  Descargar
                </Button>
              </div>
              <label className="flex items-start gap-2 text-xs text-abacos-gray">
                <input
                  type="checkbox"
                  className="mt-0.5 h-4 w-4 accent-abacos-red"
                  checked={pullConfirmed}
                  onChange={(event) => setPullConfirmed(event.target.checked)}
                />
                Confirmo que quiero descargar este modelo en mi entorno local. Puede ocupar varios
                GB.
              </label>
            </div>
          ) : null}

          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border pt-3">
            <Badge variant={currentConfig.providerId === "mock" ? "gray" : "blue"}>
              {providerLabel(currentConfig.providerId)}
              {currentConfig.model ? ` · ${currentConfig.model}` : ""}
            </Badge>
            <div className="flex gap-2">
              <Button type="button" variant="ghost" onClick={clearStoredAIConfig}>
                Usar mock
              </Button>
              <Button type="button" onClick={handleSave}>
                <ShieldCheck className="h-4 w-4" />
                Guardar sesion
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </TooltipProvider>
  );
}

export function AIProviderStatusDialog() {
  const [config, setConfig] = useState<AIProviderConfig | null>(null);

  useEffect(() => {
    const sync = () => setConfig(getStoredAIConfig());
    sync();
    window.addEventListener(AI_CONFIG_CHANGED_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(AI_CONFIG_CHANGED_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="max-w-[180px] px-2 sm:px-3"
          aria-label="Configurar IA"
        >
          <BrainCircuit className="h-4 w-4 shrink-0" aria-hidden />
          <span className="hidden truncate sm:inline">{describeAIConfig(config)}</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configuracion del motor de IA</DialogTitle>
          <DialogDescription>
            Elige API propia u Ollama local. El pipeline usara esta configuracion solo durante esta
            sesion.
          </DialogDescription>
        </DialogHeader>
        <AIProviderSetup compact />
      </DialogContent>
    </Dialog>
  );
}

function ModeButton({
  active,
  icon: Icon,
  label,
  onClick,
}: {
  active: boolean;
  icon: typeof KeyRound;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={cn(
        "flex h-10 items-center justify-center gap-2 rounded-md text-sm font-semibold transition",
        active
          ? "bg-white text-abacos-red-dark shadow-[0_10px_28px_rgba(178,13,34,0.14)]"
          : "text-abacos-gray hover:bg-white/70 hover:text-abacos-black",
      )}
      onClick={onClick}
    >
      <Icon className="h-4 w-4" aria-hidden />
      {label}
    </button>
  );
}
