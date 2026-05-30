import { AppShell } from "@/components/layout/AppShell";
import { ProjectResourcesClient } from "@/components/projects/ProjectConnectedViews";
import { PageHeader } from "@/components/ui/PageHeader";
import { ProjectTabs } from "@/components/ui/ProjectTabs";

export default async function ResourcesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <PageHeader title="Recursos didácticos" description="Materiales generados desde el documento consolidado." />
      <div className="mt-6">
        <ProjectTabs projectId={id} />
      </div>
      <ProjectResourcesClient projectId={id} />
    </AppShell>
  );
}
