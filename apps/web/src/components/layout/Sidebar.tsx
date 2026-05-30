"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpenCheck,
  ClipboardCheck,
  FileText,
  FolderKanban,
  Gauge,
  LibraryBig,
  PlusCircle,
  Settings,
  Sparkles,
  X,
  type LucideIcon,
} from "lucide-react";
import { AbacosLogo } from "@/components/brand/AbacosLogo";
import { cn } from "@/lib/utils";

type NavigationItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  projectScoped?: boolean;
  exact?: boolean;
};

function getProjectId(pathname: string) {
  return pathname.match(/^\/projects\/([^/]+)/)?.[1];
}

function buildNavItems(pathname: string): NavigationItem[] {
  const projectId = getProjectId(pathname);
  const projectBase = projectId ? `/projects/${projectId}` : "/dashboard";

  return [
    { href: "/dashboard", label: "Panel", icon: Gauge },
    { href: "/projects/new", label: "Nuevo tema", icon: PlusCircle },
    { href: projectBase, label: "Proyectos", icon: FolderKanban, projectScoped: true, exact: true },
    { href: projectId ? `${projectBase}/scientific-report` : "/dashboard", label: "Informes", icon: FileText, projectScoped: true },
    { href: projectId ? `${projectBase}/review` : "/dashboard", label: "Revision docente", icon: ClipboardCheck, projectScoped: true },
    { href: projectId ? `${projectBase}/resources` : "/dashboard", label: "Recursos generados", icon: Sparkles, projectScoped: true },
    { href: "/admin", label: "Administracion", icon: Settings },
  ];
}

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const currentProjectId = getProjectId(pathname);
  const navItems = buildNavItems(pathname);

  return (
    <nav className="grid gap-1.5">
      {navItems.map((item) => {
        const Icon = item.icon;
        const active =
          (!item.projectScoped || currentProjectId) &&
          (item.exact ? pathname === item.href : pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href)));
        return (
          <Link
            key={`${item.href}-${item.label}`}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              "group relative flex min-h-11 items-center gap-3 rounded-md px-3 py-2.5 text-sm font-semibold transition",
              active
                ? "bg-abacos-red-soft text-abacos-red-dark shadow-sm"
                : "text-abacos-gray hover:bg-abacos-red-soft hover:text-abacos-red-dark",
            )}
          >
            <span
              className={cn(
                "absolute left-0 top-1/2 h-7 w-1 -translate-y-1/2 rounded-r-full transition",
                active ? "bg-abacos-red" : "bg-transparent group-hover:bg-abacos-red/40",
              )}
              aria-hidden
            />
            <span
              className={cn(
                "grid h-8 w-8 shrink-0 place-items-center rounded-md transition",
                active ? "bg-white text-abacos-red-dark" : "bg-abacos-light text-abacos-gray group-hover:text-abacos-red-dark",
              )}
            >
              <Icon className="h-4 w-4" aria-hidden />
            </span>
            <span className="min-w-0 truncate">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-72 shrink-0 border-r border-border bg-white/92 px-4 py-5 backdrop-blur lg:block">
      <Link href="/dashboard" className="mb-8 block rounded-md outline-none focus-visible:ring-2 focus-visible:ring-abacos-red">
        <AbacosLogo />
      </Link>
      <SidebarNav />
      <div className="interactive-card mt-8 rounded-lg border border-border bg-abacos-light p-4">
        <LibraryBig className="h-5 w-5 text-abacos-red" />
        <p className="mt-3 text-sm font-semibold text-abacos-black">Regla central</p>
        <p className="mt-1 text-xs leading-5 text-abacos-gray">
          La IA propone. El profesor valida. Solo se consolidan cambios aprobados.
        </p>
      </div>
    </aside>
  );
}

export function MobileNavigation({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  useEffect(() => {
    if (!open) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onOpenChange(false);
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onOpenChange, open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <button
        type="button"
        className="absolute inset-0 bg-abacos-black/40 backdrop-blur-sm"
        aria-label="Cerrar navegacion"
        onClick={() => onOpenChange(false)}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Navegacion principal"
        className={cn(
          "absolute left-0 top-0 flex h-full w-[min(86vw,22rem)] flex-col border-r border-border bg-white px-4 py-5 shadow-[24px_0_70px_rgba(30,30,30,0.22)] transition-transform duration-200",
          "translate-x-0",
        )}
      >
        <div className="mb-6 flex items-center justify-between gap-3">
          <Link
            href="/dashboard"
            className="min-w-0 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-abacos-red"
            onClick={() => onOpenChange(false)}
          >
            <AbacosLogo compact />
          </Link>
          <button
            type="button"
            className="grid h-10 w-10 shrink-0 place-items-center rounded-md border border-border bg-white text-abacos-gray transition hover:bg-abacos-red-soft hover:text-abacos-red-dark"
            aria-label="Cerrar menu"
            onClick={() => onOpenChange(false)}
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>

        <SidebarNav onNavigate={() => onOpenChange(false)} />

        <div className="mt-auto rounded-lg border border-border bg-abacos-light p-4">
          <p className="text-sm font-semibold text-abacos-black">Modo movil</p>
          <p className="mt-1 text-xs leading-5 text-abacos-gray">
            Acceso rapido al flujo documental: documento, informes, revision y recursos.
          </p>
        </div>
      </aside>
    </div>
  );
}

export function MobileBottomNav() {
  const pathname = usePathname();
  const projectId = getProjectId(pathname);
  const projectBase = projectId ? `/projects/${projectId}` : "/dashboard";
  const items: NavigationItem[] = [
    { href: "/dashboard", label: "Panel", icon: Gauge },
    { href: "/projects/new", label: "Nuevo", icon: PlusCircle },
    { href: projectBase, label: "Tema", icon: FolderKanban, projectScoped: true, exact: true },
    { href: projectId ? `${projectBase}/review` : "/dashboard", label: "Revision", icon: ClipboardCheck, projectScoped: true },
    { href: projectId ? `${projectBase}/resources` : "/dashboard", label: "Recursos", icon: BookOpenCheck, projectScoped: true },
  ];

  return (
    <nav
      className="fixed inset-x-3 bottom-3 z-40 grid grid-cols-5 rounded-2xl border border-border bg-white/94 p-1.5 shadow-[0_18px_45px_rgba(30,30,30,0.18)] backdrop-blur-xl lg:hidden"
      aria-label="Navegacion movil"
    >
      {items.map((item) => {
        const Icon = item.icon;
        const active =
          (!item.projectScoped || projectId) &&
          (item.exact ? pathname === item.href : pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href)));
        return (
          <Link
            key={`${item.href}-${item.label}`}
            href={item.href}
            className={cn(
              "flex min-w-0 flex-col items-center justify-center gap-1 rounded-xl px-1 py-2 text-[0.68rem] font-semibold transition",
              active
                ? "bg-abacos-red text-white shadow-[0_10px_22px_rgba(178,13,34,0.24)]"
                : "text-abacos-gray hover:bg-abacos-red-soft hover:text-abacos-red-dark",
            )}
          >
            <Icon className="h-4 w-4" aria-hidden />
            <span className="max-w-full truncate">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
