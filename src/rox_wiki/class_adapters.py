import math
from typing import Dict, Any, List, Optional, Callable
from rox_wiki.engine import calculate_primary_conversions


class BaseClassAdapter:
    def __init__(self, manifest: Dict[str, Any]):
        self.manifest = manifest
        self.class_id = manifest.get('class_id', '')
        self.class_name = manifest.get('class_name', '')
        self.primary_stat = manifest.get('primary_stat', '')

    def get_skills(self) -> List[Dict[str, Any]]:
        return self.manifest.get('skills') or []

    def get_default_baseline(self) -> Dict[str, Any]:
        return self.manifest.get('default_baseline') or {}

    def get_primary_conversion_fn(self) -> Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]:
        return calculate_primary_conversions


class DragonKnightAdapter(BaseClassAdapter):
    pass


class RangerAdapter(BaseClassAdapter):
    def __init__(self, manifest: Optional[Dict[str, Any]] = None):
        if not manifest:
            manifest = {
                'class_id': 'ranger',
                'class_name': 'Ranger',
                'primary_stat': 'DEX',
                'skills': [
                    {'id': 'normal_attack', 'name': 'Normal Attack (Bow)', 'type': 'Physical', 'cooldown': 0, 'hits_per_sec': 6, 'active_in_rotation': True},
                    {'id': 'double_strafe', 'name': 'Double Strafe', 'type': 'Physical', 'cooldown': 0, 'hits_per_sec': 6, 'active_in_rotation': True},
                    {'id': 'arrow_shower', 'name': 'Arrow Shower', 'type': 'Physical', 'cooldown': 2.0, 'hits_per_sec': 0.5, 'active_in_rotation': True},
                    {'id': 'falcon_strike', 'name': 'Falcon Strike', 'type': 'Physical', 'cooldown': 4.0, 'hits_per_sec': 0.25, 'active_in_rotation': True}
                ],
                'default_baseline': {}
            }
        super().__init__(manifest)

    def get_primary_conversion_fn(self) -> Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]:
        def ranger_conversion(base_stats: Dict[str, Any], job_stats: Dict[str, Any]) -> Dict[str, Any]:
            total_dex = (base_stats.get('dex') or 0) + (job_stats.get('dex') or 0)
            total_agi = (base_stats.get('agi') or 0) + (job_stats.get('agi') or 0)
            total_luk = (base_stats.get('luk') or 0) + (job_stats.get('luk') or 0)
            total_str = (base_stats.get('str') or 0) + (job_stats.get('str') or 0)
            total_vit = (base_stats.get('vit') or 0) + (job_stats.get('vit') or 0)
            total_int = (base_stats.get('int') or 0) + (job_stats.get('int') or 0)

            if total_dex < 3000:
                fl_dex = math.floor(total_dex / 100) * 100
                dex_patk = math.floor(total_dex * 4 + (fl_dex ** 2) * 0.002 + (total_dex - fl_dex) * (fl_dex / 100 * 0.2))
            else:
                dex_patk = total_dex * 10

            return {
                'totalStats': {'str': total_str, 'agi': total_agi, 'vit': total_vit, 'int': total_int, 'dex': total_dex, 'luk': total_luk},
                'convertedPatk': dex_patk
            }
        return ranger_conversion


def get_adapter(class_id: str, manifests: Optional[Dict[str, Any]] = None) -> BaseClassAdapter:
    manifests = manifests or {}
    if class_id == 'ranger':
        manifest = manifests.get('ranger')
        return RangerAdapter(manifest)
    manifest = manifests.get(class_id) or manifests.get('dragon_knight') or {}
    return DragonKnightAdapter(manifest)
