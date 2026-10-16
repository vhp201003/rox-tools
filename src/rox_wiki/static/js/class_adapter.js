(function(global) {
  'use strict';

  class BaseClassAdapter {
    constructor(manifest) {
      this.manifest = manifest;
      this.classId = manifest.class_id;
      this.className = manifest.class_name;
      this.primaryStat = manifest.primary_stat;
    }

    getSkills() {
      return this.manifest.skills || [];
    }

    getDefaultBaseline() {
      return this.manifest.default_baseline || {};
    }

    calculatePrimaryConversion(baseStats, jobStats) {
      return { totalStats: {}, convertedPatk: 0 };
    }
  }

  class DragonKnightAdapter extends BaseClassAdapter {
    constructor(manifest) {
      super(manifest);
    }
  }

  class RangerAdapter extends BaseClassAdapter {
    constructor() {
      super({
        class_id: 'ranger',
        class_name: 'Ranger',
        primary_stat: 'DEX',
        skills: [
          { id: 'normal_attack', name: 'Normal Attack (Bow)', type: 'Physical', cooldown: 0, hits_per_sec: 6, active_in_rotation: true },
          { id: 'double_strafe', name: 'Double Strafe', type: 'Physical', cooldown: 0, hits_per_sec: 6, active_in_rotation: true },
          { id: 'arrow_shower', name: 'Arrow Shower', type: 'Physical', cooldown: 2.0, hits_per_sec: 0.5, active_in_rotation: true },
          { id: 'falcon_strike', name: 'Falcon Strike', type: 'Physical', cooldown: 4.0, hits_per_sec: 0.25, active_in_rotation: true }
        ],
        default_baseline: {
          base_level: 87,
          job_level: 17,
          stats: { str: 30, agi: 90, vit: 50, int: 20, dex: 120, luk: 60 },
          job_stats: { str: 15, agi: 35, vit: 18, int: 10, dex: 45, luk: 22 },
          battle_achievement: { str: 0, vit: 72, final_pdmg_bonus: 0.24, fire_enhance: 0.30, max_hp_pct: 0.24, final_pdmg_red: 0.16 },
          loadout: {
            weapon: { name: 'Composite Bow', type: 'Weapon', level: 1, refine: 10, upgrade: 60, enchant_city: 'Prontera', enchant_lv: 6, cards: [] },
            clothes: { name: "Vesper's Shield", type: 'Clothes', level: 1, refine: 6, upgrade: 30, enchant_city: 'Prontera', enchant_lv: 4, cards: [] },
            cloak: { name: "Vesper's Cloak", type: 'Cloak', level: 1, refine: 6, upgrade: 30, enchant_city: 'Prontera', enchant_lv: 4, cards: [] },
            shoes: { name: "Vesper's Shoes", type: 'Shoes', level: 1, refine: 6, upgrade: 30, enchant_city: 'Prontera', enchant_lv: 4, cards: [] },
            accessory_1: { name: 'Autumn Earrings', type: 'Accessory', level: 1, refine: 6, upgrade: 15, enchant_city: 'Prontera', enchant_lv: 4, cards: [] },
            accessory_2: { name: 'Autumn Earrings', type: 'Accessory', level: 1, refine: 6, upgrade: 15, enchant_city: 'Prontera', enchant_lv: 4, cards: [] },
            talisman: { name: 'Autumn Amulet', type: 'Talisman', level: 1, refine: 6, upgrade: 15, enchant_city: 'Prontera', enchant_lv: 4, cards: [] },
            costume_head: { name: 'Default Headgear', type: 'CostumeHead', level: 1, refine: 0, upgrade: 0, enchant_city: '', enchant_lv: 0, cards: [] },
            costume_eyes: { name: 'Default Face', type: 'CostumeEyes', level: 1, refine: 0, upgrade: 0, enchant_city: '', enchant_lv: 0, cards: [] },
            costume_mouth: { name: 'Default Mouth', type: 'CostumeMouth', level: 1, refine: 0, upgrade: 0, enchant_city: '', enchant_lv: 0, cards: [] },
            costume_back: { name: 'Default Back', type: 'CostumeBack', level: 1, refine: 0, upgrade: 0, enchant_city: '', enchant_lv: 0, cards: [] }
          },
          buffs: { elemental_converter: 'Fire', spear_flash: false, concentration: true, spooky_lamp: false, pet_active: true },
          target: { name: 'Lord of the Dead Lv.150', level: 150, element: 'Shadow', race: 'Formless', size: 'Large', p_def: 1200, p_def_pct: 0.40, final_p_def: 0.15, final_p_dmg_red: 0.20 }
        }
      });
    }

    calculatePrimaryConversion(baseStats, jobStats) {
      const totalDex = (baseStats.dex || 0) + (jobStats.dex || 0);
      const totalAgi = (baseStats.agi || 0) + (jobStats.agi || 0);
      const totalLuk = (baseStats.luk || 0) + (jobStats.luk || 0);
      const totalStr = (baseStats.str || 0) + (jobStats.str || 0);
      const totalVit = (baseStats.vit || 0) + (jobStats.vit || 0);
      const totalInt = (baseStats.int || 0) + (jobStats.int || 0);

      let dexPatk = 0;
      if (totalDex < 3000) {
        const flDex = Math.floor(totalDex / 100) * 100;
        dexPatk = Math.floor(totalDex * 4 + Math.pow(flDex, 2) * 0.002 + (totalDex - flDex) * (flDex / 100 * 0.2));
      } else {
        dexPatk = totalDex * 10;
      }

      return {
        totalStats: { str: totalStr, agi: totalAgi, vit: totalVit, int: totalInt, dex: totalDex, luk: totalLuk },
        convertedPatk: dexPatk
      };
    }
  }

  const registry = new Map();

  function registerClassAdapter(adapterInstance) {
    registry.set(adapterInstance.classId, adapterInstance);
  }

  function getClassAdapter(classId) {
    return registry.get(classId) || registry.get('dragon_knight');
  }

  function listRegisteredClasses() {
    return Array.from(registry.values()).map(a => ({
      classId: a.classId,
      className: a.className,
      primaryStat: a.primaryStat
    }));
  }

  global.RoxClassRegistry = {
    DragonKnightAdapter,
    RangerAdapter,
    registerClassAdapter,
    getClassAdapter,
    listRegisteredClasses
  };
})(typeof window !== 'undefined' ? window : globalThis);
