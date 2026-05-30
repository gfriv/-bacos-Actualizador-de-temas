import { AppShell } from "@/components/layout/AppShell";
import { ProjectSectionsClient } from "@/components/projects/ProjectConnectedViews";
import { PageHeader } from "@/components/ui/PageHeader";
import { ProjectTabs } from "@/components/ui/ProjectTabs";

export default async function ProjectSectionsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <PageHeader title="Secciones detectadas" description="División inicial del tema para análisis localizado." />
      <div className="mt-6">
        <ProjectTabs projectId={id} />
      </div>
      <ProjectSectionsClient projectId={id} />
    </AppShell>
  );
}
