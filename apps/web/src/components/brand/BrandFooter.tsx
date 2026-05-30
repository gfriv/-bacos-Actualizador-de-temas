import { Mail, MapPin, Phone } from "lucide-react";
import { ABACOS_BRAND } from "@/lib/brand";

export function BrandFooter() {
  return (
    <footer className="mt-10 rounded-lg border border-border bg-white/90 p-4 text-sm text-abacos-gray shadow-soft">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="font-semibold text-abacos-black">{ABACOS_BRAND.legalName}</p>
          <p className="mt-1 text-xs leading-5">
            Herramienta documental docente. La IA propone; el profesor valida.
          </p>
        </div>
        <div className="grid gap-2 text-xs sm:grid-cols-3 lg:min-w-[640px]">
          <span className="flex min-w-0 items-center gap-2">
            <MapPin className="h-4 w-4 shrink-0 text-abacos-red" aria-hidden />
            <span className="truncate">{ABACOS_BRAND.address}</span>
          </span>
          <span className="flex min-w-0 items-center gap-2">
            <Phone className="h-4 w-4 shrink-0 text-abacos-red" aria-hidden />
            <span className="truncate">
              {ABACOS_BRAND.phone} · {ABACOS_BRAND.mobile}
            </span>
          </span>
          <span className="flex min-w-0 items-center gap-2">
            <Mail className="h-4 w-4 shrink-0 text-abacos-red" aria-hidden />
            <span className="truncate">{ABACOS_BRAND.email}</span>
          </span>
        </div>
      </div>
    </footer>
  );
}
