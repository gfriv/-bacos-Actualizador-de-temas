import { AppShell } from "@/components/layout/AppShell";
import { ProjectReviewClient } from "@/components/projects/ProjectConnectedViews";
import { PageHeader } from "@/components/ui/PageHeader";
import { ProjectTabs } from "@/components/ui/ProjectTabs";

export default async function ReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <PageHeader
        title="Revisión de sugerencias"
        description="Cada sugerencia debe aceptarse, rechazarse, editarse o quedar pendiente antes de consolidar."
      />
      <div className="mt-6">
        <ProjectTabs projectId={id} />
      </div>
      <ProjectReviewClient projectId={id} />
    </AppShell>
  );
}
