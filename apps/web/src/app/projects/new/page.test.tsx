import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import NewProjectPage from "@/app/projects/new/page";

describe("NewProjectPage", () => {
  it("renders project form and document upload", () => {
    render(<NewProjectPage />);
    expect(screen.getByText("Nuevo proyecto de mejora de tema")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Titulo del tema, supuesto o unidad")).toBeInTheDocument();
    expect(screen.getByText(/preparacion de oposiciones docentes/i)).toBeInTheDocument();
    expect(screen.getByText(/Normativa de referencia/i)).toBeInTheDocument();
    expect(screen.getByText("Subir tema DOCX o PDF")).toBeInTheDocument();
  });
});
