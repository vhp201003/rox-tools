(function () {
  "use strict";

  const state = {
    tab: "monster", // "monster" | "mvp"
    viewMode: "ledger", // "ledger" | "compendium"
    page: 1,
    limit: 20,
    totalPages: 1,
    totalCount: 0,
    search: "",
    race: "",
    element: "",
    minLevel: "",
    maxLevel: "",
    sortBy: "level_asc",
    groupBy: "none", // "none" | "race" | "element"
    activePreset: null,
    debounceTimer: null,
    activeItem: null,
    abortController: null,
    cachedItems: []
  };

  const ELEMENT_HINTS = {
    "Neutral": { name: "NEUTRAL", icon: "neutral.png", glyph: "○", bg: "elem-bg-neutral" },
    "Water": { name: "WATER", icon: "water.png", glyph: "◆", bg: "elem-bg-water" },
    "Earth": { name: "EARTH", icon: "earth.png", glyph: "■", bg: "elem-bg-earth" },
    "Fire": { name: "FIRE", icon: "fire.png", glyph: "▲", bg: "elem-bg-fire" },
    "Wind": { name: "WIND", icon: "wind.png", glyph: "»", bg: "elem-bg-wind" },
    "Poison": { name: "POISON", icon: "poison.png", glyph: "⬡", bg: "elem-bg-poison" },
    "Holy": { name: "HOLY", icon: "holy.png", glyph: "✦", bg: "elem-bg-holy" },
    "Shadow": { name: "SHADOW", icon: "shadow.png", glyph: "●", bg: "elem-bg-shadow" },
    "Ghost": { name: "GHOST", icon: "ghost.png", glyph: "◇", bg: "elem-bg-ghost" },
    "Undead": { name: "UNDEAD", icon: "undead.png", glyph: "✝", bg: "elem-bg-undead" }
  };

  const RACE_BORDERS = {
    "Demi-Human": "race-border-demi-human",
    "Brute": "race-border-brute",
    "Undead": "race-border-undead",
    "Demon": "race-border-demon",
    "Insect": "race-border-insect",
    "Fish": "race-border-fish",
    "Plant": "race-border-plant",
    "Dragon": "race-border-dragon",
    "Angel": "race-border-angel",
    "Formless": "race-border-formless"
  };

  const ELEMENT_DEFENSE_MULTIPLIERS = {
    "Neutral": { "Neutral": 100, "Water": 100, "Earth": 100, "Fire": 100, "Wind": 100, "Poison": 100, "Holy": 100, "Shadow": 100, "Ghost": 70, "Undead": 100 },
    "Water": { "Wind": 175, "Neutral": 100, "Holy": 100, "Shadow": 100, "Earth": 90, "Water": 25, "Fire": 50, "Poison": 100, "Ghost": 100, "Undead": 100 },
    "Earth": { "Fire": 175, "Neutral": 100, "Holy": 100, "Shadow": 100, "Wind": 90, "Earth": 25, "Water": 100, "Poison": 100, "Ghost": 100, "Undead": 100 },
    "Fire": { "Water": 175, "Neutral": 100, "Holy": 100, "Shadow": 100, "Earth": 50, "Fire": 25, "Wind": 90, "Poison": 100, "Ghost": 100, "Undead": 100 },
    "Wind": { "Earth": 175, "Neutral": 100, "Holy": 100, "Shadow": 100, "Water": 90, "Wind": 25, "Fire": 100, "Poison": 100, "Ghost": 100, "Undead": 100 },
    "Poison": { "Fire": 125, "Holy": 125, "Earth": 125, "Wind": 125, "Water": 100, "Poison": 0, "Shadow": 50, "Ghost": 100, "Undead": 50, "Neutral": 100 },
    "Holy": { "Shadow": 150, "Undead": 150, "Neutral": 100, "Water": 75, "Earth": 75, "Fire": 75, "Wind": 75, "Poison": 100, "Ghost": 100, "Holy": 0 },
    "Shadow": { "Holy": 150, "Neutral": 100, "Water": 100, "Earth": 100, "Fire": 100, "Wind": 100, "Poison": 50, "Undead": 0, "Shadow": 0, "Ghost": 100 },
    "Ghost": { "Ghost": 150, "Neutral": 25, "Water": 100, "Earth": 100, "Fire": 100, "Wind": 100, "Holy": 75, "Shadow": 75, "Poison": 100, "Undead": 100 },
    "Undead": { "Fire": 175, "Holy": 175, "Neutral": 100, "Water": 100, "Earth": 100, "Wind": 100, "Poison": 0, "Shadow": 0, "Ghost": 100, "Undead": 0 }
  };

  const DOM = {
    html: document.documentElement,
    themeBtn: document.getElementById("btn-theme"),
    breadcrumb: document.getElementById("breadcrumb"),
    navTabs: document.getElementById("nav-tabs"),
    viewSwitcher: document.getElementById("view-switcher"),
    btnViewLedger: document.getElementById("btn-view-ledger"),
    btnViewCompendium: document.getElementById("btn-view-compendium"),
    ledgerView: document.getElementById("ledger-view"),
    compendiumView: document.getElementById("compendium-view"),
    compendiumGrid: document.getElementById("compendium-grid"),
    searchInput: document.getElementById("search-input"),
    btnClearSearch: document.getElementById("btn-clear-search"),
    filterMinLevel: document.getElementById("filter-min-level"),
    filterMaxLevel: document.getElementById("filter-max-level"),
    sortSelect: document.getElementById("sort-select"),
    groupSelect: document.getElementById("group-select"),
    btnReset: document.getElementById("btn-reset"),
    totalCount: document.getElementById("total-count"),
    presetChips: document.getElementById("preset-chips"),
    tableHead: document.getElementById("table-head"),
    tableBody: document.getElementById("table-body"),
    emptyState: document.getElementById("empty-state"),
    pageNum: document.getElementById("page-num"),
    pageTotal: document.getElementById("page-total"),
    limitSelect: document.getElementById("limit-select"),
    btnPrev: document.getElementById("btn-prev"),
    btnNext: document.getElementById("btn-next"),
    drawer: document.getElementById("drawer"),
    drawerTitle: document.getElementById("drawer-title"),
    drawerBody: document.getElementById("drawer-body"),
    btnCloseDrawer: document.getElementById("btn-close-drawer"),
    backdrop: document.getElementById("backdrop"),
    racePillRow: document.getElementById("race-pill-row"),
    elementPillRow: document.getElementById("element-pill-row"),
    filterBar: document.querySelector(".filter-bar"),
    paginationBar: document.querySelector(".pagination-bar"),
    simulatorView: document.getElementById("simulator-view")
  };

  function initTheme() {
    const saved = localStorage.getItem("rox_theme") || "dark";
    setTheme(saved);
    DOM.themeBtn.addEventListener("click", () => {
      const next = DOM.html.getAttribute("data-theme") === "dark" ? "light" : "dark";
      setTheme(next);
    });
  }

  function setTheme(t) {
    DOM.html.setAttribute("data-theme", t);
    localStorage.setItem("rox_theme", t);
    DOM.themeBtn.textContent = `THEME: ${t.toUpperCase()}`;
  }

  window.handleSpriteError = function (img) {
    const id = img.dataset.id;
    const resid = img.dataset.resid;
    const src = img.src || "";
    if (id && src.includes("/static/monsters/")) {
      if (resid && resid !== id && !src.includes(`/${resid}.png`)) {
        img.src = `/static/monsters/${resid}.png`;
      } else {
        img.src = `/static/cards/${id}.png`;
      }
    } else if (id && src.includes("/static/cards/")) {
      img.src = `/static/items/${id}.png`;
    } else {
      img.style.display = "none";
      if (img.nextElementSibling) {
        img.nextElementSibling.style.display = "inline-block";
      }
    }
  };

  function formatNum(n) {
    if (n === null || n === undefined || isNaN(n)) return "0";
    return Number(n).toLocaleString("en-US");
  }

  function formatPct(n) {
    if (n === null || n === undefined || isNaN(n)) return "0.0%";
    return `${Number(n).toFixed(1)}%`;
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function getFillClass(val) {
    const v = Number(val) || 0;
    if (v < 30) return "fill-low";
    if (v <= 60) return "fill-mid";
    return "fill-high";
  }

  function renderSplitBadge(raceName, elementName) {
    const race = (raceName || "Unknown").toUpperCase();
    const elem = elementName || "Neutral";
    const hint = ELEMENT_HINTS[elem] || { name: elem.toUpperCase(), icon: "neutral.png", glyph: "•", bg: "elem-bg-neutral" };
    return `
      <div class="split-badge" title="Race: ${escapeHtml(race)} · Element: ${escapeHtml(hint.name)}">
        <span class="split-badge-race">${escapeHtml(race)}</span>
        <span class="split-badge-elem ${hint.bg}">
          <img class="split-badge-icon" src="/static/elements/${hint.icon}" alt="" loading="lazy">
          <span>${hint.name}</span>
        </span>
      </div>
    `;
  }

  async function loadData() {
    if (state.abortController) {
      state.abortController.abort();
    }
    state.abortController = new AbortController();

    DOM.breadcrumb.textContent = `DATABASE / ${state.tab === "mvp" ? "MVP / MINI BOSSES" : "MONSTERS & FIELD"}`;

    const params = new URLSearchParams();
    params.set("category", state.tab);
    params.set("page", state.page);
    params.set("limit", state.limit);
    params.set("sort_by", state.sortBy);

    if (state.search.trim()) params.set("query", state.search.trim());
    if (state.race) params.set("race", state.race);
    if (state.element) params.set("element", state.element);
    if (state.minLevel) params.set("min_level", state.minLevel);
    if (state.maxLevel) params.set("max_level", state.maxLevel);

    try {
      const res = await fetch(`/api/db/monsters?${params.toString()}`, {
        signal: state.abortController.signal
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();

      state.totalCount = data.total;
      state.totalPages = data.total_pages;
      state.cachedItems = data.items || [];

      DOM.totalCount.textContent = formatNum(data.total);
      DOM.pageNum.textContent = data.page;
      DOM.pageTotal.textContent = data.total_pages;
      DOM.btnPrev.disabled = data.page <= 1;
      DOM.btnNext.disabled = data.page >= data.total_pages;

      renderView();
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error("Failed to load data:", err);
      }
    }
  }

  function renderView() {
    const items = state.cachedItems;
    if (!items || items.length === 0) {
      DOM.ledgerView.style.display = "none";
      DOM.compendiumView.style.display = "none";
      DOM.emptyState.style.display = "flex";
      return;
    }
    DOM.emptyState.style.display = "none";

    if (state.viewMode === "ledger") {
      DOM.ledgerView.style.display = "block";
      DOM.compendiumView.style.display = "none";
      renderLedgerTable(items);
    } else {
      DOM.ledgerView.style.display = "none";
      DOM.compendiumView.style.display = "block";
      renderCompendiumGrid(items);
    }
  }

  function renderLedgerTable(items) {
    DOM.tableBody.innerHTML = "";

    if (state.groupBy === "none") {
      items.forEach((item) => {
        DOM.tableBody.appendChild(createTableRow(item));
      });
      return;
    }

    const groupKey = state.groupBy === "race" ? "race_name" : "element_name";
    const groups = {};

    items.forEach((item) => {
      const key = item[groupKey] || "Unknown";
      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    });

    const sortedGroupNames = Object.keys(groups).sort();
    sortedGroupNames.forEach((groupName) => {
      const groupItems = groups[groupName];
      const headerRow = document.createElement("tr");
      headerRow.className = "group-header-row";

      const headerCell = document.createElement("td");
      headerCell.colSpan = 10;
      headerCell.style.background = "var(--bg-subtle)";
      headerCell.style.fontWeight = "700";
      headerCell.style.fontFamily = "var(--font-mono)";
      headerCell.style.fontSize = "11px";
      headerCell.style.letterSpacing = "0.06em";
      headerCell.innerHTML = `
        <span style="color: var(--text-primary);">${escapeHtml(groupName.toUpperCase())}</span>
        <span class="badge" style="margin-left: 8px;">${groupItems.length} ENTITIES</span>
      `;
      headerRow.appendChild(headerCell);
      DOM.tableBody.appendChild(headerRow);

      groupItems.forEach((item) => {
        DOM.tableBody.appendChild(createTableRow(item));
      });
    });
  }

  function createTableRow(item) {
    const tr = document.createElement("tr");
    tr.dataset.id = item.id;
    const raceBorderClass = RACE_BORDERS[item.race_name];
    if (raceBorderClass) tr.classList.add(raceBorderClass);

    const iconSrc = item.icon_url || `/static/monsters/${item.id}.png`;
    const resId = item.res_id || item.id;

    let typeBadge = "";
    if (item.is_mvp) {
      typeBadge = `<span class="badge badge-mvp">MVP</span>`;
    } else if (item.is_mini) {
      typeBadge = `<span class="badge badge-mini">MINI</span>`;
    }

    let cardsBadge = "";
    if (item.is_mvp || item.is_mini) {
      cardsBadge = `
        <span class="badge badge-day">DAY</span>
        <span class="badge badge-night">NIGHT</span>
        <span class="badge badge-void">VOID</span>
      `;
    } else if (item.card_id) {
      cardsBadge = `<span class="badge badge-card">CARD #${item.card_id}</span>`;
    } else {
      cardsBadge = `<span class="badge" style="color: var(--text-muted);">-</span>`;
    }

    const sizeInitial = (item.size_name || "M").charAt(0).toUpperCase();
    const defPct = Number(item.total_def) || 0;
    const mdefPct = Number(item.total_mdef) || 0;

    tr.innerHTML = `
      <td>
        <div class="entity-cell">
          <div class="avatar-wrapper">
            <img class="avatar-img" src="${iconSrc}" alt="" loading="lazy" data-id="${item.id}" data-resid="${resId}" onerror="window.handleSpriteError(this)">
            <span class="avatar-fallback" style="display: none;">${item.id}</span>
          </div>
          <div class="entity-info">
            <div class="entity-name-row">
              <span class="entity-name">${escapeHtml(item.name)}</span>
              ${typeBadge}
            </div>
            <div class="entity-sub mono">#${item.id} ${item.name_cn ? `· ${escapeHtml(item.name_cn)}` : ""}</div>
          </div>
        </div>
      </td>
      <td class="mono font-bold">${item.level}</td>
      <td>
        <span class="badge badge-size" title="${escapeHtml(item.size_name || "Medium")} Size">${sizeInitial}</span>
      </td>
      <td>
        ${renderSplitBadge(item.race_name, item.element_name)}
      </td>
      <td class="mono font-bold">${formatNum(item.max_hp)}</td>
      <td>
        <div class="stat-meter-container">
          <div class="stat-meter-header">
            <span class="mono">${formatPct(defPct)}</span>
          </div>
          <div class="stat-meter-bar">
            <div class="stat-meter-fill ${getFillClass(defPct)}" style="width: ${Math.min(100, Math.max(2, defPct))}%"></div>
          </div>
        </div>
      </td>
      <td>
        <div class="stat-meter-container">
          <div class="stat-meter-header">
            <span class="mono">${formatPct(mdefPct)}</span>
          </div>
          <div class="stat-meter-bar">
            <div class="stat-meter-fill ${getFillClass(mdefPct)}" style="width: ${Math.min(100, Math.max(2, mdefPct))}%"></div>
          </div>
        </div>
      </td>
      <td class="mono">${formatPct(item.total_crit_res)}</td>
      <td class="mono">${formatPct(item.total_flee)}</td>
      <td>${cardsBadge}</td>
    `;

    tr.addEventListener("click", () => openDrawer(item.id));
    return tr;
  }

  function renderCompendiumGrid(items) {
    DOM.compendiumGrid.innerHTML = "";

    items.forEach((item) => {
      const iconSrc = item.icon_url || `/static/monsters/${item.id}.png`;
      const resId = item.res_id || item.id;

      let typeBadge = "";
      if (item.is_mvp) {
        typeBadge = `<span class="badge badge-mvp">MVP</span>`;
      } else if (item.is_mini) {
        typeBadge = `<span class="badge badge-mini">MINI</span>`;
      }

      let cardsBadge = "";
      if (item.is_mvp || item.is_mini) {
        cardsBadge = `
          <span class="badge badge-day">DAY</span>
          <span class="badge badge-night">NIGHT</span>
          <span class="badge badge-void">VOID</span>
        `;
      } else if (item.card_id) {
        cardsBadge = `<span class="badge badge-card">CARD #${item.card_id}</span>`;
      } else {
        cardsBadge = `<span class="badge" style="color: var(--text-muted);">NO CARD</span>`;
      }

      const sizeInitial = (item.size_name || "M").charAt(0).toUpperCase();
      const defPct = Number(item.total_def) || 0;
      const mdefPct = Number(item.total_mdef) || 0;

      const cardEl = document.createElement("div");
      cardEl.className = "compendium-card";
      const raceBorderClass = RACE_BORDERS[item.race_name];
      if (raceBorderClass) cardEl.classList.add(raceBorderClass);
      cardEl.dataset.id = item.id;
      cardEl.innerHTML = `
        <div class="card-top">
          <img class="card-avatar" src="${iconSrc}" alt="" loading="lazy" data-id="${item.id}" data-resid="${resId}" onerror="window.handleSpriteError(this)">
          <div class="card-title-block">
            <div class="card-name" title="${escapeHtml(item.name)}">${escapeHtml(item.name)} ${typeBadge}</div>
            <div class="card-meta">LV ${item.level} · #${item.id}</div>
          </div>
        </div>
        <div class="card-tags">
          <span class="badge badge-size">${sizeInitial} SIZE</span>
          ${renderSplitBadge(item.race_name, item.element_name)}
        </div>
        <div class="card-stats-row">
          <div class="card-stat-item">
            <span class="card-stat-label">HEALTH</span>
            <span class="card-stat-val mono">${formatNum(item.max_hp)}</span>
          </div>
          <div class="card-stat-item">
            <span class="card-stat-label">DEFENSE</span>
            <span class="card-stat-val mono">${formatPct(defPct)}</span>
            <div class="stat-meter-bar" style="margin-top: 3px;">
              <div class="stat-meter-fill ${getFillClass(defPct)}" style="width: ${Math.min(100, Math.max(2, defPct))}%"></div>
            </div>
          </div>
        </div>
        <div class="card-drops-row">
          <span style="font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">DROPS:</span>
          ${cardsBadge}
        </div>
      `;

      cardEl.addEventListener("click", () => openDrawer(item.id));
      DOM.compendiumGrid.appendChild(cardEl);
    });
  }

  function calculateSizeMatchups(sizeName) {
    const s = (sizeName || "Medium").toLowerCase();
    if (s.includes("small")) {
      return [
        { weapon: "Dagger", pct: "100%", tag: "100% Optimal", cls: "penalty-100" },
        { weapon: "Bow", pct: "100%", tag: "100% Optimal", cls: "penalty-100" },
        { weapon: "Staff", pct: "100%", tag: "100% Optimal", cls: "penalty-100" },
        { weapon: "1H Sword", pct: "75%", tag: "75% Reduced", cls: "penalty-75" },
        { weapon: "2H Sword", pct: "75%", tag: "75% Reduced", cls: "penalty-75" },
        { weapon: "Spear", pct: "75%", tag: "75% Reduced", cls: "penalty-75" }
      ];
    } else if (s.includes("large") || s.includes("giant")) {
      return [
        { weapon: "2H Sword", pct: "100%", tag: "100% Optimal", cls: "penalty-100" },
        { weapon: "Spear", pct: "100%", tag: "100% Optimal", cls: "penalty-100" },
        { weapon: "Staff", pct: "100%", tag: "100% Optimal", cls: "penalty-100" },
        { weapon: "1H Sword", pct: "75%", tag: "75% Reduced", cls: "penalty-75" },
        { weapon: "Bow", pct: "75%", tag: "75% Reduced", cls: "penalty-75" },
        { weapon: "Dagger", pct: "50%", tag: "50% Heavy Penalty", cls: "penalty-50" }
      ];
    } else {
      // Medium
      return [
        { weapon: "1H Sword", pct: "100%", tag: "100% Optimal", cls: "penalty-100" },
        { weapon: "2H Sword", pct: "100%", tag: "100% Optimal", cls: "penalty-100" },
        { weapon: "Bow", pct: "100%", tag: "100% Optimal", cls: "penalty-100" },
        { weapon: "Staff", pct: "100%", tag: "100% Optimal", cls: "penalty-100" },
        { weapon: "Dagger", pct: "75%", tag: "75% Reduced", cls: "penalty-75" },
        { weapon: "Spear", pct: "75%", tag: "75% Reduced", cls: "penalty-75" }
      ];
    }
  }

  async function openDrawer(monsterId) {
    DOM.drawer.classList.add("open");
    DOM.backdrop.classList.add("open");
    DOM.drawerTitle.textContent = `LOADING #${monsterId}...`;
    DOM.drawerBody.innerHTML = `
      <div style="padding: 40px 10px; text-align: center; color: var(--text-muted); font-family: var(--font-mono);">
        LOADING STATS & CARDS...
      </div>
    `;

    try {
      const res = await fetch(`/api/db/monsters/${monsterId}`);
      if (!res.ok) throw new Error("HTTP " + res.status);
      const m = await res.json();
      state.activeItem = m;
      renderBentoDrawer(m);
    } catch (err) {
      console.error("Failed to fetch monster details:", err);
      DOM.drawerBody.innerHTML = `
        <div style="padding: 24px; color: #ef4444; font-family: var(--font-mono);">
          FAILED TO LOAD MONSTER DETAILS FOR ID #${monsterId}.
        </div>
      `;
    }
  }

  function renderBentoDrawer(m) {
    DOM.drawerTitle.textContent = `MONSTER DETAILS · ${m.name.toUpperCase()} (#${m.id})`;

    const iconSrc = m.icon_url || `/static/monsters/${m.id}.png`;
    const resId = m.res_id || m.id;

    let tierBadge = "";
    if (m.is_mvp) tierBadge = `<span class="badge badge-mvp">MVP BOSS</span>`;
    else if (m.is_mini) tierBadge = `<span class="badge badge-mini">MINI BOSS</span>`;
    else tierBadge = `<span class="badge badge-elem">MONSTER</span>`;

    const defPct = Number(m.total_def) || 0;
    const mdefPct = Number(m.total_mdef) || 0;
    const critResPct = Number(m.total_crit_res) || 0;
    const fleePct = Number(m.total_flee) || 0;

    const expPerKhp = m.max_hp > 0
      ? (((Number(m.base_exp) || 0) + (Number(m.job_exp) || 0)) / (m.max_hp / 1000)).toFixed(1)
      : "0.0";

    const sizeMatchups = calculateSizeMatchups(m.size_name);
    const sizeTableHtml = `
      <table class="size-matchup-table">
        <thead>
          <tr>
            <th>WEAPON TYPE</th>
            <th>EFFICIENCY</th>
            <th>STATUS</th>
          </tr>
        </thead>
        <tbody>
          ${sizeMatchups.map(w => `
            <tr>
              <td>${w.weapon}</td>
              <td class="mono font-bold">${w.pct}</td>
              <td><span class="penalty-tag ${w.cls}">${w.tag}</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;

    // Weather cards showcase
    let weatherCardsHtml = "";
    const cards = m.cards || [];
    if (cards.length > 0) {
      const hasWeather = cards.some((c) => ["Day", "Night", "Void"].includes(c.weather_phase));

      weatherCardsHtml = `
        <div class="bento-cell">
          <div class="bento-title">CARD DROPS & WEATHER PHASES</div>
          ${hasWeather ? `
            <div class="weather-tabs" id="weather-nav-tabs">
              ${cards.map((c, idx) => `
                <button type="button" class="weather-tab-btn ${idx === 0 ? "active" : ""}" data-card-idx="${idx}">
                  ${c.weather_phase.toUpperCase()}
                </button>
              `).join("")}
            </div>
          ` : ""}
          <div id="active-card-display"></div>
        </div>
      `;
    } else {
      weatherCardsHtml = `
        <div class="bento-cell">
          <div class="bento-title">CARD DROPS</div>
          <div style="color: var(--text-muted); font-size: 12px; font-family: var(--font-mono);">
            NO CARD DROPS RECORDED.
          </div>
        </div>
      `;
    }

    // Variants HTML
    let variantsHtml = "";
    if (m.variants && m.variants.length > 1) {
      variantsHtml = `
        <div class="bento-cell">
          <div class="bento-title">MONSTER LEVEL VARIANTS</div>
          <div class="variants-row">
            ${m.variants.map((v) => `
              <button type="button" class="variant-btn ${v.id === m.id ? "active" : ""}" data-id="${v.id}">
                LV ${v.level} (#${v.id})
              </button>
            `).join("")}
          </div>
        </div>
      `;
    }

    const defendingElem = m.element_name || "Neutral";
    const multipliers = ELEMENT_DEFENSE_MULTIPLIERS[defendingElem] || ELEMENT_DEFENSE_MULTIPLIERS["Neutral"];
    const sortedAttacks = Object.entries(multipliers).sort((a, b) => b[1] - a[1]);

    const weaknessItemsHtml = sortedAttacks.map(([atkElem, mult]) => {
      const hint = ELEMENT_HINTS[atkElem] || { name: atkElem.toUpperCase(), icon: "neutral.png", glyph: "•" };
      let tagClass = "mult-tag-normal";
      if (mult > 100) tagClass = "mult-tag-weak";
      else if (mult < 100) tagClass = "mult-tag-resist";

      return `
        <div class="weakness-card">
          <div class="weakness-name">
            <img class="split-badge-icon" src="/static/elements/${hint.icon}" alt="" loading="lazy">
            <span>${hint.name}</span>
          </div>
          <span class="mult-tag ${tagClass}">${mult}%</span>
        </div>
      `;
    }).join("");

    const weaknessModuleHtml = `
      <div class="bento-cell">
        <div class="bento-title">ELEMENTAL COUNTERS (DEFENDING AS ${defendingElem.toUpperCase()})</div>
        <div class="weakness-grid">
          ${weaknessItemsHtml}
        </div>
      </div>
    `;

    DOM.drawerBody.innerHTML = `
      <!-- Module 1: Core Identity -->
      <div class="bento-cell">
        <div class="bento-identity-top">
          <img class="bento-avatar" src="${iconSrc}" alt="" data-id="${m.id}" data-resid="${resId}" onerror="window.handleSpriteError(this)">
          <div class="bento-identity-info">
            <div class="bento-name">${escapeHtml(m.name)}</div>
            <div class="bento-meta-row">
              <span class="mono">#${m.id}</span>
              ${m.name_cn ? `<span>· ${escapeHtml(m.name_cn)}</span>` : ""}
            </div>
            <div style="display: flex; gap: 6px; margin-top: 4px; flex-wrap: wrap; align-items: center;">
              ${tierBadge}
              ${renderSplitBadge(m.race_name, m.element_name)}
              <span class="badge badge-size">${(m.size_name || "Medium").toUpperCase()} SIZE</span>
            </div>
            <button type="button" class="btn-wiki-test-dps btn-sim-target" id="btn-wiki-test-dps">⚔ Test DPS on this Monster</button>
          </div>
        </div>
      </div>

      <!-- Module 2: Combat Efficiency & Attributes -->
      <div class="bento-cell">
        <div class="bento-title">COMBAT ATTRIBUTES & EXP EFFICIENCY</div>
        <div class="bento-stats-grid">
          <div class="bento-stat-box">
            <div class="bento-stat-name">MAX HEALTH</div>
            <div class="bento-stat-val mono">${formatNum(m.max_hp)}</div>
          </div>
          <div class="bento-stat-box">
            <div class="bento-stat-name">EXP / kHP RATIO</div>
            <div class="bento-stat-val mono" style="color: #10b981;">${expPerKhp} exp/kHP</div>
          </div>
          <div class="bento-stat-box">
            <div class="bento-stat-name">BASE / JOB EXP</div>
            <div class="bento-stat-val mono">${formatNum(m.base_exp)} / ${formatNum(m.job_exp)}</div>
          </div>
          <div class="bento-stat-box">
            <div class="bento-stat-name">ZENY REWARD</div>
            <div class="bento-stat-val mono">${formatNum(m.zeny)} Z</div>
          </div>
          <div class="bento-stat-box">
            <div class="bento-stat-name">RAW P.DEF / M.DEF</div>
            <div class="bento-stat-val mono">${formatNum(m.p_def)} / ${formatNum(m.m_def)}</div>
          </div>
          <div class="bento-stat-box">
            <div class="bento-stat-name">HIT / FLEE</div>
            <div class="bento-stat-val mono">${formatNum(m.hit)} / ${formatNum(m.flee)}</div>
          </div>
          <div class="bento-stat-box">
            <div class="bento-stat-name">CRIT / ANTI-CRIT</div>
            <div class="bento-stat-val mono">${formatNum(m.crit)} / ${formatNum(m.anti_crit)}</div>
          </div>
          <div class="bento-stat-box">
            <div class="bento-stat-name">SPEED / RANGE</div>
            <div class="bento-stat-val mono">${m.move_speed || 0} / ${m.attack_range || 0}m</div>
          </div>
        </div>
      </div>

      <!-- Module 3: Defense & Penetration Target Meters -->
      <div class="bento-cell">
        <div class="bento-title">DEFENSE REDUCTION & PENETRATION TARGET</div>
        <div class="defense-breakdown-box">
          <div class="meter-group">
            <div class="meter-labels">
              <span>PHYSICAL DEFENSE</span>
              <span class="mono font-bold">${formatPct(defPct)}</span>
            </div>
            <div class="meter-track">
              <div class="meter-indicator ${getFillClass(defPct)}" style="width: ${Math.min(100, Math.max(2, defPct))}%"></div>
            </div>
            <div class="pen-target-note">Target: Require ${defPct.toFixed(1)}% P.Pen to bypass completely</div>
          </div>

          <div class="meter-group">
            <div class="meter-labels">
              <span>MAGIC DEFENSE</span>
              <span class="mono font-bold">${formatPct(mdefPct)}</span>
            </div>
            <div class="meter-track">
              <div class="meter-indicator ${getFillClass(mdefPct)}" style="width: ${Math.min(100, Math.max(2, mdefPct))}%"></div>
            </div>
            <div class="pen-target-note">Target: Require ${mdefPct.toFixed(1)}% M.Pen to bypass completely</div>
          </div>

          <div class="meter-group">
            <div class="meter-labels">
              <span>CRITICAL RESISTANCE</span>
              <span class="mono font-bold">${formatPct(critResPct)}</span>
            </div>
            <div class="meter-track">
              <div class="meter-indicator fill-mid" style="width: ${Math.min(100, Math.max(2, critResPct))}%"></div>
            </div>
          </div>

          <div class="meter-group">
            <div class="meter-labels">
              <span>FLEE RATE</span>
              <span class="mono font-bold">${formatPct(fleePct)}</span>
            </div>
            <div class="meter-track">
              <div class="meter-indicator fill-low" style="width: ${Math.min(100, Math.max(2, fleePct))}%"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Module 4: Size Matchup Table -->
      <div class="bento-cell">
        <div class="bento-title">WEAPON SIZE MATCHUP (${(m.size_name || "Medium").toUpperCase()})</div>
        ${sizeTableHtml}
      </div>

      <!-- Module 5: Elemental Weakness Matrix -->
      ${weaknessModuleHtml}

      <!-- Module 6: Weather Cards -->
      ${weatherCardsHtml}

      <!-- Module 7: Variants & Raw Data -->
      ${variantsHtml}

      ${m.raw ? `
        <details class="bento-cell" style="cursor: pointer;">
          <summary class="bento-title">RAW ENGINE DATA (JSON)</summary>
          <pre class="mono" style="background: var(--bg-surface); padding: 10px; border-radius: var(--radius-sm); font-size: 11px; overflow-x: auto; margin-top: 8px;">${escapeHtml(JSON.stringify(m.raw, null, 2))}</pre>
        </details>
      ` : ""}
    `;

    // Hook CALC DPS click
    const simTargetBtn = DOM.drawerBody.querySelector("#btn-wiki-test-dps, #btn-drawer-sim-target");
    if (simTargetBtn) {
      simTargetBtn.addEventListener("click", () => {
        closeDrawer();
        const simTabBtn = DOM.navTabs.querySelector('[data-tab="simulator"]');
        if (simTabBtn) simTabBtn.click();
        if (window.RoxSimulatorUI) {
          window.RoxSimulatorUI.setTargetFromWiki(m);
        }
      });
    }

    // Hook variant clicks
    DOM.drawerBody.querySelectorAll(".variant-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const vid = parseInt(btn.dataset.id, 10);
        openDrawer(vid);
      });
    });

    // Hook weather cards switching
    if (cards.length > 0) {
      function showCard(cardIndex) {
        const card = cards[cardIndex];
        const container = DOM.drawerBody.querySelector("#active-card-display");
        if (!container || !card) return;

        let phaseBadge = "";
        if (card.weather_phase === "Day") {
          phaseBadge = `<span class="badge badge-day">DAY DROP</span>`;
        } else if (card.weather_phase === "Night") {
          phaseBadge = `<span class="badge badge-night">NIGHT DROP</span>`;
        } else if (card.weather_phase === "Void") {
          phaseBadge = `<span class="badge badge-void">VOID DROP</span>`;
        }

        const qualityKey = (card.quality_name || "white").toLowerCase();
        const cardImg = card.icon_url || `/static/cards/${card.card_id}.png`;

        container.innerHTML = `
          <div class="card-showcase-box" style="margin-top: 10px;">
            <div class="card-media-col">
              <img class="card-media-img quality-${qualityKey}" src="${cardImg}" alt="" loading="lazy" data-id="${card.card_id}" onerror="window.handleSpriteError(this)">
            </div>
            <div class="card-details-col">
              <div class="card-name-text">${escapeHtml(card.name)}</div>
              <div style="display: flex; gap: 4px; flex-wrap: wrap;">
                ${phaseBadge}
                <span class="badge badge-card">SLOT: ${(card.slot_name || "GENERAL").toUpperCase()}</span>
                <span class="badge badge-card">${(card.quality_name || "WHITE").toUpperCase()}</span>
                ${card.is_mvp ? `<span class="badge badge-mvp">MVP</span>` : ""}
              </div>
              <div class="card-buff-block">
                <div class="card-buff-title">EQUIP ATTRIBUTES</div>
                <div>${escapeHtml(card.attr_desc || "No special attribute documented.")}</div>
              </div>
              ${card.deposit_desc ? `
                <div class="card-buff-block">
                  <div class="card-buff-title">ALBUM DEPOSIT ATTRIBUTES</div>
                  <div class="mono">${escapeHtml(card.deposit_desc)}</div>
                </div>
              ` : ""}
            </div>
          </div>
        `;
      }

      showCard(0);

      const navTabs = DOM.drawerBody.querySelectorAll(".weather-tab-btn");
      navTabs.forEach((btn) => {
        btn.addEventListener("click", () => {
          navTabs.forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");
          const idx = parseInt(btn.dataset.cardIdx, 10);
          showCard(idx);
        });
      });
    }
  }

  function closeDrawer() {
    DOM.drawer.classList.remove("open");
    DOM.backdrop.classList.remove("open");
  }

  function applyPreset(presetKey) {
    if (state.activePreset === presetKey) {
      // Toggle off
      state.activePreset = null;
      DOM.presetChips.querySelectorAll(".preset-chip").forEach(c => c.classList.remove("active"));
      DOM.btnReset.click();
      return;
    }

    state.activePreset = presetKey;
    DOM.presetChips.querySelectorAll(".preset-chip").forEach(c => {
      c.classList.toggle("active", c.dataset.preset === presetKey);
    });

    // Reset base parameters
    state.search = "";
    state.race = "";
    state.element = "";
    state.minLevel = "";
    state.maxLevel = "";
    state.sortBy = "level_asc";
    state.page = 1;

    DOM.searchInput.value = "";
    DOM.filterMinLevel.value = "";
    DOM.filterMaxLevel.value = "";

    DOM.racePillRow.querySelectorAll(".pill-btn").forEach(b => b.classList.toggle("active", b.dataset.race === ""));
    DOM.elementPillRow.querySelectorAll(".pill-btn").forEach(b => b.classList.toggle("active", b.dataset.element === ""));

    if (presetKey === "exp-sweetspot") {
      state.tab = "monster";
      state.minLevel = 60;
      state.maxLevel = 75;
      state.sortBy = "hp_desc";
      DOM.filterMinLevel.value = 60;
      DOM.filterMaxLevel.value = 75;
      DOM.sortSelect.value = "hp_desc";
    } else if (presetKey === "low-def") {
      state.tab = "monster";
      state.sortBy = "level_asc";
      DOM.sortSelect.value = "level_asc";
    } else if (presetKey === "high-mdef") {
      state.tab = "monster";
      state.sortBy = "level_desc";
      DOM.sortSelect.value = "level_desc";
    } else if (presetKey === "night-mvp") {
      state.tab = "mvp";
    } else if (presetKey === "weak-fire") {
      // Earth & Undead take 150-200% from Fire
      state.element = "Earth";
      DOM.elementPillRow.querySelectorAll(".pill-btn").forEach(b => b.classList.toggle("active", b.dataset.element === "Earth"));
    } else if (presetKey === "weak-water") {
      // Fire takes 200% from Water
      state.element = "Fire";
      DOM.elementPillRow.querySelectorAll(".pill-btn").forEach(b => b.classList.toggle("active", b.dataset.element === "Fire"));
    }

    // Update nav tab UI
    DOM.navTabs.querySelectorAll(".tab-btn").forEach(b => {
      b.classList.toggle("active", b.dataset.tab === state.tab);
    });

    loadData();
  }

  function initEventListeners() {
    // View Switcher (Ledger vs Compendium)
    DOM.btnViewLedger.addEventListener("click", () => {
      state.viewMode = "ledger";
      DOM.btnViewLedger.classList.add("active");
      DOM.btnViewCompendium.classList.remove("active");
      renderView();
    });

    DOM.btnViewCompendium.addEventListener("click", () => {
      state.viewMode = "compendium";
      DOM.btnViewCompendium.classList.add("active");
      DOM.btnViewLedger.classList.remove("active");
      renderView();
    });

    // Nav Tabs (Monsters vs MVP vs Simulator)
    DOM.navTabs.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.dataset.tab;
        if (state.tab === tab) return;

        DOM.navTabs.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        state.tab = tab;

        if (tab === "simulator") {
          if (DOM.filterBar) DOM.filterBar.style.display = "none";
          if (DOM.paginationBar) DOM.paginationBar.style.display = "none";
          if (DOM.viewSwitcher) DOM.viewSwitcher.style.display = "none";
          DOM.ledgerView.style.display = "none";
          DOM.compendiumView.style.display = "none";
          DOM.emptyState.style.display = "none";
          if (DOM.simulatorView) DOM.simulatorView.style.display = "grid";
          DOM.breadcrumb.textContent = "STUDIO / DPS SIMULATOR";
          if (window.RoxSimulatorUI) {
            window.RoxSimulatorUI.init();
          }
          return;
        } else {
          if (DOM.filterBar) DOM.filterBar.style.display = "block";
          if (DOM.paginationBar) DOM.paginationBar.style.display = "flex";
          if (DOM.viewSwitcher) DOM.viewSwitcher.style.display = "flex";
          if (DOM.simulatorView) DOM.simulatorView.style.display = "none";
          DOM.breadcrumb.textContent = tab === "mvp" ? "DATABASE / MVP & MINI" : "DATABASE / MONSTERS";
          state.page = 1;
          loadData();
        }
      });
    });

    // Preset Chips
    DOM.presetChips.querySelectorAll(".preset-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        applyPreset(chip.dataset.preset);
      });
    });

    // Search input debounced
    DOM.searchInput.addEventListener("input", (e) => {
      const val = e.target.value;
      DOM.btnClearSearch.style.display = val ? "block" : "none";

      clearTimeout(state.debounceTimer);
      state.debounceTimer = setTimeout(() => {
        state.search = val;
        state.page = 1;
        loadData();
      }, 250);
    });

    // Clear search
    DOM.btnClearSearch.addEventListener("click", () => {
      DOM.searchInput.value = "";
      DOM.btnClearSearch.style.display = "none";
      state.search = "";
      state.page = 1;
      loadData();
    });

    // Min / Max level filters
    DOM.filterMinLevel.addEventListener("change", (e) => {
      state.minLevel = e.target.value;
      state.page = 1;
      loadData();
    });

    DOM.filterMaxLevel.addEventListener("change", (e) => {
      state.maxLevel = e.target.value;
      state.page = 1;
      loadData();
    });

    // Sort select
    DOM.sortSelect.addEventListener("change", (e) => {
      state.sortBy = e.target.value;
      state.page = 1;
      loadData();
    });

    // Group select
    DOM.groupSelect.addEventListener("change", (e) => {
      state.groupBy = e.target.value;
      renderView();
    });

    // Reset button
    DOM.btnReset.addEventListener("click", () => {
      state.search = "";
      state.race = "";
      state.element = "";
      state.minLevel = "";
      state.maxLevel = "";
      state.sortBy = "level_asc";
      state.groupBy = "none";
      state.activePreset = null;
      state.page = 1;

      DOM.searchInput.value = "";
      DOM.btnClearSearch.style.display = "none";
      DOM.filterMinLevel.value = "";
      DOM.filterMaxLevel.value = "";
      DOM.sortSelect.value = "level_asc";
      DOM.groupSelect.value = "none";

      DOM.presetChips.querySelectorAll(".preset-chip").forEach(c => c.classList.remove("active"));
      DOM.racePillRow.querySelectorAll(".pill-btn").forEach((b) => {
        b.classList.toggle("active", b.dataset.race === "");
      });
      DOM.elementPillRow.querySelectorAll(".pill-btn").forEach((b) => {
        b.classList.toggle("active", b.dataset.element === "");
      });

      loadData();
    });

    // Race Pill clicks
    DOM.racePillRow.querySelectorAll(".pill-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        DOM.racePillRow.querySelectorAll(".pill-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        state.race = btn.dataset.race || "";
        state.page = 1;
        loadData();
      });
    });

    // Element Pill clicks
    DOM.elementPillRow.querySelectorAll(".pill-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        DOM.elementPillRow.querySelectorAll(".pill-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        state.element = btn.dataset.element || "";
        state.page = 1;
        loadData();
      });
    });

    // Pagination
    DOM.limitSelect.addEventListener("change", (e) => {
      state.limit = parseInt(e.target.value, 10);
      state.page = 1;
      loadData();
    });

    DOM.btnPrev.addEventListener("click", () => {
      if (state.page > 1) {
        state.page--;
        loadData();
      }
    });

    DOM.btnNext.addEventListener("click", () => {
      if (state.page < state.totalPages) {
        state.page++;
        loadData();
      }
    });

    // Drawer close
    DOM.btnCloseDrawer.addEventListener("click", closeDrawer);
    DOM.backdrop.addEventListener("click", closeDrawer);

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeDrawer();
      } else if (e.key === "/" && document.activeElement !== DOM.searchInput && !DOM.drawer.classList.contains("open")) {
        e.preventDefault();
        DOM.searchInput.focus();
      }
    });
  }

  function init() {
    initTheme();
    initEventListeners();
    loadData();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
