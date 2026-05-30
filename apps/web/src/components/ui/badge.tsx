import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
  {
    variants: {
      variant: {
        default: "border-transparent bg-abacos-red text-white",
        secondary: "border-transparent bg-abacos-red-soft text-abacos-red-dark",
        outline: "border-border text-abacos-gray",
        blue: "border-transparent bg-blue-50 text-abacos-blue",
        green: "border-transparent bg-green-50 text-abacos-green",
        yellow: "border-transparent bg-yellow-50 text-[#7a5b00]",
        gray: "border-transparent bg-neutral-100 text-abacos-gray",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
