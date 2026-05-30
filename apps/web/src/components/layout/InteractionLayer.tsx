"use client";

import { useEffect } from "react";

export function InteractionLayer() {
  useEffect(() => {
    const root = document.documentElement;

    function handlePointerMove(event: PointerEvent) {
      root.style.setProperty("--spotlight-x", `${event.clientX}px`);
      root.style.setProperty("--spotlight-y", `${event.clientY}px`);
      root.classList.add("spotlight-active");
    }

    function handlePointerLeave() {
      root.classList.remove("spotlight-active");
    }

    window.addEventListener("pointermove", handlePointerMove, { passive: true });
    window.addEventListener("pointerleave", handlePointerLeave);

    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerleave", handlePointerLeave);
      root.classList.remove("spotlight-active");
    };
  }, []);

  return <div className="mouse-spotlight" aria-hidden />;
}
