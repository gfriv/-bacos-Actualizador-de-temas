import { Download, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ResourceCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <article className="rounded-lg border border-border bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-abacos-red-soft text-abacos-red-dark">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <h3 className="font-semibold text-abacos-black">{title}</h3>
          <p className="mt-1 text-sm leading-6 text-abacos-gray">{description}</p>
        </div>
      </div>
      <div className="mt-5 flex gap-2">
        <Button size="sm">Generar</Button>
        <Button size="sm" variant="outline">
          <Download className="h-4 w-4" />
          Descargar
        </Button>
      </div>
    </article>
  );
}
