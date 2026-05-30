import { AppShell } from "@/components/layout/AppShell";
import { DashboardClient, NewProjectAction } from "@/components/projects/DashboardClient";
import { PageHeader } from "@/components/ui/PageHeader";

export default function DashboardPage() {
  return (
    <AppShell>
      <PageHeader
        title="Panel de trabajo docente"
        description="Seguimiento de proyectos de mejora de temas, informes pendientes y recursos generados."
        actions={<NewProjectAction />}
      />
      <DashboardClient />
    </AppShell>
  );
}
