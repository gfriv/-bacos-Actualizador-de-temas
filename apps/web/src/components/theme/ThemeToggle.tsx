"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function ThemeToggle({ compact = false, className }: { compact?: boolean; className?: string }) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = mounted && resolvedTheme === "dark";
  const label = isDark ? "Activar modo claro" : "Activar modo noche";

  return (
    <Button
      type="button"
      variant="outline"
      size={compact ? "icon" : "sm"}
      className={cn("theme-toggle", compact ? "w-10" : "min-w-32", className)}
      aria-label={label}
      title={label}
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      <span className="relative grid h-4 w-4 place-items-center">
        <Sun
          className={cn(
            "absolute h-4 w-4 transition duration-200",
            isDark ? "scale-75 opacity-0" : "scale-100 opacity-100",
          )}
          aria-hidden
        />
        <Moon
          className={cn(
            "absolute h-4 w-4 transition duration-200",
            isDark ? "scale-100 opacity-100" : "scale-75 opacity-0",
          )}
          aria-hidden
        />
      </span>
      {compact ? <span className="sr-only">{label}</span> : <span>{isDark ? "Modo claro" : "Modo noche"}</span>}
    </Button>
  );
}
