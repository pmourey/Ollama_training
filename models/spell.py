from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from models.dice import DamageDice
from models.enums import ClassType


@dataclass
class Spell:
	"""A spell that can be cast by spellcasters."""
	name: str
	class_type: ClassType
	level: int
	damage_dice: Optional[DamageDice]
	effect: str
	dc_type: str
	dc_success: str  # "half", "none", or ""
	description: str
	# indique si le sort peut viser plusieurs cibles simultanément
	multi_target: bool = False

	def __eq__(self, other: object) -> bool:
		return isinstance(other, Spell) and self.name == other.name

	@property
	def value(self) -> float:
		dice = self.damage_dice
		if dice is None:
			return 0.0
		average_roll = (1 + dice.roll_dice) / 2
		return (dice.num_dice * average_roll) + dice.bonus

BENEFICIAL_EFFECTS = {'heal', 'buff', 'shield', 'cleanse', 'revive'}

def is_beneficial(spell: Spell) -> bool:
    """Sorts qui doivent viser un allié plutôt qu'un monstre."""
    return spell.effect in BENEFICIAL_EFFECTS
