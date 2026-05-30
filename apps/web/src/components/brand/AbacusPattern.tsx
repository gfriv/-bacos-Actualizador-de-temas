import { cn } from "@/lib/utils";

const beads = [
  ["bg-abacos-blue", "left-[14%]"],
  ["bg-abacos-green", "left-[30%]"],
  ["bg-abacos-yellow", "left-[54%]"],
  ["bg-abacos-red", "left-[76%]"],
];

export function AbacusPattern({ className }: { className?: string }) {
  return (
    <div className={cn("relative overflow-hidden rounded-lg border border-border bg-white", className)} aria-hidden>
      <div className="absolute inset-x-4 top-1/4 h-px bg-abacos-black/15" />
      <div className="absolute inset-x-4 top-1/2 h-px bg-abacos-black/15" />
      <div className="absolute inset-x-4 top-3/4 h-px bg-abacos-black/15" />
      {beads.map(([color, left], row) =>
        [0, 1, 2].map((line) => (
          <span
            key={`${row}-${line}`}
            className={cn(
              "absolute h-3 w-3 rounded-full shadow-sm",
              color,
              left,
              line === 0 && "top-[calc(25%-6px)]",
              line === 1 && "top-[calc(50%-6px)] translate-x-8",
              line === 2 && "top-[calc(75%-6px)] -translate-x-4",
            )}
          />
        )),
      )}
    </div>
  );
}
