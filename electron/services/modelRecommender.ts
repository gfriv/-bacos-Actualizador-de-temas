import type { HardwareProfile, ModelRecommendation } from "../types/desktop";

const CATALOG: ModelRecommendation[] = [
  {
    modelName: "qwen2.5:3b-instruct",
    displayName: "Qwen 2.5 3B Instruct",
    family: "qwen",
    minRamGB: 8,
    recommendedRamGB: 12,
    estimatedDownloadGB: 2.2,
    quality: "basic",
    speed: "fast",
    suitability: "safe_local",
    reason: "Modelo ligero para equipos modestos y pruebas de flujo documental.",
    warnings: ["Puede quedarse corto para documentos largos o análisis curricular fino."]
  },
  {
    modelName: "qwen2.5:7b-instruct",
    displayName: "Qwen 2.5 7B Instruct",
    family: "qwen",
    minRamGB: 16,
    recommendedRamGB: 24,
    estimatedDownloadGB: 4.7,
    quality: "medium",
    speed: "medium",
    suitability: "balanced",
    reason: "Buen equilibrio para análisis documental en español y tareas de razonamiento.",
    warnings: ["En CPU puede ser lento con temas extensos."]
  },
  {
    modelName: "gemma2:9b",
    displayName: "Gemma 2 9B",
    family: "gemma",
    minRamGB: 16,
    recommendedRamGB: 32,
    estimatedDownloadGB: 5.5,
    quality: "medium",
    speed: "medium",
    suitability: "balanced",
    reason: "Alternativa equilibrada para generación de recursos y resúmenes.",
    warnings: ["Requiere revisar especialmente normativa y fuentes."]
  },
  {
    modelName: "llama3.1:8b",
    displayName: "Llama 3.1 8B",
    family: "llama",
    minRamGB: 16,
    recommendedRamGB: 32,
    estimatedDownloadGB: 4.9,
    quality: "medium",
    speed: "medium",
    suitability: "balanced",
    reason: "Modelo generalista razonable para consolidación y recursos.",
    warnings: ["No sustituye búsqueda normativa ni validación docente."]
  },
  {
    modelName: "qwen2.5:14b-instruct",
    displayName: "Qwen 2.5 14B Instruct",
    family: "qwen",
    minRamGB: 32,
    recommendedRamGB: 64,
    estimatedDownloadGB: 9,
    quality: "high",
    speed: "slow",
    suitability: "advanced_local",
    reason: "Opción local avanzada para equipos con mucha RAM o GPU.",
    warnings: ["Descarga grande. No recomendable para portátiles con poca memoria."]
  }
];

export function recommendModels(profile: HardwareProfile): ModelRecommendation[] {
  const warnings: ModelRecommendation[] = [];
  if (profile.totalRamGB < 8) {
    warnings.push({
      modelName: "api",
      displayName: "API recomendada",
      family: "other",
      minRamGB: 0,
      recommendedRamGB: 0,
      quality: "high",
      speed: "fast",
      suitability: "api_recommended",
      reason: "El equipo tiene menos de 8 GB de RAM. Para documentos reales conviene usar API.",
      warnings: ["El modo local puede bloquearse o tardar demasiado."]
    });
  }

  const local = CATALOG.map((item) => adaptSuitability(item, profile)).filter(
    (item) => profile.totalRamGB >= item.minRamGB || item.suitability === "not_recommended"
  );
  return [...warnings, ...local].sort(rankRecommendation);
}

function adaptSuitability(
  recommendation: ModelRecommendation,
  profile: HardwareProfile
): ModelRecommendation {
  const diskWarning =
    profile.diskFreeGB !== undefined &&
    recommendation.estimatedDownloadGB !== undefined &&
    profile.diskFreeGB < recommendation.estimatedDownloadGB + 2
      ? `Espacio libre bajo: requiere aproximadamente ${recommendation.estimatedDownloadGB} GB.`
      : null;
  const ramWarning =
    profile.totalRamGB < recommendation.recommendedRamGB
      ? `Recomendado ${recommendation.recommendedRamGB} GB de RAM para trabajar con comodidad.`
      : null;
  const suitability =
    profile.totalRamGB < recommendation.minRamGB || diskWarning
      ? "not_recommended"
      : recommendation.suitability;
  return {
    ...recommendation,
    suitability,
    warnings: [
      ...recommendation.warnings,
      ...(ramWarning ? [ramWarning] : []),
      ...(diskWarning ? [diskWarning] : [])
    ]
  };
}

function rankRecommendation(a: ModelRecommendation, b: ModelRecommendation): number {
  const order = {
    api_recommended: 0,
    safe_local: 1,
    balanced: 2,
    advanced_local: 3,
    not_recommended: 4
  };
  return order[a.suitability] - order[b.suitability] || a.recommendedRamGB - b.recommendedRamGB;
}
