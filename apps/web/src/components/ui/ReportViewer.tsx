import { FileText } from "lucide-react";

export function ReportViewer({ title, markdown }: { title: string; markdown: string }) {
  return (
    <div className="rounded-lg border border-border bg-white">
      <div className="flex items-center gap-2 border-b border-border px-5 py-4">
        <FileText className="h-5 w-5 text-abacos-red" />
        <h2 className="font-semibold text-abacos-black">{title}</h2>
      </div>
      <pre className="whitespace-pre-wrap p-5 text-sm leading-7 text-abacos-black">{markdown}</pre>
    </div>
  );
}
