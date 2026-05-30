import { AppShell } from "@/components/layout/AppShell";
import { ProjectOverviewClient } from "@/components/projects/ProjectConnectedViews";
import { PageHeader } from "@/components/ui/PageHeader";
import { ProjectTabs } from "@/components/ui/ProjectTabs";

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <PageHeader
        title="Proyecto de mejora de tema"
        description="Resumen operativo del flujo: documento, análisis, revisión docente, consolidación y recursos."
      />
      <div className="mt-6">
        <ProjectTabs projectId={id} />
      </div>
      <ProjectOverviewClient projectId={id} />
    </AppShell>
  );
}
