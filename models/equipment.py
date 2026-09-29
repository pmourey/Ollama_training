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


# --- Conversion helpers between plain-dict inventory items (as loaded from
# data/*.json or dropped as loot) and the typed equipment dataclasses used by
# Hero.weapon / Hero.armor / Hero.shield. These are shared by the console
# simulation and the GUI so both can equip/unequip items the same way.

def weapon_from_item(item: dict) -> Weapon:
	"""Build a Weapon from an inventory dict (expects a 'damage' die size)."""
	dmg = item.get('damage', 4)
	try:
		sides = int(dmg)
	except (TypeError, ValueError):
		sides = 4
	return Weapon(name=item.get('name', 'Weapon'), damage_dice=DamageDice(1, sides))


def weapon_to_item(weapon: Weapon) -> dict:
	"""Convert an equipped Weapon back into a plain inventory dict."""
	return {
		'name': weapon.name,
		'type': 'weapon',
		'damage': getattr(weapon.damage_dice, 'roll_dice', 4),
	}


def armor_from_item(item: dict) -> Armor:
	try:
		bonus = int(item.get('bonus', 0) or 0)
	except (TypeError, ValueError):
		bonus = 0
	return Armor(name=item.get('name', 'Armor'), bonus=bonus)


def armor_to_item(armor: Armor) -> dict:
	return {'name': armor.name, 'type': 'armor', 'bonus': armor.bonus}


def shield_from_item(item: dict) -> Shield:
	try:
		bonus = int(item.get('bonus', 0) or 0)
	except (TypeError, ValueError):
		bonus = 0
	return Shield(name=item.get('name', 'Shield'), bonus=bonus)


def shield_to_item(shield: Shield) -> dict:
	return {'name': shield.name, 'type': 'shield', 'bonus': shield.bonus}
