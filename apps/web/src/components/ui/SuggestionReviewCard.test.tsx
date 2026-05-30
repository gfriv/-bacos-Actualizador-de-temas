import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SuggestionReviewCard } from "@/components/ui/SuggestionReviewCard";
import { TooltipProvider } from "@/components/ui/tooltip";

describe("SuggestionReviewCard", () => {
  it("renders review actions and traceability", () => {
    render(
      <TooltipProvider>
        <SuggestionReviewCard
          section="1. Introducción"
          original="Texto original"
          proposed="Texto propuesto"
          justification="Justificación"
          source="MockProvider"
          confidence="medium"
          status="pending"
        />
      </TooltipProvider>,
    );

    expect(screen.getByText("Texto original")).toBeInTheDocument();
    expect(screen.getByText("Texto propuesto")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Aceptar/i })).toBeInTheDocument();
    expect(screen.getByText("MockProvider")).toBeInTheDocument();
  });
});
