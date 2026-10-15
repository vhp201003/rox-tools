# ROX Wiki Design Specification: Command Cockpit Edition

> **A high-performance, information-dense, zero-slop design system for ROX: Ragnarok X Game Database & Wiki.**
> **Philosophy:** Actionable game intelligence, zero AI slop, dual-mode versatility (Ledger vs Compendium), Bento Grid inspection.

---

## 1. Core Principles

1. **Zero AI Slop & Zero Decorative Gimmicks**:
   - No random emoji characters anywhere in UI controls, headers, or status chips.
   - No fake drop-shadow blobs or gratuitous purple gradient goo.
   - No rigid ASCII brackets (`[...]` completely eradicated).
   - High Signal-to-Noise Ratio: Every pixel and color communicates game mechanics.
   - Game asset sprites (`/static/monsters/{id}.png`, `/static/cards/{id}.png`) are genuine game data.

2. **Dual-Mode Data Representation**:
   - **Ledger View (Default)**: High-density, fast-scanning table view (36-40px row height) featuring horizontal mini progress meters for `DEF %` and `M.DEF %`, size tags (`S`, `M`, `L`), and semantic element tags.
   - **Compendium View**: Responsive card grid showcasing monster artwork, quick stat overviews, element/race tags, and direct drop previews.

3. **Smart Intent Presets (Omni-Presets)**:
   - One-click shortcuts for frequent game queries:
     - `BEST EXP (LV 60-75)`: Sweetspot farming zone.
     - `LOW DEF (< 30%)`: Vulnerable targets for fast farming.
     - `HIGH M.DEF (> 50%)`: High magic resistance targets.
     - `NIGHT WEATHER MVP`: Direct access to night drop bosses.
     - `WEAK TO FIRE`: Targets taking 150-200% fire damage.
     - `WEAK TO WATER`: Targets taking 200% water damage.

4. **Bento Matrix Inspector**:
   - Five dedicated modules inside the deep inspection drawer:
     - **Identity & Profile**: High-res avatar, name, ID, CN name, boss tier, element with semantic left accent, race, size.
     - **Combat Attributes & Efficiency**: Max HP, Base P.DEF / M.DEF, EXP, Zeny, Hit, Flee, Crit, Anti-Crit, and `EXP/kHP` efficiency ratio.
     - **Defense & Penetration Target**: Visual horizontal gauges for physical and magical defense reduction + target penetration % needed to reduce target DEF to 0.
     - **Weapon Size Matchup Table**: Real-time damage penalty matrix for Dagger, 1H Sword, 2H Sword, Spear, Bow, and Staff according to monster size (Small, Medium, Large).
     - **Weather Phase Card Vault**: Segmented switcher for Day, Night, and Void drops with official game card art, quality-colored border, equipment slot, and combat/deposit buffs.

5. **Zero-Build Architecture**:
   - Standard HTML5 + Scoped CSS Custom Properties + Modular Vanilla ES6 JavaScript.
   - Served directly by FastAPI. Instant load times, zero bundle overhead.

---

## 2. Design Tokens & Color Palette

### 2.1 CSS Variables

```css
:root {
  --bg-canvas: #090d16;
  --bg-surface: #101626;
  --bg-subtle: #162035;
  --bg-muted: #1c2942;
  --bg-hover: #1e2c47;
  --border: rgba(255, 255, 255, 0.08);
  --border-strong: rgba(255, 255, 255, 0.16);
  --border-focus: #3b82f6;

  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --text-muted: #73849f;

  /* 10 Semantic ROX Element Tokens */
  --elem-neutral: #94a3b8;
  --elem-water: #3b82f6;
  --elem-earth: #f59e0b;
  --elem-fire: #ef4444;
  --elem-wind: #10b981;
  --elem-poison: #14b8a6;
  --elem-holy: #eab308;
  --elem-shadow: #8b5cf6;
  --elem-ghost: #06b6d4;
  --elem-undead: #a855f7;

  /* Card & Boss Quality Tokens */
  --tier-mvp: #f59e0b;
  --tier-mini: #a855f7;
  --card-white: #94a3b8;
  --card-blue: #38bdf8;
  --card-purple: #c084fc;
  --card-gold: #f59e0b;

  --radius-sm: 4px;
  --radius: 8px;
  --radius-pill: 9999px;
}
```

---

## 3. Keyboard Shortcuts

- `/` : Focus search input immediately.
- `Escape` : Dismiss monster dossier drawer.
