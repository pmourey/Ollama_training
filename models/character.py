from __future__ import annotations

from dataclasses import dataclass, field
from random import randint
from typing import List

import game_state
from models.abilities import Abilities
from models.enums import ClassType, Condition
from models.equipment import (
	Armor, Equipment, Shield, Weapon,
	armor_from_item, shield_from_item, weapon_from_item,
)
from models.dice import DamageDice
from models.race import Race
from models.spell import Spell
from models.status import NEGATIVE_EFFECTS, ActiveEffect


@dataclass
class Character:
	id: int
	name: str
	level: int
	hp: int
	max_hp: int
	gold: int
	xp: int
	condition: Condition = Condition.OK
	is_blessed: bool = False
	abilities: Abilities = field(default_factory=Abilities)
	effects: list[ActiveEffect] = field(default_factory=list)

	@property
	def is_dead(self) -> bool:
		"""Un personnage est mort si ses HP tombent à 0 (version simplifiée)."""
		return self.hp <= 0

	@property
	def status(self) -> str:
		return f'{self.name} HP: {self.hp}/{self.max_hp}'

	@property
	def str(self) -> int:
		return self.abilities.strength

	@property
	def int(self) -> int:
		return self.abilities.intelligence

	@property
	def dex(self) -> int:
		return self.abilities.dexterity

	@property
	def con(self) -> int:
		return self.abilities.constitution

	@property
	def wis(self) -> int:
		return self.abilities.wisdom

	@property
	def cha(self) -> int:
		return self.abilities.charisma

	@property
	def armor_class(self) -> int:
		"""Classe d'armure par défaut (sans armure)."""
		return 10 + self.abilities.dex_mod

	@property
	def attack_bonus(self) -> int:
		"""Bonus d'attaque de base (Maîtrise + Force par défaut)."""
		proficiency_bonus = 2 + ((self.level - 1) // 4)
		return self.abilities.str_mod + proficiency_bonus + self.attack_modifier()

	def saving_throw(self, dc_type: str, dc: int) -> bool:
		roll = randint(1, 20)
		modifiers = {
			'str': self.abilities.str_mod,
			'int': self.abilities.int_mod,
			'wis': self.abilities.wis_mod,
			'dex': self.abilities.dex_mod,
			'con': self.abilities.con_mod,
			'cha': self.abilities.cha_mod
		}
		return roll + modifiers[dc_type] >= dc

	def add_effect(self, effect: ActiveEffect) -> None:
		self.effects = [current for current in self.effects if current.kind != effect.kind]
		self.effects.append(effect)
		self._sync_status()

	def has_effect(self, kind: str) -> bool:
		return self.get_effect(kind) is not None

	def get_effect(self, kind: str) -> ActiveEffect | None:
		for effect in self.effects:
			if effect.kind == kind:
				return effect
		return None

	def effect_magnitude(self, kind: str) -> int:
		effect = self.get_effect(kind)
		return effect.magnitude if effect else 0

	def consume_effect(self, kind: str) -> ActiveEffect | None:
		found: ActiveEffect | None = None
		kept: list[ActiveEffect] = []
		for effect in self.effects:
			if effect.kind == kind and found is None:
				found = effect
			else:
				kept.append(effect)
		self.effects = kept
		if found is not None:
			self._sync_status()
		return found

	def clear_effects(self) -> None:
		self.effects.clear()
		self._sync_status()

	def has_negative_effect(self) -> bool:
		return any(effect.kind in NEGATIVE_EFFECTS for effect in self.effects)

	def cleanse_negative(self) -> list[str]:
		removed = [effect.kind for effect in self.effects if effect.kind in NEGATIVE_EFFECTS]
		if not removed:
			return []
		self.effects = [effect for effect in self.effects if effect.kind not in NEGATIVE_EFFECTS]
		self._sync_status()
		return removed

	def tick_effects(self) -> list[str]:
		"""Avance les durées d'un round. Le round de lancement ne compte pas."""
		kept: list[ActiveEffect] = []
		expired: list[ActiveEffect] = []
		for effect in self.effects:
			if effect.turns is None:
				kept.append(effect)
				continue
			if effect.just_applied:
				effect.just_applied = False
				kept.append(effect)
				continue
			effect.turns -= 1
			if effect.turns <= 0:
				expired.append(effect)
			else:
				kept.append(effect)
		self.effects = kept
		if expired:
			self._sync_status()
		return [
			f'[Effect] {self.name} is no longer affected by {effect.spell_name or effect.kind}.'
			for effect in expired
		]

	def ac_modifiers(self) -> int:
		modifier = 0
		if self.has_effect('shield'):
			modifier += self.effect_magnitude('shield')
		if self.has_effect('foresight'):
			modifier += self.effect_magnitude('foresight')
		if self.has_effect('blind'):
			modifier -= 2
		if self.has_effect('restrained'):
			modifier -= 2
		return modifier

	def attack_modifier(self) -> int:
		modifier = 0
		if self.has_effect('blind'):
			modifier -= 2
		if self.has_effect('frighten'):
			modifier -= 2
		if self.has_effect('disadvantage'):
			modifier -= 2
		if self.has_effect('foresight'):
			modifier += self.effect_magnitude('foresight')
		return modifier

	def _sync_status(self) -> None:
		self.is_blessed = self.has_effect('bless')
		order = (
			('sleep', Condition.UNCONSCIOUS),
			('paralyze', Condition.PARALYZED),
			('restrained', Condition.RESTRAINED),
			('frighten', Condition.FRIGHTENED),
			('blind', Condition.BLINDED),
		)
		self.condition = Condition.OK
		for kind, condition in order:
			if self.has_effect(kind):
				self.condition = condition
				return

	def receive_damage(self, damage: int) -> str:
		"""Applique des dégâts. Death Ward retient la cible à 1 PV une fois."""
		amount = max(0, damage)
		if amount == 0:
			return ''
		if self.has_effect('death_ward') and self.hp > 0 and self.hp - amount <= 0:
			self.hp = 1
			ward = self.consume_effect('death_ward')
			source = ward.spell_name if ward else 'Death Ward'
			return f'{source} keeps {self.name} at 1 HP!'
		self.hp -= amount
		return ''

	def take_damage(self, damage: int) -> int:
		"""Applique les dégâts bruts (pas de réduction d'armure en 5e)."""
		before = self.hp
		self.receive_damage(damage)
		return max(0, before - self.hp)

	def get_initiative(self) -> int:
		roll = randint(1, 20) + self.abilities.dex_mod
		if self.has_effect('restrained'):
			roll -= 2
		return roll


@dataclass(kw_only=True)
class Hero(Character):
	"""Hero with class, race, equipment and spellcasting."""
	class_type: ClassType
	race: Race
	armor: Armor
	weapon: Weapon
	shield: Shield
	inventory: List[Equipment] = field(default_factory=list)
	spellcasting_ability: str = ''
	spells: List[Spell] = field(default_factory=list)
	max_spell_slots: list[int] = field(default_factory=lambda: [0] * 10)
	current_spell_slots: list[int] = field(default_factory=lambda: [0] * 10)

	# New attributes: class hit die, multi-attack count and battlefield position
	hit_dice: int = 8
	multi_attack: int = 1
	position: str = 'front'

	def can_cast_spell(self, spell: Spell) -> bool:
		return self.current_spell_slots[spell.level - 1] > 0

	def cast_spell(self, spell: Spell, targets: list[Character]) -> None:
		"""Cast a spell; delegates effect resolution to BattleSystem."""
		from combat.battle import BattleSystem

		if self.current_spell_slots[spell.level - 1] <= 0:
			game_state.uprint(f'[Spell] {self.name} cannot cast {spell.name} (insufficient slots)!')
			return

		self.current_spell_slots[spell.level - 1] -= 1
		level_idx = spell.level - 1
		while len(game_state.spells_cast) <= level_idx:
			game_state.spells_cast.append({})
		game_state.spells_cast[level_idx][spell.name] = game_state.spells_cast[level_idx].get(spell.name, 0) + 1
		BattleSystem.spells_inc()
		BattleSystem.resolve_spell_effect(self, targets, spell)

	# ------------------------------------------------------------ Equipment
	#
	# Design note: the inventory is a persistent record of every item a hero
	# has ever found (including items currently equipped). Equipping an item
	# from the inventory does NOT remove it from the list; it only updates
	# the corresponding weapon/armor/shield slot. This keeps the inventory
	# consistent with items shown/equipped at character creation (see
	# simulation.build_party_from_heroes) and lets the GUI freely re-equip
	# past gear. Use remove_from_inventory() to actually delete an item.
	def _find_inventory_index(self, item: dict) -> int | None:
		"""Locate an inventory item by identity first, then by equality."""
		for idx, it in enumerate(self.inventory):
			if it is item:
				return idx
		for idx, it in enumerate(self.inventory):
			if it == item:
				return idx
		return None

	def _is_equipped(self, item: dict) -> bool:
		item_type = item.get('type')
		name = item.get('name')
		if item_type == 'weapon':
			return self.weapon is not None and self.weapon.name == name
		if item_type == 'armor':
			return self.armor is not None and self.armor.name == name
		if item_type == 'shield':
			return self.shield is not None and self.shield.name == name
		return False

	def remove_from_inventory(self, item: dict) -> str:
		"""Delete an item from the inventory (used by the GUI 'Supprimer' action).

		If the removed item happens to be currently equipped, the corresponding
		slot is reset to its bare default so the hero is never left referencing
		a deleted item.
		"""
		idx = self._find_inventory_index(item)
		if idx is None:
			return f"Objet introuvable dans l'inventaire de {self.name}."
		removed = self.inventory.pop(idx)
		msg = f"{removed.get('name', 'Objet')} supprimé de l'inventaire de {self.name}."
		if self._is_equipped(removed):
			item_type = removed.get('type')
			if item_type == 'weapon':
				self.weapon = Weapon(name='Fists', damage_dice=DamageDice(1, 4))
			elif item_type == 'armor':
				self.armor = Armor(name='Cloth', bonus=0)
			elif item_type == 'shield':
				self.shield = Shield(name='None', bonus=0)
			msg += ' (déséquipé)'
		game_state.uprint(msg)
		return msg

	def equip_item(self, item: dict) -> str:
		"""Equip an inventory item, dispatching by its 'type' field."""
		item_type = item.get('type')
		if item_type == 'weapon':
			return self.equip_weapon(item)
		if item_type == 'armor':
			return self.equip_armor(item)
		if item_type == 'shield':
			return self.equip_shield(item)
		return f"{item.get('name', 'Objet')} ne peut pas être équipé."

	def equip_weapon(self, item: dict) -> str:
		new_weapon = weapon_from_item(item)
		self.weapon = new_weapon
		msg = f'{self.name} équipe {new_weapon.name}.'
		game_state.uprint(msg)
		return msg

	def equip_armor(self, item: dict) -> str:
		new_armor = armor_from_item(item)
		self.armor = new_armor
		msg = f'{self.name} équipe {new_armor.name}.'
		game_state.uprint(msg)
		return msg

	def equip_shield(self, item: dict) -> str:
		new_shield = shield_from_item(item)
		self.shield = new_shield
		msg = f'{self.name} équipe {new_shield.name}.'
		game_state.uprint(msg)
		return msg

	def unequip_weapon(self) -> str:
		old = self.weapon
		if old is None or old.name == 'Fists':
			return f'{self.name} ne porte aucune arme à retirer.'
		self.weapon = Weapon(name='Fists', damage_dice=DamageDice(1, 4))
		msg = f'{self.name} range {old.name}.'
		game_state.uprint(msg)
		return msg

	def unequip_armor(self) -> str:
		old = self.armor
		if old is None or old.name in ('Cloth', 'None'):
			return f'{self.name} ne porte aucune armure à retirer.'
		self.armor = Armor(name='Cloth', bonus=0)
		msg = f'{self.name} retire {old.name}.'
		game_state.uprint(msg)
		return msg

	def unequip_shield(self) -> str:
		old = self.shield
		if old is None or old.name == 'None':
			return f'{self.name} ne porte aucun bouclier à retirer.'
		self.shield = Shield(name='None', bonus=0)
		msg = f'{self.name} range {old.name}.'
		game_state.uprint(msg)
		return msg

	@property
	def dc_value(self) -> int:
		def prof_bonus_char(x: int) -> int:
			return x // 4 + 1

		modifiers = {
			'str': self.abilities.str_mod,
			'int': self.abilities.int_mod,
			'wis': self.abilities.wis_mod,
			'dex': self.abilities.dex_mod,
			'con': self.abilities.con_mod,
		}
		spell_mod = modifiers.get(self.spellcasting_ability, 0)
		return 8 + spell_mod + prof_bonus_char(self.level)

	@property
	def armor_class(self) -> int:
		"""CA 5e : 10 + armure + bouclier + Dex (plafonnée selon le type)."""
		armor_bonus = self.armor.bonus
		shield_bonus = self.shield.bonus
		dex_mod = self.abilities.dex_mod
		armor_name = self.armor.name.lower()

		if 'chainmail' in armor_name or 'plate' in armor_name:
			base = 10 + armor_bonus + shield_bonus
		elif 'hide' in armor_name or 'scale' in armor_name:
			base = 10 + armor_bonus + min(2, dex_mod) + shield_bonus
		else:
			base = 10 + armor_bonus + dex_mod + shield_bonus
		return base + self.ac_modifiers()

	@property
	def attack_bonus(self) -> int:
		"""Bonus d'attaque 5e : maîtrise + attribut selon la classe."""
		proficiency_bonus = 2 + ((self.level - 1) // 4)
		if self.class_type in [ClassType.RANGER, ClassType.ROGUE]:
			ability = self.abilities.dex_mod
		elif self.class_type == ClassType.WIZARD:
			ability = self.abilities.int_mod
		else:
			ability = self.abilities.str_mod
		return ability + proficiency_bonus + self.attack_modifier()

	def attack(self, target: Character) -> int:
		"""Jet de dégâts d'arme (la CA gère le toucher)."""
		damage = self.weapon.damage_dice.roll
		if self.class_type in [ClassType.RANGER, ClassType.ROGUE]:
			damage += self.abilities.dex_mod
		elif self.class_type == ClassType.WIZARD:
			damage += self.abilities.int_mod
		else:
			damage += self.abilities.str_mod
		return max(1, damage)
