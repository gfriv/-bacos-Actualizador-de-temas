import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AIProviderSetup } from "@/components/ai/AIProviderSetup";

vi.mock("@/lib/api", () => ({
  apiFetch: vi.fn(async (path: string) => {
    if (path === "/ai/providers") {
      return [
        {
          id: "mock",
          display_name: "MockProvider",
          mode: "local",
          requires_api_key: false,
          supports_model_listing: false,
          recommended_models: [{ id: "mock", display_name: "MockProvider", recommended: true }],
        },
        {
          id: "ollama",
          display_name: "Ollama local",
          mode: "local",
          requires_api_key: false,
          supports_model_listing: true,
          default_base_url: "http://localhost:11434",
          recommended_models: [
            { id: "qwen2.5:7b-instruct", display_name: "Qwen", recommended: true },
          ],
        },
      ];
    }
    return {};
  }),
}));

describe("AIProviderSetup", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  it("renders API/local provider selector and safety copy", async () => {
    render(<AIProviderSetup />);

    expect(screen.getByText("Motor de IA")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "API" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Local" })).toBeInTheDocument();
    expect(await screen.findByText(/Ollama debe estar arrancado/i)).toBeInTheDocument();
  });
});
