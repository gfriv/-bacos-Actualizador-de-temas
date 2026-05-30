import Image from "next/image";
import { cn } from "@/lib/utils";

export function AbacosLogo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <div className={cn("flex items-center", className)} aria-label="Ábacos Centro de Estudios">
      <Image
        src="/brand/abacos-logo-transparent.png"
        alt="Ábacos Centro de Estudios"
        width={256}
        height={256}
        className={cn(compact ? "h-11 w-auto" : "h-28 w-auto")}
        priority
      />
    </div>
  );
}
