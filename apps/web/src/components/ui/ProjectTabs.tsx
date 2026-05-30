"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpenCheck,
  ClipboardCheck,
  FileSearch,
  FileText,
  Layers3,
  LayoutDashboard,
  Scale,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "", label: "Resumen", icon: LayoutDashboard },
  { href: "/document", label: "Documento original", icon: FileText },
  { href: "/sections", label: "Secciones", icon: Layers3 },
  { href: "/scientific-report", label: "Informe científico", icon: FileSearch },
  { href: "/curriculum-report", label: "Informe curricular", icon: Scale },
  { href: "/review", label: "Revisión docente", icon: ClipboardCheck },
  { href: "/consolidated", label: "Consolidado", icon: BookOpenCheck },
  { href: "/resources", label: "Recursos", icon: Sparkles },
];

export function ProjectTabs({ projectId }: { projectId: string }) {
  const pathname = usePathname();

  return (
    <nav
      className="-mx-3 flex gap-2 overflow-x-auto border-b border-border px-3 pb-3 [scrollbar-width:none] sm:mx-0 sm:px-0 lg:flex-wrap lg:overflow-visible [&::-webkit-scrollbar]:hidden"
      aria-label="Navegación del proyecto"
    >
      {tabs.map((tab) => {
        const href = `/projects/${projectId}${tab.href}`;
        const isActive = pathname === href;
        const Icon = tab.icon;

        return (
          <Link
            key={tab.href}
            href={href}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "inline-flex min-h-10 shrink-0 items-center gap-2 rounded-md border px-3 py-2 text-sm font-semibold transition",
              isActive
                ? "border-abacos-red bg-abacos-red text-white shadow-sm"
                : "border-border bg-white text-abacos-gray hover:border-abacos-red-soft hover:bg-abacos-red-soft hover:text-abacos-red-dark",
            )}
          >
            <Icon className="h-4 w-4" aria-hidden />
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
