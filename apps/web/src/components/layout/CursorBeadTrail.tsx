"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";

type Bead = {
  id: number;
  x: number;
  y: number;
  color: string;
  drift: number;
  fall: number;
  midDrift: number;
  midFall: number;
  size: number;
  delay: number;
};

const beadColors = ["#1F5EA8", "#4C9A4B", "#B20D22", "#E6B72E", "#8F0A1B"];
const beadPattern = [
  { offsetX: 8, offsetY: 10, size: 8, drift: -10, fall: 46, delay: 0 },
  { offsetX: -1, offsetY: 15, size: 6, drift: 8, fall: 56, delay: 44 },
];
const beadLifetimeMs = 920;
const suppressedTargets = [
  "a",
  "button",
  "[role='button']",
  "input",
  "textarea",
  "select",
  "[contenteditable='true']",
  "[disabled]",
  "[aria-disabled='true']",
  ".clickable",
  ".cursor-pointer",
  ".cursor-text",
  ".cursor-help",
  ".cursor-wait",
  ".cursor-grab",
  ".cursor-grabbing",
  ".cursor-not-allowed",
  ".loading",
  ".is-loading",
  "[aria-busy='true']",
  ".draggable",
  "[draggable='true']",
].join(",");

export function CursorBeadTrail() {
  const [beads, setBeads] = useState<Bead[]>([]);
  const idRef = useRef(0);
  const lastRef = useRef(0);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const finePointer = window.matchMedia("(pointer: fine)");
    if (reducedMotion.matches || !finePointer.matches) return;

    function handlePointerMove(event: PointerEvent) {
      if (event.pointerType && event.pointerType !== "mouse") return;
      if (document.documentElement.dataset.abacosCursors === "off") return;
      if (event.target instanceof Element && event.target.closest(suppressedTargets)) return;

      const now = performance.now();
      if (now - lastRef.current < 58) return;
      lastRef.current = now;

      const newBeads = beadPattern.map((pattern, index) => {
        const id = idRef.current + 1;
        idRef.current = id;
        const color = beadColors[(id + index) % beadColors.length];
        const drift = pattern.drift + ((id % 5) - 2) * 2;
        const fall = pattern.fall + (id % 4) * 5;
        return {
          id,
          x: event.clientX + pattern.offsetX,
          y: event.clientY + pattern.offsetY,
          color,
          drift,
          fall,
          midDrift: Math.round(drift * 0.38),
          midFall: Math.round(fall * 0.36),
          size: pattern.size + (id % 2),
          delay: pattern.delay,
        } satisfies Bead;
      });

      setBeads((current) => [...current.slice(-18), ...newBeads]);
      for (const bead of newBeads) {
        window.setTimeout(() => {
          setBeads((current) => current.filter((item) => item.id !== bead.id));
        }, beadLifetimeMs + bead.delay + 60);
      }
    }

    window.addEventListener("pointermove", handlePointerMove, { passive: true });
    return () => window.removeEventListener("pointermove", handlePointerMove);
  }, []);

  if (beads.length === 0) return null;

  return (
    <div className="cursor-bead-layer" aria-hidden="true">
      {beads.map((bead) => (
        <span
          key={bead.id}
          className="cursor-bead"
          style={
            {
              "--bead-x": `${bead.x}px`,
              "--bead-y": `${bead.y}px`,
              "--bead-drift": `${bead.drift}px`,
              "--bead-fall": `${bead.fall}px`,
              "--bead-mid-drift": `${bead.midDrift}px`,
              "--bead-mid-fall": `${bead.midFall}px`,
              "--bead-size": `${bead.size}px`,
              "--bead-color": bead.color,
              "--bead-glow": `${bead.color}33`,
              "--bead-delay": `${bead.delay}ms`,
            } as CSSProperties
          }
        />
      ))}
    </div>
  );
}
