import { FileUp } from "lucide-react";

export function DocumentDropzone({
  fileName,
  onFileChange,
}: {
  fileName?: string;
  onFileChange?: (file: File | null) => void;
}) {
  return (
    <label className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-abacos-red/45 bg-abacos-red-soft/45 px-6 py-8 text-center transition hover:bg-abacos-red-soft">
      <FileUp className="h-8 w-8 text-abacos-red-dark" aria-hidden />
      <span className="mt-3 text-sm font-semibold text-abacos-black">
        {fileName ?? "Subir tema DOCX o PDF"}
      </span>
      <span className="mt-1 max-w-md text-xs leading-5 text-abacos-gray">
        DOCX es el formato preferente. Los PDF escaneados requerirán OCR en una fase posterior.
      </span>
      <input
        className="sr-only"
        type="file"
        accept=".docx,.pdf"
        onChange={(event) => onFileChange?.(event.target.files?.[0] ?? null)}
      />
    </label>
  );
}
