from __future__ import annotations

from dataclasses import dataclass


# Statuts retirés par cleanse. Les bonus (bless, shield, smite, death_ward…) restent.
NEGATIVE_EFFECTS = frozenset({
	'sleep',
	'blind',
	'paralyze',
	'frighten',
	'restrained',
	'disadvantage',
})


@dataclass
class ActiveEffect:
	"""Statut posé par un sort, avec une durée en rounds.

	`turns is None` : l'effet dure jusqu'à consommation (smite, death ward).
	`just_applied` : le tick de fin du round de lancement ne consomme pas un tour,
	pour que l'effet soit encore actif au round suivant.
	"""

	kind: str
	turns: int | None
	magnitude: int = 0
	spell_name: str = ''
	extra: str = ''
	just_applied: bool = True
