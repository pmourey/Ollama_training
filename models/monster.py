from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from models.abilities import Abilities
from models.character import Character
from models.dice import DamageDice
from models.equipment import Equipment


@dataclass
class MonsterType:
	name: str
	hit_dice: DamageDice
	ac: int
	damage_dice: DamageDice
	spellcasting: bool = False

	@property
	def level(self) -> int:
		return self.hit_dice.num_dice

	@property
	def damage(self) -> int:
		return self.damage_dice.roll


@dataclass(kw_only=True)
class Monster(Character):
	type: MonsterType
	ac: int
	damage: int
	inventory: List[Equipment] = field(default_factory=list)

	@property
	def armor_class(self) -> int:
		return self.ac + self.ac_modifiers()

	@property
	def attack_bonus(self) -> int:
		proficiency_bonus = 2 + ((self.level - 1) // 4)
		return self.abilities.str_mod + proficiency_bonus + self.attack_modifier()

	def attack(self, target: Character) -> int:
		"""Jet de dégâts (la CA gère le toucher)."""
		damage = self.type.damage_dice.roll + self.abilities.str_mod
		return max(1, damage)
