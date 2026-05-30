import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import NewProjectPage from "@/app/projects/new/page";

describe("NewProjectPage", () => {
  it("renders project form and document upload", () => {
    render(<NewProjectPage />);
    expect(screen.getByText("Nuevo proyecto de mejora de tema")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Título del tema, supuesto o unidad")).toBeInTheDocument();
    expect(screen.getByText(/preparación de oposiciones docentes/i)).toBeInTheDocument();
    expect(screen.getByText("Subir tema DOCX o PDF")).toBeInTheDocument();
  });
});
