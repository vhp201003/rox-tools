(function(global) {
  'use strict';

  const simState = {
    initialized: false,
    staticData: null,
    currentClassId: 'dragon_knight',
    activeAdapter: null,
    buildA: null,
    buildB: null,
    activeSlot: 'A', // 'A' | 'B'
    compareMode: false,
    monsterCache: []
  };

  async function initSimulatorStudio() {
    if (simState.initialized) return;

    try {
      const [staticRes, dkRes] = await Promise.all([
        fetch('/ui/data/static_game_data.json'),
        fetch('/ui/data/dragon_knight_manifest.json')
      ]);

      if (!staticRes.ok || !dkRes.ok) {
        throw new Error('Failed to load simulator data files');
      }

      simState.staticData = await staticRes.json();
      const dkManifest = await dkRes.json();

      const dkAdapter = new global.RoxClassRegistry.DragonKnightAdapter(dkManifest);
      const rangerAdapter = new global.RoxClassRegistry.RangerAdapter();
      global.RoxClassRegistry.registerClassAdapter(dkAdapter);
      global.RoxClassRegistry.registerClassAdapter(rangerAdapter);

      simState.activeAdapter = dkAdapter;
      simState.buildA = JSON.parse(JSON.stringify(dkAdapter.getDefaultBaseline()));
      simState.buildB = JSON.parse(JSON.stringify(simState.buildA));

      renderSimulatorUI();
      bindSimulatorEvents();
      recalculateAndRender();

      simState.initialized = true;
    } catch (err) {
      console.error('Simulator Studio Init Error:', err);
    }
  }

  function getActiveBuild() {
    return simState.activeSlot === 'A' ? simState.buildA : simState.buildB;
  }

  function renderSimulatorUI() {
    const build = getActiveBuild();
    if (!build) return;

    // 1. Core Stats
    const stats = build.stats || {};
    ['str', 'agi', 'vit', 'int', 'dex', 'luk'].forEach(s => {
      const el = document.getElementById(`sim-stat-${s}`);
      if (el) el.value = stats[s] || 0;
    });

    // 1b. Battle Achievements (Editable)
    const ba = build.battle_achievement || {};
    const setNum = (id, val, defaultVal) => {
      const el = document.getElementById(id);
      if (el) el.value = val !== undefined ? val : defaultVal;
    };
    setNum('sim-ba-str', ba.str, 72);
    setNum('sim-ba-fpdmg', ba.final_pdmg_bonus, 0.24);
    setNum('sim-ba-fire', ba.fire_enhance, 0.30);
    setNum('sim-ba-hp', ba.max_hp_pct, 0.24);

    // 1c. Progression Pillars
    const prog = build.progression || {};
    const title = prog.title || {};
    setNum('sim-title-patk', title.patk, 0);
    setNum('sim-title-ppen', title.ppen, 0);
    setNum('sim-title-fdmg', title.fdmg, 0);
    setNum('sim-title-crit', title.crit, 0);
    const shineSel = document.getElementById('sim-shine-points');
    if (shineSel) shineSel.value = String(prog.shine_points || 0);

    // 2. Buffs
    const buffs = build.buffs || {};
    const setChecked = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.checked = !!val;
    };
    setChecked('sim-buff-converter', buffs.elemental_converter === 'Fire');
    setChecked('sim-buff-spear-flash', buffs.spear_flash);
    setChecked('sim-buff-concentration', buffs.concentration);
    setChecked('sim-buff-spooky-lamp', buffs.spooky_lamp);
    setChecked('sim-buff-pet', buffs.pet_active);

    // 2b. Populate Pet Select (Normal Pets & SP Pets)
    const petSel = document.getElementById('sim-pet-select');
    if (petSel && simState.staticData && petSel.options.length <= 1) {
      if (simState.staticData.sp_pets_catalog) {
        const spGroup = document.createElement('optgroup');
        spGroup.label = '--- SP PETS ---';
        Object.keys(simState.staticData.sp_pets_catalog).forEach(pName => {
          const opt = document.createElement('option');
          opt.value = pName;
          opt.textContent = `[SP] ${pName}`;
          spGroup.appendChild(opt);
        });
        petSel.appendChild(spGroup);
      }
      if (simState.staticData.pets_catalog) {
        const normGroup = document.createElement('optgroup');
        normGroup.label = '--- NORMAL PETS ---';
        Object.keys(simState.staticData.pets_catalog).forEach(pName => {
          const opt = document.createElement('option');
          opt.value = pName;
          opt.textContent = pName;
          normGroup.appendChild(opt);
        });
        petSel.appendChild(normGroup);
      }
    }
    const petSummaryEl = document.getElementById('sim-pet-active-summary');
    if (petSummaryEl) {
      const p = build.pet || {};
      const statCount = p.custom_stats ? Object.keys(p.custom_stats).length : 0;
      petSummaryEl.textContent = p.name ? `Pet: ${p.name} (${statCount} Direct Stats Ingested)` : 'Pet: None (Click Configure to Select)';
    }

    const divSummaryEl = document.getElementById('sim-divinity-active-summary');
    if (divSummaryEl) {
      const divCount = Object.keys(build.divinity || {}).length;
      divSummaryEl.textContent = `${divCount || 8} Divinity Parts Configured`;
    }

    const comp = build.companion || {};
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val || 0;
    };
    setVal('sim-companion-str', comp.str);
    setVal('sim-companion-int', comp.int);
    setVal('sim-companion-patk-pct', comp.patk_pct);
    setVal('sim-companion-crit-dmg', comp.crit_dmg);
    setVal('sim-companion-fpdmg', comp.final_pdmg_bonus);
    setVal('sim-companion-fire', comp.fire_enhance);

    // 2c. Populate Debuff Select
    const debuffSel = document.getElementById('sim-debuff-select');
    if (debuffSel && simState.staticData?.mvp_debuffs && debuffSel.options.length <= 1) {
      simState.staticData.mvp_debuffs.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.name;
        opt.textContent = `${d.name} (RES ${d.debuff_res})`;
        debuffSel.appendChild(opt);
      });
    }

    // 2d. Populate Divinity List
    const divList = document.getElementById('sim-divinity-list');
    if (divList && simState.staticData?.divinity_catalog) {
      const activeDiv = build.divinity || {};
      let divHtml = '';
      Object.keys(simState.staticData.divinity_catalog).forEach((dName, idx) => {
        const pData = simState.staticData.divinity_catalog[dName];
        const currentPart = activeDiv[dName] || { name: dName, level: 0, quality: 'gold', selected_substats: [] };
        const selectedSubs = currentPart.selected_substats || [];

        let subChips = '';
        if (pData.substats) {
          Object.keys(pData.substats).forEach(sName => {
            const isSel = selectedSubs.includes(sName);
            subChips += `<span class="card-socket-chip ${isSel ? 'filled' : ''} btn-div-substat" data-part="${dName}" data-sub="${sName}" style="margin: 1px;">${sName}</span>`;
          });
        }

        divHtml += `
          <div style="margin-bottom: 6px; padding: 4px; background: var(--bg-canvas); border: 1px solid var(--border); border-radius: var(--radius-sm);">
            <div class="studio-row" style="justify-content: space-between; margin-bottom: 4px;">
              <span class="font-bold" style="font-size: 10px;">[P${idx + 1}] ${dName}</span>
              <div style="display: flex; gap: 4px;">
                <select class="filter-select sim-div-quality-select" data-name="${dName}" style="font-size: 9.5px; padding: 2px 4px; width: 62px; height: 22px;">
                  <option value="gold" ${currentPart.quality === 'gold' ? 'selected' : ''}>Gold</option>
                  <option value="purple" ${currentPart.quality === 'purple' ? 'selected' : ''}>Purple</option>
                  <option value="blue" ${currentPart.quality === 'blue' ? 'selected' : ''}>Blue</option>
                </select>
                <select class="filter-select sim-div-level-select" data-name="${dName}" style="font-size: 9.5px; padding: 2px 4px; width: 50px; height: 22px;">
                  ${[0, 1, 2, 3, 4, 5, 6, 7].map(lv => `<option value="${lv}" ${currentPart.level === lv ? 'selected' : ''}>L${lv}</option>`).join('')}
                </select>
              </div>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 2px;">
              ${subChips}
            </div>
          </div>
        `;
      });
      divList.innerHTML = divHtml;
    }

    // 3. Target Monster Name
    const targetEl = document.getElementById('sim-target-name');
    if (targetEl && build.target) {
      targetEl.textContent = build.target.name || 'Training Dummy';
    }

    // 4. Render 11 Gear Slots
    renderGearSlots();
  }

  function renderGearSlots() {
    const grid = document.getElementById('sim-gear-grid');
    if (!grid) return;

    const build = getActiveBuild();
    const loadout = build.loadout || {};
    const allSlots = [
      { key: 'weapon', label: 'WEAPON', type: 'Weapon', page: 1 },
      { key: 'clothes', label: 'CLOTHES', type: 'Clothes', page: 1 },
      { key: 'cloak', label: 'CLOAK', type: 'Cloak', page: 1 },
      { key: 'shoes', label: 'SHOES', type: 'Shoes', page: 1 },
      { key: 'accessory_1', label: 'ACC 1', type: 'Accessory', page: 1 },
      { key: 'accessory_2', label: 'ACC 2', type: 'Accessory', page: 1 },
      { key: 'talisman', label: 'TALISMAN', type: 'Talisman', page: 1 },
      { key: 'costume_head', label: 'HEAD', type: 'CostumeHead', page: 2 },
      { key: 'costume_eyes', label: 'EYES', type: 'CostumeEyes', page: 2 },
      { key: 'costume_mouth', label: 'MOUTH', type: 'CostumeMouth', page: 2 },
      { key: 'costume_back', label: 'BACK', type: 'CostumeBack', page: 2 }
    ];

    const activePage = simState.gearPage || 1;
    const slots = allSlots.filter(s => s.page === activePage);

    const socketCapacity = {
      weapon: 4,
      clothes: 2,
      cloak: 2,
      shoes: 2,
      accessory_1: 1,
      accessory_2: 1,
      talisman: 1,
      costume_head: 1,
      costume_eyes: 1,
      costume_mouth: 1,
      costume_back: 1
    };

    const cities = ['Prontera', 'Morroc', 'Alberta', 'Izlude Island', 'Payon', 'Geffen', 'Glast Heim', 'Comodo', 'Umbala', 'Juno'];

    let html = '';
    slots.forEach(s => {
      const item = loadout[s.key] || { name: 'None', refine: 0, upgrade: 0, enchant_city: 'Prontera', enchant_lv: 0, cards: [] };
      const isCostume = s.key.startsWith('costume_');
      const maxSockets = socketCapacity[s.key] || 1;
      const cardsList = Array.isArray(item.cards) ? item.cards : [];

      if (!Array.isArray(item.enchant_lines) || item.enchant_lines.length < 3) {
        const legacyCity = item.enchant_city || 'Prontera';
        const legacyLv = Number(item.enchant_lv) || 0;
        const defaultStat = legacyCity === 'Prontera' ? 'STR' : (legacyCity === 'Morroc' ? 'P.ATK' : 'Final P.DMG Bonus');
        item.enchant_lines = [
          { city: legacyCity, stat: defaultStat, level: legacyLv },
          { city: legacyCity, stat: defaultStat, level: legacyLv },
          { city: legacyCity, stat: defaultStat, level: legacyLv }
        ];
      }

      let socketChipsHtml = '';
      for (let i = 0; i < maxSockets; i++) {
        const cardName = cardsList[i];
        if (cardName) {
          socketChipsHtml += `<span class="card-socket-chip filled btn-pick-card" data-slot="${s.key}" data-type="${s.type}" data-socket="${i}" title="${cardName}">[${i + 1}] ${cardName}</span>`;
        } else {
          socketChipsHtml += `<span class="card-socket-chip btn-pick-card" data-slot="${s.key}" data-type="${s.type}" data-socket="${i}">[+] Socket ${i + 1}</span>`;
        }
      }

      let encCategory = 'armor';
      if (s.key === 'weapon') encCategory = 'weapon';
      else if (['accessory_1', 'accessory_2', 'talisman'].includes(s.key)) encCategory = 'accessory';

      let enchantLinesHtml = '';
      item.enchant_lines.forEach((line, lineIdx) => {
        const lineCity = line.city || 'Prontera';
        const availableStats = Object.keys(simState.staticData?.enchant_cities?.[lineCity]?.[encCategory] || { STR: 1 });
        const lineStat = line.stat || availableStats[0] || 'STR';
        const lineLv = Number(line.level) || 0;

        enchantLinesHtml += `
            <div class="studio-row" style="gap: 3px; margin-top: 3px; align-items: center;">
              <span class="field-lbl" style="width: 14px; font-size: 8.5px;">L${lineIdx + 1}</span>
              <select class="filter-select sel-enc-line-city" data-slot="${s.key}" data-line="${lineIdx}" style="font-size: 9px; padding: 2px 3px; width: 62px; height: 22px;">
                ${cities.map(c => `<option value="${c}" ${lineCity === c ? 'selected' : ''}>${c.split(' ')[0]}</option>`).join('')}
              </select>
              <select class="filter-select sel-enc-line-stat" data-slot="${s.key}" data-line="${lineIdx}" style="font-size: 9px; padding: 2px 3px; flex: 1; height: 22px;">
                ${availableStats.map(st => `<option value="${st}" ${lineStat === st ? 'selected' : ''}>${st}</option>`).join('')}
              </select>
              <div class="stepper-group" style="height: 22px;">
                <button type="button" class="stepper-btn btn-enc-line-down" data-slot="${s.key}" data-line="${lineIdx}">-</button>
                <span class="stepper-val mono font-bold" style="font-size: 8.5px; min-width: 20px;">L${lineLv}</span>
                <button type="button" class="stepper-btn btn-enc-line-up" data-slot="${s.key}" data-line="${lineIdx}">+</button>
              </div>
            </div>
        `;
      });

      html += `
        <div class="gear-card" data-slot="${s.key}">
          <div class="gear-card-header">
            <span class="gear-slot-tag">[${s.label}]</span>
            <button type="button" class="gear-select-btn font-bold btn-pick-item" data-slot="${s.key}" data-type="${s.type}">${item.name}</button>
          </div>
          <div class="gear-controls-row">
            ${!isCostume ? `
              <div class="gear-field">
                <span class="field-lbl">REF</span>
                <div class="stepper-group">
                  <button type="button" class="stepper-btn btn-step-down" data-slot="${s.key}" data-field="refine">-</button>
                  <span class="stepper-val mono font-bold" id="val-${s.key}-refine">+${item.refine || 0}</span>
                  <button type="button" class="stepper-btn btn-step-up" data-slot="${s.key}" data-field="refine">+</button>
                </div>
              </div>
              <div class="gear-field">
                <span class="field-lbl">UPG</span>
                <div class="stepper-group">
                  <button type="button" class="stepper-btn btn-step-down" data-slot="${s.key}" data-field="upgrade">-</button>
                  <span class="stepper-val mono font-bold" id="val-${s.key}-upgrade">${item.upgrade || 0}</span>
                  <button type="button" class="stepper-btn btn-step-up" data-slot="${s.key}" data-field="upgrade">+</button>
                </div>
              </div>
            ` : '<div class="costume-badge mono">[COSTUME STATS]</div>'}
          </div>
          <div style="margin-top: 4px; padding-top: 4px; border-top: 1px dashed var(--border);">
            <div style="font-size: 8.5px; font-weight: 700; color: var(--text-muted); margin-bottom: 2px;">3-LINE ENCHANTMENT (LV.1-15)</div>
            ${enchantLinesHtml}
          </div>
          <div class="card-sockets-row">
            ${socketChipsHtml}
          </div>
        </div>
      `;
    });

    grid.innerHTML = html;

    if (!grid.dataset.delegated) {
      grid.dataset.delegated = 'true';

      grid.addEventListener('click', (e) => {
        const pickItemBtn = e.target.closest('.btn-pick-item');
        if (pickItemBtn) {
          openItemPicker(pickItemBtn.dataset.slot, pickItemBtn.dataset.type);
          return;
        }

        const pickCardBtn = e.target.closest('.btn-pick-card');
        if (pickCardBtn) {
          const socketIdx = Number(pickCardBtn.dataset.socket) || 0;
          openCardPicker(pickCardBtn.dataset.slot, pickCardBtn.dataset.type, socketIdx);
          return;
        }

        const encUpBtn = e.target.closest('.btn-enc-line-up');
        if (encUpBtn) {
          const slot = encUpBtn.dataset.slot;
          const lineIdx = Number(encUpBtn.dataset.line);
          const b = getActiveBuild();
          if (b.loadout?.[slot]?.enchant_lines?.[lineIdx]) {
            const curLv = Number(b.loadout[slot].enchant_lines[lineIdx].level) || 0;
            if (curLv < 15) b.loadout[slot].enchant_lines[lineIdx].level = curLv + 1;
            renderGearSlots();
            recalculateAndRender();
          }
          return;
        }

        const encDownBtn = e.target.closest('.btn-enc-line-down');
        if (encDownBtn) {
          const slot = encDownBtn.dataset.slot;
          const lineIdx = Number(encDownBtn.dataset.line);
          const b = getActiveBuild();
          if (b.loadout?.[slot]?.enchant_lines?.[lineIdx]) {
            const curLv = Number(b.loadout[slot].enchant_lines[lineIdx].level) || 0;
            b.loadout[slot].enchant_lines[lineIdx].level = Math.max(0, curLv - 1);
            renderGearSlots();
            recalculateAndRender();
          }
          return;
        }

        const stepUpBtn = e.target.closest('.btn-step-up');
        if (stepUpBtn) {
          const slot = stepUpBtn.dataset.slot;
          const field = stepUpBtn.dataset.field;
          const b = getActiveBuild();
          if (b.loadout[slot]) {
            const currentVal = Number(b.loadout[slot][field]) || 0;
            if (field === 'refine') {
              if (currentVal < 15) b.loadout[slot][field] = currentVal + 1;
            } else {
              b.loadout[slot][field] = currentVal + (field === 'upgrade' ? 5 : 1);
            }
            renderSimulatorUI();
            recalculateAndRender();
          }
          return;
        }

        const stepDownBtn = e.target.closest('.btn-step-down');
        if (stepDownBtn) {
          const slot = stepDownBtn.dataset.slot;
          const field = stepDownBtn.dataset.field;
          const b = getActiveBuild();
          if (b.loadout[slot]) {
            const step = field === 'upgrade' ? 5 : 1;
            b.loadout[slot][field] = Math.max(0, (Number(b.loadout[slot][field]) || 0) - step);
            renderSimulatorUI();
            recalculateAndRender();
          }
          return;
        }
      });

      grid.addEventListener('change', (e) => {
        const citySel = e.target.closest('.sel-enc-line-city');
        if (citySel) {
          const slot = citySel.dataset.slot;
          const lineIdx = Number(citySel.dataset.line);
          const b = getActiveBuild();
          if (b.loadout?.[slot]?.enchant_lines?.[lineIdx]) {
            b.loadout[slot].enchant_lines[lineIdx].city = citySel.value;
            const encCat = slot === 'weapon' ? 'weapon' : (['accessory_1', 'accessory_2', 'talisman'].includes(slot) ? 'accessory' : 'armor');
            const availableStats = Object.keys(simState.staticData?.enchant_cities?.[citySel.value]?.[encCat] || {});
            b.loadout[slot].enchant_lines[lineIdx].stat = availableStats[0] || 'STR';
            renderGearSlots();
            recalculateAndRender();
          }
          return;
        }

        const statSel = e.target.closest('.sel-enc-line-stat');
        if (statSel) {
          const slot = statSel.dataset.slot;
          const lineIdx = Number(statSel.dataset.line);
          const b = getActiveBuild();
          if (b.loadout?.[slot]?.enchant_lines?.[lineIdx]) {
            b.loadout[slot].enchant_lines[lineIdx].stat = statSel.value;
            recalculateAndRender();
          }
          return;
        }
      });
    }
  }

  function openItemPicker(slotKey, itemType) {
    const catalog = simState.staticData?.equip_base?.[itemType] || simState.staticData?.equip_base?.[slotKey] || [];
    if (!catalog.length) return;

    let modal = document.getElementById('sim-active-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'sim-active-modal';
      modal.className = 'sim-modal';
      document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <div class="sim-modal-header">
        <strong class="mono">[SELECT ${itemType.toUpperCase()}]</strong>
        <button type="button" class="btn-text" id="sim-modal-close">ESC / CLOSE</button>
      </div>
      <div class="sim-modal-body">
        ${catalog.map(eq => `
          <div class="sim-picker-item" data-name="${eq.name}">
            <span class="font-bold">${eq.name}</span>
            <span class="mono text-muted">${Object.keys(eq.stats || {}).join(', ')}</span>
          </div>
        `).join('')}
      </div>
    `;

    modal.querySelector('#sim-modal-close').onclick = () => modal.remove();
    modal.querySelectorAll('.sim-picker-item').forEach(it => {
      it.onclick = () => {
        const b = getActiveBuild();
        if (b.loadout?.[slotKey]) {
          b.loadout[slotKey].name = it.dataset.name;
          renderSimulatorUI();
          recalculateAndRender();
        }
        modal.remove();
      };
    });
  }

  function openCardPicker(slotKey, itemType, socketIdx = 0) {
    let catKey = 'Weapon';
    if (itemType === 'Clothes') catKey = 'Clothes';
    else if (itemType === 'Cloak') catKey = 'Cloak';
    else if (itemType === 'Shoes') catKey = 'Shoes';
    else if (itemType === 'Accessory' || itemType === 'Talisman') catKey = 'Accessory';
    else if (itemType.startsWith('Costume')) catKey = 'Headgear';

    const cards = simState.staticData?.cards_catalog?.[catKey] || [];
    if (!cards.length) return;

    let modal = document.getElementById('sim-active-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'sim-active-modal';
      modal.className = 'sim-modal';
      document.body.appendChild(modal);
    }

    modal.innerHTML = `
      <div class="sim-modal-header">
        <strong class="mono">[SELECT CARD: ${slotKey.toUpperCase()} - SOCKET ${socketIdx + 1}]</strong>
        <button type="button" class="btn-text" id="sim-modal-close">ESC / CLOSE</button>
      </div>
      <div class="sim-modal-body">
        <div class="sim-picker-item" data-name="NONE" style="color: #ef4444;">
          <span class="font-bold">[REMOVE CARD FROM SOCKET ${socketIdx + 1}]</span>
        </div>
        ${cards.slice(0, 100).map(c => `
          <div class="sim-picker-item" data-name="${c.name}">
            <span class="font-bold">${c.name}</span>
            <span class="mono text-muted">${Object.entries(c.stats || {}).map(([k, v]) => `${k}+${v}`).join(', ')}</span>
          </div>
        `).join('')}
      </div>
    `;

    modal.querySelector('#sim-modal-close').onclick = () => modal.remove();
    modal.querySelectorAll('.sim-picker-item').forEach(it => {
      it.onclick = () => {
        const b = getActiveBuild();
        if (b.loadout?.[slotKey]) {
          if (!Array.isArray(b.loadout[slotKey].cards)) b.loadout[slotKey].cards = [];
          if (it.dataset.name === 'NONE') {
            b.loadout[slotKey].cards[socketIdx] = null;
            b.loadout[slotKey].cards = b.loadout[slotKey].cards.filter(Boolean);
          } else {
            b.loadout[slotKey].cards[socketIdx] = it.dataset.name;
          }
          renderSimulatorUI();
          recalculateAndRender();
        }
        modal.remove();
      };
    });
  }

  function openDivinityStudioModal() {
    if (!simState.staticData?.divinity_catalog) return;
    const cat = simState.staticData.divinity_catalog;
    const partNames = Object.keys(cat);
    if (!partNames.length) return;

    let modal = document.getElementById('sim-active-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'sim-active-modal';
      document.body.appendChild(modal);
    }
    modal.className = 'sim-modal sim-modal-wide';

    if (!simState.activeDivPart || !cat[simState.activeDivPart]) {
      simState.activeDivPart = partNames[0];
    }
    let filterQuery = '';

    const formatStatDisplay = (sn, valObj, q) => {
      if (valObj === undefined || valObj === null) return '0';
      const isPct = typeof valObj === 'object' ? valObj.is_pct : !['STR', 'AGI', 'VIT', 'INT', 'DEX', 'LUK', 'P.DMG Bonus', 'M.DMG Bonus'].includes(sn);
      const raw = typeof valObj === 'object' ? (valObj[q] !== undefined ? valObj[q] : valObj.gold || 0) : valObj;
      if (isPct) {
        const pctVal = Math.round(raw * 10000) / 100;
        return `+${pctVal.toFixed(2)}%`;
      }
      return `+${Math.round(raw).toLocaleString()}`;
    };

    const renderContent = () => {
      const activePartName = simState.activeDivPart;
      const partData = cat[activePartName] || {};
      const b = getActiveBuild();
      if (!b.divinity) b.divinity = {};
      if (!b.divinity[activePartName]) {
        b.divinity[activePartName] = { name: activePartName, level: 0, quality: 'gold', selected_substats: [] };
      }
      const currentPart = b.divinity[activePartName];
      if (currentPart.level === undefined) currentPart.level = 0;
      if (!currentPart.quality) currentPart.quality = 'gold';
      const selectedSubs = currentPart.selected_substats || [];

      const q = currentPart.quality || 'gold';
      const lvl = String(currentPart.level);
      const allSubstats = Object.entries(partData.substats || {});
      const query = filterQuery.trim().toLowerCase();
      const filtered = allSubstats.filter(([sn]) => !query || sn.toLowerCase().includes(query));

      const pinned = filtered.filter(([sn]) => selectedSubs.includes(sn));
      const unpinned = filtered.filter(([sn]) => !selectedSubs.includes(sn));
      const sortedSubstats = [...pinned, ...unpinned];

      const chipsHtml = sortedSubstats.map(([sn, valObj]) => {
        const isSel = selectedSubs.includes(sn);
        const displayVal = formatStatDisplay(sn, valObj, q);
        return `
          <div class="div-substat-chip ${isSel ? 'active' : ''}" data-part="${activePartName}" data-sub="${sn}">
            <span>${isSel ? '✓ ' : ''}${sn}</span>
            <span class="mono" style="font-size: 9px; opacity: 0.9; color: var(--border-focus);">${displayVal}</span>
          </div>
        `;
      }).join('');

      // Main stats calculation for display
      const mainObj = partData.main_levels?.[lvl];
      const mainStatsNames = partData.stat_names || [];
      let mainStatsDisplayHtml = '';
      if (mainObj && mainStatsNames.length > 0) {
        const rawMVal = mainObj[q] !== undefined ? mainObj[q] : (mainObj.gold || 0);
        mainStatsDisplayHtml = mainStatsNames.map(mName => {
          const isPct = !['Max HP', 'Max SP', 'P.ATK', 'M.ATK', 'P.DEF', 'M.DEF'].includes(mName);
          const disp = isPct ? `+${(Math.round(rawMVal * 10000) / 100).toFixed(2)}%` : `+${Math.round(rawMVal).toLocaleString()}`;
          return `<span style="display: inline-block; background: var(--bg-hover); padding: 2px 6px; border-radius: var(--radius-sm); border: 1px solid var(--border); font-family: var(--font-mono); font-size: 10px; margin-right: 4px;"><strong>${mName}:</strong> <span style="color: #10b981;">${disp}</span></span>`;
        }).join('');
      } else {
        mainStatsDisplayHtml = '<span class="text-muted" style="font-size: 10px;">None</span>';
      }

      modal.innerHTML = `
        <div class="sim-modal-header">
          <div>
            <strong class="mono" style="font-size: 13px;">[DIVINITY INSCRIPTION STUDIO: I - VIII]</strong>
            <span class="text-muted" style="font-size: 10px; margin-left: 8px;">Main Stat (Lv.0-7) + 2 Substats (Full 53 Pool)</span>
          </div>
          <button type="button" class="btn-text font-bold" id="sim-modal-close">ESC / CLOSE</button>
        </div>
        <div class="div-tabs-nav">
          ${partNames.map((p, idx) => `
            <button type="button" class="div-tab-btn ${p === activePartName ? 'active' : ''}" data-part="${p}">
              [P${idx + 1}] ${p}
            </button>
          `).join('')}
        </div>
        <div class="sim-modal-body" style="padding: 12px;">
          <div style="background: var(--bg-canvas); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px; margin-bottom: 8px;">
            <div class="studio-row" style="justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 6px;">
              <div style="display: flex; gap: 8px; align-items: center;">
                <span class="font-bold" style="font-size: 11px;">[MAIN STAT LEVEL]:</span>
                <select class="filter-select" id="modal-div-level" style="font-size: 10px; height: 26px; padding: 2px 6px; min-width: 75px;">
                  ${[0, 1, 2, 3, 4, 5, 6, 7].map(l => `<option value="${l}" ${Number(currentPart.level) === l ? 'selected' : ''}>Level ${l}</option>`).join('')}
                </select>
                <span class="font-bold" style="font-size: 11px; margin-left: 6px;">[QUALITY]:</span>
                <select class="filter-select" id="modal-div-quality" style="font-size: 10px; height: 26px; padding: 2px 8px; min-width: 135px;">
                  <option value="gold" ${q === 'gold' ? 'selected' : ''}>Gold Quality Tier</option>
                  <option value="purple" ${q === 'purple' ? 'selected' : ''}>Purple Quality Tier</option>
                  <option value="blue" ${q === 'blue' ? 'selected' : ''}>Blue Quality Tier</option>
                </select>
              </div>
              <div style="flex: 1; max-width: 220px;">
                <input type="text" id="modal-div-search" class="filter-input-text" placeholder="Search 53 substats..." value="${filterQuery}" style="font-size: 10px; padding: 3px 6px; height: 26px; width: 100%;">
              </div>
            </div>
            <div style="font-size: 10.5px; display: flex; align-items: center; gap: 6px;">
              <span class="text-muted font-bold">[MAIN STAT]:</span>
              ${mainStatsDisplayHtml}
            </div>
          </div>
          <div style="font-size: 9.5px; color: var(--text-muted); margin-bottom: 6px; display: flex; justify-content: space-between;">
            <span>Selected <strong>${selectedSubs.length}</strong> Substats in this slot (Unlimited Selection, ticked stats pin to top):</span>
            <span style="color: var(--border-focus);">${q.toUpperCase()} Quality Rates Applied</span>
          </div>
          <div class="div-substat-grid" style="max-height: 280px; overflow-y: auto;">
            ${chipsHtml || '<div class="text-muted" style="padding: 8px; font-size: 11px;">No substats match search filter.</div>'}
          </div>
        </div>
      `;

      modal.querySelector('#sim-modal-close').onclick = () => {
        modal.remove();
        renderSimulatorUI();
        recalculateAndRender();
      };

      modal.querySelectorAll('.div-tab-btn').forEach(btn => {
        btn.onclick = () => {
          simState.activeDivPart = btn.dataset.part;
          renderContent();
        };
      });

      const lvlSel = modal.querySelector('#modal-div-level');
      if (lvlSel) {
        lvlSel.onchange = (e) => {
          currentPart.level = Number(e.target.value) || 0;
          renderContent();
          recalculateAndRender();
        };
      }

      const qSel = modal.querySelector('#modal-div-quality');
      if (qSel) {
        qSel.onchange = (e) => {
          currentPart.quality = e.target.value;
          renderContent();
          recalculateAndRender();
        };
      }

      const searchInput = modal.querySelector('#modal-div-search');
      if (searchInput) {
        searchInput.oninput = (e) => {
          filterQuery = e.target.value;
          renderContent();
          const freshSearch = modal.querySelector('#modal-div-search');
          if (freshSearch) {
            freshSearch.focus();
            freshSearch.setSelectionRange(filterQuery.length, filterQuery.length);
          }
        };
      }

      modal.querySelectorAll('.div-substat-chip').forEach(chip => {
        chip.onclick = () => {
          const sub = chip.dataset.sub;
          const idx = selectedSubs.indexOf(sub);
          if (idx >= 0) {
            selectedSubs.splice(idx, 1);
          } else {
            selectedSubs.push(sub);
          }
          currentPart.selected_substats = selectedSubs;
          renderContent();
          recalculateAndRender();
        };
      });

    };

    renderContent();
  }

  function openPetSanctuaryModal() {
    if (!simState.staticData) return;
    const petsCat = simState.staticData.pets_catalog || {};
    const spPetsCat = simState.staticData.sp_pets_catalog || {};

    let modal = document.getElementById('sim-active-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'sim-active-modal';
      document.body.appendChild(modal);
    }
    modal.className = 'sim-modal sim-modal-wide';

    const b = getActiveBuild();
    if (!b.pet) b.pet = { name: '', custom_stats: {} };
    const p = b.pet;
    let petSearchQuery = '';

    const allPetEntries = [
      ...Object.keys(spPetsCat).map(name => ({ name, type: 'SP' })),
      ...Object.keys(petsCat).map(name => ({ name, type: 'NORMAL' }))
    ];

    const renderContent = () => {
      const activeName = p.name || '';
      const isSp = !!spPetsCat[activeName];
      const templateStats = isSp ? spPetsCat[activeName] : (petsCat[activeName] || ['STR', 'AGI', 'VIT', 'INT', 'DEX', 'LUK']);

      const query = petSearchQuery.trim().toLowerCase();
      const filteredPets = allPetEntries.filter(entry => !query || entry.name.toLowerCase().includes(query));

      let customInputsHtml = '';
      templateStats.forEach(st => {
        const val = p.custom_stats?.[st] !== undefined ? p.custom_stats[st] : 30;
        customInputsHtml += `
          <div class="stat-input-group" style="padding: 4px;">
            <span class="stat-lbl" style="width: 130px; font-size: 9.5px;" title="${st}">${st}</span>
            <input type="number" class="filter-input-num modal-pet-stat-input" data-stat="${st}" value="${val}" step="any" style="font-size: 10px; height: 22px; width: 65px;">
          </div>
        `;
      });

      modal.innerHTML = `
        <div class="sim-modal-header">
          <div>
            <strong class="mono" style="font-size: 13px;">[PET SANCTUARY STUDIO]</strong>
            <span class="text-muted" style="font-size: 10px; margin-left: 8px;">Direct Stat Ingestion • Normal (6 Stats) / SP (8 Stats)</span>
          </div>
          <button type="button" class="btn-text font-bold" id="sim-modal-close">ESC / CLOSE</button>
        </div>
        <div class="sim-modal-body" style="padding: 12px; display: grid; grid-template-columns: 240px 1fr; gap: 12px;">
          <div style="border-right: 1px solid var(--border); padding-right: 10px; display: flex; flex-direction: column;">
            <input type="text" id="modal-pet-search" class="filter-input-text" placeholder="Search Pet Name..." value="${petSearchQuery}" style="font-size: 10px; padding: 4px 6px; margin-bottom: 6px; height: 24px;">
            <div id="modal-pet-list" style="max-height: 320px; overflow-y: auto; flex: 1;">
              ${filteredPets.map(pet => `
                <div class="sim-picker-item ${pet.name === activeName ? 'active' : ''}" data-name="${pet.name}" style="${pet.name === activeName ? 'background: rgba(59, 130, 246, 0.15); border-color: #3b82f6;' : ''}">
                  <span class="font-bold">${pet.type === 'SP' ? '[SP] ' : ''}${pet.name}</span>
                  <span class="mono text-muted" style="font-size: 9px;">${pet.type}</span>
                </div>
              `).join('')}
            </div>
          </div>
          <div>
            <div style="background: var(--bg-canvas); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px; margin-bottom: 10px;">
              <span class="font-bold" style="font-size: 12px; color: var(--border-focus);">${activeName ? (isSp ? '[SP PET] ' : '[NORMAL PET] ') + activeName : 'No Pet Selected'}</span>
              <span class="text-muted" style="font-size: 10px; margin-left: 8px;">(${templateStats.length} In-Game Stats Applied Directly)</span>
            </div>
            <div style="font-size: 10px; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">
              ENTER ACTUAL IN-GAME STAT VALUES:
            </div>
            <div class="stats-grid-6" style="grid-template-columns: repeat(2, 1fr); gap: 4px;">
              ${customInputsHtml}
            </div>
          </div>
        </div>
      `;

      modal.querySelector('#sim-modal-close').onclick = () => {
        modal.remove();
        renderSimulatorUI();
        recalculateAndRender();
      };

      const petSearchInput = modal.querySelector('#modal-pet-search');
      if (petSearchInput) {
        petSearchInput.oninput = (e) => {
          petSearchQuery = e.target.value;
          renderContent();
          const freshSearch = modal.querySelector('#modal-pet-search');
          if (freshSearch) {
            freshSearch.focus();
            freshSearch.setSelectionRange(petSearchQuery.length, petSearchQuery.length);
          }
        };
      }

      modal.querySelectorAll('.sim-picker-item').forEach(it => {
        it.onclick = () => {
          p.name = it.dataset.name;
          p.custom_stats = {};
          const isSelectedSp = !!spPetsCat[p.name];
          const stats = isSelectedSp ? spPetsCat[p.name] : (petsCat[p.name] || ['STR', 'AGI', 'VIT', 'INT', 'DEX', 'LUK']);
          stats.forEach(sn => {
            p.custom_stats[sn] = 30;
          });
          renderContent();
          recalculateAndRender();
        };
      });

      modal.querySelectorAll('.modal-pet-stat-input').forEach(inp => {
        inp.oninput = (e) => {
          const st = inp.dataset.stat;
          if (!p.custom_stats) p.custom_stats = {};
          p.custom_stats[st] = Number(e.target.value) || 0;
          recalculateAndRender();
        };
      });
    };

    renderContent();
  }

  function recalculateAndRender() {
    if (!simState.staticData || !simState.activeAdapter) return;

    const debuffs = {
      final_p_def: Number(document.getElementById('sim-debuff-fdef')?.value || 0),
      final_p_dmg_red: Number(document.getElementById('sim-debuff-fpdmg')?.value || 0)
    };
    const isPvp = simState.isPvpMode || false;

    // PVP Cockpit target stats (SSOT Output Q17:R27)
    let pvpDefender = null;
    if (isPvp) {
      pvpDefender = {
        p_def: Number(document.getElementById('sim-pvp-pdef')?.value || 0),
        final_p_def: Number(document.getElementById('sim-pvp-fpdef')?.value || 0),
        final_p_dmg_red: Number(document.getElementById('sim-pvp-fpred')?.value || 0),
        final_dmg_red: Number(document.getElementById('sim-pvp-fred')?.value || 0),
        p_dmg_red: Number(document.getElementById('sim-pvp-pred')?.value || 0),
        pvp_final_p_dmg_red: Number(document.getElementById('sim-pvp-pvpfpred')?.value || 0),
        pvp_p_dmg_red: Number(document.getElementById('sim-pvp-pvppred')?.value || 0),
        element_res: Number(document.getElementById('sim-pvp-attrres')?.value || 0)
      };
    }

    const buildA = simState.buildA;
    const targetA = isPvp ? pvpDefender : buildA.target;
    const tallyA = global.RoxSimulatorEngine.tallyPlayerStats(buildA, simState.staticData);
    const simResA = global.RoxSimulatorEngine.simulateCombatTimeline(
      simState.activeAdapter.getSkills(),
      tallyA.stats,
      targetA,
      buildA.buffs,
      simState.staticData,
      debuffs,
      isPvp
    );

    let tallyB = null;
    let simResB = null;
    if (simState.compareMode) {
      const buildB = simState.buildB;
      const targetB = isPvp ? pvpDefender : buildB.target;
      tallyB = global.RoxSimulatorEngine.tallyPlayerStats(buildB, simState.staticData);
      simResB = global.RoxSimulatorEngine.simulateCombatTimeline(
        simState.activeAdapter.getSkills(),
        tallyB.stats,
        targetB,
        buildB.buffs,
        simState.staticData,
        debuffs,
        isPvp
      );
    }

    const currentSimRes = simState.activeSlot === 'A' ? simResA : (simResB || simResA);
    const currentTally = simState.activeSlot === 'A' ? tallyA : (tallyB || tallyA);

    // Update Headline Metrics
    const dpsEl = document.getElementById('sim-metric-dps');
    const dpmEl = document.getElementById('sim-metric-dpm');
    const critHitEl = document.getElementById('sim-metric-crit-hit');
    const nonCritHitEl = document.getElementById('sim-metric-noncrit-hit');

    if (dpsEl) dpsEl.textContent = currentSimRes.dps.toLocaleString();
    if (dpmEl) dpmEl.textContent = `DPM: ${(currentSimRes.totalDmg3m / 1000000).toFixed(2)}M / 3 MINS`;

    const firstHit = currentSimRes.hitsBreakdown[0] || { damagePerHit: 0 };
    if (critHitEl) critHitEl.textContent = firstHit.damagePerHit.toLocaleString();
    if (nonCritHitEl) nonCritHitEl.textContent = `Normal Attack: ${firstHit.damagePerHit.toLocaleString()}`;

    // Update 9-Skill Rotation Damage Parity Matrix
    const skillTableBody = document.getElementById('sim-skill-table-body');
    if (skillTableBody && simState.activeAdapter) {
      const skills = simState.activeAdapter.getSkills();
      let tableHtml = '';
      skills.forEach(sk => {
        const dmg = global.RoxSimulatorEngine.calculateSkillDamage(
          sk,
          currentTally.stats,
          getActiveBuild().target,
          getActiveBuild().buffs,
          simState.staticData,
          debuffs,
          isPvp
        );
        const hitInfo = currentSimRes.hitsBreakdown.find(h => h.skillId === sk.id) || { hitsIn60s: 0, totalSkillDmg: 0 };
        tableHtml += `
          <tr>
            <td><strong>${sk.name}</strong></td>
            <td class="diff-pos">${dmg.critHitDmg.toLocaleString()}</td>
            <td>${dmg.nonCritHitDmg.toLocaleString()}</td>
            <td>${hitInfo.hitsIn60s}</td>
            <td class="font-bold">${hitInfo.totalSkillDmg.toLocaleString()}</td>
          </tr>
        `;
      });
      skillTableBody.innerHTML = tableHtml;
    }

    // Update Awakening Badges
    const awkBadgesEl = document.getElementById('sim-awakening-badges');
    if (awkBadgesEl) {
      const awk = currentTally.awakenings;
      awkBadgesEl.innerHTML = `
        <span class="badge ${awk.refineAwakening > 0 ? 'badge-active' : ''}">REF AWK +${(awk.refineAwakening * 100).toFixed(0)}%</span>
        <span class="badge ${awk.upgradeAwakening > 0 ? 'badge-active' : ''}">UPG AWK +${(awk.upgradeAwakening * 100).toFixed(0)}%</span>
        <span class="badge ${awk.enchantAwakening > 0 ? 'badge-active' : ''}">ENC AWK +${(awk.enchantAwakening * 100).toFixed(0)}%</span>
      `;
    }

    // Update Tally Box
    const tallyBox = document.getElementById('sim-tally-summary');
    if (tallyBox) {
      const s = currentTally.stats;
      tallyBox.innerHTML = `
        <div class="tally-line"><span>TOTAL P.ATK:</span> <strong class="mono font-bold">${(s['P.ATK'] || 0).toLocaleString()}</strong></div>
        <div class="tally-line"><span>TOTAL STR:</span> <strong class="mono">${(s['STR'] || 0).toLocaleString()}</strong></div>
        <div class="tally-line"><span>P.PEN:</span> <strong class="mono">+${((s['P.PEN'] || 0) * 100).toFixed(1)}%</strong></div>
        <div class="tally-line"><span>FINAL P.DMG:</span> <strong class="mono">+${((s['Final P.DMG Bonus'] || 0) * 100).toFixed(1)}%</strong></div>
        <div class="tally-line"><span>CRIT DMG:</span> <strong class="mono">+${((s['Crit DMG Bonus'] || 0) * 100).toFixed(1)}%</strong></div>
      `;
    }

    // Update Trace Terminal
    const traceEl = document.getElementById('sim-trace-terminal');
    if (traceEl) {
      const sampleHit = global.RoxSimulatorEngine.calculateSkillDamage(
        simState.activeAdapter.getSkills()[0],
        currentTally.stats,
        getActiveBuild().target,
        getActiveBuild().buffs,
        simState.staticData,
        debuffs,
        isPvp
      );
      traceEl.textContent = global.RoxSimulatorEngine.generateDamageWaterfallTrace(sampleHit);
    }

    // Update A/B Diff Panel if compareMode is active
    const diffPanel = document.getElementById('sim-diff-panel');
    if (diffPanel && simState.compareMode && simResA && simResB) {
      const deltaDps = simResB.dps - simResA.dps;
      const deltaDpsPct = simResA.dps > 0 ? ((deltaDps / simResA.dps) * 100).toFixed(2) : '0.00';
      const isPositive = deltaDps >= 0;
      diffPanel.innerHTML = `
        <div class="diff-header font-bold">[A/B LIVE DELTA]</div>
        <div class="diff-row">
          <span>DPS DELTA:</span>
          <span class="mono font-bold ${isPositive ? 'diff-pos' : 'diff-neg'}">
            ${isPositive ? '+' : ''}${deltaDps.toLocaleString()} (${isPositive ? '+' : ''}${deltaDpsPct}%)
          </span>
        </div>
      `;
    }
  }

  function bindSimulatorEvents() {
    // 2-Page Gear Tabs
    const tabCombat = document.getElementById('tab-gear-combat');
    const tabCostumes = document.getElementById('tab-gear-costumes');
    if (tabCombat && tabCostumes) {
      tabCombat.addEventListener('click', () => {
        simState.gearPage = 1;
        tabCombat.classList.add('active');
        tabCombat.style.borderBottomColor = 'var(--border-focus)';
        tabCombat.style.color = 'var(--text-primary)';
        tabCostumes.classList.remove('active');
        tabCostumes.style.borderBottomColor = 'transparent';
        tabCostumes.style.color = 'var(--text-muted)';
        renderGearSlots();
      });

      tabCostumes.addEventListener('click', () => {
        simState.gearPage = 2;
        tabCostumes.classList.add('active');
        tabCostumes.style.borderBottomColor = 'var(--border-focus)';
        tabCostumes.style.color = 'var(--text-primary)';
        tabCombat.classList.remove('active');
        tabCombat.style.borderBottomColor = 'transparent';
        tabCombat.style.color = 'var(--text-muted)';
        renderGearSlots();
      });
    }

    // Modal Studio Openers
    const btnOpenPetModal = document.getElementById('sim-btn-open-pet-modal');
    if (btnOpenPetModal) {
      btnOpenPetModal.addEventListener('click', () => {
        openPetSanctuaryModal();
      });
    }

    const btnOpenDivModal = document.getElementById('sim-btn-open-divinity-modal');
    if (btnOpenDivModal) {
      btnOpenDivModal.addEventListener('click', () => {
        openDivinityStudioModal();
      });
    }

    // Accordion Header Toggle
    document.querySelectorAll('.sim-accordion-header').forEach(header => {
      header.addEventListener('click', () => {
        const targetId = header.dataset.target;
        const content = document.getElementById(targetId);
        const arrow = header.querySelector('.mono');
        if (content) {
          const isActive = content.classList.contains('active');
          content.classList.toggle('active', !isActive);
          if (arrow) arrow.textContent = isActive ? '▸' : '▾';
        }
      });
    });

    // PVP Mode Toggle
    const pvpBtn = document.getElementById('sim-btn-toggle-pvp');
    const pvpCockpit = document.getElementById('sim-pvp-cockpit');
    if (pvpBtn) {
      pvpBtn.addEventListener('click', () => {
        simState.isPvpMode = !simState.isPvpMode;
        pvpBtn.textContent = simState.isPvpMode ? 'MODE: PVP' : 'MODE: PVE';
        pvpBtn.classList.toggle('active', simState.isPvpMode);
        if (pvpCockpit) pvpCockpit.style.display = simState.isPvpMode ? 'block' : 'none';
        recalculateAndRender();
      });
    }

    // PVP Cockpit inputs binding
    [
      'sim-pvp-pdef', 'sim-pvp-fpdef', 'sim-pvp-fpred', 'sim-pvp-fred',
      'sim-pvp-pred', 'sim-pvp-pvpfpred', 'sim-pvp-pvppred', 'sim-pvp-attrres'
    ].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', () => recalculateAndRender());
    });

    // Pet Change
    const petSel = document.getElementById('sim-pet-select');
    if (petSel) {
      petSel.addEventListener('change', (e) => {
        const b = getActiveBuild();
        if (!b.pet) b.pet = {};
        b.pet.name = e.target.value;
        recalculateAndRender();
      });
    }

    const petStarsSel = document.getElementById('sim-pet-stars');
    if (petStarsSel) {
      petStarsSel.addEventListener('change', (e) => {
        const b = getActiveBuild();
        if (!b.pet) b.pet = {};
        b.pet.stars = Number(e.target.value) || 6;
        recalculateAndRender();
      });
    }

    // Companion inputs binding
    const compInputs = [
      ['sim-companion-str', 'str'],
      ['sim-companion-int', 'int'],
      ['sim-companion-patk-pct', 'patk_pct'],
      ['sim-companion-crit-dmg', 'crit_dmg'],
      ['sim-companion-fpdmg', 'final_pdmg_bonus'],
      ['sim-companion-fire', 'fire_enhance']
    ];
    compInputs.forEach(([id, key]) => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('input', (e) => {
          const b = getActiveBuild();
          if (!b.companion) b.companion = {};
          b.companion[key] = Number(e.target.value) || 0;
          recalculateAndRender();
        });
      }
    });

    // Debuff inputs
    const debuffSel = document.getElementById('sim-debuff-select');
    if (debuffSel) {
      debuffSel.addEventListener('change', (e) => {
        const dObj = simState.staticData?.mvp_debuffs?.find(d => d.name === e.target.value);
        if (dObj) {
          const fdefEl = document.getElementById('sim-debuff-fdef');
          if (fdefEl) fdefEl.value = (dObj.debuff_res / 1000).toFixed(2);
        }
        recalculateAndRender();
      });
    }
    ['sim-debuff-fdef', 'sim-debuff-fpdmg'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', () => recalculateAndRender());
    });

    // Divinity delegation (level, quality, and substats)
    const divList = document.getElementById('sim-divinity-list');
    if (divList) {
      divList.addEventListener('change', (e) => {
        const b = getActiveBuild();
        if (!b.divinity) b.divinity = {};
        if (e.target.classList.contains('sim-div-level-select')) {
          const dName = e.target.dataset.name;
          const lv = Number(e.target.value) || 0;
          if (!b.divinity[dName]) b.divinity[dName] = { name: dName, level: lv, quality: 'gold', selected_substats: [] };
          else b.divinity[dName].level = lv;
          recalculateAndRender();
        } else if (e.target.classList.contains('sim-div-quality-select')) {
          const dName = e.target.dataset.name;
          const q = e.target.value;
          if (!b.divinity[dName]) b.divinity[dName] = { name: dName, level: 0, quality: q, selected_substats: [] };
          else b.divinity[dName].quality = q;
          recalculateAndRender();
        }
      });

      divList.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-div-substat');
        if (btn) {
          const part = btn.dataset.part;
          const sub = btn.dataset.sub;
          const b = getActiveBuild();
          if (!b.divinity) b.divinity = {};
          if (!b.divinity[part]) b.divinity[part] = { name: part, level: 0, quality: 'gold', selected_substats: [] };
          if (!Array.isArray(b.divinity[part].selected_substats)) b.divinity[part].selected_substats = [];

          const idx = b.divinity[part].selected_substats.indexOf(sub);
          if (idx >= 0) {
            b.divinity[part].selected_substats.splice(idx, 1);
            btn.classList.remove('filled');
          } else {
            b.divinity[part].selected_substats.push(sub);
            btn.classList.add('filled');
          }
          recalculateAndRender();
        }
      });
    }
    // Class Select
    const classSel = document.getElementById('sim-class-select');
    if (classSel) {
      classSel.addEventListener('change', (e) => {
        const clsId = e.target.value;
        const adapter = global.RoxClassRegistry.getClassAdapter(clsId);
        if (adapter) {
          simState.currentClassId = clsId;
          simState.activeAdapter = adapter;
          simState.buildA = JSON.parse(JSON.stringify(adapter.getDefaultBaseline()));
          simState.buildB = JSON.parse(JSON.stringify(simState.buildA));
          renderSimulatorUI();
          recalculateAndRender();
        }
      });
    }

    // Seed SSOT Button
    const seedBtn = document.getElementById('sim-btn-seed-baseline');
    if (seedBtn) {
      seedBtn.addEventListener('click', () => {
        if (simState.activeAdapter) {
          const baseline = simState.activeAdapter.getDefaultBaseline();
          if (simState.activeSlot === 'A') simState.buildA = JSON.parse(JSON.stringify(baseline));
          else simState.buildB = JSON.parse(JSON.stringify(baseline));
          renderSimulatorUI();
          recalculateAndRender();
        }
      });
    }

    // Core Stats Inputs
    ['str', 'agi', 'vit', 'int', 'dex', 'luk'].forEach(s => {
      const el = document.getElementById(`sim-stat-${s}`);
      if (el) {
        el.addEventListener('input', (e) => {
          const b = getActiveBuild();
          if (!b.stats) b.stats = {};
          b.stats[s] = Number(e.target.value) || 0;
          recalculateAndRender();
        });
      }
    });

    // Battle Achievements (Editable)
    const baInputs = [
      ['sim-ba-str', 'str'],
      ['sim-ba-fpdmg', 'final_pdmg_bonus'],
      ['sim-ba-fire', 'fire_enhance'],
      ['sim-ba-hp', 'max_hp_pct']
    ];
    baInputs.forEach(([id, key]) => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('input', (e) => {
          const b = getActiveBuild();
          if (!b.battle_achievement) b.battle_achievement = {};
          b.battle_achievement[key] = Number(e.target.value) || 0;
          if (key === 'str') b.battle_achievement.vit = Number(e.target.value) || 0;
          recalculateAndRender();
        });
      }
    });

    // Progression Pillars: Title Stats & Shine Points
    const titleInputs = [
      ['sim-title-patk', 'patk'],
      ['sim-title-ppen', 'ppen'],
      ['sim-title-fdmg', 'fdmg'],
      ['sim-title-crit', 'crit']
    ];
    titleInputs.forEach(([id, key]) => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('input', (e) => {
          const b = getActiveBuild();
          if (!b.progression) b.progression = {};
          if (!b.progression.title) b.progression.title = {};
          b.progression.title[key] = Number(e.target.value) || 0;
          recalculateAndRender();
        });
      }
    });

    const shineSel = document.getElementById('sim-shine-points');
    if (shineSel) {
      shineSel.addEventListener('change', (e) => {
        const b = getActiveBuild();
        if (!b.progression) b.progression = {};
        b.progression.shine_points = Number(e.target.value) || 0;
        recalculateAndRender();
      });
    }


    // Buff checkboxes
    const bindBuff = (id, key, valOn, valOff) => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('change', (e) => {
          const b = getActiveBuild();
          if (!b.buffs) b.buffs = {};
          b.buffs[key] = e.target.checked ? valOn : valOff;
          recalculateAndRender();
        });
      }
    };
    bindBuff('sim-buff-converter', 'elemental_converter', 'Fire', 'Neutral');
    bindBuff('sim-buff-spear-flash', 'spear_flash', true, false);
    bindBuff('sim-buff-concentration', 'concentration', true, false);
    bindBuff('sim-buff-spooky-lamp', 'spooky_lamp', true, false);
    bindBuff('sim-buff-pet', 'pet_active', true, false);

    // Sandbox Buttons
    const btnA = document.getElementById('sim-btn-mode-a');
    const btnB = document.getElementById('sim-btn-mode-b');
    const btnClone = document.getElementById('sim-btn-clone-b');
    const btnDiff = document.getElementById('sim-btn-diff');
    const diffPanel = document.getElementById('sim-diff-panel');

    if (btnA) {
      btnA.addEventListener('click', () => {
        simState.activeSlot = 'A';
        btnA.classList.add('active');
        if (btnB) btnB.classList.remove('active');
        renderSimulatorUI();
        recalculateAndRender();
      });
    }

    if (btnClone) {
      btnClone.addEventListener('click', () => {
        simState.buildB = JSON.parse(JSON.stringify(simState.buildA));
        if (btnB) btnB.style.display = 'inline-block';
        if (btnDiff) btnDiff.style.display = 'inline-block';
        alert('Build A cloned to Build B! Switch to Build B to tweak stats.');
      });
    }

    if (btnB) {
      btnB.addEventListener('click', () => {
        simState.activeSlot = 'B';
        btnB.classList.add('active');
        if (btnA) btnA.classList.remove('active');
        renderSimulatorUI();
        recalculateAndRender();
      });
    }

    if (btnDiff) {
      btnDiff.addEventListener('click', () => {
        simState.compareMode = !simState.compareMode;
        btnDiff.classList.toggle('active', simState.compareMode);
        if (diffPanel) diffPanel.style.display = simState.compareMode ? 'block' : 'none';
        recalculateAndRender();
      });
    }

    // Share URL
    const btnShare = document.getElementById('sim-btn-copy-url');
    if (btnShare) {
      btnShare.addEventListener('click', () => {
        const payload = JSON.stringify(getActiveBuild());
        const encoded = btoa(encodeURIComponent(payload));
        window.location.hash = `build=${encoded}`;
        navigator.clipboard?.writeText(window.location.href);
        alert('Build URL copied to clipboard!');
      });
    }

    // Reset Defaults
    const btnReset = document.getElementById('sim-btn-reset-defaults');
    if (btnReset) {
      btnReset.addEventListener('click', () => {
        if (confirm('Reset to SSOT Dragon Knight Golden Reference?')) {
          const baseline = simState.activeAdapter.getDefaultBaseline();
          simState.buildA = JSON.parse(JSON.stringify(baseline));
          simState.buildB = JSON.parse(JSON.stringify(baseline));
          recalculateAndRender();
        }
      });
    }

    // Close modal on Escape key
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const modal = document.getElementById('sim-active-modal');
        if (modal) {
          modal.remove();
          renderSimulatorUI();
          recalculateAndRender();
        }
      }
    });
  }

  // Contextual Bridge: Set monster as target from Wiki
  function setTargetFromWiki(monster) {
    if (!monster) return;
    const b = getActiveBuild();
    b.target = {
      id: monster.id,
      name: `${monster.name} Lv.${monster.level}`,
      level: monster.level,
      element: monster.element_name || monster.element,
      race: monster.race_name || monster.race,
      size: monster.size,
      p_def: monster.base_def || 0,
      p_def_pct: (monster.def_pct || 0) / 100,
      final_p_def: (monster.final_def_pct || 0) / 100,
      final_p_dmg_red: (monster.final_p_dmg_red || 0) / 100
    };

    renderSimulatorUI();
    recalculateAndRender();
  }

  global.RoxSimulatorUI = {
    init: initSimulatorStudio,
    setTargetFromWiki,
    recalculate: recalculateAndRender
  };
})(typeof window !== 'undefined' ? window : globalThis);
