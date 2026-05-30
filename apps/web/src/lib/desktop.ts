export function isDesktopRuntime(): boolean {
  return typeof window !== "undefined" && Boolean(window.abacosDesktop?.isDesktop);
}

export function desktopApi() {
  return typeof window !== "undefined" ? window.abacosDesktop : undefined;
}
