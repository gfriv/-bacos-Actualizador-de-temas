"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { DocumentDropzone } from "@/components/ui/DocumentDropzone";
import { SectionCard } from "@/components/ui/SectionCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createProject, getToken, runResearchAnalysis, uploadDocument } from "@/lib/api";

const areaSuggestions = [
  "Educación Infantil",
  "Educación Primaria",
  "Pedagogía Terapéutica",
  "Audición y Lenguaje",
  "Inglés - Primaria",
  "Educación Física - Primaria",
  "Música - Primaria",
  "Biología y Geología",
  "Geografía e Historia",
  "Lengua Castellana y Literatura",
  "Matemáticas",
  "Formación Profesional",
];

const levelSuggestions = [
  "Oposiciones Educación Infantil",
  "Oposiciones Educación Primaria",
  "Oposiciones Secundaria",
  "Oposiciones Formación Profesional",
  "Oposiciones Escuela Oficial de Idiomas",
  "Educación Infantil",
  "Educación Primaria",
  "ESO",
  "Bachillerato",
  "Formación Profesional",
];

const legalFrameworkSuggestions = [
  "LOMLOE, Real Decreto 95/2022 de Educación Infantil, convocatoria de oposiciones y normativa autonómica aplicable.",
  "LOMLOE, Real Decreto 157/2022 de Educación Primaria, convocatoria de oposiciones y normativa autonómica aplicable.",
  "LOMLOE, Real Decreto 217/2022 de ESO, convocatoria de oposiciones y normativa autonómica aplicable.",
  "LOMLOE, Real Decreto 243/2022 de Bachillerato, convocatoria de oposiciones y normativa autonómica aplicable.",
  "Extremadura: Ley 4/2011 de Educación de Extremadura, Decreto 98/2022 de Educación Infantil, Orden de 9 de diciembre de 2022 de evaluación y convocatoria de oposiciones.",
  "Extremadura: Ley 4/2011 de Educación de Extremadura, Decreto 107/2022 de Educación Primaria, Orden de 9 de diciembre de 2022 de evaluación y convocatoria de oposiciones.",
  "Extremadura: Decretos 110/2022 de ESO y 109/2022 de Bachillerato, Orden de 9 de diciembre de 2022 de evaluación y convocatoria de oposiciones.",
  "Extremadura: normativa autonómica DOE/Educarex vigente, decreto curricular de etapa y convocatoria específica aportada por el docente.",
  "Normativa estatal, convocatoria de oposiciones y decreto autonómico aportados por el docente.",
];

export function NewProjectForm() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  function applyLegalFramework(event: React.MouseEvent<HTMLButtonElement>, value: string) {
    const field = event.currentTarget.form?.elements.namedItem("legal_framework");
    if (field instanceof HTMLTextAreaElement) {
      field.value = value;
      field.focus();
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!getToken()) {
      toast.error("Inicia sesión antes de crear proyectos.");
      router.push("/login");
      return;
    }

    const formData = new FormData(event.currentTarget);
    setLoading(true);
    try {
      const project = await createProject({
        title: String(formData.get("title") ?? ""),
        area: String(formData.get("area") ?? ""),
        educational_level: String(formData.get("educational_level") ?? ""),
        legal_framework: String(formData.get("legal_framework") ?? ""),
        bibliography_notes: String(formData.get("bibliography_notes") ?? ""),
        instructions: String(formData.get("instructions") ?? ""),
      });
      if (file) {
        await uploadDocument(project.id, file);
        await runResearchAnalysis(project.id);
        toast.success("Proyecto creado, documento analizado e informes con búsqueda generados.");
        router.push(`/projects/${project.id}/review`);
      } else {
        toast.success("Proyecto creado como borrador.");
        router.push(`/projects/${project.id}`);
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo crear el proyecto");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="mt-6 grid gap-6 xl:grid-cols-[1fr_360px]" onSubmit={handleSubmit}>
      <SectionCard title="Datos del tema">
        <div className="grid gap-4">
          <div className="rounded-md border border-border bg-abacos-light p-3 text-xs leading-5 text-abacos-gray">
            También sirve para preparación de oposiciones docentes: Infantil, Primaria, Secundaria,
            Formación Profesional, EOI y especialidades como PT, AL, Inglés, Música o Educación Física.
          </div>
          <Input name="title" placeholder="Título del tema, supuesto o unidad" required />
          <Input name="area" list="abacos-area-suggestions" placeholder="Área, cuerpo o especialidad" required />
          <Input
            name="educational_level"
            list="abacos-level-suggestions"
            placeholder="Nivel educativo o proceso selectivo"
            required
          />
          <Textarea
            name="legal_framework"
            placeholder="Legislación educativa, convocatoria y normativa autonómica de referencia"
            required
          />
          <div className="grid gap-2 rounded-md border border-border bg-white/75 p-3 text-xs leading-5 text-abacos-gray">
            <p className="font-semibold text-abacos-black">Ejemplos para oposiciones</p>
            {legalFrameworkSuggestions.map((item) => (
              <button
                key={item}
                type="button"
                className="rounded-md px-2 py-1 text-left transition hover:bg-abacos-red-soft hover:text-abacos-red-dark"
                onClick={(event) => applyLegalFramework(event, item)}
              >
                {item}
              </button>
            ))}
          </div>
          <Textarea name="bibliography_notes" placeholder="Bibliografía base opcional" />
          <Textarea
            name="instructions"
            placeholder="Instrucciones adicionales: tribunal, comunidad autónoma, enfoque de oposición, extensión, etc."
          />
          <datalist id="abacos-area-suggestions">
            {areaSuggestions.map((item) => (
              <option key={item} value={item} />
            ))}
          </datalist>
          <datalist id="abacos-level-suggestions">
            {levelSuggestions.map((item) => (
              <option key={item} value={item} />
            ))}
          </datalist>
          <Button type="submit" disabled={loading}>
            {loading ? "Creando y analizando..." : "Crear proyecto"}
          </Button>
        </div>
      </SectionCard>
      <SectionCard title="Documento original" description="DOCX preferente; PDF si contiene texto extraíble.">
        <DocumentDropzone fileName={file?.name} onFileChange={setFile} />
      </SectionCard>
    </form>
  );
}
