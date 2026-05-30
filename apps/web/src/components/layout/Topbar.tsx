"use client";

import Link from "next/link";
import { Bell, Menu, ShieldCheck, UserRound } from "lucide-react";
import { AIProviderStatusDialog } from "@/components/ai/AIProviderSetup";
import { AbacosLogo } from "@/components/brand/AbacosLogo";
import { CommandPalette } from "@/components/layout/CommandPalette";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { Button } from "@/components/ui/button";

export function Topbar({ onOpenNavigation }: { onOpenNavigation?: () => void }) {
  return (
    <div className="sticky top-0 z-30 flex h-16 items-center justify-between gap-2 border-b border-border bg-white/88 px-3 backdrop-blur-xl sm:px-4 lg:px-6">
      <div className="flex min-w-0 items-center gap-2 sm:gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="shrink-0 lg:hidden"
          aria-label="Abrir navegacion"
          onClick={onOpenNavigation}
        >
          <Menu className="h-5 w-5" />
        </Button>
        <Link href="/dashboard" className="min-w-0 shrink lg:hidden" aria-label="Ir al panel">
          <AbacosLogo compact />
        </Link>
        <div className="hidden min-w-0 items-center gap-3 text-sm text-abacos-gray lg:flex">
          <span className="grid h-8 w-8 place-items-center rounded-md bg-abacos-red-soft text-abacos-red-dark">
            <ShieldCheck className="h-4 w-4" aria-hidden />
          </span>
          <span className="truncate">
            Herramienta documental para actualizacion cientifica de temas.
          </span>
        </div>
      </div>
      <div className="flex min-w-0 shrink-0 items-center gap-1.5 sm:gap-2">
        <div className="md:hidden">
          <CommandPalette compact />
        </div>
        <div className="hidden md:block">
          <CommandPalette />
        </div>
        <ThemeToggle compact />
        <AIProviderStatusDialog />
        <Button
          variant="ghost"
          size="icon"
          className="hidden sm:inline-flex"
          aria-label="Notificaciones"
        >
          <Bell className="h-5 w-5" />
        </Button>
        <Button variant="outline" size="sm" className="px-2 sm:px-3">
          <UserRound className="h-4 w-4" />
          <span className="hidden sm:inline">Profesor</span>
        </Button>
      </div>
    </div>
  );
}
