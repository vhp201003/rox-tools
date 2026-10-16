# ROX Wiki & DPS Simulator — Design Specification

> **Comprehensive UI/UX Design System for Ragnarok X: Next Generation Database & DPS Simulator.**  
> Built with zero AI slop, OLED Dark Obsidian theme, Modular Bento Architecture, and Detailed Stat Delta Calibration.

---

## 1. Design System Hierarchy

This project follows the **Master + Page Overrides** design system structure:

- **Global Master Specification**: [`docs/design-system/rox-wiki/MASTER.md`](file:///D:/CenNextWorkSpace/rox-tool/docs/design-system/rox-wiki/MASTER.md)  
  *Defines color tokens, typography, spacing, elevational depth, quality tiers, and accessibility guidelines.*
- **Simulator & Calibrator Page Override**: [`docs/design-system/rox-wiki/pages/simulator.md`](file:///D:/CenNextWorkSpace/rox-tool/docs/design-system/rox-wiki/pages/simulator.md)  
  *Defines the 4-Bento Modular Architecture, Center Modal micro-editing flow, Detailed Stat Sheet, and +/- Delta Offset mechanics.*

---

## 2. Core Principles

1. **Information-Dense Gaming Tool**:
   - Zero AI slop: no arbitrary emoji icons, no fake drop-shadow gradients, no ASCII brackets.
   - Genuine game assets: official card artwork, monster sprites, and element iconography.
   - 100% In-Game ROX English terminology (`Equipment`, `Combat`, `Costume`, `Inscriptions`, `Flash Proc`, `Companions`, `Elemental Counters`).

2. **Dual-Mode Versatility**:
   - **Mode 1: Wiki Database**: High-density ledger table and responsive monster card compendium with deep bento inspection drawer.
   - **Mode 2: DPS Simulator Cockpit**: 4-Bento modular dashboard with focused center modals and real-time damage telemetry.
   - **1-Click Bridge**: Seamlessly simulate DPS against any monster directly from its Wiki details card.

3. **Zero Layout Shift (CLS < 0.01)**:
   - All numerical meters, DPS counters, and delta inputs use `font-variant-numeric: tabular-nums` and monospace styling.
   - Numbers update in-place without triggering layout reflows.

---

## 3. The 4-Bento Simulator Architecture

```
+-------------------------------------------------------------+-------------------------------------------------------------+
| BENTO 1: EQUIPMENT & SOCKETS                                | BENTO 3: COMBAT TELEMETRY HUD                               |
| • 8 Combat slots (2-col balanced: 4 Weapon/Acc, 4 Armor)   | • Target monster selector (Drake, Dracula, Strouf...)       |
| • 6 Costume slots tab                                       | • Live Average DPS (60s), Total Damage (3m)                |
| • Quick Refine, Upgrade, Enchant, Card socket pills         | • Crit Hit, Normal Hit, Waterfall Damage Trace log          |
+-------------------------------------------------------------+-------------------------------------------------------------+
| BENTO 2: SECONDARY SYSTEMS TILES                            | BENTO 4: DETAILED STAT CALIBRATOR (Master Merged Sheet)     |
| • Base Stats Tile: STR/AGI/VIT points (Click ➔ Modal)       | • 4 Columns: Stat Name | Gear Base | +/- Offset | Total    |
| • Divinity Inscriptions Tile: 8 Parts + Flash (Click ➔ Modal)| • Live delta inputs (+/-) for what-if min-max testing       |
| • Companions Tile: 4 Active Pets (Click ➔ Modal)            | • Immediate 1:1 match with in-game Character Sheet          |
| • Buffs & Titles Tile: Food, Awakening, Guild (Click ➔ Modal)| • Instant 16ms calculation reactivity                       |
+-------------------------------------------------------------+-------------------------------------------------------------+
```

---

## 4. Color Palette & Design Tokens

### 4.1 Tonal Surfaces (OLED Dark Obsidian)
- **Canvas Background**: `#090D16` (Deep void, zero glare).
- **Card Surface**: `#111827` (Slate 900, +8% luminance).
- **Elevated Modals & Drawers**: `#182234` (+14% luminance, `backdrop-filter: blur(8px)`).
- **Subtle Borders**: `#1E293B`.
- **Primary Text**: `#F8FAFC` (15.2:1 contrast ratio).
- **Muted Text**: `#94A3B8` (5.5:1 contrast ratio).

### 4.2 In-Game Quality Tiers
- **White (Normal)**: `#CBD5E1`
- **Blue (Rare / Upgrade)**: `#38BDF8`
- **Purple (Epic / Valkyrie)**: `#A855F7`
- **Gold (Legendary / MVP / Flash)**: `#F59E0B`
- **Red (Ancient / Divine)**: `#EF4444`

### 4.3 Detailed Stat Calibrator Tokens
- **Positive Offset (`+`)**: Emerald `#10B981` (Border) / `rgba(16, 185, 129, 0.08)` (Background).
- **Negative Offset (`-`)**: Rose `#F43F5E` (Border) / `rgba(244, 63, 94, 0.08)` (Background).
- **Zero Offset (`0`)**: Slate `#1E293B` (Border) / `#0B101B` (Background).

### 4.4 Combat Results
- **Average DPS**: `#F59E0B` (Amber Gold, 28px Mono).
- **Total Damage**: `#38BDF8` (Electric Cyan).
- **Critical Hit**: `#F43F5E` (Crimson Rose).
- **Normal Hit**: `#E2E8F0` (Silver White).

---

## 5. Keyboard Navigation & Accessibility

- `/` : Focus search input immediately.
- `Escape` : Dismiss monster drawer or active center modal.
- `Enter` : Confirm and close active modal.
- All clickable elements enforce minimum 44×44px hit target with visible focus rings.
