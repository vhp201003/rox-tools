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
    monsterCache: [],
    lastResultsA: null,
    lastResultsB: null,
    lastSimRes: null,
    viewingSharedProfile: false
  };

  const dirtyState = {
    isDirty: false,
    modules: new Set()
  };

  function getOrCreateProfileId() {
    let id = localStorage.getItem('rox-profile-id');
    if (!id) {
      id = (typeof crypto !== 'undefined' && crypto.randomUUID) ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
      localStorage.setItem('rox-profile-id', id);
    }
    return id;
  }

  let autoCalcTimeout = null;
  let autoCalcAbortController = null;

  function triggerAutoCalculate() {
    if (autoCalcTimeout) clearTimeout(autoCalcTimeout);
    autoCalcTimeout = setTimeout(async () => {
      const build = getActiveBuild();
      if (!build) return;

      if (autoCalcAbortController) {
        autoCalcAbortController.abort();
      }
      autoCalcAbortController = new AbortController();

      build.is_pvp = !!simState.isPvpMode;
      if (!build.debuffs) build.debuffs = {};
      build.debuffs.final_p_def = Number(document.getElementById('sim-debuff-fdef')?.value || 0);
      build.debuffs.final_p_dmg_red = Number(document.getElementById('sim-debuff-fpdmg')?.value || 0);

      if (build.is_pvp) {
        build.pvp_target = {
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

      try {
        const res = await fetch('/api/sim/calculate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ build: build }),
          signal: autoCalcAbortController.signal
        });
        if (res.ok) {
          const data = await res.json();
          if (simState.activeSlot === 'A') simState.lastResultsA = data;
          else simState.lastResultsB = data;
          renderSimulationResults();
        }
      } catch (err) {
        if (err.name !== 'AbortError') console.error('Auto-calculate error:', err);
      }
    }, 150);
  }

  function markDirty(moduleName) {
    dirtyState.isDirty = true;
    if (moduleName) dirtyState.modules.add(moduleName);
    updateDirtyUI();
    triggerAutoCalculate();
  }

  function clearDirty() {
    dirtyState.isDirty = false;
    dirtyState.modules.clear();
    updateDirtyUI();
  }

  function updateDirtyUI() {
    const commitBtn = document.getElementById('sim-btn-commit');
    if (commitBtn) {
      if (dirtyState.isDirty && !simState.viewingSharedProfile) {
        commitBtn.style.display = 'inline-block';
        commitBtn.classList.add('dirty-pulse');
      } else {
        commitBtn.style.display = 'none';
        commitBtn.classList.remove('dirty-pulse');
      }
    }
  }

  async function commitBuild() {
    const uuid = getOrCreateProfileId();
    const build = getActiveBuild();
    if (!build) return;

    build.is_pvp = !!simState.isPvpMode;
    if (!build.debuffs) build.debuffs = {};
    build.debuffs.final_p_def = Number(document.getElementById('sim-debuff-fdef')?.value || 0);
    build.debuffs.final_p_dmg_red = Number(document.getElementById('sim-debuff-fpdmg')?.value || 0);

    if (build.is_pvp) {
      build.pvp_target = {
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

    const commitBtn = document.getElementById('sim-btn-commit');
    if (commitBtn) commitBtn.textContent = 'COMPUTING...';

    try {
      const res = await fetch('/api/sim/profiles/' + uuid, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ build: build })
      });

      if (res.ok) {
        const data = await res.json();
        if (simState.activeSlot === 'B') {
          simState.lastResultsB = data.computed_results;
        } else {
          simState.lastResultsA = data.computed_results;
        }
        renderComputedResults(data.computed_results);
        clearDirty();
        if (commitBtn) commitBtn.textContent = '[ COMMIT CHANGES ]';
      } else {
        if (commitBtn) commitBtn.textContent = 'COMMIT (RETRY)';
      }
    } catch (e) {
      console.error('Commit error:', e);
      if (commitBtn) commitBtn.textContent = 'COMMIT (RETRY)';
    }
  }

  async function fetchAndRenderProfile() {
    // Check if share URL parameter is provided
    const urlParams = new URLSearchParams(window.location.search);
    const sharedProfileId = urlParams.get('profile');

    if (sharedProfileId) {
      try {
        const res = await fetch('/api/sim/profiles/' + sharedProfileId);
        if (res.ok) {
          const profile = await res.json();
          if (profile.build_data) {
            simState.buildA = profile.build_data;
            simState.buildB = JSON.parse(JSON.stringify(simState.buildA));
            simState.viewingSharedProfile = sharedProfileId !== getOrCreateProfileId();
            renderSimulatorUI();
            if (profile.computed_results) {
              simState.lastResultsA = profile.computed_results;
              simState.lastResultsB = profile.computed_results;
              renderComputedResults(profile.computed_results);
            }
            if (simState.viewingSharedProfile) enterReadOnlyMode();
            clearDirty();
            return;
          }
        } else {
          alert('Shared profile not found or expired. Loaded default profile.');
        }
      } catch (e) {
        console.warn('Shared profile load error:', e);
      }
    }

    const uuid = getOrCreateProfileId();
    try {
      const res = await fetch('/api/sim/profiles/' + uuid);
      if (res.ok) {
        const profile = await res.json();
        if (profile.build_data) {
          simState.buildA = profile.build_data;
          simState.buildB = JSON.parse(JSON.stringify(simState.buildA));
          renderSimulatorUI();
          if (profile.computed_results) {
            simState.lastResultsA = profile.computed_results;
            simState.lastResultsB = profile.computed_results;
            renderComputedResults(profile.computed_results);
            clearDirty();
            return;
          }
        }
      }
    } catch (e) {
      console.warn('Profile fetch error, falling back to default:', e);
    }
    // No saved profile or failed
    markDirty('init');
  }

  function enterReadOnlyMode() {
    const commitBtn = document.getElementById('sim-btn-commit');
    if (commitBtn) commitBtn.style.display = 'none';

    const existingBanner = document.getElementById('shared-profile-banner');
    if (!existingBanner) {
      const banner = document.createElement('div');
      banner.id = 'shared-profile-banner';
      banner.style.cssText = 'background: #1e3a8a; color: #93c5fd; padding: 6px 12px; font-size: 11px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; border-radius: 4px; margin-bottom: 8px;';
      banner.innerHTML = '<span>[ VIEWING SHARED PROFILE ] Read-Only</span> <button type="button" id="btn-fork-profile" style="background: #3b82f6; color: white; border: none; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 10px; font-weight: bold;">Fork to My Profile</button>';
      const targetCard = document.getElementById('sim-target-card');
      if (targetCard && targetCard.parentNode) {
        targetCard.parentNode.insertBefore(banner, targetCard);
      }

      document.getElementById('btn-fork-profile')?.addEventListener('click', () => {
        simState.viewingSharedProfile = false;
        banner.remove();
        window.history.replaceState(null, '', window.location.pathname);
        markDirty('fork');
      });
    }
  }

  function renderComputedResults(currentSimRes) {
    if (!currentSimRes) return;
    const currentTally = { stats: currentSimRes.talliedStats || {}, awakenings: currentSimRes.awakenings || {} };

    // Update Headline Metrics
    const dpsEl = document.getElementById('sim-metric-dps');
    const dpmEl = document.getElementById('sim-metric-dpm');
    const critHitEl = document.getElementById('sim-metric-crit-hit');
    const nonCritHitEl = document.getElementById('sim-metric-noncrit-hit');

    if (dpsEl) dpsEl.textContent = Number(currentSimRes.dps || 0).toLocaleString();
    if (dpmEl) dpmEl.textContent = 'DPM: ' + ((Number(currentSimRes.totalDmg3m || 0)) / 1000000).toFixed(2) + 'M / 3 MINS';

    const hits = currentSimRes.hitsBreakdown || [];
    const firstHit = hits[0] || { damagePerHit: 0 };
    if (critHitEl) critHitEl.textContent = Number(firstHit.damagePerHit || 0).toLocaleString();
    if (nonCritHitEl) nonCritHitEl.textContent = 'Normal Attack: ' + Number(firstHit.damagePerHit || 0).toLocaleString();

    // Update 9-Skill Rotation Damage Parity Matrix
    const skillTableBody = document.getElementById('sim-skill-table-body');
    if (skillTableBody && simState.activeAdapter) {
      const skills = simState.activeAdapter.getSkills();
      let tableHtml = '';
      skills.forEach(sk => {
        const hitInfo = hits.find(h => h.skillId === sk.id) || { damagePerHit: 0, hitsIn60s: 0, totalSkillDmg: 0 };
        tableHtml += '<tr>' +
          '<td><strong>' + sk.name + '</strong></td>' +
          '<td class="diff-pos">' + Number(hitInfo.damagePerHit || 0).toLocaleString() + '</td>' +
          '<td>' + Number(hitInfo.damagePerHit || 0).toLocaleString() + '</td>' +
          '<td>' + hitInfo.hitsIn60s + '</td>' +
          '<td class="font-bold">' + Number(hitInfo.totalSkillDmg || 0).toLocaleString() + '</td>' +
          '</tr>';
      });
      skillTableBody.innerHTML = tableHtml;
    }

    // Update Awakening Badges
    const awkBadgesEl = document.getElementById('sim-awakening-badges');
    if (awkBadgesEl) {
      const awk = currentTally.awakenings;
      awkBadgesEl.innerHTML =
        '<span class="badge ' + (awk.refineAwakening > 0 ? 'badge-active' : '') + '">REF AWK +' + (awk.refineAwakening * 100).toFixed(0) + '%</span> ' +
        '<span class="badge ' + (awk.upgradeAwakening > 0 ? 'badge-active' : '') + '">UPG AWK +' + (awk.upgradeAwakening * 100).toFixed(0) + '%</span> ' +
        '<span class="badge ' + (awk.enchantAwakening > 0 ? 'badge-active' : '') + '">ENC AWK +' + (awk.enchantAwakening * 100).toFixed(0) + '%</span>';
    }

    // Update Tally Box
    const tallyBox = document.getElementById('sim-tally-summary');
    if (tallyBox) {
      const s = currentTally.stats;
      tallyBox.innerHTML =
        '<div class="tally-line"><span>TOTAL P.ATK:</span> <strong class="mono font-bold">' + (Number(s["P.ATK"] || 0)).toLocaleString() + '</strong></div>' +
        '<div class="tally-line"><span>TOTAL STR:</span> <strong class="mono">' + (Number(s["STR"] || 0)).toLocaleString() + '</strong></div>' +
        '<div class="tally-line"><span>P.PEN:</span> <strong class="mono">+' + ((Number(s["P.PEN"] || 0)) * 100).toFixed(1) + '%</strong></div>' +
        '<div class="tally-line"><span>FINAL P.DMG:</span> <strong class="mono">+' + ((Number(s["Final P.DMG Bonus"] || 0)) * 100).toFixed(1) + '%</strong></div>' +
        '<div class="tally-line"><span>CRIT DMG:</span> <strong class="mono">+' + ((Number(s["Crit DMG Bonus"] || 0)) * 100).toFixed(1) + '%</strong></div>';
    }

    // Update Stat Breakdown Accordion (100% Traceability)
    const breakdownBox = document.getElementById('sim-stat-breakdown-accordion');
    if (breakdownBox && currentSimRes.statBreakdown) {
      let bdHtml = '';
      const bkStats = Object.keys(currentSimRes.statBreakdown);
      bkStats.forEach(statKey => {
        const sources = currentSimRes.statBreakdown[statKey];
        const totalVal = Object.values(sources).reduce((a, b) => a + Number(b || 0), 0);
        bdHtml += `
          <details style="margin-bottom: 4px; border-bottom: 1px dashed var(--border); padding-bottom: 2px;">
            <summary style="cursor: pointer; display: flex; justify-content: space-between; font-weight: 700; color: var(--text-primary); padding: 2px 0;">
              <span>${statKey}</span>
              <span class="mono font-bold" style="color: var(--border-focus);">${Number(totalVal).toLocaleString()}</span>
            </summary>
            <div style="padding-left: 8px; margin-top: 2px; color: var(--text-secondary); display: flex; flex-direction: column; gap: 2px;">
              ${Object.entries(sources).map(([src, val]) => `
                <div style="display: flex; justify-content: space-between; font-size: 9.5px;">
                  <span style="text-transform: uppercase;">${src.replace(/_/g, ' ')}:</span>
                  <span class="mono">+${Number(val).toLocaleString()}</span>
                </div>
              `).join('')}
            </div>
          </details>
        `;
      });
      breakdownBox.innerHTML = bdHtml || '<div style="color: var(--text-muted);">No breakdown available</div>';
    }

    const dollAwk = document.getElementById('sim-awakening-badges-doll');
    if (dollAwk && awkBadgesEl) {
      dollAwk.innerHTML = awkBadgesEl.innerHTML;
    }

    // Update A/B Diff Panel if compareMode is active
    const diffPanel = document.getElementById('sim-diff-panel');
    if (diffPanel && simState.compareMode && simState.lastResultsA && simState.lastResultsB) {
      const deltaDps = simState.lastResultsB.dps - simState.lastResultsA.dps;
      const deltaDpsPct = simState.lastResultsA.dps > 0 ? ((deltaDps / simState.lastResultsA.dps) * 100).toFixed(2) : '0.00';
      const isPositive = deltaDps >= 0;
      diffPanel.innerHTML =
        '<div class="diff-header font-bold">[A/B SERVER DELTA]</div>' +
        '<div class="diff-row">' +
        '<span>DPS DELTA:</span>' +
        '<span class="mono font-bold ' + (isPositive ? 'diff-pos' : 'diff-neg') + '">' +
        (isPositive ? '+' : '') + deltaDps.toLocaleString() + ' (' + (isPositive ? '+' : '') + deltaDpsPct + '%)' +
        '</span></div>';
    }

    simState.lastSimRes = currentSimRes;
    updateBentoSummaryTiles();
    renderStatCalibrator();
  }

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
      await fetchAndRenderProfile();

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
    updateBentoSummaryTiles();
    renderStatCalibrator();
  }

  function isTwoHandedWeapon(weapon) {
    if (!weapon) return false;
    const name = typeof weapon === 'string' ? weapon : (weapon.name || '');
    const type = (typeof weapon === 'object' && weapon.type) ? weapon.type : '';
    const combined = (name + ' ' + type).toLowerCase();
    return combined.includes('2h') || combined.includes('two-hand') || combined.includes('bow') || combined.includes('katar') || combined.includes('broadsword') || combined.includes('claymore') || combined.includes('spear');
  }

  const COMBAT_LEFT_SLOTS = [
    { key: 'clothes', label: 'CLOTHES / ARMOR', type: 'Clothes' },
    { key: 'cloak', label: 'CLOAK', type: 'Cloak' },
    { key: 'shoes', label: 'SHOES', type: 'Shoes' },
    { key: 'accessory_1', label: 'ACCESSORY 1', type: 'Accessory' }
  ];

  const COMBAT_RIGHT_SLOTS = [
    { key: 'weapon', label: 'MAIN-HAND', type: 'Weapon' },
    { key: 'shield', label: 'SHIELD / OFF-HAND', type: 'Shield' },
    { key: 'talisman', label: 'TALISMAN', type: 'Talisman' },
    { key: 'accessory_2', label: 'ACCESSORY 2', type: 'Accessory' }
  ];

  const COSTUME_LEFT_SLOTS = [
    { key: 'costume_head', label: 'HEAD TOP', type: 'CostumeHead' },
    { key: 'costume_eyes', label: 'HEAD MID', type: 'CostumeEyes' },
    { key: 'costume_mouth', label: 'HEAD BTM', type: 'CostumeMouth' }
  ];

  const COSTUME_RIGHT_SLOTS = [
    { key: 'costume_back', label: 'BACK', type: 'CostumeBack' },
    { key: 'costume_tail', label: 'TAIL', type: 'CostumeTail' },
    { key: 'costume_mask', label: 'EXTRA / MASK', type: 'CostumeMask' }
  ];

  const COMBAT_SLOTS = [...COMBAT_LEFT_SLOTS, ...COMBAT_RIGHT_SLOTS];
  const COSTUME_SLOTS = [...COSTUME_LEFT_SLOTS, ...COSTUME_RIGHT_SLOTS];

  function switchPaperDollTab(tabKey) {
    simState.paperDollTab = tabKey;
    const btnCombat = document.getElementById('tab-gear-combat');
    const btnCostume = document.getElementById('tab-gear-costumes');
    if (btnCombat && btnCostume) {
      btnCombat.classList.toggle('active', tabKey === 'combat');
      btnCostume.classList.toggle('active', tabKey === 'costumes' || tabKey === 'costume');
    }
    renderPaperDoll();
  }

  function renderSlotCard(s, loadout, is2H) {
    const item = loadout[s.key] || { name: 'Empty', refine: 0, upgrade: 0, enchant_city: 'Prontera', enchant_lv: 0, cards: [] };
    const isCostume = s.key.startsWith('costume_');
    const isShieldLocked = s.key === 'shield' && is2H;

    let maxSockets = 2;
    if (s.key === 'weapon') {
      maxSockets = is2H ? 5 : 3;
    } else if (s.key === 'shield') {
      maxSockets = is2H ? 0 : 2;
    } else {
      maxSockets = 2;
    }

    const cardsList = Array.isArray(item.cards) ? item.cards : [];
    const quality = item.quality || (isCostume ? 'purple' : 'gold');
    const tierClass = 'tier-' + (quality.toLowerCase() || 'white');

    let dotsHtml = '';
    for (let i = 0; i < maxSockets; i++) {
      const isFilled = !!cardsList[i];
      dotsHtml += `<span class="card-socket-dot ${isFilled ? 'filled' : ''}" title="${cardsList[i] || 'Empty Socket'}"></span>`;
    }

    let encBrief = '';
    if (!isCostume && Array.isArray(item.enchant_lines) && item.enchant_lines.length > 0) {
      const l1 = item.enchant_lines[0];
      const sameCity = item.enchant_lines.every(l => l.city === l1.city);
      encBrief = sameCity ? `${l1.city.split(' ')[0]} L${l1.level || 0}` : 'Enchanted (3L)';
    }

    const lockedBadgeHtml = isShieldLocked ? `<div class="slot-locked-badge">[Locked by 2H]</div>` : '';
    const lockedClass = isShieldLocked ? 'slot-locked' : '';

    return `
      <div class="doll-slot ${lockedClass}" data-slot="${s.key}" id="slot-${s.key}">
        ${lockedBadgeHtml}
        <div class="doll-slot-header">
          <span class="doll-slot-tag">[${s.label}]</span>
          <span class="doll-slot-tier ${tierClass}">${quality.toUpperCase()}</span>
        </div>
        <div class="doll-slot-name" title="${item.name || ''}">${item.name || 'Empty'}</div>
        <div class="doll-slot-badges">
          ${!isCostume ? `
            <span class="doll-pill doll-pill-refine">+${item.refine || 0}</span>
            <span class="doll-pill doll-pill-upgrade">U.${item.upgrade || 0}</span>
          ` : '<span class="doll-pill" style="color: var(--text-muted);">COSTUME</span>'}
          ${encBrief ? `<span class="doll-slot-enchant">${encBrief}</span>` : ''}
        </div>
        <div class="doll-slot-cards">${dotsHtml}</div>
      </div>
    `;
  }

  function renderPaperDoll() {
    const doll = document.getElementById('sim-paper-doll');
    if (!doll) return;

    const build = getActiveBuild();
    const loadout = build.loadout || {};
    const activeTab = simState.paperDollTab || 'combat';
    const isCostumeTab = (activeTab === 'costumes' || activeTab === 'costume');

    const is2H = isTwoHandedWeapon(loadout.weapon);
    if (!loadout.shield) {
      loadout.shield = { name: 'Empty Shield', type: 'Shield', refine: 0, upgrade: 0, cards: [] };
    }
    loadout.shield.is_disabled = is2H;

    const leftSlots = isCostumeTab ? COSTUME_LEFT_SLOTS : COMBAT_LEFT_SLOTS;
    const rightSlots = isCostumeTab ? COSTUME_RIGHT_SLOTS : COMBAT_RIGHT_SLOTS;
    const allTabSlots = [...leftSlots, ...rightSlots];

    const leftHtml = leftSlots.map(s => renderSlotCard(s, loadout, is2H)).join('');
    const rightHtml = rightSlots.map(s => renderSlotCard(s, loadout, is2H)).join('');

    const rawClass = build.class_name || build.class_id || simState.currentClass || 'dragon_knight';
    const className = String(rawClass).replace(/_/g, ' ').toUpperCase();
    const baseLv = build.base_level || 87;
    const jobLv = build.job_level || 17;

    const centerHtml = `
      <div class="doll-center-preview">
        <div class="doll-center-pedestal">
          <div class="doll-avatar-halo"></div>
          <div class="doll-avatar-icon">
            <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"/>
              <path d="M12 6v6l4 2"/>
            </svg>
          </div>
          <div class="doll-center-class">${className}</div>
          <div class="doll-center-levels">Lv.${baseLv} / Job.${jobLv}</div>
          <div class="doll-center-mode-tag">[${isCostumeTab ? 'WARDROBE (6 SLOTS)' : 'COMBAT (8 SLOTS)'}]</div>
        </div>
      </div>
    `;

    doll.innerHTML = `
      <div class="doll-column doll-col-left">${leftHtml}</div>
      ${centerHtml}
      <div class="doll-column doll-col-right">${rightHtml}</div>
    `;

    allTabSlots.forEach(s => {
      const el = document.getElementById('slot-' + s.key);
      if (el && !(s.key === 'shield' && is2H)) {
        el.onclick = () => openEquipDrawer(s.key);
      }
    });
  }

  function renderGearSlots() {
    renderPaperDoll();
  }

  function openEquipDrawer(slotKey) {
    simState.activeDrawerSlot = slotKey;
    const drawer = document.getElementById('sim-equip-drawer');
    const backdrop = document.getElementById('sim-drawer-backdrop');
    if (!drawer || !backdrop) return;

    const build = getActiveBuild();
    const loadout = build.loadout || {};
    const allSlots = [...COMBAT_SLOTS, ...COSTUME_SLOTS];
    const slotInfo = allSlots.find(s => s.key === slotKey) || { key: slotKey, label: slotKey.toUpperCase(), type: 'Weapon' };
    const item = loadout[slotKey] || { name: 'Empty', refine: 0, upgrade: 0, enchant_city: 'Prontera', enchant_lv: 0, cards: [] };

    document.querySelectorAll('.doll-slot').forEach(el => el.classList.remove('active-editing'));
    const activeDollEl = document.getElementById('slot-' + slotKey);
    if (activeDollEl) activeDollEl.classList.add('active-editing');

    const slotBadge = document.getElementById('drawer-slot-tag');
    const slotTitle = document.getElementById('drawer-slot-title');
    if (slotBadge) slotBadge.textContent = '[' + slotInfo.label + ']';
    if (slotTitle) slotTitle.textContent = item.name || 'EMPTY SLOT';

    renderDrawerContent(slotInfo, item);

    backdrop.style.display = 'block';
    drawer.classList.add('open');
  }

  function closeEquipDrawer() {
    const drawer = document.getElementById('sim-equip-drawer');
    const backdrop = document.getElementById('sim-drawer-backdrop');
    if (drawer) drawer.classList.remove('open');
    if (backdrop) backdrop.style.display = 'none';
    document.querySelectorAll('.doll-slot').forEach(el => el.classList.remove('active-editing'));
    simState.activeDrawerSlot = null;
    renderPaperDoll();
  }

  function renderDrawerContent(slotInfo, item) {
    const body = document.getElementById('drawer-equip-body');
    if (!body) return;

    const slotKey = slotInfo.key;
    const isCostume = slotKey.startsWith('costume_');
    const quality = item.quality || (isCostume ? 'purple' : 'gold');
    const cities = ['Prontera', 'Morroc', 'Alberta', 'Izlude Island', 'Payon', 'Geffen', 'Glast Heim', 'Comodo', 'Umbala', 'Juno'];
    const build = getActiveBuild();
    const is2H = isTwoHandedWeapon(build.loadout?.weapon);
    let maxSockets = 2;
    if (slotKey === 'weapon') {
      maxSockets = is2H ? 5 : 3;
    } else if (slotKey === 'shield') {
      maxSockets = is2H ? 0 : 2;
    } else {
      maxSockets = 2;
    }
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

    let encCategory = 'armor';
    if (slotKey === 'weapon') encCategory = 'weapon';
    else if (['accessory_1', 'accessory_2', 'talisman'].includes(slotKey)) encCategory = 'accessory';

    let enchantLinesHtml = '';
    item.enchant_lines.forEach((line, lineIdx) => {
      const lineCity = line.city || 'Prontera';
      const availableStats = Object.keys(simState.staticData?.enchant_cities?.[lineCity]?.[encCategory] || { STR: 1 });
      const lineStat = line.stat || availableStats[0] || 'STR';
      const lineLv = Number(line.level) || 0;

      enchantLinesHtml += `
        <div class="studio-row" style="gap: 4px; margin-top: 4px; align-items: center;">
          <span class="field-lbl" style="width: 22px; font-weight: 700;">L${lineIdx + 1}:</span>
          <select class="filter-select drawer-enc-city" data-slot="${slotKey}" data-line="${lineIdx}" style="font-size: 11px; padding: 2px 4px; width: 90px; height: 26px;">
            ${cities.map(c => `<option value="${c}" ${lineCity === c ? 'selected' : ''}>${c.split(' ')[0]}</option>`).join('')}
          </select>
          <select class="filter-select drawer-enc-stat" data-slot="${slotKey}" data-line="${lineIdx}" style="font-size: 11px; padding: 2px 4px; flex: 1; height: 26px;">
            ${availableStats.map(st => `<option value="${st}" ${lineStat === st ? 'selected' : ''}>${st}</option>`).join('')}
          </select>
          <div class="stepper-group" style="height: 26px;">
            <button type="button" class="stepper-btn drawer-enc-down" data-slot="${slotKey}" data-line="${lineIdx}">-</button>
            <span class="stepper-val mono font-bold" style="font-size: 11px; min-width: 26px;">L${lineLv}</span>
            <button type="button" class="stepper-btn drawer-enc-up" data-slot="${slotKey}" data-line="${lineIdx}">+</button>
          </div>
        </div>
      `;
    });

    let cardSocketsHtml = '';
    for (let i = 0; i < maxSockets; i++) {
      const cardName = cardsList[i];
      cardSocketsHtml += `
        <div class="studio-row" style="justify-content: space-between; padding: 4px 6px; background: var(--bg-canvas); border: 1px solid var(--border); border-radius: var(--radius-sm); margin-top: 4px;">
          <div style="display: flex; align-items: center; gap: 6px;">
            <span class="card-socket-dot ${cardName ? 'filled' : ''}"></span>
            <span style="font-size: 11px; font-weight: ${cardName ? '700' : '400'}; color: ${cardName ? 'var(--text-primary)' : 'var(--text-muted)'};">
              ${cardName ? `[Slot ${i + 1}] ${cardName}` : `[Slot ${i + 1}] Empty Socket`}
            </span>
          </div>
          <div style="display: flex; gap: 4px;">
            <button type="button" class="btn-text drawer-pick-card" data-slot="${slotKey}" data-type="${slotInfo.type}" data-socket="${i}" style="font-size: 10px; padding: 2px 6px;">
              ${cardName ? 'CHANGE' : 'SELECT'}
            </button>
            ${cardName ? `<button type="button" class="btn-text drawer-clear-card" data-slot="${slotKey}" data-socket="${i}" style="font-size: 10px; color: #ef4444; padding: 2px 4px;">✕</button>` : ''}
          </div>
        </div>
      `;
    }

    body.innerHTML = `
      <div class="studio-section" style="padding: 0 0 10px 0;">
        <label class="studio-label">EQUIPPED ITEM & WIKI SELECTION</label>
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; background: var(--bg-canvas); padding: 8px; border: 1px solid var(--border); border-radius: var(--radius-sm);">
          <div>
            <div style="font-weight: 700; font-size: 13px; color: var(--text-primary);">${item.name || 'Empty'}</div>
            <div style="font-size: 9px; font-family: var(--font-mono); color: var(--border-focus); margin-top: 2px;">TYPE: ${slotInfo.type.toUpperCase()} | QUALITY: ${quality.toUpperCase()}</div>
          </div>
          <button type="button" class="btn-action font-bold btn-pick-item" data-slot="${slotKey}" data-type="${slotInfo.type}" style="padding: 4px 10px; font-size: 11px;">CHANGE ITEM</button>
        </div>
      </div>

      ${!isCostume ? `
        <div class="studio-section" style="padding: 10px 0;">
          <label class="studio-label">REFINEMENT & UPGRADE DUAL CONTROLS</label>
          <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span class="field-lbl font-bold">REFINEMENT LEVEL (+0 to +20)</span>
              <span class="mono font-bold" id="drawer-refine-display" style="color: #34d399; font-size: 12px;">+${item.refine || 0}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <input type="range" id="drawer-slider-refine" min="0" max="20" value="${item.refine || 0}" style="flex: 1; accent-color: #34d399; cursor: pointer;">
              <input type="number" id="drawer-num-refine" min="0" max="20" value="${item.refine || 0}" class="filter-input-num" style="width: 48px; text-align: center; font-weight: 700;">
            </div>
          </div>

          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span class="field-lbl font-bold">UPGRADE LEVEL (0 to 240)</span>
              <span class="mono font-bold" id="drawer-upgrade-display" style="color: #38bdf8; font-size: 12px;">Lv.${item.upgrade || 0}</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <input type="range" id="drawer-slider-upgrade" min="0" max="240" step="5" value="${item.upgrade || 0}" style="flex: 1; accent-color: #38bdf8; cursor: pointer;">
              <input type="number" id="drawer-num-upgrade" min="0" max="240" step="5" value="${item.upgrade || 0}" class="filter-input-num" style="width: 48px; text-align: center; font-weight: 700;">
            </div>
          </div>
        </div>
      ` : ''}

      ${!isCostume ? `
        <div class="studio-section" style="padding: 10px 0;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <label class="studio-label" style="margin: 0;">3-LINE INDEPENDENT ENCHANTMENT (LV.1-15)</label>
            <span style="font-size: 9px; color: var(--text-muted);">Duplicates Allowed</span>
          </div>
          <div id="drawer-enchant-rows">
            ${enchantLinesHtml}
          </div>
        </div>
      ` : ''}

      <div class="studio-section" style="padding: 10px 0; border: none;">
        <label class="studio-label">CARD SOCKETING (${cardsList.filter(Boolean).length}/${maxSockets} SLOTTED)</label>
        <div>
          ${cardSocketsHtml}
        </div>
      </div>

      <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 8px;">
        <button type="button" class="btn-action font-bold" id="btn-save-equip-item" style="padding: 6px 16px; font-size: 11px; background: linear-gradient(135deg, #0284c7, #2563eb); color: #fff; border: 1px solid #38bdf8; border-radius: 4px; cursor: pointer;">
          SAVE & COMMIT
        </button>
      </div>
    `;

    bindDrawerEvents(slotInfo, item);
  }

  function bindDrawerEvents(slotInfo, item) {
    const slotKey = slotInfo.key;
    const b = getActiveBuild();

    const sliderRef = document.getElementById('drawer-slider-refine');
    const numRef = document.getElementById('drawer-num-refine');
    const dispRef = document.getElementById('drawer-refine-display');
    if (sliderRef && numRef) {
      const syncRefine = (val) => {
        const num = Math.min(20, Math.max(0, Number(val) || 0));
        sliderRef.value = num;
        numRef.value = num;
        if (dispRef) dispRef.textContent = '+' + num;
        item.refine = num;
        renderPaperDoll();
        markDirty();
      };
      sliderRef.oninput = (e) => syncRefine(e.target.value);
      numRef.oninput = (e) => syncRefine(e.target.value);
    }

    const sliderUpg = document.getElementById('drawer-slider-upgrade');
    const numUpg = document.getElementById('drawer-num-upgrade');
    const dispUpg = document.getElementById('drawer-upgrade-display');
    if (sliderUpg && numUpg) {
      const syncUpgrade = (val) => {
        const num = Math.min(240, Math.max(0, Number(val) || 0));
        sliderUpg.value = num;
        numUpg.value = num;
        if (dispUpg) dispUpg.textContent = 'Lv.' + num;
        item.upgrade = num;
        renderPaperDoll();
        markDirty();
      };
      sliderUpg.oninput = (e) => syncUpgrade(e.target.value);
      numUpg.oninput = (e) => syncUpgrade(e.target.value);
    }

    const pickItemBtn = document.querySelector('.btn-pick-item');
    if (pickItemBtn) {
      pickItemBtn.onclick = () => openItemPicker(slotKey, slotInfo.type);
    }

    document.querySelectorAll('.drawer-enc-city').forEach(sel => {
      sel.onchange = () => {
        const lineIdx = Number(sel.dataset.line);
        if (item.enchant_lines?.[lineIdx]) {
          item.enchant_lines[lineIdx].city = sel.value;
          const encCat = slotKey === 'weapon' ? 'weapon' : (['accessory_1', 'accessory_2', 'talisman'].includes(slotKey) ? 'accessory' : 'armor');
          const availableStats = Object.keys(simState.staticData?.enchant_cities?.[sel.value]?.[encCat] || {});
          item.enchant_lines[lineIdx].stat = availableStats[0] || 'STR';
          renderDrawerContent(slotInfo, item);
          renderPaperDoll();
          markDirty();
        }
      };
    });

    document.querySelectorAll('.drawer-enc-stat').forEach(sel => {
      sel.onchange = () => {
        const lineIdx = Number(sel.dataset.line);
        if (item.enchant_lines?.[lineIdx]) {
          item.enchant_lines[lineIdx].stat = sel.value;
          renderPaperDoll();
          markDirty();
        }
      };
    });

    document.querySelectorAll('.drawer-enc-up').forEach(btn => {
      btn.onclick = () => {
        const lineIdx = Number(btn.dataset.line);
        if (item.enchant_lines?.[lineIdx]) {
          const curLv = Number(item.enchant_lines[lineIdx].level) || 0;
          if (curLv < 15) item.enchant_lines[lineIdx].level = curLv + 1;
          renderDrawerContent(slotInfo, item);
          renderPaperDoll();
          markDirty();
        }
      };
    });

    document.querySelectorAll('.drawer-enc-down').forEach(btn => {
      btn.onclick = () => {
        const lineIdx = Number(btn.dataset.line);
        if (item.enchant_lines?.[lineIdx]) {
          const curLv = Number(item.enchant_lines[lineIdx].level) || 0;
          item.enchant_lines[lineIdx].level = Math.max(0, curLv - 1);
          renderDrawerContent(slotInfo, item);
          renderPaperDoll();
          markDirty();
        }
      };
    });

    document.querySelectorAll('.drawer-pick-card').forEach(btn => {
      btn.onclick = () => {
        const socketIdx = Number(btn.dataset.socket) || 0;
        openCardPicker(slotKey, slotInfo.type, socketIdx);
      };
    });

    document.querySelectorAll('.drawer-clear-card').forEach(btn => {
      btn.onclick = () => {
        const socketIdx = Number(btn.dataset.socket) || 0;
        if (Array.isArray(item.cards)) {
          item.cards[socketIdx] = null;
          item.cards = item.cards.filter(Boolean);
          renderDrawerContent(slotInfo, item);
          renderPaperDoll();
          markDirty();
        }
      };
    });

    const btnSaveItem = document.getElementById('btn-save-equip-item');
    if (btnSaveItem) {
      btnSaveItem.onclick = () => {
        closeEquipDrawer();
        markDirty('equipment');
        const commitBtn = document.getElementById('btn-commit-profile');
        if (commitBtn && typeof commitBtn.click === 'function') {
          commitBtn.click();
        }
      };
    }
  }

  function openItemPicker(slotKey, itemType) {
    let catalog = simState.staticData?.equip_base?.[itemType] || simState.staticData?.equip_base?.[slotKey] || [];
    if (!catalog.length && (itemType.startsWith('Costume') || slotKey.startsWith('costume_'))) {
      catalog = simState.staticData?.equip_base?.['CostumeBack'] || [
        { name: `Classic ${slotKey.replace('costume_', '').toUpperCase()}`, stats: {} }
      ];
    }
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
          markDirty();
        }
        modal.remove();
      };
    });
  }

  function openCardPicker(slotKey, itemType, socketIdx = 0) {
    let catKey = 'Weapon';
    if (itemType === 'Clothes' || itemType === 'Shield') catKey = 'Clothes';
    else if (itemType === 'Cloak') catKey = 'Cloak';
    else if (itemType === 'Shoes') catKey = 'Shoes';
    else if (itemType === 'Accessory' || itemType === 'Talisman') catKey = 'Accessory';
    else if (itemType && (itemType.startsWith('Costume') || itemType.startsWith('Headgear'))) catKey = 'Headgear';

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
          markDirty();
        }
        modal.remove();
      };
    });
  }

  const DIVINITY_PARTS = [
    { index: 1, key: 'Part I', name: 'Spear of Eternity' },
    { index: 2, key: 'Part II', name: 'Thunderous Hammer' },
    { index: 3, key: 'Part III', name: 'Blade of Godslayer' },
    { index: 4, key: 'Part IV', name: 'Wolf Shackles' },
    { index: 5, key: 'Part V', name: 'Stormrage Halberd' },
    { index: 6, key: 'Part VI', name: "Chanter's Harp" },
    { index: 7, key: 'Part VII', name: 'Bow of Winter' },
    { index: 8, key: 'Part VIII', name: "Reaper's Scythe" }
  ];

  const DIV_COL_OFFENSE_MAIN = [
    'P.ATK%', 'M.ATK%', 'Final P.PEN', 'Final M.PEN',
    'P.DMG Bonus', 'P.DMG Bonus%', 'M.DMG Bonus', 'M.DMG Bonus%',
    'Final P.DMG Bonus', 'Final M.DMG Bonus'
  ];

  const DIV_COL_OFFENSE_TACTICAL = [
    'Final ASPD', 'Final Haste', 'Final Crit', 'Crit DMG Bonus',
    'Bonus DMG to Small', 'Bonus DMG to Medium', 'Bonus DMG to Large',
    'Physical Lifesteal', 'Magic Lifesteal'
  ];

  const DIV_COL_DEFENSE_MAIN = [
    'Max HP%', 'Max SP%',
    'Final P.DEF', 'Final M.DEF',
    'Final P.DMG RED', 'Final M.DMG RED'
  ];

  const DIV_COL_DEFENSE_TACTICAL = [
    'Final Anti-Crit', 'Final Flee',
    'P.DMG Reflect', 'M.DMG Reflect',
    'HP Regen per 5s', 'SP Regen per 5s'
  ];

  const DIV_COL_ATTRIBUTES = [
    'STR', 'STR%', 'AGI', 'AGI%', 'VIT', 'VIT%',
    'INT', 'INT%', 'DEX', 'DEX%', 'LUK', 'LUK%'
  ];

  const DIV_COL_ELEMENTS = [
    'Fire Enhance', 'Water Enhance', 'Wind Enhance', 'Earth Enhance',
    'Holy Enhance', 'Shadow Enhance', 'Ghost Enhance', 'Undead Enhance',
    'Poison Enhance', 'Neutral Enhance'
  ];

  function openDivinityModal() {
    const modal = document.getElementById('divinity-modal');
    if (!modal) return;

    if (!simState.activeDivPart) {
      simState.activeDivPart = DIVINITY_PARTS[0].name;
    }

    const tabsContainer = document.getElementById('divinity-parts-tabs');
    if (tabsContainer) {
      tabsContainer.innerHTML = DIVINITY_PARTS.map((p, idx) => {
        const isActive = (p.name === simState.activeDivPart || p.key === simState.activeDivPart);
        return `
          <button type="button" class="div-tab-btn ${isActive ? 'active' : ''}" data-part="${p.name}">
            [P${idx + 1}] ${p.name}
          </button>
        `;
      }).join('');

      tabsContainer.querySelectorAll('.div-tab-btn').forEach(btn => {
        btn.onclick = () => {
          simState.activeDivPart = btn.dataset.part;
          tabsContainer.querySelectorAll('.div-tab-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          renderDivinityModalBody();
        };
      });
    }

    renderDivinityModalBody();
    modal.style.display = 'flex';
  }

  function closeDivinityModal() {
    const modal = document.getElementById('divinity-modal');
    if (modal) modal.style.display = 'none';
    renderSimulatorUI();
  }

  function renderDivinityModalBody() {
    const body = document.getElementById('divinity-modal-body');
    if (!body) return;

    const cat = simState.staticData?.divinity_catalog || {};
    let activePartName = simState.activeDivPart || DIVINITY_PARTS[0].name;
    const partDef = DIVINITY_PARTS.find(p => p.name === activePartName || p.key === activePartName) || DIVINITY_PARTS[0];
    activePartName = partDef.name;
    simState.activeDivPart = activePartName;

    const partData = cat[activePartName] || {};
    const b = getActiveBuild();
    if (!b.divinity) b.divinity = {};
    if (!b.divinity[activePartName] && b.divinity[partDef.key]) {
      b.divinity[activePartName] = b.divinity[partDef.key];
      delete b.divinity[partDef.key];
    }
    if (!b.divinity[activePartName]) {
      b.divinity[activePartName] = {
        name: activePartName,
        part_index: partDef.index,
        level: 0,
        quality: 'gold',
        selected_substats: [],
        has_flash: false,
        flash_active: false
      };
    }
    const currentPart = b.divinity[activePartName];
    currentPart.name = activePartName;
    currentPart.part_index = partDef.index;
    if (currentPart.level === undefined) currentPart.level = 0;
    if (!currentPart.quality) currentPart.quality = 'gold';
    if (currentPart.has_flash === undefined) currentPart.has_flash = !!currentPart.flash_active;
    if (currentPart.flash_active === undefined) currentPart.flash_active = !!currentPart.has_flash;
    const selectedSubs = Array.isArray(currentPart.selected_substats) ? currentPart.selected_substats : [];
    currentPart.selected_substats = selectedSubs;

    const q = currentPart.quality || 'gold';
    const lvl = Number(currentPart.level) || 0;
    const isGoldLv7 = (q === 'gold' && lvl === 7);

    const statNames = partData.stat_names || [];
    const mainLevelsObj = (partData.main_levels || {})[String(lvl)] || {};
    const mainVal = mainLevelsObj[q] !== undefined ? mainLevelsObj[q] : (mainLevelsObj.gold || 0);
    const mainStatsFormatted = statNames.map(sn => {
      const isPct = !['STR', 'AGI', 'VIT', 'INT', 'DEX', 'LUK', 'Max HP', 'Max SP', 'P.ATK', 'M.ATK', 'P.DEF', 'M.DEF', 'P.DMG Bonus', 'M.DMG Bonus', 'P.DMG RED', 'M.DMG RED'].includes(sn);
      const valStr = isPct ? `+${(Math.round(mainVal * 10000) / 100).toFixed(2)}%` : `+${Math.round(mainVal).toLocaleString()}`;
      return `${sn} ${valStr}`;
    }).join(' / ');

    const prevScrolls = Array.from(body.querySelectorAll('.div-column-scroll')).map(el => el.scrollTop);

    const formatStatDisplay = (sn, valObj, qualityTier) => {
      if (valObj === undefined || valObj === null) return '0';
      const isPct = typeof valObj === 'object' ? valObj.is_pct : !['STR', 'AGI', 'VIT', 'INT', 'DEX', 'LUK', 'P.DMG Bonus', 'M.DMG Bonus'].includes(sn);
      const raw = typeof valObj === 'object' ? (valObj[qualityTier] !== undefined ? valObj[qualityTier] : valObj.gold || 0) : valObj;
      return isPct ? `+${(Math.round(raw * 10000) / 100).toFixed(2)}%` : `+${Math.round(raw).toLocaleString()}`;
    };

    const renderSubChip = (sn) => {
      const valObj = (partData.substats || {})[sn];
      if (valObj === undefined) return '';
      const isSel = selectedSubs.includes(sn);
      const displayVal = formatStatDisplay(sn, valObj, q);
      return `
        <div class="div-substat-chip ${isSel ? 'active' : ''}" data-part="${activePartName}" data-sub="${sn}">
          <span class="chip-name">${isSel ? '✓ ' : ''}${sn}</span>
          <span class="mono chip-val">${displayVal}</span>
        </div>
      `;
    };

    const offMainChips = DIV_COL_OFFENSE_MAIN.map(renderSubChip).filter(Boolean).join('');
    const offTacChips = DIV_COL_OFFENSE_TACTICAL.map(renderSubChip).filter(Boolean).join('');
    const defMainChips = DIV_COL_DEFENSE_MAIN.map(renderSubChip).filter(Boolean).join('');
    const defTacChips = DIV_COL_DEFENSE_TACTICAL.map(renderSubChip).filter(Boolean).join('');
    const attrChips = DIV_COL_ATTRIBUTES.map(renderSubChip).filter(Boolean).join('');
    const elemChips = DIV_COL_ELEMENTS.map(renderSubChip).filter(Boolean).join('');

    const knownStats = new Set([
      ...DIV_COL_OFFENSE_MAIN, ...DIV_COL_OFFENSE_TACTICAL,
      ...DIV_COL_DEFENSE_MAIN, ...DIV_COL_DEFENSE_TACTICAL,
      ...DIV_COL_ATTRIBUTES, ...DIV_COL_ELEMENTS
    ]);
    const extraStats = Object.keys(partData.substats || {}).filter(s => !knownStats.has(s));
    const extraChips = extraStats.map(renderSubChip).filter(Boolean).join('');

    const col1Count = [...DIV_COL_OFFENSE_MAIN, ...DIV_COL_OFFENSE_TACTICAL, ...extraStats].filter(s => selectedSubs.includes(s)).length;
    const col2Count = [...DIV_COL_DEFENSE_MAIN, ...DIV_COL_DEFENSE_TACTICAL].filter(s => selectedSubs.includes(s)).length;
    const col3Count = [...DIV_COL_ATTRIBUTES, ...DIV_COL_ELEMENTS].filter(s => selectedSubs.includes(s)).length;

    body.innerHTML = `
      <div style="background: var(--bg-canvas); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 12px; margin-bottom: 8px;">
        <div class="studio-row" style="justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div style="display: flex; gap: 8px; align-items: center;">
            <span class="font-bold" style="font-size: 11px;">Quality:</span>
            <select class="filter-select" id="modal-div-quality" style="font-size: 11px; height: 26px; padding: 2px 8px; width: 100px;">
              <option value="blue" ${q === 'blue' ? 'selected' : ''}>Blue</option>
              <option value="purple" ${q === 'purple' ? 'selected' : ''}>Purple</option>
              <option value="gold" ${q === 'gold' ? 'selected' : ''}>Gold</option>
            </select>

            <span class="font-bold" style="font-size: 11px; margin-left: 6px;">Level:</span>
            <select class="filter-select" id="modal-div-level" style="font-size: 11px; height: 26px; padding: 2px 6px; width: 80px;">
              ${[0, 1, 2, 3, 4, 5, 6, 7].map(l => `<option value="${l}" ${lvl === l ? 'selected' : ''}>Lv.${l}</option>`).join('')}
            </select>
          </div>

          <div style="display: flex; gap: 12px; align-items: center;">
            <div style="font-size: 11px; color: var(--text-muted);">
              Main Stat: <span class="mono font-bold" style="color: var(--accent, #38BDF8);">${mainStatsFormatted || 'None'}</span>
            </div>
            <div style="font-size: 10px; color: var(--text-muted);">
              Active: <span class="mono font-bold" style="color: var(--border-focus);">${selectedSubs.length}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="div-columns-container">
        <!-- Col 1: Offense -->
        <div class="div-column-card">
          <div class="div-col-header">
            <div class="div-col-title-wrap">
              <span class="div-col-indicator" style="background: var(--hud-dps, #F59E0B);"></span>
              <span class="div-col-title" style="color: var(--hud-dps, #F59E0B);">Offense & Combat</span>
            </div>
            <span class="div-col-badge ${col1Count > 0 ? 'active' : ''}">${col1Count} active</span>
          </div>
          <div class="div-column-scroll">
            <div class="div-subgroup-title">ATK & Penetration</div>
            <div class="div-subgroup-chips">${offMainChips || '<div class="text-muted" style="padding: 4px;">None</div>'}</div>
            <div class="div-subgroup-title" style="margin-top: 6px;">Crit, Speed & Special</div>
            <div class="div-subgroup-chips">${offTacChips || '<div class="text-muted" style="padding: 4px;">None</div>'}</div>
            ${extraChips ? `<div class="div-subgroup-title" style="margin-top: 6px;">Other</div><div class="div-subgroup-chips">${extraChips}</div>` : ''}
          </div>
        </div>

        <!-- Col 2: Defense -->
        <div class="div-column-card">
          <div class="div-col-header">
            <div class="div-col-title-wrap">
              <span class="div-col-indicator" style="background: var(--offset-pos, #10B981);"></span>
              <span class="div-col-title" style="color: var(--offset-pos, #10B981);">Defense & Survival</span>
            </div>
            <span class="div-col-badge ${col2Count > 0 ? 'active' : ''}">${col2Count} active</span>
          </div>
          <div class="div-column-scroll">
            <div class="div-subgroup-title">HP, DEF & Reduction</div>
            <div class="div-subgroup-chips">${defMainChips || '<div class="text-muted" style="padding: 4px;">None</div>'}</div>
            <div class="div-subgroup-title" style="margin-top: 6px;">Avoidance, Reflect & Regen</div>
            <div class="div-subgroup-chips">${defTacChips || '<div class="text-muted" style="padding: 4px;">None</div>'}</div>
          </div>
        </div>

        <!-- Col 3: Attributes & Elements -->
        <div class="div-column-card">
          <div class="div-col-header">
            <div class="div-col-title-wrap">
              <span class="div-col-indicator" style="background: var(--accent, #38BDF8);"></span>
              <span class="div-col-title" style="color: var(--accent, #38BDF8);">Attr & Elements</span>
            </div>
            <span class="div-col-badge ${col3Count > 0 ? 'active' : ''}">${col3Count} active</span>
          </div>
          <div class="div-column-scroll">
            <div class="div-subgroup-title">Base Attributes (12)</div>
            <div class="div-subgroup-chips">${attrChips || '<div class="text-muted" style="padding: 4px;">None</div>'}</div>
            <div class="div-subgroup-title" style="margin-top: 6px;">Element Enhance (10)</div>
            <div class="div-subgroup-chips">${elemChips || '<div class="text-muted" style="padding: 4px;">None</div>'}</div>
          </div>
        </div>
      </div>
    `;

    body.querySelectorAll('.div-column-scroll').forEach((el, idx) => {
      if (prevScrolls[idx] !== undefined) el.scrollTop = prevScrolls[idx];
    });

    const qSel = document.getElementById('modal-div-quality');
    const lvlSel = document.getElementById('modal-div-level');

    if (qSel) {
      qSel.onchange = (e) => {
        currentPart.quality = e.target.value;
        renderDivinityModalBody();
        markDirty('divinity');
      };
    }

    if (lvlSel) {
      lvlSel.onchange = (e) => {
        currentPart.level = Number(e.target.value) || 0;
        renderDivinityModalBody();
        markDirty('divinity');
      };
    }

    body.querySelectorAll('.div-substat-chip').forEach(chip => {
      chip.onclick = () => {
        const sub = chip.dataset.sub;
        const idx = selectedSubs.indexOf(sub);
        if (idx >= 0) {
          selectedSubs.splice(idx, 1);
        } else {
          selectedSubs.push(sub);
        }
        currentPart.selected_substats = selectedSubs;
        renderDivinityModalBody();
        markDirty('divinity');
      };
    });
  }

  const COMPANIONS = ['Spark', 'Wraith', 'Cloudsong', 'Bubbles'];

  const COMPANION_OFFENSIVE_STATS = [
    'P.ATK', 'P.ATK%', 'M.ATK', 'M.ATK%', 'Final P.PEN', 'Final M.PEN',
    'Final P.DMG Bonus', 'Final M.DMG Bonus', 'Final Crit', 'Crit DMG Bonus',
    'Final ASPD', 'Final Haste', 'Bonus DMG to Size', 'Element Enhance'
  ];

  const COMPANION_DEFENSIVE_STATS = [
    'Max HP', 'Max HP%', 'Final P.DEF', 'Final M.DEF', 'Final P.DMG RED',
    'Final M.DMG RED', 'Final Anti-Crit', 'Crit DMG RED', 'Final Flee',
    'HP Regen per 5s'
  ];

  function openCompanionModal() {
    const modal = document.getElementById('companion-modal');
    if (!modal) return;

    if (!simState.activeCompanion) simState.activeCompanion = COMPANIONS[0];

    const tabsNav = document.getElementById('companion-tabs');
    if (tabsNav) {
      tabsNav.querySelectorAll('.companion-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.companion === simState.activeCompanion);
        btn.onclick = () => {
          simState.activeCompanion = btn.dataset.companion;
          tabsNav.querySelectorAll('.companion-tab-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          renderCompanionModalBody();
        };
      });
    }

    renderCompanionModalBody();
    modal.style.display = 'flex';
  }

  function closeCompanionModal() {
    const modal = document.getElementById('companion-modal');
    if (modal) modal.style.display = 'none';
    renderSimulatorUI();
  }

  function renderCompanionModalBody() {
    const body = document.getElementById('companion-modal-body');
    if (!body) return;

    const b = getActiveBuild();
    if (!b.companion) b.companion = {};
    if (!b.companion.companions) b.companion.companions = {};

    COMPANIONS.forEach(cName => {
      if (!b.companion.companions[cName]) {
        b.companion.companions[cName] = {
          offense: [
            { stat: 'P.ATK', value: 0 },
            { stat: 'P.ATK%', value: 0 },
            { stat: 'Final P.DMG Bonus', value: 0 }
          ],
          defense: [
            { stat: 'Max HP', value: 0 },
            { stat: 'Final P.DEF', value: 0 },
            { stat: 'Final P.DMG RED', value: 0 }
          ]
        };
      }
    });

    const activeCompanion = simState.activeCompanion || COMPANIONS[0];
    const compData = b.companion.companions[activeCompanion];

    let offLinesHtml = '';
    compData.offense.forEach((line, idx) => {
      offLinesHtml += `
        <div class="companion-line-row">
          <span class="companion-line-label">#${idx + 1}</span>
          <select class="filter-select comp-off-stat" data-idx="${idx}" style="flex: 1; font-size: 11px; height: 26px;">
            ${COMPANION_OFFENSIVE_STATS.map(st => `<option value="${st}" ${line.stat === st ? 'selected' : ''}>${st}</option>`).join('')}
          </select>
          <input type="number" class="filter-input-num comp-off-val" data-idx="${idx}" value="${line.value || 0}" step="any" style="width: 80px; height: 26px; text-align: right; font-weight: 700;">
        </div>
      `;
    });

    let defLinesHtml = '';
    compData.defense.forEach((line, idx) => {
      defLinesHtml += `
        <div class="companion-line-row">
          <span class="companion-line-label">#${idx + 1}</span>
          <select class="filter-select comp-def-stat" data-idx="${idx}" style="flex: 1; font-size: 11px; height: 26px;">
            ${COMPANION_DEFENSIVE_STATS.map(st => `<option value="${st}" ${line.stat === st ? 'selected' : ''}>${st}</option>`).join('')}
          </select>
          <input type="number" class="filter-input-num comp-def-val" data-idx="${idx}" value="${line.value || 0}" step="any" style="width: 80px; height: 26px; text-align: right; font-weight: 700;">
        </div>
      `;
    });

    body.innerHTML = `
      <div style="font-size: 10px; color: var(--text-muted); margin-bottom: 8px;">
        Direct Stat Inscriptions for <strong>${activeCompanion}</strong>:
      </div>
      <div class="companion-modal-grid">
        <div class="companion-col-offense">
          <div class="col-header">
            <span>⚔ Offense (3 Lines)</span>
            <span style="font-size: 9px; opacity: 0.8;">Amber/Crimson</span>
          </div>
          ${offLinesHtml}
        </div>
        <div class="companion-col-defense">
          <div class="col-header">
            <span>🛡 Defense (3 Lines)</span>
            <span style="font-size: 9px; opacity: 0.8;">Cyan/Emerald</span>
          </div>
          ${defLinesHtml}
        </div>
      </div>
    `;

    const syncCompanionTally = () => {
      COMPANION_OFFENSIVE_STATS.forEach(st => { b.companion[st] = 0; });
      COMPANION_DEFENSIVE_STATS.forEach(st => { b.companion[st] = 0; });

      Object.values(b.companion.companions).forEach(cObj => {
        (cObj.offense || []).forEach(l => {
          if (l.stat && l.value) b.companion[l.stat] = (b.companion[l.stat] || 0) + Number(l.value);
        });
        (cObj.defense || []).forEach(l => {
          if (l.stat && l.value) b.companion[l.stat] = (b.companion[l.stat] || 0) + Number(l.value);
        });
      });

      b.companion.patk_pct = b.companion['P.ATK%'] || 0;
      b.companion.crit_dmg = b.companion['Crit DMG Bonus'] || 0;
      b.companion.final_pdmg_bonus = b.companion['Final P.DMG Bonus'] || 0;
      b.companion.fire_enhance = b.companion['Element Enhance'] || 0;

      markDirty('companion');
    };

    body.querySelectorAll('.comp-off-stat').forEach(sel => {
      sel.onchange = (e) => {
        const idx = Number(sel.dataset.idx);
        compData.offense[idx].stat = e.target.value;
        syncCompanionTally();
      };
    });

    body.querySelectorAll('.comp-off-val').forEach(inp => {
      inp.oninput = (e) => {
        const idx = Number(inp.dataset.idx);
        compData.offense[idx].value = Number(e.target.value) || 0;
        syncCompanionTally();
      };
    });

    body.querySelectorAll('.comp-def-stat').forEach(sel => {
      sel.onchange = (e) => {
        const idx = Number(sel.dataset.idx);
        compData.defense[idx].stat = e.target.value;
        syncCompanionTally();
      };
    });

    body.querySelectorAll('.comp-def-val').forEach(inp => {
      inp.oninput = (e) => {
        const idx = Number(inp.dataset.idx);
        compData.defense[idx].value = Number(e.target.value) || 0;
        syncCompanionTally();
      };
    });
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
        markDirty();
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
          markDirty();
        };
      });

      modal.querySelectorAll('.modal-pet-stat-input').forEach(inp => {
        inp.oninput = (e) => {
          const st = inp.dataset.stat;
          if (!p.custom_stats) p.custom_stats = {};
          p.custom_stats[st] = Number(e.target.value) || 0;
          markDirty();
        };
      });
    };

    renderContent();
  }

  function recalculateAndRender() {
    markDirty('manual');
  }

  const CALIBRATOR_GROUPS = [
    {
      name: 'Base Offense',
      stats: [
        { key: 'P.ATK', label: 'Physical Attack (P.ATK)', isPct: false },
        { key: 'P.ATK%', label: 'Physical Attack % (P.ATK%)', isPct: true },
        { key: 'M.ATK', label: 'Magical Attack (M.ATK)', isPct: false },
        { key: 'M.ATK%', label: 'Magical Attack % (M.ATK%)', isPct: true },
        { key: 'ASPD', label: 'Attack Speed (ASPD)', isPct: false },
        { key: 'Final ASPD', label: 'Final ASPD', isPct: true },
        { key: 'Final Haste', label: 'Final Haste', isPct: true }
      ]
    },
    {
      name: 'Penetration & Defense Ignore',
      stats: [
        { key: 'P.PEN', label: 'Physical Penetration (P.PEN)', isPct: true },
        { key: 'Final P.PEN', label: 'Final Physical Penetration', isPct: true },
        { key: 'M.PEN', label: 'Magical Penetration (M.PEN)', isPct: true },
        { key: 'Final M.PEN', label: 'Final Magical Penetration', isPct: true },
        { key: 'P.Ignore DEF', label: 'Physical Ignore DEF', isPct: true },
        { key: 'M.Ignore DEF', label: 'Magical Ignore DEF', isPct: true }
      ]
    },
    {
      name: 'Critical',
      stats: [
        { key: 'Crit', label: 'Critical (Crit)', isPct: false },
        { key: 'Final Crit', label: 'Final Critical', isPct: true },
        { key: 'Crit DMG Bonus', label: 'Critical DMG Bonus', isPct: true }
      ]
    },
    {
      name: 'Special Multipliers',
      stats: [
        { key: 'Final P.DMG Bonus', label: 'Final P.DMG Bonus', isPct: true },
        { key: 'Final M.DMG Bonus', label: 'Final M.DMG Bonus', isPct: true },
        { key: 'Bonus DMG to Size', label: 'Bonus DMG to Size', isPct: true },
        { key: 'Bonus DMG to Target Quality', label: 'Bonus DMG to Quality (MVP/Mini)', isPct: true },
        { key: 'Fire Enhance', label: 'Element Enhance (Fire)', isPct: true }
      ]
    }
  ];

  function formatCalibratorVal(val, isPct) {
    const num = Number(val) || 0;
    if (isPct) {
      return (num * 100).toFixed(1) + '%';
    }
    return Math.round(num).toLocaleString();
  }

  function renderStatCalibrator() {
    const tbody = document.getElementById('calibrator-table-body');
    if (!tbody) return;

    const build = getActiveBuild();
    if (!build) return;
    if (!build.stat_injection) build.stat_injection = {};

    const tallied = simState.lastSimRes?.talliedStats || {};

    let html = '';
    CALIBRATOR_GROUPS.forEach(group => {
      html += `
        <tr class="calibrator-group-header">
          <td colspan="4">${group.name}</td>
        </tr>
      `;
      group.stats.forEach(st => {
        const offset = build.stat_injection[st.key] !== undefined ? Number(build.stat_injection[st.key]) : 0;
        const effective = tallied[st.key] !== undefined ? Number(tallied[st.key]) : offset;
        const base = effective - offset;

        let inputClass = 'calibrator-offset-input offset-zero';
        let displayOffset = '';
        if (offset > 0) {
          inputClass = 'calibrator-offset-input offset-pos';
          displayOffset = st.isPct ? `+${(offset * 100).toFixed(1)}%` : `+${offset}`;
        } else if (offset < 0) {
          inputClass = 'calibrator-offset-input offset-neg';
          displayOffset = st.isPct ? `${(offset * 100).toFixed(1)}%` : `${offset}`;
        } else {
          displayOffset = '0';
        }

        html += `
          <tr data-stat="${st.key}">
            <td class="calibrator-stat-name">${st.label}</td>
            <td class="calibrator-base-val">${formatCalibratorVal(base, st.isPct)}</td>
            <td style="text-align: center;">
              <input type="text"
                class="${inputClass}"
                data-stat="${st.key}"
                data-ispct="${st.isPct ? '1' : '0'}"
                value="${displayOffset}"
                title="Type +/- delta offset. Supports raw or percentage e.g. +1000 or +10%">
            </td>
            <td class="calibrator-effective-val">${formatCalibratorVal(effective, st.isPct)}</td>
          </tr>
        `;
      });
    });

    tbody.innerHTML = html;

    tbody.querySelectorAll('.calibrator-offset-input').forEach(input => {
      input.addEventListener('focus', () => {
        if (input.value === '0') input.value = '';
      });

      input.addEventListener('blur', () => {
        if (!input.value.trim()) {
          input.value = '0';
          input.className = 'calibrator-offset-input offset-zero';
        }
      });

      input.addEventListener('change', (e) => {
        handleCalibratorInputChange(e.target);
      });

      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.target.blur();
        }
      });
    });
  }

  function handleCalibratorInputChange(input) {
    const statKey = input.dataset.stat;
    const isPct = input.dataset.ispct === '1';
    const rawStr = (input.value || '').trim();

    const build = getActiveBuild();
    if (!build) return;
    if (!build.stat_injection) build.stat_injection = {};

    let num = 0;
    if (rawStr) {
      const hasPctSign = rawStr.endsWith('%');
      const cleanVal = parseFloat(rawStr.replace(/[^0-9.-]/g, ''));
      if (!isNaN(cleanVal)) {
        if (isPct) {
          if (hasPctSign || Math.abs(cleanVal) >= 1) {
            num = cleanVal / 100;
          } else {
            num = cleanVal;
          }
        } else {
          num = cleanVal;
        }
      }
    }

    if (num !== 0) {
      build.stat_injection[statKey] = num;
      if (num > 0) {
        input.className = 'calibrator-offset-input offset-pos';
        input.value = isPct ? `+${(num * 100).toFixed(1)}%` : `+${num}`;
      } else {
        input.className = 'calibrator-offset-input offset-neg';
        input.value = isPct ? `${(num * 100).toFixed(1)}%` : `${num}`;
      }
    } else {
      delete build.stat_injection[statKey];
      input.className = 'calibrator-offset-input offset-zero';
      input.value = '0';
    }

    markDirty('stat_offsets');
  }

  function updateBentoSummaryTiles() {
    const build = getActiveBuild();
    if (!build) return;

    // 1. Base Stats
    const s = build.stats || {};
    const baseSummaryEl = document.getElementById('tile-base-stats-summary');
    if (baseSummaryEl) {
      baseSummaryEl.textContent = `STR ${s.str || 0} · AGI ${s.agi || 0} · VIT ${s.vit || 0} · INT ${s.int || 0} · DEX ${s.dex || 0} · LUK ${s.luk || 0}`;
    }

    // 2. Divinity
    const divCount = Object.keys(build.divinity || {}).length;
    const divSummaryEl = document.getElementById('tile-divinity-summary');
    const divBadgeEl = document.getElementById('tile-divinity-badge');
    if (divSummaryEl) {
      const flashActive = build.buffs?.spear_flash ? ' · Flash Active' : '';
      divSummaryEl.textContent = `${divCount || 8} Parts Configured${flashActive}`;
    }
    if (divBadgeEl) {
      divBadgeEl.textContent = `${divCount || 8}/8 GOLD`;
    }

    // 3. Companions
    const compSummaryEl = document.getElementById('tile-companions-summary');
    if (compSummaryEl) {
      compSummaryEl.textContent = 'Spark, Wraith, Cloudsong, Bubbles · 24 Stat Lines';
    }

    // 4. Buffs & Titles
    const buffs = build.buffs || {};
    const activeBuffs = [];
    if (buffs.elemental_converter && buffs.elemental_converter !== 'Neutral') activeBuffs.push(buffs.elemental_converter);
    if (buffs.spear_flash) activeBuffs.push('Flash');
    if (buffs.concentration) activeBuffs.push('Concentration');
    if (buffs.spooky_lamp) activeBuffs.push('Lamp');
    if (buffs.pet_active) activeBuffs.push('Pet');

    const shinePts = build.progression?.shine_points || 0;
    const buffsSummaryEl = document.getElementById('tile-buffs-summary');
    const buffsBadgeEl = document.getElementById('tile-buffs-badge');
    if (buffsSummaryEl) {
      const buffNames = activeBuffs.length > 0 ? activeBuffs.join(', ') : 'None';
      buffsSummaryEl.textContent = `${buffNames} · Shine Pts: ${shinePts}`;
    }
    if (buffsBadgeEl) {
      buffsBadgeEl.textContent = `${activeBuffs.length} BUFFS ACTIVE`;
    }
  }

  function openBaseStatsModal() {
    const modal = document.getElementById('modal-base-stats');
    if (!modal) return;
    const build = getActiveBuild();
    const stats = build?.stats || {};
    ['str', 'agi', 'vit', 'int', 'dex', 'luk'].forEach(s => {
      const inp = document.getElementById(`modal-stat-${s}`);
      if (inp) inp.value = stats[s] || 0;
    });
    modal.style.display = 'flex';
  }

  function closeBaseStatsModal() {
    const modal = document.getElementById('modal-base-stats');
    if (modal) modal.style.display = 'none';
    renderSimulatorUI();
  }

  function openBuffsModal() {
    const modal = document.getElementById('modal-buffs');
    if (!modal) return;
    const build = getActiveBuild();
    const buffs = build?.buffs || {};
    const setChecked = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.checked = !!val;
    };
    setChecked('modal-buff-converter', buffs.elemental_converter === 'Fire');
    setChecked('modal-buff-spear-flash', buffs.spear_flash);
    setChecked('modal-buff-concentration', buffs.concentration);
    setChecked('modal-buff-spooky-lamp', buffs.spooky_lamp);
    setChecked('modal-buff-pet', buffs.pet_active);

    const shineSel = document.getElementById('modal-shine-points');
    if (shineSel) shineSel.value = String(build?.progression?.shine_points || 0);

    modal.style.display = 'flex';
  }

  function closeBuffsModal() {
    const modal = document.getElementById('modal-buffs');
    if (modal) modal.style.display = 'none';
    renderSimulatorUI();
  }

  function bindSimulatorEvents() {
    const btnCommit = document.getElementById('sim-btn-commit');
    if (btnCommit) {
      btnCommit.addEventListener('click', () => {
        commitBuild();
      });
    }
    // 2-Page Gear Tabs
    const tabCombat = document.getElementById('tab-gear-combat');
    const tabCostumes = document.getElementById('tab-gear-costumes');
    if (tabCombat) {
      tabCombat.addEventListener('click', () => {
        switchPaperDollTab('combat');
      });
    }
    if (tabCostumes) {
      tabCostumes.addEventListener('click', () => {
        switchPaperDollTab('costumes');
      });
    }

    // Modal Studio Openers & Closers
    const btnOpenPetModal = document.getElementById('sim-btn-open-pet-modal');
    if (btnOpenPetModal) {
      btnOpenPetModal.addEventListener('click', () => {
        openPetSanctuaryModal();
      });
    }

    const btnOpenDivModal = document.getElementById('sim-btn-open-divinity-modal');
    if (btnOpenDivModal) {
      btnOpenDivModal.addEventListener('click', () => {
        openDivinityModal();
      });
    }

    const btnOpenCompModal = document.getElementById('sim-btn-open-companion-modal');
    if (btnOpenCompModal) {
      btnOpenCompModal.addEventListener('click', () => {
        openCompanionModal();
      });
    }

    const btnCloseDivModal = document.getElementById('btn-close-divinity-modal');
    if (btnCloseDivModal) {
      btnCloseDivModal.addEventListener('click', () => {
        closeDivinityModal();
      });
    }

    const btnCloseCompModal = document.getElementById('btn-close-companion-modal');
    if (btnCloseCompModal) {
      btnCloseCompModal.addEventListener('click', () => {
        closeCompanionModal();
      });
    }

    const divModal = document.getElementById('divinity-modal');
    if (divModal) {
      divModal.addEventListener('click', (e) => {
        if (e.target === divModal) closeDivinityModal();
      });
    }

    const compModal = document.getElementById('companion-modal');
    if (compModal) {
      compModal.addEventListener('click', (e) => {
        if (e.target === compModal) closeCompanionModal();
      });
    }

    // Bento 2 Tiles -> Modal triggers
    const tileBase = document.getElementById('tile-base-stats');
    if (tileBase) tileBase.addEventListener('click', openBaseStatsModal);

    const tileDiv = document.getElementById('tile-divinity');
    if (tileDiv) tileDiv.addEventListener('click', openDivinityModal);

    const tileComp = document.getElementById('tile-companions');
    if (tileComp) tileComp.addEventListener('click', openCompanionModal);

    const tileBuffs = document.getElementById('tile-buffs');
    if (tileBuffs) tileBuffs.addEventListener('click', openBuffsModal);

    // Modal Close buttons
    const btnCloseBase = document.getElementById('btn-close-base-stats-modal');
    if (btnCloseBase) btnCloseBase.addEventListener('click', closeBaseStatsModal);

    const btnCloseBuffs = document.getElementById('btn-close-buffs-modal');
    if (btnCloseBuffs) btnCloseBuffs.addEventListener('click', closeBuffsModal);

    // Modal Backdrop clicks
    const baseModal = document.getElementById('modal-base-stats');
    if (baseModal) {
      baseModal.addEventListener('click', (e) => {
        if (e.target === baseModal) closeBaseStatsModal();
      });
    }

    const buffsModal = document.getElementById('modal-buffs');
    if (buffsModal) {
      buffsModal.addEventListener('click', (e) => {
        if (e.target === buffsModal) closeBuffsModal();
      });
    }

    // Modal input bindings: Base Stats
    ['str', 'agi', 'vit', 'int', 'dex', 'luk'].forEach(s => {
      const el = document.getElementById(`modal-stat-${s}`);
      if (el) {
        el.addEventListener('input', (e) => {
          const b = getActiveBuild();
          if (!b.stats) b.stats = {};
          b.stats[s] = Number(e.target.value) || 0;
          const simInp = document.getElementById(`sim-stat-${s}`);
          if (simInp) simInp.value = b.stats[s];
          updateBentoSummaryTiles();
          markDirty();
        });
      }
    });

    // Modal input bindings: Buffs
    const bindModalBuff = (id, simId, key, valOn, valOff) => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('change', (e) => {
          const b = getActiveBuild();
          if (!b.buffs) b.buffs = {};
          b.buffs[key] = e.target.checked ? valOn : valOff;
          const simEl = document.getElementById(simId);
          if (simEl) simEl.checked = e.target.checked;
          updateBentoSummaryTiles();
          markDirty();
        });
      }
    };
    bindModalBuff('modal-buff-converter', 'sim-buff-converter', 'elemental_converter', 'Fire', 'Neutral');
    bindModalBuff('modal-buff-spear-flash', 'sim-buff-spear-flash', 'spear_flash', true, false);
    bindModalBuff('modal-buff-concentration', 'sim-buff-concentration', 'concentration', true, false);
    bindModalBuff('modal-buff-spooky-lamp', 'sim-buff-spooky-lamp', 'spooky_lamp', true, false);
    bindModalBuff('modal-buff-pet', 'sim-buff-pet', 'pet_active', true, false);

    const modalShineSel = document.getElementById('modal-shine-points');
    if (modalShineSel) {
      modalShineSel.addEventListener('change', (e) => {
        const b = getActiveBuild();
        if (!b.progression) b.progression = {};
        b.progression.shine_points = Number(e.target.value) || 0;
        const simShine = document.getElementById('sim-shine-points');
        if (simShine) simShine.value = String(b.progression.shine_points);
        updateBentoSummaryTiles();
        markDirty();
      });
    }

    // Calibrator Reset Button
    const btnResetOffsets = document.getElementById('btn-calibrator-reset');
    if (btnResetOffsets) {
      btnResetOffsets.addEventListener('click', () => {
        const b = getActiveBuild();
        if (b) {
          b.stat_injection = {};
          renderStatCalibrator();
          markDirty('stat_offsets');
        }
      });
    }

    // Accordion Header Toggle (Directly opens Divinity Modal on click per user requirement)
    document.querySelectorAll('.sim-accordion-header').forEach(header => {
      header.addEventListener('click', () => {
        const targetId = header.dataset.target;
        if (targetId === 'acc-divinity' || header.id === 'sim-header-divinity') {
          openDivinityModal();
          return;
        }
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
        markDirty();
      });
    }

    // PVP Cockpit inputs binding
    [
      'sim-pvp-pdef', 'sim-pvp-fpdef', 'sim-pvp-fpred', 'sim-pvp-fred',
      'sim-pvp-pred', 'sim-pvp-pvpfpred', 'sim-pvp-pvppred', 'sim-pvp-attrres'
    ].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', () => markDirty());
    });

    // Pet Change
    const petSel = document.getElementById('sim-pet-select');
    if (petSel) {
      petSel.addEventListener('change', (e) => {
        const b = getActiveBuild();
        if (!b.pet) b.pet = {};
        b.pet.name = e.target.value;
        markDirty();
      });
    }

    const petStarsSel = document.getElementById('sim-pet-stars');
    if (petStarsSel) {
      petStarsSel.addEventListener('change', (e) => {
        const b = getActiveBuild();
        if (!b.pet) b.pet = {};
        b.pet.stars = Number(e.target.value) || 6;
        markDirty();
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
          markDirty();
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
        markDirty();
      });
    }
    ['sim-debuff-fdef', 'sim-debuff-fpdmg'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('input', () => markDirty());
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
          markDirty();
        } else if (e.target.classList.contains('sim-div-quality-select')) {
          const dName = e.target.dataset.name;
          const q = e.target.value;
          if (!b.divinity[dName]) b.divinity[dName] = { name: dName, level: 0, quality: q, selected_substats: [] };
          else b.divinity[dName].quality = q;
          markDirty();
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
          markDirty();
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
          markDirty();
        }
      });
    }

    const seedBtn = document.getElementById('sim-btn-seed-baseline');
    if (seedBtn) {
      seedBtn.addEventListener('click', () => {
        if (simState.activeAdapter) {
          const baseline = simState.activeAdapter.getDefaultBaseline();
          if (simState.activeSlot === 'A') simState.buildA = JSON.parse(JSON.stringify(baseline));
          else simState.buildB = JSON.parse(JSON.stringify(baseline));
          renderSimulatorUI();
          markDirty();
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
          markDirty();
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
          markDirty();
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
          markDirty();
        });
      }
    });

    const shineSel = document.getElementById('sim-shine-points');
    if (shineSel) {
      shineSel.addEventListener('change', (e) => {
        const b = getActiveBuild();
        if (!b.progression) b.progression = {};
        b.progression.shine_points = Number(e.target.value) || 0;
        markDirty();
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
          markDirty();
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
        markDirty();
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
        markDirty();
      });
    }

    if (btnDiff) {
      btnDiff.addEventListener('click', () => {
        simState.compareMode = !simState.compareMode;
        btnDiff.classList.toggle('active', simState.compareMode);
        if (diffPanel) diffPanel.style.display = simState.compareMode ? 'block' : 'none';
        markDirty();
      });
    }

    // Share URL
    const btnShare = document.getElementById('sim-btn-copy-url');
    if (btnShare) {
      btnShare.addEventListener('click', () => {
        const uuid = getOrCreateProfileId();
        const shareUrl = `${window.location.origin}${window.location.pathname}?profile=${uuid}`;
        navigator.clipboard?.writeText(shareUrl);
        alert('Profile URL copied to clipboard: ' + shareUrl);
      });
    }

    // Reset Defaults
    const btnReset = document.getElementById('sim-btn-reset-defaults');
    if (btnReset) {
      btnReset.addEventListener('click', () => {
        if (confirm('Reset to default Dragon Knight build?')) {
          const baseline = simState.activeAdapter.getDefaultBaseline();
          simState.buildA = JSON.parse(JSON.stringify(baseline));
          simState.buildB = JSON.parse(JSON.stringify(baseline));
          markDirty();
        }
      });
    }

    // Equipment Drawer Close & Backdrop
    const btnCloseDrawer = document.getElementById('btn-close-equip-drawer');
    if (btnCloseDrawer) {
      btnCloseDrawer.addEventListener('click', () => closeEquipDrawer());
    }
    const drawerBackdrop = document.getElementById('sim-drawer-backdrop');
    if (drawerBackdrop) {
      drawerBackdrop.addEventListener('click', () => closeEquipDrawer());
    }

    // Base & Job Level Inputs
    const baseLvEl = document.getElementById('sim-base-level');
    if (baseLvEl) {
      baseLvEl.addEventListener('input', (e) => {
        const b = getActiveBuild();
        b.base_level = Number(e.target.value) || 87;
        markDirty();
      });
    }
    const jobLvEl = document.getElementById('sim-job-level');
    if (jobLvEl) {
      jobLvEl.addEventListener('input', (e) => {
        const b = getActiveBuild();
        b.job_level = Number(e.target.value) || 17;
        markDirty();
      });
    }

    // Close modal & drawer on Escape key
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeEquipDrawer();
        closeDivinityModal();
        closeCompanionModal();
        closeBaseStatsModal();
        closeBuffsModal();
        const modal = document.getElementById('sim-active-modal');
        if (modal) {
          modal.remove();
          renderSimulatorUI();
          markDirty();
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
    markDirty();
  }

  global.RoxSimulatorUI = {
    init: initSimulatorStudio,
    setTargetFromWiki,
    recalculate: () => markDirty('external'),
    commit: commitBuild
  };
})(typeof window !== 'undefined' ? window : globalThis);
