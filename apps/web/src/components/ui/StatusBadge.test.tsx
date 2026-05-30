import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusBadge } from "@/components/ui/StatusBadge";

describe("StatusBadge", () => {
  it("shows pending status with semantic data attribute", () => {
    render(<StatusBadge status="pending" />);
    expect(screen.getByText("Pendiente")).toHaveAttribute("data-status", "pending");
  });

  it("shows approved status", () => {
    render(<StatusBadge status="approved" />);
    expect(screen.getByText("Aprobada")).toHaveAttribute("data-status", "approved");
  });
});
