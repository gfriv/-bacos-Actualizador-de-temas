import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge } from "@/components/ui/StatusBadge";

export default function AdminPage() {
  return (
    <AppShell>
      <PageHeader title="Administración" description="Vista inicial para roles, auditoría y configuración técnica." />
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <SectionCard title="Usuarios">
          <p className="text-sm text-abacos-gray">Roles previstos: admin, teacher, reviewer.</p>
        </SectionCard>
        <SectionCard title="ModelRouter">
          <StatusBadge status="processing" />
          <p className="mt-3 text-sm text-abacos-gray">
            Proveedor configurable en backend mediante variables de entorno.
          </p>
        </SectionCard>
        <SectionCard title="Auditoría">
          <p className="text-sm text-abacos-gray">Registro de acciones críticas preparado en backend.</p>
        </SectionCard>
      </div>
    </AppShell>
  );
}
