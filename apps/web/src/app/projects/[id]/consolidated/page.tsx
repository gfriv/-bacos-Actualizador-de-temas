import { AppShell } from "@/components/layout/AppShell";
import { ProjectConsolidatedClient } from "@/components/projects/ProjectConnectedViews";
import { PageHeader } from "@/components/ui/PageHeader";
import { ProjectTabs } from "@/components/ui/ProjectTabs";

export default async function ConsolidatedPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <PageHeader title="Documento consolidado" description="Generación controlada del documento final." />
      <div className="mt-6">
        <ProjectTabs projectId={id} />
      </div>
      <ProjectConsolidatedClient projectId={id} />
    </AppShell>
  );
}
