import { AbacosLogo } from "@/components/brand/AbacosLogo";
import { AbacusPattern } from "@/components/brand/AbacusPattern";
import { ThemeToggle } from "@/components/theme/ThemeToggle";

export function BrandHeader() {
  return (
    <header className="relative overflow-hidden border-b border-border bg-white">
      <AbacusPattern className="pointer-events-none absolute right-6 top-1/2 hidden h-16 w-40 -translate-y-1/2 opacity-20 xl:block" />
      <div className="relative mx-auto flex max-w-7xl items-center justify-between gap-8 px-4 py-5 sm:px-6 lg:px-8">
        <div className="shrink-0">
          <AbacosLogo />
        </div>
        <div className="hidden max-w-[24rem] rounded-md bg-white/90 px-3 py-2 text-right text-sm leading-6 text-abacos-gray shadow-sm md:block xl:mr-48">
          Actualización científica, revisión docente y recursos didácticos derivados.
        </div>
        <ThemeToggle compact className="shrink-0" />
      </div>
    </header>
  );
}
