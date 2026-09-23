from __future__ import annotations

from dataclasses import dataclass

from models.dice import DamageDice


@dataclass
class Armor:
	name: str
	bonus: int


@dataclass
class Weapon:
	name: str
	damage_dice: DamageDice

	def __repr__(self) -> str:
		return f'{self.name} {self.damage_dice}'


@dataclass
class Shield:
	name: str
	bonus: int


@dataclass
class Equipment:
	type: Armor | Weapon | Shield
	desc: str
	weight: int
	size: int
	cost: int
