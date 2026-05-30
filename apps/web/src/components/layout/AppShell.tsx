"use client";

import { useState, type ReactNode } from "react";
import { CommandPalette } from "@/components/layout/CommandPalette";
import { InteractionLayer } from "@/components/layout/InteractionLayer";
import { MobileBottomNav, MobileNavigation, Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

export function AppShell({ children }: { children: ReactNode }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen overflow-x-hidden bg-abacos-light">
      <InteractionLayer />
      <MobileNavigation open={mobileNavOpen} onOpenChange={setMobileNavOpen} />
      <div className="flex">
        <Sidebar />
        <div className="relative z-10 min-w-0 flex-1">
          <Topbar onOpenNavigation={() => setMobileNavOpen(true)} />
          <main className="mx-auto w-full max-w-7xl px-3 pb-28 pt-4 sm:px-6 sm:pt-6 lg:px-8 lg:pb-8">
            {children}
          </main>
        </div>
      </div>
      <MobileBottomNav />
      <div className="fixed bottom-5 right-5 z-40 hidden xl:block">
        <CommandPalette compact />
      </div>
    </div>
  );
}
