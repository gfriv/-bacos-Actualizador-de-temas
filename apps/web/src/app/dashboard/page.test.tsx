import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import DashboardPage from "@/app/dashboard/page";

describe("DashboardPage", () => {
  it("renders dashboard metrics and recent projects", () => {
    render(<DashboardPage />);
    expect(screen.getByText("Panel de trabajo docente")).toBeInTheDocument();
    expect(screen.getByText("Sesión requerida")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ir al acceso" })).toHaveAttribute("href", "/login");
  });
});
