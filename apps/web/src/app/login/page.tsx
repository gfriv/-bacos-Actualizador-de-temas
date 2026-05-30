import { BrandHeader } from "@/components/brand/BrandHeader";
import { LoginForm } from "@/components/auth/LoginForm";
import { AIProviderSetup } from "@/components/ai/AIProviderSetup";
import { FirstRunWizard } from "@/components/desktop/FirstRunWizard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-abacos-light">
      <BrandHeader />
      <main className="mx-auto grid min-h-[calc(100vh-96px)] max-w-7xl items-center gap-8 px-4 py-10 lg:grid-cols-[minmax(0,1fr)_500px]">
        <section>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-abacos-red-dark">
            Revisión docente obligatoria
          </p>
          <h1 className="mt-3 max-w-2xl text-4xl font-bold tracking-tight text-abacos-black">
            Actualiza temas académicos y de oposición sin perder el control profesional.
          </h1>
          <p className="mt-4 max-w-xl text-base leading-7 text-abacos-gray">
            Sube un DOCX o PDF, revisa informes científicos y curriculares, valida sugerencias y
            genera recursos didácticos para Infantil, Primaria, Secundaria, FP u otras
            especialidades.
          </p>
          <div className="mt-8 grid max-w-xl gap-3 sm:grid-cols-3">
            {["Analiza", "Valida", "Oposiciones"].map((item) => (
              <div
                key={item}
                className="rounded-md border border-border bg-white/75 p-3 text-sm font-semibold text-abacos-black"
              >
                {item}
              </div>
            ))}
          </div>
        </section>
        <div className="grid gap-4">
          <FirstRunWizard />
          <AIProviderSetup />
          <Card className="relative overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-1 bg-abacos-red" aria-hidden />
            <CardHeader>
              <CardTitle>Acceso del profesorado</CardTitle>
            </CardHeader>
            <CardContent>
              <LoginForm />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
