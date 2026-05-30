const SECRET_PATTERNS = [
  /sk-[A-Za-z0-9_-]{8,}/g,
  /(api[_-]?key["'\s:=]+)[A-Za-z0-9._-]{8,}/gi,
  /(authorization["'\s:=]+bearer\s+)[A-Za-z0-9._-]{8,}/gi,
  /(x-abacos-ai-config["'\s:=]+)[A-Za-z0-9._-]{16,}/gi
];

export function redactSecrets(value: unknown): string {
  let text = typeof value === "string" ? value : JSON.stringify(value);
  if (!text) return "";
  for (const pattern of SECRET_PATTERNS) {
    text = text.replace(pattern, (_match, prefix: string | undefined) =>
      prefix ? `${prefix}[redacted]` : "[redacted]"
    );
  }
  return text;
}
