import { AppShell } from "@/components/layout/AppShell";
import { ProjectDocumentClient } from "@/components/projects/ProjectConnectedViews";
import { PageHeader } from "@/components/ui/PageHeader";
import { ProjectTabs } from "@/components/ui/ProjectTabs";

export default async function ProjectDocumentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <PageHeader title="Documento original" description="Texto extraído del archivo DOCX/PDF subido por el profesor." />
      <div className="mt-6">
        <ProjectTabs projectId={id} />
      </div>
      <ProjectDocumentClient projectId={id} />
    </AppShell>
  );
}
