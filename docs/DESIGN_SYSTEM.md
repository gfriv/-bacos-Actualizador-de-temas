# Design System

## Identity

The UI is inspired by Academia Ábacos: academic, close, professional and clear. It should feel like a serious tool for teachers, not a generic startup dashboard.

## Color Tokens

- `--abacos-red: #B20D22`
- `--abacos-red-dark: #8F0A1B`
- `--abacos-red-soft: #F8E8EA`
- `--abacos-black: #1E1E1E`
- `--abacos-gray: #4A4A4A`
- `--abacos-light: #F7F7F5`
- `--abacos-white: #FFFFFF`
- `--abacos-blue: #1F5EA8`
- `--abacos-green: #4C9A4B`
- `--abacos-yellow: #E6B72E`

## Usage

- Red is the primary action color. Use it sparingly.
- General backgrounds stay light.
- Cards are white with discreet borders.
- Headers can use small red rails, not heavy red blocks.
- Status colors:
  - pending: yellow;
  - approved: green;
  - rejected: gray or soft red;
  - processing: blue.

## Abacus Motif

Use subtle rails, circular beads and modular separators. Avoid decorative excess. The motif should support hierarchy and rhythm.

## Logo

The logo is integrated as brand assets in `apps/web/public/brand`:

- `abacos-logo-transparent.png` for the full institutional mark with transparent background.
- `abacos-logo.svg` as the previous vector fallback.
- `abacos-mark.svg` for compact navigation surfaces.

Use `AbacosLogo` instead of embedding image tags directly, so sizing and accessibility remain consistent.

## Tone

Spanish from Spain. Professional, academic and clear. Interface text should address teachers and reinforce that human validation is mandatory.

## Dashboard Pattern

The dashboard is an operational work surface, not a marketing page. It should show:

- the next action for the teacher;
- a compact metric row with contextual tooltips;
- an operational radar with distribution by workflow state;
- motion feedback for priority cards and review actions;
- a workflow map for document state;
- a review queue for projects that need human decisions;
- a detailed table below the overview.

Tooltips are used for definitions and scope, not for hiding core instructions. Every metric must explain what it counts and why it matters.

## Motion And Polish

- Use restrained motion for hierarchy: card entrance, hover elevation and button light sweeps.
- Primary buttons may use a subtle glow only on important actions such as review, consolidation or demo access.
- Avoid looping decorative animation that distracts from reading.
- Charting must support operational decisions, not decorate empty space.
- The product ships with an optional night mode. It uses black backgrounds, off-white and gold typography, and red Ábacos as a restrained accent. It must remain a professional reading mode, not a neon theme.
