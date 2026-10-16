# ROX Wiki Design System — Master Specification (SSOT)

> **Global Source of Truth for ROX Wiki & DPS Simulator.**
> Governs visual hierarchy, OLED dark obsidian theme, typography, component tokens, accessibility, and zero-layout-shift rules.
> For page-specific overrides, see `docs/design-system/rox-wiki/pages/simulator.md`.

---

## 1. Core Principles

1. **Information-Dense Gaming Tool**:
   - High signal-to-noise ratio: every pixel, badge, and color communicates game mechanics.
   - Zero AI slop, zero arbitrary drop-shadow blobs, zero cartoon emoji icons (use SVG or in-game asset sprites).
   - Eradicate developer jargon (`[PILLAR 02]`, `SSOT Golden Ref`, ASCII brackets).
   - 100% Authentic In-Game Ragnarok X (ROX Global / SEA) English terminology.

2. **Zero Layout Shift (CLS < 0.01)**:
   - All numbers, damage meters, combat telemetry, and stat steppers must use tabular figures (`font-variant-numeric: tabular-nums`).
   - Container heights and column widths are fixed or use CSS Grid aspect ratios to prevent jumping during calculation cycles.

3. **Accessibility & Eye Comfort (WCAG AAA)**:
   - Deep OLED Obsidian palette (`#090D16`) eliminates eye fatigue during multi-hour theorycrafting sessions.
   - Text contrast ratio exceeds 15:1 for primary headings and 5.5:1 for secondary metadata.
   - Interactive touch targets strictly adhere to minimum 44×44px with 8px gaps.

---

## 2. Design Tokens & Color Palette

### 2.1 Surfaces & Elevational Depth (OLED Dark Obsidian)

```css
:root {
  /* Tonal Surface Depths */
  --bg-canvas: #090D16;          /* Deepest obsidian void background */
  --bg-card: #111827;            /* Bento card tile surface (+8% luminance) */
  --bg-elevated: #182234;        /* Center modal popups & slide-over drawers */
  --bg-input: #0B101B;           /* Recessed input / field container */
  --bg-hover: #1E293B;           /* Hover highlight state (150ms transition) */

  /* Structural Dividers */
  --border-subtle: #1E293B;      /* Low-contrast component boundaries */
  --border-card: #233044;        /* Bento card outline */
  --border-focus: #38BDF8;       /* Active focus / selection ring */

  /* Typographic Contrast */
  --text-primary: #F8FAFC;       /* 15.2:1 contrast — headers, stat values, DPS */
  --text-secondary: #CBD5E1;     /* 10.4:1 contrast — item names, tab labels */
  --text-muted: #94A3B8;         /* 5.5:1 contrast — tags, units, empty states */
  --text-disabled: #475569;      /* 3.1:1 contrast — locked slots, read-only */
}
```

### 2.2 ROX Quality Tier Palette (In-Game Quality ADN)

```css
:root {
  --tier-white: #CBD5E1;         /* Normal / Common */
  --tier-blue: #38BDF8;          /* Rare / Valuables / Upgrade */
  --tier-purple: #A855F7;        /* Epic / Valkyrie / Purple Cards */
  --tier-gold: #F59E0B;          /* Legendary / MVP / Flash Proc / Refine */
  --tier-red: #EF4444;           /* Ancient / Divine Artifacts */
}
```

### 2.3 Detailed Stat Calibrator & Delta Tokens

```css
:root {
  /* Positive Delta (Buff / Gain) */
  --offset-pos: #10B981;
  --offset-pos-bg: rgba(16, 185, 129, 0.08);
  --offset-pos-border: #10B981;

  /* Negative Delta (Debuff / Reduction) */
  --offset-neg: #F43F5E;
  --offset-neg-bg: rgba(244, 63, 94, 0.08);
  --offset-neg-border: #F43F5E;

  /* Neutral / Zero Delta */
  --offset-zero: #475569;
  --offset-zero-bg: #0B101B;
  --offset-zero-border: #1E293B;
}
```

### 2.4 Combat Telemetry & DPS Meters

```css
:root {
  --hud-dps: #F59E0B;            /* Amber Gold — Live 60s DPS ticker */
  --hud-total: #38BDF8;          /* Electric Cyan — 3m Total Damage */
  --hud-crit: #F43F5E;           /* Crimson Rose — Critical Hit Damage */
  --hud-normal: #E2E8F0;         /* Silver White — Normal Hit Damage */
  --hud-speed: #06B6D4;          /* Aqua Speed — ASPD / Haste Cooldown */
}
```

### 2.5 Elemental Counters Matrix (ROX 10 Elements)

```css
:root {
  --elem-neutral: #94A3B8;
  --elem-water: #06B6D4;
  --elem-earth: #D97706;
  --elem-fire: #EF4444;
  --elem-wind: #10B981;
  --elem-poison: #8B5CF6;
  --elem-holy: #FCD34D;
  --elem-shadow: #6366F1;
  --elem-ghost: #EC4899;
  --elem-undead: #94A3B8;
}
```

---

## 3. Typography & Spacing Standard

### 3.1 Type Scale

- **Display & Big KPI**: Orbitron or Outfit, 28px – 32px, Bold 700.
- **Section Headers**: Outfit / Inter, 14px – 16px, Semi-Bold 600, Uppercase, tracking +0.05em.
- **Interactive Body / Labels**: Inter, 12px – 14px, Regular 400 & Medium 500.
- **Numeric Values & Formulas**: JetBrains Mono, 11px – 14px, `font-variant-numeric: tabular-nums;`.

### 3.2 Spacing System (4pt / 8dp Grid)

| Token | Pixels | Usage |
| :--- | :---: | :--- |
| `--space-xs` | `4px` | Badge padding, micro gaps between pills |
| `--space-sm` | `8px` | Gap between slot badges, input inner padding |
| `--space-md` | `12px`| Bento tile compact inner padding |
| `--space-lg` | `16px`| Bento grid gutter, modal content padding |
| `--space-xl` | `24px`| Modal outer padding, major section margins |

---

## 4. Component Rules

### 4.1 Bento Box Tiles
- Border radius: `12px` (compact) or `16px` (standard).
- Background: `--bg-card` with 1px border `--border-card`.
- Hover state: Subtle border glow `--border-focus` with 150ms ease transition.

### 4.2 Interactive Center Modals
- Backdrop: `rgba(9, 13, 22, 0.75)` with `backdrop-filter: blur(8px)`.
- Modal Dialog: Centered fixed position, max-width 640px – 720px, max-height 85vh.
- Animation: Scale 0.96 $\rightarrow$ 1.0, Opacity 0 $\rightarrow$ 1 in 200ms ease-out.
- Keyboard: `Escape` closes modal, `Enter` confirms changes. Focus trapped inside modal.

### 4.3 Number Steppers & Delta Inputs
- No native arrow spinners (disable `-webkit-inner-spin-button`).
- Always show explicit prefix: `+` for positive values, `-` for negative.
- Live reactive change triggers recalculation within 16ms without page reload.
