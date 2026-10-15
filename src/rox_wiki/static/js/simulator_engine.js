(function(global) {
  'use strict';

  function calculatePrimaryConversions(baseStats, jobStats) {
    const totalStr = (baseStats.str || 0) + (jobStats.str || 0);
    const totalAgi = (baseStats.agi || 0) + (jobStats.agi || 0);
    const totalVit = (baseStats.vit || 0) + (jobStats.vit || 0);
    const totalInt = (baseStats.int || 0) + (jobStats.int || 0);
    const totalDex = (baseStats.dex || 0) + (jobStats.dex || 0);
    const totalLuk = (baseStats.luk || 0) + (jobStats.luk || 0);

    let strPatk = 0;
    if (totalStr < 3000) {
      const flStr = Math.floor(totalStr / 100) * 100;
      strPatk = Math.floor(totalStr * 4 + Math.pow(flStr, 2) * 0.002 + (totalStr - flStr) * (flStr / 100 * 0.2));
    } else {
      strPatk = totalStr * 10;
    }

    let lukPatk = 0;
    if (totalLuk < 3000) {
      const flLuk = Math.floor(totalLuk / 100) * 100;
      lukPatk = Math.floor(totalLuk * 0.5 + Math.pow(flLuk, 2) * 0.000025 + (totalLuk - flLuk) * (flLuk / 100 * 0.025));
    } else {
      lukPatk = totalLuk * 1.25;
    }

    let dexPatk = 0;
    if (totalDex < 3000) {
      const flDex = Math.floor(totalDex / 100) * 100;
      dexPatk = Math.floor(totalDex * 0.2 + Math.pow(flDex, 2) * 0.00001 + (totalDex - flDex) * (flDex / 100 * 0.01));
    } else {
      dexPatk = totalDex * 0.5;
    }

    return {
      totalStats: { str: totalStr, agi: totalAgi, vit: totalVit, int: totalInt, dex: totalDex, luk: totalLuk },
      convertedPatk: strPatk + lukPatk + dexPatk
    };
  }

  function calculateAwakeningBonuses(loadout, staticData) {
    const tiers = staticData.awakening_tiers || {};
    let refBonus = 0;
    let upgBonus = 0;
    let encBonus = 0;

    const slotKeys = Object.keys(loadout || {});
    let refLevels = [];
    let upgWeapon = 0;
    let upgArmor = [];
    let upgAcc = [];
    let encTotals = [];

    slotKeys.forEach(k => {
      const item = loadout[k];
      if (!item) return;
      const isCostume = k.startsWith('costume_');
      if (!isCostume && item.refine !== undefined) refLevels.push(Number(item.refine) || 0);
      if (!isCostume && item.upgrade !== undefined) {
        const u = Number(item.upgrade) || 0;
        if (k === 'weapon') upgWeapon = u;
        else if (['clothes', 'cloak', 'shoes'].includes(k)) upgArmor.push(u);
        else if (['accessory_1', 'accessory_2', 'talisman'].includes(k)) upgAcc.push(u);
      }
      if (Array.isArray(item.enchant_lines) && item.enchant_lines.length > 0) {
        const sumLv = item.enchant_lines.reduce((acc, l) => acc + (Number(l.level) || 0), 0);
        encTotals.push(sumLv);
      } else if (item.enchant_lv !== undefined) {
        encTotals.push((Number(item.enchant_lv) || 0) * 3);
      }
    });

    if (tiers.refine) {
      for (let i = tiers.refine.length - 1; i >= 0; i--) {
        const t = tiers.refine[i];
        const match = refLevels.filter(lvl => lvl >= t.req_level).length;
        if (match >= t.req_count) {
          refBonus = t.bonus;
          break;
        }
      }
    }

    if (tiers.upgrade) {
      for (let i = tiers.upgrade.length - 1; i >= 0; i--) {
        const t = tiers.upgrade[i];
        let count = 0;
        if (upgWeapon >= t.req_weapon) count++;
        count += upgArmor.filter(u => u >= t.req_armor).length;
        count += upgAcc.filter(u => u >= t.req_acc).length;
        if (count >= t.req_count) {
          upgBonus = t.bonus;
          break;
        }
      }
    }

    if (tiers.enchant) {
      for (let i = tiers.enchant.length - 1; i >= 0; i--) {
        const t = tiers.enchant[i];
        const match = encTotals.filter(e => e >= t.req_total).length;
        if (match >= t.req_count) {
          encBonus = t.bonus;
          break;
        }
      }
    }

    return { refineAwakening: refBonus, upgradeAwakening: upgBonus, enchantAwakening: encBonus };
  }

  function tallyPlayerStats(build, staticData) {
    const stats = {};
    const addStat = (k, v) => {
      if (!k || v === undefined || v === null || isNaN(v)) return;
      stats[k] = (stats[k] || 0) + Number(v);
    };

    const conv = calculatePrimaryConversions(build.stats || {}, build.job_stats || {});
    addStat('STR', conv.totalStats.str);
    addStat('AGI', conv.totalStats.agi);
    addStat('VIT', conv.totalStats.vit);
    addStat('INT', conv.totalStats.int);
    addStat('DEX', conv.totalStats.dex);
    addStat('LUK', conv.totalStats.luk);
    addStat('P.ATK', conv.convertedPatk);

    const ba = build.battle_achievement || {};
    addStat('STR', ba.str);
    addStat('VIT', ba.vit);
    addStat('Final P.DMG Bonus', ba.final_pdmg_bonus);
    addStat('Fire Enhance', ba.fire_enhance);
    addStat('Max HP%', ba.max_hp_pct);
    addStat('Final P.DMG RED', ba.final_pdmg_red);

    const prog = build.progression || {};
    if (prog.title) {
      addStat('P.ATK', prog.title.patk);
      addStat('P.PEN', prog.title.ppen);
      addStat('Final DMG Bonus', prog.title.fdmg);
      addStat('Crit', prog.title.crit);
    }
    if (prog.shine_points) {
      const spPts = Number(prog.shine_points) || 0;
      addStat('P.ATK', Math.floor(spPts * 1.5));
      addStat('Max HP', Math.floor(spPts * 10));
    }

    const awk = calculateAwakeningBonuses(build.loadout || {}, staticData);

    const loadout = build.loadout || {};
    Object.keys(loadout).forEach(slotKey => {
      const item = loadout[slotKey];
      if (!item) return;

      const isCostume = slotKey.startsWith('costume_');
      const slotCatalog = staticData.equip_base?.[item.type] || staticData.equip_base?.[slotKey] || [];
      const baseItem = slotCatalog.find(b => b.name === item.name);
      if (baseItem && baseItem.stats) {
        Object.keys(baseItem.stats).forEach(sn => addStat(sn, baseItem.stats[sn]));
      }

      if (!isCostume && baseItem && baseItem.up_id && item.upgrade) {
        const upTable = staticData.upgrade_tables?.[String(baseItem.up_id)];
        const upStats = upTable?.[String(item.upgrade)];
        if (upStats) {
          Object.keys(upStats).forEach(sn => {
            const rawVal = upStats[sn];
            const boostedVal = Math.floor(rawVal * (1 + awk.upgradeAwakening));
            addStat(sn, boostedVal);
          });
        }
      }

      if (!isCostume && baseItem && baseItem.ref_id && item.refine) {
        const refTable = staticData.refine_tables?.[String(baseItem.ref_id)];
        const refStats = refTable?.[String(item.refine)];
        if (refStats) {
          Object.keys(refStats).forEach(sn => {
            const rawVal = refStats[sn];
            const boostedVal = rawVal * (1 + awk.refineAwakening);
            addStat(sn, boostedVal);
          });
        }
      }

      if (Array.isArray(item.enchant_lines) && item.enchant_lines.length > 0) {
        let catKey = 'armor';
        if (slotKey === 'weapon') catKey = 'weapon';
        else if (['accessory_1', 'accessory_2', 'talisman'].includes(slotKey)) catKey = 'accessory';
        item.enchant_lines.forEach(line => {
          if (!line || !line.city || !line.stat || !line.level) return;
          const encCity = staticData.enchant_cities?.[line.city];
          if (encCity) {
            const catStats = encCity[catKey] || {};
            const rate = catStats[line.stat] || 0;
            const encMultiplier = (Number(line.level) || 1) * (1 + awk.enchantAwakening);
            addStat(line.stat, rate * encMultiplier);
          }
        });
      } else if (item.enchant_city && item.enchant_lv) {
        const encCity = staticData.enchant_cities?.[item.enchant_city];
        if (encCity) {
          const encMultiplier = (Number(item.enchant_lv) || 1) * (1 + awk.enchantAwakening);
          let catKey = 'armor';
          if (slotKey === 'weapon') catKey = 'weapon';
          else if (['accessory_1', 'accessory_2', 'talisman'].includes(slotKey)) catKey = 'accessory';
          const catStats = encCity[catKey] || {};
          Object.keys(catStats).forEach(sn => {
            const rate = catStats[sn];
            addStat(sn, rate * encMultiplier);
          });
        }
      }

      if (Array.isArray(item.cards)) {
        item.cards.forEach(cardName => {
          Object.keys(staticData.cards_catalog || {}).forEach(cat => {
            const cardObj = staticData.cards_catalog[cat].find(c => c.name === cardName);
            if (cardObj && cardObj.stats) {
              Object.keys(cardObj.stats).forEach(sn => addStat(sn, cardObj.stats[sn]));
            }
          });
        });
      }
    });

    const pet = build.pet || {};
    if (pet.name && (build.buffs?.pet_active !== false)) {
      if (pet.custom_stats && Object.keys(pet.custom_stats).length > 0) {
        Object.keys(pet.custom_stats).forEach(sn => {
          const rawVal = Number(pet.custom_stats[sn]) || 0;
          addStat(sn, rawVal);
        });
      } else {
        const petStats = staticData.pets_catalog?.[pet.name] || staticData.sp_pets_catalog?.[pet.name] || [];
        petStats.forEach(sn => {
          addStat(sn, 30);
        });
      }
    }

    const companion = build.companion || {};
    addStat('STR', companion.str);
    addStat('INT', companion.int);
    addStat('P.ATK%', companion.patk_pct);
    addStat('Crit DMG Bonus', companion.crit_dmg);
    addStat('Final P.DMG Bonus', companion.final_pdmg_bonus);
    addStat('Fire Enhance', companion.fire_enhance);

    const divinity = build.divinity || {};
    Object.keys(divinity).forEach(partKey => {
      const partConfig = divinity[partKey];
      if (!partConfig) return;
      const partData = staticData.divinity_catalog?.[partConfig.name] || staticData.divinity_catalog?.[partKey];
      if (partData) {
        const q = partConfig.quality || 'gold';
        const lvl = String(partConfig.level !== undefined ? partConfig.level : 0);
        
        // Tally Main Stats from main_levels (e.g. Max HP, P.ATK/M.ATK, P.ATK%/M.ATK%)
        const mainObj = partData.main_levels?.[lvl];
        if (mainObj && Array.isArray(partData.stat_names)) {
          const mainVal = mainObj[q] || mainObj.gold || 0;
          partData.stat_names.forEach(mStat => {
            addStat(mStat, mainVal);
          });
        }
        
        // Tally Substats (up to 2 chosen substats from full pool)
        if (Array.isArray(partConfig.selected_substats)) {
          partConfig.selected_substats.forEach(sn => {
            const sObj = partData.substats?.[sn];
            if (sObj !== undefined) {
              const sVal = typeof sObj === 'object' ? (sObj[q] || sObj.gold || 0) : sObj;
              addStat(sn, sVal);
            }
          });
        }
      }
    });

    const sets = staticData.equip_sets || [];
    sets.forEach(s => {
      if (s.name && build.buffs?.[s.name]) {
        addStat(s.stat || 'Final DMG Bonus', 0.10);
      }
    });

    const injected = build.stat_injection || {};
    Object.keys(injected).forEach(sn => {
      addStat(sn, injected[sn]);
    });

    const buffs = build.buffs || {};
    if (buffs.spear_flash) {
      addStat('Final P.DMG Bonus', 0.20);
    }
    if (buffs.concentration) {
      addStat('P.ATK%', 0.15);
      addStat('Hit', 50);
    }
    if (buffs.spooky_lamp) {
      addStat('Final P.DMG Bonus', 0.10);
    }

    const flatPercentPairs = [
      ['P.ATK', 'P.ATK%'],
      ['P.DEF', 'P.DEF%'],
      ['M.ATK', 'M.ATK%'],
      ['M.DEF', 'M.DEF%'],
      ['ASPD', 'ASPD%'],
      ['Max HP', 'Max HP%'],
      ['STR', 'STR%'],
      ['AGI', 'AGI%'],
      ['VIT', 'VIT%'],
      ['INT', 'INT%'],
      ['DEX', 'DEX%'],
      ['LUK', 'LUK%']
    ];

    flatPercentPairs.forEach(([flatKey, pctKey]) => {
      if (stats[flatKey] && stats[pctKey]) {
        stats[flatKey] = Math.floor(stats[flatKey] * (1 + stats[pctKey]));
      }
    });

    return { stats, awakenings: awk };
  }

  function calculateNetPen(pPen, finalPPen, targetPDef, targetFinalPDef, debuffFinalPDef) {
    const rawNet = (pPen || 0) + (finalPPen || 0) - (targetPDef || 0) - (targetFinalPDef || 0) - (debuffFinalPDef || 0);
    return rawNet > 1.5 ? (rawNet * 2 - 1.5) : rawNet;
  }

  function calculateSkillDamage(skill, playerStats, target, buffs, staticData, debuffs = {}, isPvp = false) {
    const pAtk = playerStats['P.ATK'] || 0;
    const pPen = playerStats['P.PEN'] || 0;
    const finalPPen = playerStats['Final P.PEN'] || 0;
    const finalPDmgBonus = playerStats['Final P.DMG Bonus'] || 0;
    const pDmgBonus = playerStats['P.DMG Bonus'] || 0;
    const critDmgBonus = playerStats['Crit DMG Bonus'] || 1.5;
    const finalDmgBonus = playerStats['Final DMG Bonus'] || 0;
    const dmgIncrease = playerStats['Damage Increase'] || 0;

    const targetPDef = target.p_def_pct || 0;
    const targetFinalPDef = (target.final_p_def || 0) - (debuffs.final_p_def || 0);
    const targetFinalPDmgRed = (target.final_p_dmg_red || 0) - (debuffs.final_p_dmg_red || 0);
    const targetFinalDmgRed = (target.final_dmg_red || 0) - (debuffs.final_dmg_red || 0);
    const targetPDmgRed = (target.p_dmg_red || 0) - (debuffs.p_dmg_red || 0);

    const netPen = calculateNetPen(pPen, finalPPen, targetPDef, targetFinalPDef, 0);
    const netFpdb = finalPDmgBonus - targetFinalPDmgRed;

    const attackerElem = buffs.elemental_converter || 'Fire';
    const defenderElem = target.element || 'Shadow';
    const elemCounter = isPvp ? 1.0 : (staticData.element_matrix?.[attackerElem]?.[defenderElem] ?? 1.0);
    const elemEnhance = playerStats[attackerElem + ' Enhance'] || 0;
    const elemFactor = elemCounter + elemEnhance;

    const attrBonus = isPvp ? 0 : (playerStats['Bonus DMG to ' + defenderElem + ' Attribute Monster'] || 0);
    const raceBonus = isPvp ? 0 : (playerStats['Bonus DMG to ' + (target.race || 'Formless')] || 0);

    const weaponSizeMod = isPvp ? 1.0 : (staticData.size_penalty?.[target.size || 'Large'] ?? 1.0);
    const sizeBonus = isPvp ? 0 : (playerStats['Bonus DMG to ' + (target.size || 'Large')] || 0);
    const sizeFactor = weaponSizeMod + sizeBonus;

    const netFinalDmgBonus = finalDmgBonus - targetFinalDmgRed;

    let baseSkillMultiplier = pAtk;
    switch (skill.id) {
      case 'double_blow':
        baseSkillMultiplier = Math.floor(pAtk * 1.5);
        break;
      case 'wind_cutter':
        baseSkillMultiplier = Math.floor(pAtk * 1.8);
        break;
      case 'storm_slash':
        baseSkillMultiplier = Math.floor(pAtk * 2.2);
        break;
      case 'ignition_break':
        const strBonus = Math.min(15, (playerStats['STR'] || 0) / 800);
        baseSkillMultiplier = Math.floor(pAtk * (3 + strBonus));
        break;
      case 'dusk_claymore':
        baseSkillMultiplier = Math.floor(pAtk * 7.02);
        break;
      case 'demolition':
        baseSkillMultiplier = Math.floor(pAtk * 2.38) * 10;
        break;
      case 'phantom':
        baseSkillMultiplier = Math.floor(pAtk * 17.4);
        break;
      case 'spooky_lamp':
        baseSkillMultiplier = Math.floor(pAtk * 20) * 6;
        break;
      default:
        baseSkillMultiplier = pAtk;
    }

    const spearFlashMod = buffs.spear_flash ? 1.4 : 1.0;

    let critHitDmg = 0;
    let nonCritHitDmg = 0;

    if (isPvp) {
      const pvpFinalPDmgBonus = playerStats['PVP Final P.DMG Bonus'] || 0;
      const pvpPDmgBonus = playerStats['PVP P.DMG Bonus'] || 0;
      const targetPvpFinalPDmgRed = (target.pvp_final_p_dmg_red || 0) - (debuffs.pvp_final_p_dmg_red || 0);
      const targetPvpPDmgRed = (target.pvp_p_dmg_red || 0) - (debuffs.pvp_p_dmg_red || 0);

      const netW = netFpdb;
      const netAA = netFinalDmgBonus;
      const netAB = pDmgBonus - targetPDmgRed;
      const netAD = pvpFinalPDmgBonus - targetPvpFinalPDmgRed;
      const pvpMult = skill.id === 'normal_attack' ? 8 : 16;

      const pvpCoreCrit = (baseSkillMultiplier * critDmgBonus + netAB) * (1 + netW) * elemFactor * (1 + netAA);
      critHitDmg = Math.floor(pvpMult * (Math.pow(Math.max(0, pvpCoreCrit), 0.6) - targetPvpPDmgRed) * (1 + netAD) + pvpPDmgBonus);

      const pvpCoreNonCrit = (baseSkillMultiplier * (1 + netPen) + netAB) * (1 + netW) * elemFactor * (1 + netAA);
      nonCritHitDmg = Math.floor(pvpMult * (Math.pow(Math.max(0, pvpCoreNonCrit), 0.6) - targetPvpPDmgRed) * (1 + netAD) + pvpPDmgBonus);
    } else {
      const innerCritTerm = Math.floor(baseSkillMultiplier * critDmgBonus + pDmgBonus);
      critHitDmg = Math.floor(
        innerCritTerm *
        (1 + netFpdb) *
        elemFactor *
        (1 + attrBonus) *
        (1 + raceBonus) *
        (1 + netFinalDmgBonus) *
        sizeFactor *
        (1 + dmgIncrease)
      );
      critHitDmg = Math.floor(critHitDmg * spearFlashMod);

      const innerNonCritTerm = Math.floor(baseSkillMultiplier * (1 + netPen) + pDmgBonus);
      nonCritHitDmg = Math.floor(
        innerNonCritTerm *
        (1 + netFpdb) *
        elemFactor *
        (1 + attrBonus) *
        (1 + raceBonus) *
        (1 + netFinalDmgBonus) *
        sizeFactor *
        (1 + dmgIncrease)
      );
      nonCritHitDmg = Math.floor(nonCritHitDmg * spearFlashMod);
    }

    return {
      skillId: skill.id,
      skillName: skill.name,
      critHitDmg: Math.max(0, critHitDmg),
      nonCritHitDmg: Math.max(0, nonCritHitDmg),
      factors: {
        baseMultiplier: baseSkillMultiplier,
        netPen,
        netFpdb,
        elemFactor,
        attrBonus,
        raceBonus,
        sizeFactor,
        netFinalDmgBonus,
        dmgIncrease,
        spearFlashMod,
        isPvp
      }
    };
  }

  function simulateCombatTimeline(skills, playerStats, target, buffs, staticData, debuffs = {}, isPvp = false) {
    const hitsBreakdown = [];
    let totalDmg60s = 0;

    skills.forEach(sk => {
      const dmgRes = calculateSkillDamage(sk, playerStats, target, buffs, staticData, debuffs, isPvp);
      let hitsIn60s = 0;
      switch (sk.id) {
        case 'normal_attack':
          hitsIn60s = 6 * 60;
          break;
        case 'double_blow':
          hitsIn60s = 6 * 60;
          break;
        case 'wind_cutter':
          hitsIn60s = 6 * 60;
          break;
        case 'storm_slash':
          hitsIn60s = Math.floor(60 / 2.5);
          break;
        case 'dusk_claymore':
          hitsIn60s = Math.floor(60 / 5.0 * 2.5);
          break;
        case 'demolition':
          hitsIn60s = 2;
          break;
        case 'spooky_lamp':
          hitsIn60s = 2;
          break;
        default:
          hitsIn60s = 0;
      }

      const totalSkillDmg = dmgRes.critHitDmg * hitsIn60s;
      totalDmg60s += totalSkillDmg;

      hitsBreakdown.push({
        skillId: sk.id,
        skillName: sk.name,
        damagePerHit: dmgRes.critHitDmg,
        hitsIn60s,
        totalSkillDmg
      });
    });

    const dps = Math.floor(totalDmg60s / 60);
    const totalDmg3m = totalDmg60s * 3;

    return {
      dps,
      totalDmg60s,
      totalDmg3m,
      hitsBreakdown
    };
  }

  function generateDamageWaterfallTrace(damageResult) {
    const f = damageResult.factors;
    return [
      `[01] Base Skill ATK:       ${f.baseMultiplier.toLocaleString()} (P.ATK base)`,
      `[02] Net Effective PEN:     +${(f.netPen * 100).toFixed(2)}% (Target DEF mitigated)`,
      `[03] Final P.DMG Bonus:     +${(f.netFpdb * 100).toFixed(2)}% net`,
      `[04] Element Matrix:        x${f.elemFactor.toFixed(3)} (Advantage + Enhance)`,
      `[05] Race & Attribute:      +${((f.raceBonus + f.attrBonus) * 100).toFixed(2)}%`,
      `[06] Size Scaling:          x${f.sizeFactor.toFixed(2)} (Weapon size modifier)`,
      `[07] Final Bonus & Inc:     +${((f.netFinalDmgBonus + f.dmgIncrease) * 100).toFixed(2)}%`,
      `[08] 1-Hit Crit Damage:     ${damageResult.critHitDmg.toLocaleString()} (Spear Flash x${f.spearFlashMod.toFixed(1)})`
    ].join('\n');
  }

  global.RoxSimulatorEngine = {
    calculatePrimaryConversions,
    calculateAwakeningBonuses,
    tallyPlayerStats,
    calculateNetPen,
    calculateSkillDamage,
    simulateCombatTimeline,
    generateDamageWaterfallTrace
  };
})(typeof window !== 'undefined' ? window : globalThis);
