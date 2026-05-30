"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, KeyRound, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { loginDemo, registerAndLogin } from "@/lib/api";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("profesor@example.com");
  const [password, setPassword] = useState("abacos-demo");
  const [fullName, setFullName] = useState("Profesor Ábacos");
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    try {
      await registerAndLogin(email, password, fullName);
      toast.success("Sesión iniciada");
      router.push("/dashboard");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo iniciar sesión");
    } finally {
      setLoading(false);
    }
  }

  async function handleDemoLogin() {
    setDemoLoading(true);
    try {
      await loginDemo();
      toast.success("Modo demo docente iniciado");
      router.push("/dashboard");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "No se pudo iniciar la demo");
    } finally {
      setDemoLoading(false);
    }
  }

  return (
    <div className="grid gap-5">
      <Button
        type="button"
        size="lg"
        className="relative h-12 overflow-hidden shadow-[0_0_28px_rgba(178,13,34,0.22)]"
        onClick={handleDemoLogin}
        disabled={demoLoading}
      >
        <span className="absolute inset-0 bg-[linear-gradient(110deg,transparent,rgba(255,255,255,0.28),transparent)] opacity-60" />
        <Sparkles className="h-4 w-4" aria-hidden />
        {demoLoading ? "Preparando demo..." : "Entrar en demo docente"}
        <ArrowRight className="h-4 w-4" aria-hidden />
      </Button>

      <div className="flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.14em] text-abacos-gray">
        <span className="h-px flex-1 bg-border" />
        Acceso local
        <span className="h-px flex-1 bg-border" />
      </div>

      <form className="grid gap-4" onSubmit={handleSubmit}>
        <Input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          aria-label="Correo electrónico"
        />
        <Input
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          aria-label="Nombre completo"
        />
        <Input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          aria-label="Contraseña"
        />
        <Button type="submit" variant="outline" disabled={loading}>
          <KeyRound className="h-4 w-4" aria-hidden />
          {loading ? "Entrando..." : "Entrar con usuario local"}
        </Button>
      </form>
    </div>
  );
}
