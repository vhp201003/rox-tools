from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, model_validator


class EnchantLinePayload(BaseModel):
    line_index: int = Field(default=1, ge=1, le=3)
    city: str
    stat: str
    level: float = Field(default=1.0, ge=0.0, le=20.0)


class EquipSlotPayload(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    tab_type: str = "combat"
    is_disabled: bool = False
    upgrade: Optional[float] = 0.0
    refine: Optional[float] = 0.0
    enchant_city: Optional[str] = None
    enchant_lv: Optional[float] = None
    enchant_lines: List[EnchantLinePayload] = Field(default_factory=list)
    cards: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_slot_rules(self) -> "EquipSlotPayload":
        item_type = str(self.type or "").lower()
        is_1h = (
            "1h" in item_type
            or "one-handed" in item_type
            or "one handed" in item_type
            or item_type in ["dagger", "mace", "rod", "book", "axe", "1h sword", "1h staff"]
        )
        is_2h = not is_1h and any(
            kw in item_type for kw in ["2h", "two-handed", "two handed", "bow", "katar", "spear"]
        )

        if is_2h:
            max_cards = 5
        elif is_1h:
            max_cards = 3
        else:
            max_cards = 2 if self.type is not None else 5

        if len(self.cards) > max_cards:
            raise ValueError(
                f"Slot type '{self.type}' permits maximum {max_cards} cards, received {len(self.cards)}"
            )

        if self.tab_type == "costume":
            self.upgrade = 0.0
            self.refine = 0.0
            self.enchant_lines = []
            self.enchant_city = None
            self.enchant_lv = None

        return self


class CompanionLinePayload(BaseModel):
    stat_name: str
    value: float


class CompanionSlotPayload(BaseModel):
    slot_index: int = Field(default=1, ge=1, le=4)
    name: str = ""
    offensive: List[CompanionLinePayload] = Field(default_factory=list, max_length=3)
    defensive: List[CompanionLinePayload] = Field(default_factory=list, max_length=3)


class DivinityPartPayload(BaseModel):
    part_index: int = Field(default=1, ge=1, le=8)
    name: Optional[str] = None
    rarity: str = Field(default="gold")
    level: int = Field(default=0, ge=0, le=7)
    has_flash: bool = False
    affixes: List[str] = Field(default_factory=list)
    substats: Dict[str, float] = Field(default_factory=dict)


class BuildPayload(BaseModel):
    class_id: str = "dragon_knight"
    is_pvp: bool = False
    stats: Dict[str, float] = Field(default_factory=dict)
    job_stats: Dict[str, float] = Field(default_factory=dict)
    battle_achievement: Dict[str, float] = Field(default_factory=dict)
    loadout: Dict[str, EquipSlotPayload] = Field(default_factory=dict)
    buffs: Dict[str, Any] = Field(default_factory=dict)
    pet: Dict[str, Any] = Field(default_factory=dict)
    companion: Union[List[CompanionSlotPayload], Dict[str, Any]] = Field(default_factory=dict)
    divinity: Union[List[DivinityPartPayload], Dict[str, Any]] = Field(default_factory=dict)
    progression: Dict[str, Any] = Field(default_factory=dict)
    target: Dict[str, Any] = Field(default_factory=dict)
    pvp_target: Optional[Dict[str, float]] = None
    debuffs: Dict[str, float] = Field(default_factory=dict)
    stat_injection: Dict[str, float] = Field(default_factory=dict)
    inscriptions: Dict[str, float] = Field(default_factory=dict)
    card_awakening: Dict[str, float] = Field(default_factory=dict)
    guild_blessing: Dict[str, float] = Field(default_factory=dict)
    active_equip_sets: List[str] = Field(default_factory=list)
    skip_class_passives: bool = False

    @model_validator(mode="after")
    def sync_weapon_and_shield_state(self) -> "BuildPayload":
        if isinstance(self.loadout, dict):
            weapon = self.loadout.get("weapon")
            shield = self.loadout.get("shield")
            if weapon:
                item_type = str(getattr(weapon, "type", "") or "").lower()
                is_1h = (
                    "1h" in item_type
                    or "one-handed" in item_type
                    or "one handed" in item_type
                    or item_type in ["dagger", "mace", "rod", "book", "axe", "1h sword", "1h staff"]
                )
                is_2h = not is_1h and any(
                    kw in item_type for kw in ["2h", "two-handed", "two handed", "bow", "katar", "spear"]
                )
                if is_2h and shield:
                    if isinstance(shield, EquipSlotPayload):
                        shield.is_disabled = True
                        shield.cards = []
                        shield.refine = 0.0
                        shield.upgrade = 0.0
                        shield.enchant_lines = []
                    elif isinstance(shield, dict):
                        shield["is_disabled"] = True
                        shield["cards"] = []
                        shield["refine"] = 0.0
                        shield["upgrade"] = 0.0
                        shield["enchant_lines"] = []
        return self


class SimulationResult(BaseModel):
    dps: int
    totalDmg60s: int
    totalDmg3m: int
    talliedStats: Dict[str, float]
    statBreakdown: Optional[Dict[str, Dict[str, float]]] = None
    awakenings: Dict[str, float]
    hitsBreakdown: List[Dict[str, Any]]


class CommitRequest(BaseModel):
    build: BuildPayload


class ProfileResponse(BaseModel):
    id: str
    class_id: str
    build_data: Dict[str, Any]
    computed_results: Optional[Dict[str, Any]] = None
    computed_dps: int = 0
    updated_at: str
