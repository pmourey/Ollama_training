from __future__ import annotations

from random import choice, randint
from typing import List

from game_state import uprint
from models.character import Character, Hero
from models.enums import Condition
from models.spell import Spell


class BattleSystem:
	"""Combat 5e : d20 + attack_bonus vs armor_class."""

	spells_count: int = 0

	@classmethod
	def spells_inc(cls) -> None:
		cls.spells_count += 1

	@staticmethod
	def calculate_hit_chance(attacker: Character, defender: Character) -> float:
		if defender.condition in [Condition.UNCONSCIOUS, Condition.PARALYZED]:
			return 1.0
		needed_roll = defender.armor_class - attacker.attack_bonus
		if needed_roll <= 1:
			faces = 19
		elif needed_roll >= 20:
			faces = 1
		else:
			faces = 20 - needed_roll + 1
		return faces / 20.0

	@staticmethod
	def resolve_spell_effect(caster: Hero, targets: list[Character], spell: Spell) -> None:
		"""Delegate spell effect resolution to combat.effects registry handlers.

		Builds a CastContext and calls the resolved handler.apply for each target.
		This centralizes special-case handling implemented in combat/effects/*.
		"""
		from combat.effects.base import CastContext
		from combat.effects import registry
		from game_state import uprint

		ctx = CastContext(caster=caster, spell=spell)
		handler = registry.resolve(spell)
		for target in targets:
			# handler may perform saves, damage, add ActiveEffect, etc.
			try:
					msg = handler.apply(ctx, target)
			except Exception:
					# Fallback to a generic message if a handler fails unexpectedly
					msg = f'[Spell] {caster.name} casts {spell.name} on {target.name}!'
			uprint(msg)

	@staticmethod
	def melee_attack(attacker: Character, defenders: list[Character]) -> None:
		for defender in defenders:
			if defender.condition in [Condition.UNCONSCIOUS, Condition.PARALYZED]:
				damage = BattleSystem._roll_damage(attacker, defender, is_critical=True)
				defender.hp -= damage
				msg = (
					f'{attacker.name} touche AUTOMATIQUEMENT {defender.name} '
					f'(sans défense) pour un COUP CRITIQUE de {damage} dégâts !'
				)
			else:
				d20_roll = randint(1, 20)
				attack_bonus = attacker.attack_bonus
				total_attack = d20_roll + attack_bonus
				ac = defender.armor_class

				if d20_roll == 1:
					fumble_damage = randint(1, 4)
					attacker.hp -= fumble_damage
					action = choice([
						'glisse lamentablement en attaquant et s\'entaille la jambe',
						'frappe un mur de pierre par maladresse',
						'perd l\'équilibre et se cogne la tête',
					])
					msg = (
						f'❌ ÉCHEC CRITIQUE ! {attacker.name} fait un 1 naturel... '
						f'Il {action} ! Il subit {fumble_damage} dégâts.'
					)
					if attacker.is_dead:
						msg += f' {attacker.name} s\'est tué !'
				elif d20_roll == 20:
					damage = BattleSystem._roll_damage(attacker, defender, is_critical=True)
					defender.hp -= damage
					msg = (
						f'🎯 COUP CRITIQUE ! {attacker.name} fait un 20 naturel '
						f'et inflige {damage} dégâts à {defender.name} !'
					)
				elif total_attack >= ac:
					damage = BattleSystem._roll_damage(attacker, defender, is_critical=False)
					defender.hp -= damage
					msg = (
						f'{attacker.name} (jet: {d20_roll} + {attack_bonus} = {total_attack}) '
						f'TOUCHE {defender.name} (CA: {ac}) pour {damage} dégâts !'
					)
				else:
					msg = (
						f'{attacker.name} (jet: {d20_roll} + {attack_bonus} = {total_attack}) '
						f'RATE {defender.name} (CA: {ac}) !'
					)
			uprint(msg)

	@staticmethod
	def perform_attack(attacker: Character, defender: Character) -> tuple[bool, int]:
		if defender.condition in [Condition.UNCONSCIOUS, Condition.PARALYZED]:
			return True, BattleSystem._roll_damage(attacker, defender, is_critical=True)
		d20_roll = randint(1, 20)
		if d20_roll == 1:
			return False, 0
		if d20_roll == 20:
			return True, BattleSystem._roll_damage(attacker, defender, is_critical=True)
		if (d20_roll + attacker.attack_bonus) >= defender.armor_class:
			return True, BattleSystem._roll_damage(attacker, defender, is_critical=False)
		return False, 0

	@staticmethod
	def _roll_damage(attacker: Character, defender: Character, is_critical: bool = False) -> int:
		base_damage = attacker.attack(defender)  # type: ignore[attr-defined]
		if attacker.is_blessed:
			d4 = randint(1, 4)
			base_damage += d4
			uprint(f'✨ Bless s\'applique ! +{d4} aux dégâts.')
		if is_critical:
			base_damage *= 2
		return max(1, base_damage)

	@staticmethod
	def combat(attacker: Character, defender: Character, party: List[Hero]) -> None:
		"""Decide between casting a spell or making a weapon attack.

		Strategy uses effect handler metadata (ai_role, ai_status, ai_priority) to
		rank and select spells. Handlers are resolved via registry.resolve(spell).

		Algorithm (high level):
		- collect usable spells and resolve their handlers
		- sort spells by handler.ai_priority (lower first)
		- consider each spell in order and test applicability based on ai_role:
		  - heal: if any ally below threshold
		  - buff: if not all allies have ai_status
		  - control: if target lacks ai_status
		  - smite: always applicable (adds effect to target)
		  - damage: fallback when other roles not applicable
		- if no spell chosen, perform melee attack
		"""
		from combat.effects import registry

		# Only spellcasters (Hero) consider spells
		if isinstance(attacker, Hero) and attacker.spells:
			usable = [s for s in attacker.spells if attacker.can_cast_spell(s)]
			if usable:
				# pair spells with their handlers
				pairs = [(s, registry.resolve(s)) for s in usable]
				# sort by priority
				pairs.sort(key=lambda sv: getattr(sv[1], 'ai_priority', 50))

				# utility predicates
				allies = [a for a in party if a.hp > 0]
				heal_threshold = 0.9

				for spell, handler in pairs:
					role = getattr(handler, 'ai_role', 'other')
					status = getattr(handler, 'ai_status', '')
					# Heal if an ally is below threshold
					if role == 'heal':
						vulnerable = [a for a in allies if a.hp / a.max_hp <= heal_threshold]
						if vulnerable:
							target = min(vulnerable, key=lambda a: a.hp)
							attacker.cast_spell(spell, [target])
							return
					# Buff if not everyone has the status
					if role == 'buff':
						if not all(getattr(a, 'is_blessed', False) for a in allies):
							attacker.cast_spell(spell, allies)
							return
					# Control (condition) if defender lacks status.
					# If the handler role indicates a control/debuff, target the defender;
					# otherwise (buffs like shield) apply to allies who lack the status.
					if role == 'control' or status:
						if status:
							if role == 'control':
								if not defender.has_effect(status):
									attacker.cast_spell(spell, [defender])
									return
							else:
								# treat as a positive status (buff/shield) and apply to allies missing it
								targets_missing = [a for a in allies if not a.has_effect(status)]
								if targets_missing:
									attacker.cast_spell(spell, targets_missing)
									return
						# fall through if nothing applicable
					# Smite is applied to target (adds effect for next hit)
					if role == 'smite':
						attacker.cast_spell(spell, [defender])
						return
					# Damage fallback
					if role == 'damage' or 'damage' in spell.effect:
						attacker.cast_spell(spell, [defender])
						return
					# Shield
					if role == 'shield':
						target = min(party, key=lambda c: c.hp / c.armor_class)
						attacker.cast_spell(spell, [target])
						return

		# No spell chosen or cannot cast: melee attack
		BattleSystem.melee_attack(attacker, [defender])
