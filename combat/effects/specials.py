"""Traitements individuels : le sort ne suit pas seulement sa catégorie JSON.

Enregistrés par nom dans le registre, ils sont choisis avant le gestionnaire
de catégorie. Pour un nouveau cas, ajouter une classe ici et un `register_spell`.
"""

from __future__ import annotations

from combat.effects.base import CastContext, EffectHandler, scaled_duration
from combat.effects.handlers import ShieldHandler
from models.character import Character
from models.status import ActiveEffect


class ShieldSpellHandler(ShieldHandler):
	"""Shield / Shield Wild : +5 CA, un round, comme le sort de bouclier arcanique."""
	#ai_priority = 5

	def apply(self, ctx: CastContext, target: Character) -> str:
		target.add_effect(ActiveEffect(
			kind='shield', turns=1, magnitude=5, spell_name=ctx.spell.name,
		))
		return f'[Spell] {ctx.spell.name} raises {target.name}\'s AC by 5 for 1 round!'


class DeathWardHandler(EffectHandler):
	ai_role = 'buff'
	ai_status = 'death_ward'
	ai_priority = 15

	def apply(self, ctx: CastContext, target: Character) -> str:
		target.add_effect(ActiveEffect(
			kind='death_ward', turns=None, spell_name=ctx.spell.name,
		))
		return f'[Spell] {ctx.spell.name} protects {target.name} from the next killing blow!'


class TimeStopHandler(EffectHandler):
	ai_role = 'buff'
	ai_status = 'time_stop'
	ai_priority = 12

	def apply(self, ctx: CastContext, target: Character) -> str:
		target.add_effect(ActiveEffect(
			kind='time_stop', turns=1, spell_name=ctx.spell.name,
		))
		return (
			f'[Spell] {ctx.caster.name} stops time with {ctx.spell.name}; '
			f'the next strike cannot miss!'
		)


class MindBlankHandler(EffectHandler):
	ai_role = 'buff'
	ai_status = 'mind_blank'

	def apply(self, ctx: CastContext, target: Character) -> str:
		turns = max(2, ctx.spell.level // 2)
		target.add_effect(ActiveEffect(
			kind='mind_blank', turns=turns, spell_name=ctx.spell.name,
		))
		return f'[Spell] {ctx.spell.name} shields {target.name}\'s mind for {turns} round(s)!'


class ForesightHandler(EffectHandler):
	ai_role = 'buff'
	ai_status = 'foresight'

	def apply(self, ctx: CastContext, target: Character) -> str:
		turns = scaled_duration(ctx.spell.level)
		target.add_effect(ActiveEffect(
			kind='foresight', turns=turns, magnitude=2, spell_name=ctx.spell.name,
		))
		return (
			f'[Spell] {ctx.spell.name} grants {target.name} '
			f'+2 AC and +2 to hit for {turns} round(s)!'
		)


class ReviveHandler(EffectHandler):
	"""Revivify / Resurrection : relève un allié à 1 PV, sinon dissipe les malus."""

	ai_role = 'revive'

	def apply(self, ctx: CastContext, target: Character) -> str:
		removed = target.cleanse_negative()
		cleansed = f' Cleansed: {", ".join(removed)}.' if removed else ''
		if target.hp <= 0:
			target.hp = 1
			return f'[Spell] {ctx.spell.name} revives {target.name} to 1 HP!{cleansed}'
		if removed:
			return (
				f'[Spell] {ctx.caster.name} casts {ctx.spell.name} '
				f'and cleanses {target.name} ({", ".join(removed)})!'
			)
		return (
			f'[Spell] {ctx.caster.name} casts {ctx.spell.name} on {target.name}, '
			f'but there is nothing to restore.'
		)


class MiracleHandler(EffectHandler):
	"""Wish / Absolute Salvation : soins complets et dissipation."""

	ai_role = 'revive'

	def apply(self, ctx: CastContext, target: Character) -> str:
		removed = target.cleanse_negative()
		target.hp = target.max_hp
		cleansed = f' Cleansed: {", ".join(removed)}.' if removed else ''
		return f'[Spell] {ctx.spell.name} fully restores {target.name}!{cleansed}'
