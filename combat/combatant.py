from __future__ import annotations

from dataclasses import dataclass

from models.character import Character


@dataclass
class Combatant:
	"""Wrapper for characters that can participate in combat."""
	character: Character
	initiative: int

	def __lt__(self, other: Combatant) -> bool:
		return self.initiative < other.initiative
