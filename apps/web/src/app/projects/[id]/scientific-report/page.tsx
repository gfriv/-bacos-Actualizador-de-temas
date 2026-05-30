import { AppShell } from "@/components/layout/AppShell";
import { ProjectReportClient } from "@/components/projects/ProjectConnectedViews";
import { PageHeader } from "@/components/ui/PageHeader";
import { ProjectTabs } from "@/components/ui/ProjectTabs";

export default async function ScientificReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <PageHeader title="Informe científico" description="Diagnóstico de actualización científica del tema." />
      <div className="mt-6">
        <ProjectTabs projectId={id} />
      </div>
      <ProjectReportClient projectId={id} reportType="scientific_update" />
    </AppShell>
  );
}
