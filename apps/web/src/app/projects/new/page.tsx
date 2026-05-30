import { AppShell } from "@/components/layout/AppShell";
import { NewProjectForm } from "@/components/projects/NewProjectForm";
import { PageHeader } from "@/components/ui/PageHeader";

export default function NewProjectPage() {
  return (
    <AppShell>
      <PageHeader
        title="Nuevo proyecto de mejora de tema"
        description="Define el contexto académico u opositor y sube el documento que será analizado."
      />
      <NewProjectForm />
    </AppShell>
  );
}
