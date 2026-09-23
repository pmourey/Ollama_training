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
		for target in targets:
			if spell.effect == 'heal':
				heal_amount = spell.damage_dice.roll if spell.damage_dice else 0
				target.hp = min(target.max_hp, target.hp + heal_amount)
				msg = f'[Spell] {caster.name} heals {target.name} for {heal_amount} HP!'
			elif spell.effect == 'buff':
				target.is_blessed = True
				msg = f'[Spell] {caster.name} bless {target.name}!'
			elif 'damage' in spell.effect:
				damage = spell.damage_dice.roll if spell.damage_dice else 0
				if spell.dc_type and target.saving_throw(spell.dc_type, caster.dc_value):
					if spell.dc_success == 'half':
						hp_loss = max(1, damage // 2)
						target.hp -= hp_loss
						msg = (
							f'[Spell] {target.name} saves against {spell.name} '
							f'and takes half damage ({hp_loss} HP)!'
						)
					else:
						msg = f'[Spell] {target.name} saves against {spell.name} and takes no damage!'
				else:
					target.hp -= damage
					msg = (
						f'[Spell] {caster.name} casts {spell.name} '
						f'and deals {damage} damage to {target.name}!'
					)
			elif spell.effect == 'sleep':
				target.condition = Condition.UNCONSCIOUS
				msg = f'[Spell] {target.name} falls asleep due to {spell.name}!'
			else:
				msg = f'[Spell] {caster.name} casts {spell.name} on {target.name}!'
			uprint(msg)

	@staticmethod
	def melee_attack(attacker: Character, defenders: list[Character]) -> None:
		for defender in defenders:
			if defender.condition in [Condition.UNCONSCIOUS, Condition.PARALYZED]:
				damage = BattleSystem._roll_damage(attacker, defender, is_critical=True)
				defender.hp -= damage
				msg = (
					f'[Weapon] {attacker.name} touche AUTOMATIQUEMENT {defender.name} '
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
						f'[Weapon] ❌ ÉCHEC CRITIQUE ! {attacker.name} fait un 1 naturel... '
						f'Il {action} ! Il subit {fumble_damage} dégâts.'
					)
					if attacker.is_dead:
						msg += f' {attacker.name} s\'est tué !'
				elif d20_roll == 20:
					damage = BattleSystem._roll_damage(attacker, defender, is_critical=True)
					defender.hp -= damage
					msg = (
						f'[Weapon] 🎯 COUP CRITIQUE ! {attacker.name} fait un 20 naturel '
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
		if isinstance(attacker, Hero) and attacker.spells:
			usable = [s for s in attacker.spells if attacker.can_cast_spell(s)]
			if usable:
				heals = [s for s in usable if s.effect == 'heal']
				allies = [a for a in party if a.hp / a.max_hp <= 0.9]
				if heals and allies:
					spell = max(heals, key=lambda x: x.level * x.value)
					attacker.cast_spell(spell, [min(allies, key=lambda a: a.hp)])
					return

				buffs = [s for s in usable if s.effect == 'buff']
				sleeps = [s for s in usable if s.effect == 'sleep']
				damages = [s for s in usable if 'damage' in s.effect]

				if buffs and not all(c.is_blessed for c in party):
					attacker.cast_spell(buffs[0], party)
					return
				if sleeps and defender.condition != Condition.UNCONSCIOUS:
					attacker.cast_spell(sleeps[0], [defender])
					return
				if damages:
					spell = max(damages, key=lambda x: x.level * x.value)
					attacker.cast_spell(spell, [defender])
					return

		BattleSystem.melee_attack(attacker, [defender])
