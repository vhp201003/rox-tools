# Page Design Specification: DPS Simulator & Calibrator Cockpit

> **Parent:** `docs/design-system/rox-wiki/MASTER.md`  
> **Route / View:** `#tab-content-sim` (DPS Simulator Mode)  
> **Focus:** 4-Cluster Bento Architecture, Micro-Editing Center Modals, Detailed Stat Calibrator (+/- Delta Table).

---

## 1. Modular Bento Architecture (4 Clusters)

The Simulator interface is arranged into 4 distinct Bento Clusters:

```
+-----------------------------------------------------------+-----------------------------------------------------------+
| BENTO 1: EQUIPMENT & SOCKETS (320px - 380px)              | BENTO 3: COMBAT TELEMETRY HUD (360px - 420px)             |
| Balanced 2-Column Paper Doll (4 Combat Left, 4 Right)     | Target Monster Selector, Live 60s DPS, 3m Total Damage,   |
| 6 Costume Slots Tab. Click slot to open Equipment Drawer. | Crit & Normal Hit damage, Waterfall damage trace.         |
+-----------------------------------------------------------+-----------------------------------------------------------+
| BENTO 2: SECONDARY SYSTEMS TILES                          | BENTO 4: DETAILED STAT CALIBRATOR (Master Merged Sheet)   |
| Compact tiles: Base Stats, Inscriptions, Companions,      | Consolidated stat table: Derived Gear Base + Manual +/-   |
| Combat Buffs. Click tile to open Center Modal Popup.      | Delta Offset = Effective Total Stat. Instant recalculate. |
+-----------------------------------------------------------+-----------------------------------------------------------+
```

---

## 2. Interaction Flow: Micro-Editing via Center Modals

### 2.1 The 3-Step User Journey

1. **Glance & Identify (Bento 1 & 2)**:
   - User sees high-level status badges on the Bento tile (e.g., `8/8 Inscriptions Active`, `4/4 Companions Configured`, `STR 99 / AGI 80`).
   - Clicking the tile or the edit button `[✎]` triggers the dedicated **Center Modal**.

2. **Focused Editing in Center Modal**:
   - Background is darkened and blurred (`backdrop-filter: blur(8px)`).
   - Only the controls for that specific subsystem are active:
     - **Divinity Modal**: Quality (Blue/Purple/Gold), Level (Lv.0–Lv.7), Flash Proc toggle, 2 Substat Inscription chips.
     - **Companion Modal**: 4 Companion tabs (Spark, Wraith, Cloudsong, Bubbles), 3 Offense lines + 3 Defense lines.
     - **Base Stats Modal**: STR, AGI, VIT, INT, DEX, LUK sliders and allocated points tally.
     - **Buffs & Titles Modal**: Food buffs, Potions, Awakening tiers, Guild blessings.
   - Closing the modal (`ESC`, `[✕]`, or `[Confirm]`) updates the Bento tile immediately.

3. **Auto-Aggregation into Detailed Stat Sheet (Bento 4)**:
   - Closing any modal automatically runs the client-side aggregation function `calculateDerivedStats()`.
   - All stat contributions are summed and populated into the `GEAR BASE` column of Bento 4.

---

## 3. Bento 4: Detailed Stat Calibrator (+/- Delta Table)

### 3.1 Table Schema

Every combat-relevant stat in ROX is represented in a 4-column row:

| Column | Type | Width | Description |
| :--- | :---: | :---: | :--- |
| **Stat Name** | Text | 32% | Official ROX English in-game stat identifier. |
| **Gear Base** | Readonly Number | 22% | Auto-calculated sum from Bento 1 & 2 (Muted silver `#94A3B8`). |
| **+/- Offset** | Editable Input | 24% | User delta adjustment (`step="any"`). Emerald if positive, Rose if negative. |
| **Effective Total** | Computed Value | 22% | Final stat passed to Python DPS Engine (`Base + Offset`). Highlighted white. |

### 3.2 Stat Group Hierarchy

Rows are grouped into collapsible accordions mirroring the in-game Character Sheet:
1. **Base Offense**: `P.ATK`, `M.ATK`, `P.ATK%`, `M.ATK%`, `Final ASPD`, `Final Haste`.
2. **Penetration & Defense Ignore**: `Final P.PEN`, `Final M.PEN`, `P.Ignore DEF`, `M.Ignore DEF`.
3. **Critical Multipliers**: `Final Crit`, `Crit DMG Bonus`.
4. **Special Bonus DMG**: `Final P.DMG Bonus`, `Final M.DMG Bonus`, `Bonus DMG to Size (S/M/L)`, `Bonus DMG to Race`, `Bonus DMG to Target Quality (MVP/Mini)`, `Element Enhance`.

### 3.3 Visual States for Offset Input

```css
/* Positive Offset (> 0) */
.offset-input[data-state="positive"] {
  border-color: #10B981;
  background-color: rgba(16, 185, 129, 0.08);
  color: #34D399;
}

/* Negative Offset (< 0) */
.offset-input[data-state="negative"] {
  border-color: #F43F5E;
  background-color: rgba(244, 63, 94, 0.08);
  color: #FB7185;
}

/* Zero / Unmodified Offset (== 0) */
.offset-input[data-state="zero"] {
  border-color: #1E293B;
  background-color: #0B101B;
  color: #64748B;
}
```

---

## 4. Real-time Calculation Reactivity

- Any change in the `[+/- Offset]` input triggers `markDirty('stat_offsets')`.
- The frontend debounces computation by **80ms**:
  1. Computes `effective_stats` locally.
  2. Sends payload to `POST /api/sim/calculate`.
  3. Updates the live DPS ticker in Bento 3.
- If network latency > 200ms, the DPS ticker shows a subtle shimmer animation without blocking input.
