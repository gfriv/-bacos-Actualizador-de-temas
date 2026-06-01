"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { DocumentDropzone } from "@/components/ui/DocumentDropzone";
import { SectionCard } from "@/components/ui/SectionCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  createProject,
  getToken,
  listLegalFrameworks,
  runResearchAnalysis,
  uploadDocument,
  type LegalFrameworkOption,
} from "@/lib/api";

const areaSuggestions = [
  "Educacion Infantil",
  "Educacion Primaria",
  "Pedagogia Terapeutica",
  "Audicion y Lenguaje",
  "Ingles - Primaria",
  "Educacion Fisica - Primaria",
  "Musica - Primaria",
  "Biologia y Geologia",
  "Geografia e Historia",
  "Lengua Castellana y Literatura",
  "Matematicas",
  "Formacion Profesional",
];

const levelSuggestions = [
  "Oposiciones Educacion Infantil",
  "Oposiciones Educacion Primaria",
  "Oposiciones Secundaria",
  "Oposiciones Formacion Profesional",
  "Oposiciones Escuela Oficial de Idiomas",
  "Educacion Infantil",
  "Educacion Primaria",
  "ESO",
  "Bachillerato",
  "Formacion Profesional",
];

const fallbackLegalFrameworks: LegalFrameworkOption[] = [
  {
    id: "auto",
    label: "Inferencia automatica por etapa",
    value: "",
    description: "El sistema propone normativa inicial desde area, nivel y fuentes oficiales recuperadas.",
  },
  {
    id: "extremadura_infantil",
    label: "Extremadura · Educacion Infantil",
    value:
      "LOMLOE, Real Decreto 95/2022, Ley 4/2011 de Educacion de Extremadura, Decreto 98/2022 de Educacion Infantil de Extremadura, evaluacion autonomica y convocatoria aplicable.",
    description: "Marco inicial para Infantil en Extremadura.",
  },
  {
    id: "extremadura_primaria",
    label: "Extremadura · Educacion Primaria",
    value:
      "LOMLOE, Real Decreto 157/2022, Ley 4/2011 de Educacion de Extremadura, Decreto 107/2022 de Educacion Primaria de Extremadura, evaluacion autonomica y convocatoria aplicable.",
    description: "Marco inicial para Primaria en Extremadura.",
  },
  {
    id: "extremadura_secundaria",
    label: "Extremadura · ESO/Bachillerato",
    value:
      "LOMLOE, Real Decreto 217/2022 de ESO, Real Decreto 243/2022 de Bachillerato, Ley 4/2011 de Educacion de Extremadura, decretos curriculares autonomicos vigentes, evaluacion autonomica y convocatoria aplicable.",
    description: "Marco inicial para Secundaria y Bachillerato en Extremadura.",
  },
  {
    id: "estatal_oposiciones",
    label: "Estatal · Oposiciones docentes",
    value:
      "LOMLOE/LOE vigente, curriculo estatal de la etapa, Real Decreto 276/2007 de ingreso docente, convocatoria autonomica aplicable y normativa curricular autonomica vigente.",
    description: "Base estatal para oposiciones; debe completarse con comunidad autonoma concreta.",
  },
];

export function NewProjectForm() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [legalOptions, setLegalOptions] = useState<LegalFrameworkOption[]>(fallbackLegalFrameworks);
  const [selectedLegalId, setSelectedLegalId] = useState("auto");

  useEffect(() => {
    void listLegalFrameworks()
      .then((options) => setLegalOptions(options.length > 0 ? options : fallbackLegalFrameworks))
      .catch(() => setLegalOptions(fallbackLegalFrameworks));
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!getToken()) {
      toast.error("Inicia sesion antes de crear proyectos.");
      router.push("/login");
      return;
    }

    const formData = new FormData(event.currentTarget);
    const selectedLegal = legalOptions.find((option) => option.id === selectedLegalId);
    setLoading(true);
    try {
      const project = await createProject({
        title: String(formData.get("title") ?? ""),
        area: String(formData.get("area") ?? ""),
        educational_level: String(formData.get("educational_level") ?? ""),
        legal_framework:
          selectedLegalId === "custom"
            ? String(formData.get("legal_framework_custom") ?? "")
            : (selectedLegal?.value ?? ""),
        bibliography_notes: String(formData.get("bibliography_notes") ?? ""),
        instructions: String(formData.get("instructions") ?? ""),
      });
      if (file) {
        await uploadDocument(project.id, file);
        await runResearchAnalysis(project.id);
        toast.success("Proyecto creado, documento analizado e informes con busqueda generados.");
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

  const selectedLegal = legalOptions.find((option) => option.id === selectedLegalId);

  return (
    <form className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]" onSubmit={handleSubmit}>
      <SectionCard title="Datos del tema">
        <div className="grid gap-4">
          <div className="rounded-md border border-border bg-abacos-light p-3 text-xs leading-5 text-abacos-gray">
            Tambien sirve para preparacion de oposiciones docentes: Infantil, Primaria, Secundaria,
            Formacion Profesional, EOI y especialidades como PT, AL, Ingles, Musica o Educacion Fisica.
          </div>
          <Input name="title" placeholder="Titulo del tema, supuesto o unidad" required />
          <Input name="area" list="abacos-area-suggestions" placeholder="Area, cuerpo o especialidad" required />
          <Input
            name="educational_level"
            list="abacos-level-suggestions"
            placeholder="Nivel educativo o proceso selectivo"
            required
          />

          <div className="grid gap-2">
            <label className="text-sm font-semibold text-abacos-black">
              Normativa de referencia
              <span className="ml-1 font-normal text-abacos-gray">(opcional)</span>
            </label>
            <Select value={selectedLegalId} onValueChange={setSelectedLegalId}>
              <SelectTrigger>
                <SelectValue placeholder="Elegir marco normativo" />
              </SelectTrigger>
              <SelectContent>
                {legalOptions.map((option) => (
                  <SelectItem key={option.id} value={option.id}>
                    {option.label}
                  </SelectItem>
                ))}
                <SelectItem value="custom">Escribir normativa manual</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs leading-5 text-abacos-gray">
              {selectedLegalId === "custom"
                ? "Introduce solo la normativa que quieras fijar. El sistema seguira contrastando fuentes oficiales."
                : (selectedLegal?.description ??
                  "Si no indicas normativa, el sistema la inferira y la marcara para verificacion docente.")}
            </p>
            {selectedLegalId === "custom" ? (
              <Textarea
                name="legal_framework_custom"
                placeholder="Normativa, convocatoria o comunidad autonoma concreta"
              />
            ) : null}
          </div>

          <Textarea name="bibliography_notes" placeholder="Bibliografia base opcional" />
          <Textarea
            name="instructions"
            placeholder="Instrucciones adicionales: tribunal, comunidad autonoma, enfoque de oposicion, extension, etc."
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
      <SectionCard title="Documento original" description="DOCX preferente; PDF si contiene texto extraible.">
        <DocumentDropzone fileName={file?.name} onFileChange={setFile} />
      </SectionCard>
    </form>
  );
}
