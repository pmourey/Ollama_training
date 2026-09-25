from __future__ import annotations

from random import randint

from combat.effects.base import CastContext, EffectHandler, scaled_duration
from models.character import Character
from models.spell import Spell
from models.status import ActiveEffect


class FallbackHandler(EffectHandler):
	def apply(self, ctx: CastContext, target: Character) -> str:
		return f'[Spell] {ctx.caster.name} casts {ctx.spell.name} on {target.name}!'


class DamageHandler(EffectHandler):
	ai_role = 'damage'

	def matches(self, spell: Spell) -> bool:
		return 'damage' in spell.effect

	def apply(self, ctx: CastContext, target: Character) -> str:
		spell = ctx.spell
		if 'psychic' in spell.effect and target.has_effect('mind_blank'):
			return f'[Spell] {target.name}\'s mind is blank; {spell.name} has no effect!'
		damage = spell.damage_dice.roll if spell.damage_dice else 0
		if spell.dc_type and target.saving_throw(spell.dc_type, ctx.caster.dc_value):
			if spell.dc_success == 'half':
				damage = max(1, damage // 2)
				note = target.receive_damage(damage)
				msg = (
					f'[Spell] {target.name} saves against {spell.name} '
					f'and takes half damage ({damage} HP)!'
				)
				return f'{msg} {note}'.strip()
			return f'[Spell] {target.name} saves against {spell.name} and takes no damage!'
		note = target.receive_damage(damage)
		msg = (
			f'[Spell] {ctx.caster.name} casts {spell.name} '
			f'and deals {damage} damage to {target.name}!'
		)
		return f'{msg} {note}'.strip()


class HealHandler(EffectHandler):
	ai_role = 'heal'

	def matches(self, spell: Spell) -> bool:
		return spell.effect == 'heal'

	def apply(self, ctx: CastContext, target: Character) -> str:
		heal_amount = ctx.spell.damage_dice.roll if ctx.spell.damage_dice else 0
		target.hp = min(target.max_hp, target.hp + heal_amount)
		return f'[Spell] {ctx.caster.name} heals {target.name} for {heal_amount} HP!'


class BuffHandler(EffectHandler):
	ai_role = 'buff'
	ai_status = 'bless'

	def matches(self, spell: Spell) -> bool:
		return spell.effect == 'buff'

	def apply(self, ctx: CastContext, target: Character) -> str:
		turns = scaled_duration(ctx.spell.level)
		target.add_effect(ActiveEffect(kind='bless', turns=turns, spell_name=ctx.spell.name))
		return f'[Spell] {ctx.caster.name} blesses {target.name} for {turns} round(s)!'


class ShieldHandler(EffectHandler):
	"""+CA temporaire. Shield / Shield Wild sont surclassés dans specials.py."""

	ai_role = 'shield'
	ai_status = 'shield'

	def matches(self, spell: Spell) -> bool:
		return spell.effect == 'shield'

	def apply(self, ctx: CastContext, target: Character) -> str:
		magnitude = 2 + ctx.spell.level // 2
		turns = scaled_duration(ctx.spell.level)
		target.add_effect(ActiveEffect(
			kind='shield', turns=turns, magnitude=magnitude, spell_name=ctx.spell.name,
		))
		return (
			f'[Spell] {ctx.caster.name} shields {target.name} '
			f'(+{magnitude} AC for {turns} round(s))!'
		)


class CleanseHandler(EffectHandler):
	ai_role = 'cleanse'

	def matches(self, spell: Spell) -> bool:
		return spell.effect == 'cleanse'

	def apply(self, ctx: CastContext, target: Character) -> str:
		removed = target.cleanse_negative()
		if removed:
			return (
				f'[Spell] {ctx.caster.name} cleanses {target.name} '
				f'({", ".join(removed)})!'
			)
		return (
			f'[Spell] {ctx.caster.name} casts {ctx.spell.name} on {target.name}, '
			f'but there is nothing to cleanse.'
		)


class SmiteHandler(EffectHandler):
	"""Charge la prochaine attaque d'arme au lieu d'infliger les dégâts tout de suite."""

	ai_role = 'smite'
	ai_status = 'smite'
	ai_priority = 25

	def matches(self, spell: Spell) -> bool:
		return spell.effect == 'smite' or 'smite' in spell.name.lower()

	def apply(self, ctx: CastContext, target: Character) -> str:
		spell = ctx.spell
		if spell.damage_dice:
			bonus = spell.damage_dice.roll
		else:
			bonus = sum(randint(1, 8) for _ in range(max(1, spell.level)))
		extra = 'blind' if 'blinding' in spell.name.lower() else ''
		target.add_effect(ActiveEffect(
			kind='smite',
			turns=2,
			magnitude=bonus,
			spell_name=spell.name,
			extra=extra,
		))
		detail = f'+{bonus} on the next weapon hit'
		if extra:
			detail += ' and blinds on hit'
		return f'[Spell] {ctx.caster.name} invokes {spell.name} ({detail})!'


class ConditionHandler(EffectHandler):
	"""Aveuglement, paralysie, effroi, entrave, sommeil, malus."""

	def __init__(
		self,
		key: str,
		kind: str,
		verb: str,
		*,
		mental: bool = False,
		priority: int = 50,
	) -> None:
		self.key = key
		self.kind = kind
		self.verb = verb
		self.mental = mental
		self.ai_role = 'control'
		self.ai_status = kind
		self.ai_priority = priority

	def matches(self, spell: Spell) -> bool:
		return spell.effect == self.key

	def apply(self, ctx: CastContext, target: Character) -> str:
		resisted = self.resisted(ctx, target)
		if resisted:
			return resisted
		turns = scaled_duration(ctx.spell.level)
		target.add_effect(ActiveEffect(kind=self.kind, turns=turns, spell_name=ctx.spell.name))
		return f'[Spell] {ctx.spell.name}: {target.name} {self.verb} for {turns} round(s)!'
