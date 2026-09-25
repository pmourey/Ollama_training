from __future__ import annotations

from dataclasses import dataclass

from models.character import Character, Hero
from models.spell import Spell


def scaled_duration(level: int) -> int:
	"""Durée courte indexée sur le niveau du sort (1 round au niveau 1)."""
	return max(1, (level + 1) // 2)


@dataclass
class CastContext:
	caster: Hero
	spell: Spell


class EffectHandler:
	"""Gestionnaire d'une catégorie d'effet, ou d'un sort précis.

	`ai_role` indique au combat comment le sort est choisi.
	`ai_status` est le statut posé sur la cible (vide si le sort n'en pose pas).
	`ai_priority` ordonne les contrôles : plus petit = tenté en premier.
	"""

	ai_role: str = 'other'
	ai_status: str = ''
	ai_priority: int = 50
	mental: bool = False

	def matches(self, spell: Spell) -> bool:
		return False

	def apply(self, ctx: CastContext, target: Character) -> str:
		raise NotImplementedError

	def resisted(self, ctx: CastContext, target: Character) -> str | None:
		"""Message si l'effet ne se pose pas. `None` s'il s'applique."""
		if self.mental and target.has_effect('mind_blank'):
			return f'[Spell] {target.name} resists {ctx.spell.name} (Mind Blank)!'
		if ctx.spell.dc_type and target.saving_throw(ctx.spell.dc_type, ctx.caster.dc_value):
			return f'[Spell] {target.name} saves against {ctx.spell.name}!'
		return None
