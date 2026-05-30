export const projectStatuses = [
  "draft",
  "document_uploaded",
  "processing",
  "reports_generated",
  "under_review",
  "consolidated",
  "resources_generated",
  "error",
] as const;

export const suggestionStatuses = ["pending", "approved", "rejected", "edited"] as const;

export type ProjectStatus = (typeof projectStatuses)[number];
export type SuggestionStatus = (typeof suggestionStatuses)[number];

export * from "./ai";
