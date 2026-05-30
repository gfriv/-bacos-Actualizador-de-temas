"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  BookOpenCheck,
  ClipboardCheck,
  FileText,
  FolderKanban,
  Gauge,
  PlusCircle,
  Search,
  Settings,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

type CommandItem = {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
};

function currentProjectBase(pathname: string) {
  const projectId = pathname.match(/^\/projects\/([^/]+)/)?.[1];
  return projectId ? `/projects/${projectId}` : null;
}

function buildCommandItems(pathname: string): CommandItem[] {
  const projectBase = currentProjectBase(pathname);
  const projectItems: CommandItem[] = projectBase
    ? [
        { href: projectBase, label: "Resumen de proyecto", description: "Abrir el flujo de trabajo del tema.", icon: FolderKanban },
        { href: `${projectBase}/document`, label: "Documento original", description: "Subir o revisar el DOCX/PDF.", icon: FileText },
        { href: `${projectBase}/review`, label: "Revision docente", description: "Aceptar, rechazar o editar sugerencias.", icon: ClipboardCheck },
        { href: `${projectBase}/consolidated`, label: "Documento consolidado", description: "Integrar solo cambios aprobados.", icon: BookOpenCheck },
        { href: `${projectBase}/resources`, label: "Recursos didacticos", description: "Generar materiales desde el consolidado.", icon: Sparkles },
      ]
    : [
        {
          href: "/dashboard",
          label: "Proyectos",
          description: "Elige un proyecto para activar documento, revision, consolidado y recursos.",
          icon: FolderKanban,
        },
      ];

  return [
    { href: "/dashboard", label: "Panel operativo", description: "Ver proyectos, alertas y prioridades.", icon: Gauge },
    { href: "/projects/new", label: "Nuevo tema", description: "Crear un proyecto de mejora documental.", icon: PlusCircle },
    ...projectItems,
    { href: "/admin", label: "Administracion", description: "Gestionar el entorno del MVP.", icon: Settings },
  ];
}

export function CommandPalette({ compact = false }: { compact?: boolean }) {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const commandItems = buildCommandItems(pathname);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={cn(
          "button-premium flex items-center gap-2 rounded-md border border-border bg-white text-sm font-semibold text-abacos-gray transition hover:border-abacos-red-soft hover:bg-abacos-red-soft hover:text-abacos-red-dark",
          compact ? "h-10 w-10 justify-center px-0" : "h-10 px-3",
        )}
        aria-label="Abrir buscador de acciones"
      >
        <Search className="h-4 w-4" aria-hidden />
        {compact ? null : (
          <>
            <span>Buscar accion</span>
            <kbd className="rounded border border-border bg-abacos-light px-1.5 py-0.5 text-[0.68rem] text-abacos-gray">
              Ctrl K
            </kbd>
          </>
        )}
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="overflow-hidden p-0">
          <DialogHeader className="border-b border-border px-5 py-4">
            <DialogTitle>Acciones rapidas</DialogTitle>
          </DialogHeader>
          <Command className="bg-white">
            <div className="flex items-center gap-3 border-b border-border px-4">
              <Search className="h-4 w-4 text-abacos-gray" aria-hidden />
              <Command.Input
                className="h-12 flex-1 bg-transparent text-sm outline-none placeholder:text-abacos-gray"
                placeholder="Buscar proyecto, informe, revision o recurso..."
              />
            </div>
            <Command.Empty className="px-5 py-8 text-sm text-abacos-gray">No hay acciones con ese termino.</Command.Empty>
            <Command.List className="max-h-[420px] overflow-auto p-2">
              {commandItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Command.Item
                    key={`${item.href}-${item.label}`}
                    value={`${item.label} ${item.description}`}
                    onSelect={() => {
                      setOpen(false);
                      router.push(item.href);
                    }}
                    className="flex cursor-pointer items-start gap-3 rounded-md px-3 py-3 outline-none aria-selected:bg-abacos-red-soft"
                  >
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-abacos-light text-abacos-red-dark">
                      <Icon className="h-4 w-4" aria-hidden />
                    </span>
                    <span className="min-w-0">
                      <span className="block text-sm font-semibold text-abacos-black">{item.label}</span>
                      <span className="mt-0.5 block text-xs leading-5 text-abacos-gray">{item.description}</span>
                    </span>
                  </Command.Item>
                );
              })}
            </Command.List>
            <div className="border-t border-border bg-abacos-light px-5 py-3 text-xs text-abacos-gray">
              Atajo: Ctrl K. El flujo sigue siendo documental: documento, informes, revision, consolidado y recursos.
            </div>
          </Command>
        </DialogContent>
      </Dialog>
    </>
  );
}
