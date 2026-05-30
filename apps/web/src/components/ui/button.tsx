import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "button-premium inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-abacos-red disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-abacos-red text-white shadow-[0_10px_24px_rgba(178,13,34,0.22)] hover:bg-abacos-red-dark",
        secondary: "bg-abacos-red-soft text-abacos-red-dark hover:bg-[#f2d4d8]",
        outline: "border border-border bg-white text-abacos-black hover:border-abacos-red-soft hover:bg-abacos-light",
        ghost: "text-abacos-gray hover:bg-abacos-red-soft hover:text-abacos-red-dark",
        destructive: "bg-abacos-red-dark text-white hover:bg-abacos-red",
      },
      size: {
        default: "h-10 px-4",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-5",
        icon: "h-10 w-10 px-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
    );
  },
);
Button.displayName = "Button";

export { buttonVariants };
