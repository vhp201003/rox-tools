import json
from pathlib import Path
from typing import Dict, Any, Optional

ROOT = Path(__file__).resolve().parent.parent.parent
CURVES_FILE = ROOT / "data" / "growth_curves.json"

_GROWTH_CURVES: Dict[int, Dict[str, float]] = {}

def load_growth_curves() -> Dict[int, Dict[str, float]]:
    global _GROWTH_CURVES
    if not _GROWTH_CURVES and CURVES_FILE.exists():
        with open(CURVES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            _GROWTH_CURVES = {int(k): v for k, v in data.items()}
    return _GROWTH_CURVES

def estimate_arang_pdef(level: int) -> int:
    tiers = [(100, 480), (120, 635), (130, 730), (140, 845), (150, 970), (160, 1110)]
    if level <= tiers[0][0]:
        return tiers[0][1]
    if level >= tiers[-1][0]:
        return tiers[-1][1]
    for i in range(len(tiers) - 1):
        l1, d1 = tiers[i]
        l2, d2 = tiers[i + 1]
        if l1 <= level <= l2:
            return round(d1 + (d2 - d1) * (level - l1) / (l2 - l1))
    return 730

def scale_monster(monster: Dict[str, Any], target_level: int) -> Dict[str, Any]:
    scaled = dict(monster)
    target_level = max(1, min(200, target_level))
    base_level = max(1, int(monster.get("level") or 1))

    scaled["target_level"] = target_level
    scaled["base_level"] = base_level

    if target_level == base_level:
        scaled["is_scaled"] = False
        scaled["scale_ratio"] = 1.0
        return scaled

    curves = load_growth_curves()
    g_base = curves.get(base_level) or {"hp": float(base_level * 50), "def": float(base_level * 3), "atk": float(base_level * 3)}
    g_target = curves.get(target_level) or {"hp": float(target_level * 50), "def": float(target_level * 3), "atk": float(target_level * 3)}

    hp_ratio = g_target["hp"] / max(1.0, g_base["hp"])
    def_ratio = g_target["def"] / max(1.0, g_base["def"])
    atk_ratio = g_target["atk"] / max(1.0, g_base["atk"])

    base_hp = int(monster.get("max_hp") or 100)
    base_pdef = int(monster.get("p_def") or 0)
    base_mdef = int(monster.get("m_def") or 0)
    base_pdps = int(monster.get("p_dps") or 0)
    base_mdps = int(monster.get("m_dps") or 0)
    base_hit = int(monster.get("hit") or 0)
    base_flee = int(monster.get("flee") or 0)
    base_exp = int(monster.get("base_exp") or 0)
    job_exp = int(monster.get("job_exp") or 0)

    scaled["level"] = target_level
    scaled["max_hp"] = max(1, round(base_hp * hp_ratio))
    scaled["p_def"] = max(0, round(base_pdef * def_ratio))
    scaled["m_def"] = max(0, round(base_mdef * def_ratio))
    scaled["p_dps"] = max(0, round(base_pdps * atk_ratio))
    scaled["m_dps"] = max(0, round(base_mdps * atk_ratio))
    scaled["hit"] = max(0, base_hit + 3 * (target_level - base_level))
    scaled["flee"] = max(0, base_flee + 3 * (target_level - base_level))

    exp_ratio = (target_level / base_level) ** 1.35
    scaled["base_exp"] = max(0, round(base_exp * exp_ratio))
    scaled["job_exp"] = max(0, round(job_exp * exp_ratio))

    if monster.get("is_mvp") or monster.get("is_mini") or "Boss" in str(monster.get("type_name")) or monster.get("type") in (1, 2, 3):
        scaled["arang_bench_pdef"] = estimate_arang_pdef(target_level)

    scaled["is_scaled"] = True
    scaled["scale_ratio"] = round(hp_ratio, 3)
    return scaled
