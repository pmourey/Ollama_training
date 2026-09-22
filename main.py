# This is a sample Python script.
from __future__ import annotations

import json
import os
from copy import copy
from dataclasses import dataclass, field
from enum import Enum
from random import randint, choice, sample
from typing import List, Dict, Any, Optional


class ClassType(Enum):
	WIZARD = 'Wizard'
	FIGHTER = 'Fighter'
	RANGER = 'Ranger'
	ROGUE = 'Rogue'
	CLERIC = 'Cleric'
	BARD = 'Bard'
	DRUID = 'Druid'
	SORCERER = 'Sorcerer'
	PALADIN = 'Paladin'


class RaceType(Enum):
	HUMAN = 'Human'
	DWARF = 'Dwarf'
	ELF = 'Elf'
	HOBBIT = 'Hobbit'


@dataclass
class Armor:
	name: str
	bonus: int


@dataclass
class Weapon:
	name: str
	damage_dice: DamageDice

	def __repr__(self):
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


@dataclass
class Abilities:
	"""Character abilities that affect combat and spellcasting"""
	strength: int = 10
	intelligence: int = 10
	dexterity: int = 10
	wisdom: int = 10
	charisma: int = 10
	constitution: int = 10

	def __post_init__(self):
		# Ensure abilities are within valid range (3-20)
		self.strength = max(3, min(20, self.strength))
		self.intelligence = max(3, min(20, self.intelligence))
		self.dexterity = max(3, min(20, self.dexterity))
		self.wisdom = max(3, min(20, self.wisdom))
		self.charisma = max(3, min(20, self.charisma))
		self.constitution = max(3, min(20, self.constitution))

	@property
	def str_mod(self) -> int:
		"""Strength modifier for attacks and damage"""
		return (self.strength - 10) // 2

	@property
	def int_mod(self) -> int:
		"""Intelligence modifier for spellcasting"""
		return (self.intelligence - 10) // 2

	@property
	def dex_mod(self) -> int:
		"""Dexterity modifier for armor class and attacks"""
		return (self.dexterity - 10) // 2

	@property
	def wis_mod(self) -> int:
		"""Wisdom modifier for saving throws and spellcasting"""
		return (self.wisdom - 10) // 2

	@property
	def con_mod(self) -> int:
		"""Constitution modifier for hit points and saving throws"""
		return (self.constitution - 10) // 2

	@property
	def cha_mod(self) -> int:
		"""Constitution modifier for hit points and saving throws"""
		return (self.charisma - 10) // 2

@dataclass
class Spell:
	"""A spell that can be cast by spellcasters"""
	name: str
	class_type: ClassType
	level: int
	damage_dice: Optional[DamageDice]
	effect: str  # e.g., "fire damage", "heal"
	dc_type: str
	dc_success: bool
	description: str

	def __eq__(self, other):
		return self.name == other.name

	@property
	def value(self):
		dice = self.damage_dice
		# Calcule la valeur moyenne d'un dé (ex: pour un d6, (1 + 6) / 2 = 3.5)
		average_roll = (1 + dice.roll_dice) / 2

		return (dice.num_dice * average_roll) + dice.bonus



@dataclass
class Race:
	type: RaceType

	@property
	def str_mod(self):
		return 2 if self.type == RaceType.DWARF else 0

	@property
	def int_mod(self):
		return 2 if self.type == RaceType.HUMAN else 0


class Condition(Enum):
	# Les 15 conditions officielles de D&D 5e
	OK = 'ok'
	BLINDED = "blinded"
	DEAFENED = "deafened"
	RESTRAINED = "restrained"
	GRAPPLED = "grappled"
	PRONE = "prone"
	CHARMED = "charmed"
	FRIGHTENED = "frightened"
	INCAPACITATED = "incapacitated"
	PARALYZED = "paralyzed"
	PETRIFIED = "petrified"
	POISONED = "poisoned"
	STUNNED = "stunned"
	UNCONSCIOUS = "unconscious"
	INVISIBLE = "invisible"
	EXHAUSTION = "exhaustion"


@dataclass
class Character:
	id: int
	name: str
	level: int
	hp: int
	max_hp: int
	gold: int
	xp: int
	condition: Condition
	is_blessed: bool = False
	abilities: Abilities = field(default_factory=Abilities)

	@property
	def is_dead(self) -> bool:
		"""Un personnage est mort si ses HP tombent à 0 (version simplifiée)."""
		return self.hp <= 0

	@property
	def status(self):
		return f"{self.name} HP: {self.hp}/{self.max_hp}"

	@property
	def str(self):
		return self.abilities.strength

	@property
	def int(self):
		return self.abilities.intelligence

	@property
	def dex(self):
		return self.abilities.dexterity

	@property
	def con(self):
		return self.abilities.constitution

	@property
	def wis(self):
		return self.abilities.wisdom

	@property
	def cha(self):
		return self.abilities.charisma

	@property
	def armor_class(self) -> int:
		"""Classe d'armure par défaut (sans armure)"""
		return 10 + self.abilities.dex_mod

	@property
	def attack_bonus(self) -> int:
		"""Bonus d'attaque de base (Maîtrise + Force par défaut)"""
		proficiency_bonus = 2 + ((self.level - 1) // 4)
		return self.abilities.str_mod + proficiency_bonus

	def saving_throw(self, dc_type: str, dc: int) -> bool:
		"""Perform a saving throw against a spell or effect"""
		# Simple saving throw based on wisdom modifier
		roll = randint(1, 20)
		modifiers = {'str': self.abilities.str_mod, 'int': self.abilities.int_mod, 'wis': self.abilities.wis_mod, 'dex': self.abilities.dex_mod, 'con': self.abilities.con_mod}
		return roll + modifiers[dc_type] >= dc


class Hero(Character):
	"""Hero character combining Character dataclass with SpellCaster mixin"""

	def __init__(self, id: int, name: str, level: int, hp: int, max_hp: int, gold: int, xp: int, *, class_type: ClassType, race: Race, armor: Armor, weapon: Weapon, shield: Shield, inventory: List[Equipment] | None = None, abilities: Abilities | None = None, spellcasting_ability='', spells = None, max_spell_slots = None, current_spell_slots = None):
		# Initialize dataclass part
		if abilities is None:
			abilities = Abilities()
		Character.__init__(self, id=id, name=name, level=level, hp=hp, max_hp=max_hp, gold=gold, xp=xp, condition=Condition.OK, abilities=abilities)

		# Hero-specific attributes
		self.class_type: ClassType = class_type
		self.spellcasting_ability = spellcasting_ability
		self.race: Race = race
		self.armor: Armor = armor
		self.weapon: Weapon = weapon
		self.shield: Shield = shield
		self.inventory: List[Equipment] = inventory or []
		self.spells: List[Spell] = spells or []
		self.max_spell_slots: list[int] = max_spell_slots or [0] * 10
		self.current_spell_slots: list[int] = current_spell_slots or [0] * 10

	def can_cast_spell(self, spell: Spell) -> bool:
		"""Check if the spellcaster can cast a spell of given level"""
		return self.current_spell_slots[spell.level - 1] > 0

	def cast_spell(self, spell: Spell, targets: list[Character]):
		"""Cast a spell, reduce slots, and return the BattleSystem message.
		Delegates effect resolution to BattleSystem.resolve_spell_effect which also updates target HP."""
		if self.current_spell_slots[spell.level - 1] == 0:
			print(f"[Spell] {self.name} cannot cast {spell.name} (insufficient slots)!")

		# Reduce spell slots
		self.current_spell_slots[spell.level - 1] -= 1
		spells_cast[spell.level - 1][spell.name] += 1
		BattleSystem.spells_inc()

		# Use BattleSystem to resolve effect (it will apply HP changes) and return its message
		BattleSystem.resolve_spell_effect(self, targets, spell)


	@property
	def dc_value(self):
		# TODO Your Spell Save DC = 8 + your Spellcasting Ability modifier + your Proficiency Bonus + any Special Modifiers (???)
		def prof_bonus_char(x):
			return x // 4 + 1

		modifiers = {'str': self.abilities.str_mod, 'int': self.abilities.int_mod, 'wis': self.abilities.wis_mod, 'dex': self.abilities.dex_mod, 'con': self.abilities.con_mod}
		spell_casting_ability_modifier: int = modifiers.get(self.spellcasting_ability, 0)
		return 8 + spell_casting_ability_modifier + prof_bonus_char(self.level)

	@property
	def thac0(self) -> int:
		"""Calcule le THAC0 de base selon le niveau et la classe (Règles AD&D 2e)."""
		# 1. Groupe des Guerriers (Fighter, Ranger, Paladin) -> -1 par niveau
		if self.class_type in [ClassType.FIGHTER, ClassType.RANGER, ClassType.PALADIN]:
			result = max(1, 20 - (self.level - 1))

		# 2. Groupe des Prêtres (Cleric, Druid) -> -2 tous les 3 niveaux
		elif self.class_type in [ClassType.CLERIC, ClassType.DRUID]:
			result = max(1, 20 - ((self.level - 1) // 3) * 2)

		# 3. Groupe des Roublards (Rogue/Voleur, Bard) -> -1 tous les 2 niveaux
		elif self.class_type in [ClassType.ROGUE, ClassType.BARD]:
			result = max(1, 20 - (self.level - 1) // 2)

		# 4. Groupe des Magiciens (Wizard/Mage, Sorcerer*) -> -1 tous les 3 niveaux
		# *Note : Le Sorcerer n'existait pas en AD&D 2e pur, mais suit le groupe Magicien
		elif self.class_type in [ClassType.WIZARD, ClassType.SORCERER]:
			result = max(1, 20 - (self.level - 1) // 3)
		else:
			result = 20
		return result - self.abilities.str_mod - self.race.str_mod

	@property
	def armor_class(self) -> int:
		"""Calcule la CA du Héros selon son armure, son bouclier et sa Dextérité."""
		ac_base = 10
		armor_bonus = self.armor.bonus if hasattr(self, 'armor') else 0
		shield_bonus = self.shield.bonus if hasattr(self, 'shield') else 0
		dex_mod = self.abilities.dex_mod

		armor_name = self.armor.name.lower() if hasattr(self, 'armor') else ""

		if "chainmail" in armor_name or "plate" in armor_name:  # Armure lourde
			return 10 + armor_bonus + shield_bonus
		elif "hide" in armor_name or "scale" in armor_name:  # Armure intermédiaire (Max Dex +2)
			return ac_base + armor_bonus + min(2, dex_mod) + shield_bonus
		else:  # Armure légère / Tissu
			return ac_base + armor_bonus + dex_mod + shield_bonus

	@property
	def attack_bonus(self) -> int:
		"""Calcule le bonus d'attaque du Héros selon sa classe."""
		proficiency_bonus = 2 + ((self.level - 1) // 4)

		if self.class_type in [ClassType.RANGER, ClassType.ROGUE]:
			return self.abilities.dex_mod + proficiency_bonus
		elif self.class_type == ClassType.WIZARD:
			return self.abilities.int_mod + proficiency_bonus
		else:
			return self.abilities.str_mod + proficiency_bonus

	def attack(self, target: Character) -> int:
		"""Perform an attack and return damage dealt"""
		# Roll damage
		damage = self.weapon.damage_dice.roll

		# Add ability modifiers
		if self.class_type == ClassType.FIGHTER:
			damage += self.abilities.str_mod
		elif self.class_type == ClassType.RANGER or self.class_type == ClassType.ROGUE:
			damage += self.abilities.dex_mod
		elif self.class_type == ClassType.WIZARD:
			damage += self.abilities.int_mod

		return damage


	def take_damage(self, damage: int) -> int:
		"""Apply damage to character and return actual damage taken"""
		# Calculate damage reduction from armor and shield
		armor_bonus = self.armor.bonus if hasattr(self, 'armor') else 0
		shield_bonus = self.shield.bonus if hasattr(self, 'shield') else 0
		total_reduction = armor_bonus + shield_bonus

		actual_damage = max(1, damage - total_reduction)
		self.hp -= actual_damage

		return actual_damage

	def get_initiative(self) -> int:
		"""Calculate initiative roll for combat order"""
		return randint(1, 20) + self.abilities.dex_mod


@dataclass
class DamageDice:
	num_dice: int
	roll_dice: int
	bonus: int = 0

	@property
	def roll(self):
		return sum(randint(1, self.roll_dice) for _ in range(self.num_dice)) + self.bonus

	def __repr__(self):
		bonus = f'+{self.bonus}' if self.bonus else ''
		return f'{self.num_dice}d{self.roll_dice}{bonus}'

@dataclass
class MonsterType:
	name: str
	hit_dice: DamageDice
	ac: int
	damage_dice: DamageDice
	# level: int = 1  # Monster level for saving throws
	spellcasting: bool = False

	@property
	def level(self):
		return self.hit_dice.num_dice

	@property
	def damage(self):
		return self.damage_dice.roll


class Monster(Character):
	def __init__(self, id: int, name: str, level: int, hp: int, max_hp: int, gold: int, xp: int, *, type: MonsterType, ac: int, damage: int, inventory: List[Equipment] | None = None, abilities: Abilities | None = None):
		if abilities is None:
			abilities = Abilities()
		Character.__init__(self, id=id, name=name, level=level, hp=hp, max_hp=max_hp, gold=gold, xp=xp, condition=Condition.OK, abilities=abilities)
		self.type: MonsterType = type
		self.ac: int = ac
		self.damage: int = damage
		self.inventory: List[Equipment] = inventory or []

	@property
	def armor_class(self) -> int:
		"""Le monstre utilise sa CA native."""
		return self.ac

	@property
	def attack_bonus(self) -> int:
		"""Bonus d'attaque du monstre (Maîtrise + Force)."""
		proficiency_bonus = 2 + ((self.level - 1) // 4)
		return self.abilities.str_mod + proficiency_bonus

	def attack(self, target: Character) -> int:
		"""Perform an attack and return damage dealt"""
		# Calculate base damage
		damage = self.type.damage_dice.roll

		# Add ability modifiers (monster's strength modifier)
		damage += self.abilities.str_mod

		# Apply target's armor
		armor_bonus = target.armor.bonus if hasattr(target, 'armor') else 0
		damage_dealt = max(1, damage - armor_bonus)

		return damage_dealt

	def take_damage(self, damage: int) -> int:
		"""Apply damage to monster and return actual damage taken"""
		# Calculate damage reduction from armor
		armor_bonus = self.armor.bonus if hasattr(self, 'armor') else 0
		actual_damage = max(1, damage - armor_bonus)
		self.hp -= actual_damage

		return actual_damage

	def get_initiative(self) -> int:
		"""Calculate initiative roll for combat order"""
		return randint(1, 20) + self.abilities.dex_mod


class SpellLoader:
	"""Handles loading spells from JSON files"""

	@staticmethod
	def load_spells_from_file(filename: str) -> List[Spell]:
		"""Load spells from a JSON file"""
		try:
			with open(filename, 'r') as f:
				data = json.load(f)

			spells = []
			for class_dict in data:
				class_str = class_dict.get('class')
				for spell_dict in class_dict.get('spells'):
					dc = spell_dict.get('dc', None)
					dc_type = ''
					dc_success = False
					if dc:
						dc_type = dc.get('dc_type')
						dc_success = dc.get('dc_success')
					dd = spell_dict.get('damage_dice', {})
					damage_dice = DamageDice(num_dice=dd['num_dice'], roll_dice=dd['roll_dice'], bonus=dd['bonus']) if dd else None
					spell = Spell(name=spell_dict['name'], class_type=ClassType(class_str), level=spell_dict['level'], damage_dice=damage_dice, effect=spell_dict['effect'], dc_type=dc_type, dc_success=dc_success, description=spell_dict.get('description', ''))
					spells.append(spell)

			return spells

		except FileNotFoundError:
			print(f"Warning: Spell file {filename} not found.")
			return []
		except json.JSONDecodeError:
			print(f"Warning: Invalid JSON in spell file {filename}.")
			return []


class MonsterTypeLoader:
	"""Handles loading monster types from JSON files"""

	@staticmethod
	def load_monster_types_from_file(filename: str) -> List[MonsterType]:
		"""Load monster types from a JSON file"""
		try:
			with open(filename, 'r') as f:
				monster_data = json.load(f)

			monster_types = []
			for monster_dict in monster_data:
				monster_type = MonsterType(name=monster_dict['name'], hit_dice=DamageDice(num_dice=monster_dict['hit_dice']['num_dice'], roll_dice=monster_dict['hit_dice']['roll_dice'], bonus=monster_dict['hit_dice'].get('bonus', 0)), ac=monster_dict['ac'], damage_dice=DamageDice(num_dice=monster_dict['damage_dice']['num_dice'], roll_dice=monster_dict['damage_dice']['roll_dice'], bonus=monster_dict['damage_dice'].get('bonus', 0)), spellcasting=monster_dict.get('spellcasting', False))
				monster_types.append(monster_type)

			return monster_types
		except FileNotFoundError:
			print(f"Warning: Monster type file {filename} not found.")
			return []
		except json.JSONDecodeError:
			print(f"Warning: Invalid JSON in monster type file {filename}.")
			return []


@dataclass
class Combatant:
	"""Wrapper for characters that can participate in combat"""
	character: Character
	initiative: int

	def __lt__(self, other):
		return self.initiative < other.initiative


class BattleSystem:
	"""Handles battle logic between heroes and monsters"""
	spells_count: int = 0

	@classmethod
	def spells_inc(cls):
		"""Méthode de classe (statique) pour modifier la variable."""
		cls.spells_count += 1

	@staticmethod
	def calculate_hit_chance(attacker: Character, defender: Character) -> float:
		"""Calcule la probabilité théorique de toucher."""
		if hasattr(defender, 'condition') and defender.condition in [Condition.UNCONSCIOUS, Condition.PARALYZED]:
			return 1.0

		ac = defender.armor_class
		attack_bonus = attacker.attack_bonus
		needed_roll = ac - attack_bonus

		if needed_roll <= 1:
			faces_that_hit = 19
		elif needed_roll >= 20:
			faces_that_hit = 1
		else:
			faces_that_hit = 20 - needed_roll + 1

		return faces_that_hit / 20.0

	@staticmethod
	def resolve_spell_effect(caster: Hero, targets: list[Character], spell: Spell):
		"""Resolve the effect of a spell on the targets"""
		for target in targets:
			if spell.effect == "heal":
				# Healing spell
				for target in targets:
					heal_amount = spell.damage_dice.roll
					target.hp = min(target.max_hp, target.hp + heal_amount)
					msg = f"[Spell] {caster.name} heals {target.name} for {heal_amount} HP!"

			elif spell.effect == "buff":
				# Logique du sort Bless
				target.is_blessed = True
				msg =  f"[Spell] {caster.name} bless {target.name}!"

			elif spell.effect in ["fire damage", "lightning damage", "force damage", "cold damage"]:
				# Damage spell
				damage = spell.damage_dice.roll

				# Check if target makes saving throw (any character with saving_throw)
				if spell.dc_type and target.saving_throw(spell.dc_type, caster.dc_value):
					hp_loss = max(1, damage // 2) if spell.dc_success == 'half' else 0
					if hp_loss:
						target.hp -= hp_loss
						return f"[Spell] {target.name} saves against {spell.name} and takes half damage ({hp_loss} HP)!"
					else:
						return f"[Spell] {target.name} saves against {spell.name} and takes no damage!"

				else:
					target.hp -= damage
					msg =  f"[Spell] {caster.name} casts {spell.name} and deals {damage} damage to {target.name}!"

			elif spell.effect == "sleep":
				# Sleep spell - requires saving throw
				# if hasattr(target, 'saving_throw') and target.saving_throw(spell.dc_type, caster.dc_value):
				# 	return f"[Spell] {target.name} saves against {spell.name} and remains awake!"
				# else:
				target.condition = Condition.UNCONSCIOUS
				msg =  f"[Spell] {target.name} falls asleep due to {spell.name}!"

			else:
				msg = f"[Spell] {caster.name} casts {spell.name} on {target.name}!"

			uprint(msg)

	@staticmethod
	def melee_attack(attacker: Character, defenders: list[Character]):
		"""Résout une attaque en utilisant un jet de 1d20 et gère les échecs critiques."""
		for defender in defenders:
			# 1. Gestion des cibles sans défense
			if hasattr(defender, 'condition') and defender.condition in [Condition.UNCONSCIOUS, Condition.PARALYZED]:
				damage = BattleSystem._roll_damage(attacker, defender, is_critical=True)
				defender.hp -= damage
				msg = f"[Weapon] {attacker.name} touche AUTOMATIQUEMENT {defender.name} (sans défense) pour un COUP CRITIQUE de {damage} dégâts !"

			else:
				# 2. Lancer du d20
				d20_roll = randint(1, 20)
				attack_bonus = attacker.attack_bonus
				total_attack = d20_roll + attack_bonus
				ac = defender.armor_class

				# --- GESTION DU 1 NATUREL (ÉCHEC CRITIQUE) ---
				if d20_roll == 1:
					# Calcul des dégâts de maladresse subis par l'attaquant (ex: 1d4 + son propre modificateur de Force/Dex)
					fumble_damage = randint(1, 4)
					attacker.hp -= fumble_damage

					# Liste d'actions spéciales de maladresse pour l'immersion
					fumble_actions = [f"glisse lamentablement en attaquant et s'entaille la jambe", f"frappe un mur de pierre par maladresse, faisant vibrer son arme douloureusement", f"perd l'équilibre sous l'élan de son coup et se cogne la tête"]
					chosen_action = choice(fumble_actions)

					status_msg = f"[Weapon] ❌ ÉCHEC CRITIQUE ! {attacker.name} fait un 1 naturel... Il {chosen_action} ! Il subit {fumble_damage} dégâts."
					if attacker.is_dead:
						status_msg += f" {attacker.name} s'est tué !"
					msg = status_msg

				# 3. Réussite Critique (20 naturel)
				elif d20_roll == 20:
					damage = BattleSystem._roll_damage(attacker, defender, is_critical=True)
					defender.hp -= damage
					msg = f"[Weapon] 🎯 COUP CRITIQUE ! {attacker.name} fait un 20 naturel et inflige {damage} dégâts à {defender.name} !"

				# 4. Jet normal contre Classe d'Armure (CA)
				else:
					if total_attack >= ac:
						damage = BattleSystem._roll_damage(attacker, defender, is_critical=False)
						defender.hp -= damage
						msg = f"{attacker.name} (jet: {d20_roll} + {attack_bonus} = {total_attack}) TOUCHE {defender.name} (CA: {ac}) pour {damage} dégâts !"
					else:
						msg = f"{attacker.name} (jet: {d20_roll} + {attack_bonus} = {total_attack}) RATE {defender.name} (CA: {ac}) !"

			uprint(msg)

	@staticmethod
	def perform_attack(attacker: Character, defender: Character) -> tuple[bool, int]:
		"""Exécute l'attaque en arrière-plan et renvoie (hit_success, damage_dealt)."""
		if hasattr(defender, 'condition') and defender.condition in [Condition.UNCONSCIOUS, Condition.PARALYZED]:
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
		"""Méthode interne pour calculer et appliquer les dégâts."""
		base_damage = attacker.attack(defender)

		if attacker.is_blessed:
			d4 = randint(1, 4)
			base_damage += d4
			uprint(f"✨ Bless s'applique ! +{d4} au jet d'attaque.")

		if is_critical:
			base_damage *= 2

		return max(1, base_damage)

	@staticmethod
	def combat(attacker: Character, defender: Character, party: List[Hero]):
		"""Execute a single combat round"""
		# Determine if attacker is a spellcaster et un personnage (Note: monstres ne lancent pas encore de sorts)
		if isinstance(attacker, Hero) and attacker.spells:
			# Filter spells to only those allowed for the class and affordable by slots
			usable_spells = [s for s in attacker.spells if attacker.can_cast_spell(s)]

			# Smart selection: prefer healing when any ally is below 40% HP and spell heals; else prefer highest-level damaging spell
			if usable_spells:
				# If attacker is allied party member, attempt to heal allies
				healing_spells = [s for s in usable_spells if s.effect == 'heal']
				allies_to_heal = [a for a in party if a.hp / a.max_hp <= 0.9]
				if healing_spells and allies_to_heal:
					spell = max(healing_spells, key=lambda x: x.level * x.value)
					low_ally = min(allies_to_heal, key=lambda a: a.hp)
					attacker.cast_spell(spell, [low_ally])
				else:
					""" 1. Utilitaires & Soutien (Buffs & Combat Modifiers) """
					buff_spells = [s for s in usable_spells if s.effect == 'buff']
					# shield (Bouclier) : Augmente temporairement l'Armure (ac) du lanceur ou d'un allié.
					shield_spells = [s for s in usable_spells if s.effect == 'shield']
					# disadvantage (Malus) : Force la cible à rater ou réduire son prochain dé de dégâts.
					disadvantage_spells = [s for s in usable_spells if s.effect == 'disadvantage']
					# smite (Châtiment) : Ajoute un bonus de dégâts directement indexé sur la prochaine attaque physique (Paladin).
					smite_spells = [s for s in usable_spells if s.effect == 'smite']
					# cleanse (Dissipation) : Retire un effet de statut négatif (sleep, blind, etc.) sur un allié.
					cleanse_spells = [s for s in usable_spells if s.effect == 'cleanse']
					""" 2. Altérations d'État & Contrôle (Crowd Control / Debuffs) """
					sleep_spells = [s for s in usable_spells if s.effect == 'sleep']
					# paralyze (Paralysie) : Empêche totalement la cible d'attaquer pendant son tour.
					paralyse_spells = [s for s in usable_spells if s.effect == 'paralyse']
					# blind (Aveuglement) : Réduit l'Armure (ac) ou donne un malus aux dés de dégâts de la cible.
					blind_spells = [s for s in usable_spells if s.effect == 'blind']
					# frighten (Effroi) : Diminue les chances de toucher ou la défense de la cible (Bard/Paladin).
					frighten_spells = [s for s in usable_spells if s.effect == 'frighten']
					# restrained (Entravé) : Réduit l'esquive ou l'initiative.
					restrained_spells = [s for s in usable_spells if s.effect == 'restrained']
					""" 3. Dégâts Élémentaires & Magiques (Damage Types: acid/poison/necrotic/radiant/radiant/thunder) """
					damage_spells = [s for s in usable_spells if 'damage' in s.effect]

					if buff_spells and not all(c.is_blessed for c in party):
						attacker.cast_spell(buff_spells[0], party)
					elif sleep_spells and not defender.condition.UNCONSCIOUS:
						attacker.cast_spell(sleep_spells[0], [defender])
					elif damage_spells:
						# otherwise pick highest-level damaging spell and best target
						spell = max(damage_spells, key=lambda x: x.level * x.value)
						# prefer target with highest hp among defenders (to finish big ones)
						attacker.cast_spell(spell, [defender])
					else:
						# Regular attack
						BattleSystem.melee_attack(attacker, [defender])
		else:
			# Regular attack
			BattleSystem.melee_attack(attacker, [defender])


def load_game_data():
	"""Load monster types, spells, classes, races, and equipment from JSON files"""
	monster_types = MonsterTypeLoader.load_monster_types_from_file("monsters.json")
	spells = SpellLoader.load_spells_from_file("spells.json")

	# Load classes
	classes = []
	if os.path.exists('classes.json'):
		try:
			with open('classes.json', 'r') as f:
				classes = json.load(f)
		except Exception:
			print('Warning: failed to load classes.json')

	# Load races
	races = []
	if os.path.exists('races.json'):
		try:
			with open('races.json', 'r') as f:
				races = json.load(f)
		except Exception:
			print('Warning: failed to load races.json')

	# Load weapons
	weapons = []
	if os.path.exists('weapons.json'):
		try:
			with open('weapons.json', 'r') as f:
				weapons = json.load(f)
		except Exception:
			print('Warning: failed to load weapons.json')

	# Load armors
	armors = []
	if os.path.exists('armors.json'):
		try:
			with open('armors.json', 'r') as f:
				armors = json.load(f)
		except Exception:
			print('Warning: failed to load armors.json')

	# Load shields
	shields = []
	if os.path.exists('shields.json'):
		try:
			with open('shields.json', 'r') as f:
				shields = json.load(f)
		except Exception:
			print('Warning: failed to load shields.json')

	# Load heroes
	heroes_data = []
	if os.path.exists('heroes.json'):
		try:
			with open('heroes.json', 'r') as f:
				heroes_data = json.load(f)
		except Exception:
			print('Warning: failed to load heroes.json')

	# Load spell categories (map class -> allowed spell effects)
	spell_categories = {}
	if os.path.exists('spell_categories.json'):
		try:
			with open('spell_categories.json', 'r') as f:
				spell_categories = json.load(f)
		except Exception:
			print('Warning: failed to load spell_categories.json')

	return monster_types, spells, classes, races, weapons, armors, shields, heroes_data, spell_categories


def build_party_from_heroes(heroes_data, spells, classes, races, weapons, armors, shields, spell_categories, party_size=5):
	from random import sample
	if not heroes_data:
		return []
	num = min(party_size, len(heroes_data))
	melee_chars = [char_dict for char_dict in heroes_data if char_dict['class'] in ('Fighter', 'Paladin', 'Ranger', 'Rogue')]
	spellcaster_chars = [char_dict for char_dict in heroes_data if char_dict not in melee_chars][:party_size // 2]
	selection = sample(melee_chars, party_size // 2) + sample(spellcaster_chars, party_size // 2)
	party = []
	for h in selection:
		class_str = h.get('class', '').title()
		cls = getattr(ClassType, class_str.upper(), None)

		# map race safely
		race_name = h.get('race', '')
		race = None
		try:
			race = Race(type=RaceType[race_name.upper()])
		except Exception:
			race = Race(type=RaceType.HUMAN)

		# abilities
		ab = h.get('abilities', {})
		abilities = Abilities(**{k: ab.get(k, 10) for k in ['strength', 'intelligence', 'dexterity', 'wisdom', 'charisma', 'constitution']})

		damage = next((w['damage'] for w in weapons if w['name'] == h.get('weapon')), 1)
		weapon = Weapon(name=h.get('weapon', 'Fists'), damage_dice=DamageDice(1, damage))
		armor = Armor(name=h.get('armor', 'Cloth'), bonus=next((a['bonus'] for a in armors if a['name'] == h.get('armor')), 0))
		shield = Shield(name=h.get('shield', 'None'), bonus=next((s['bonus'] for s in shields if s['name'] == h.get('shield')), 0))

		# determine spell slots
		spellcasting_ability = [c.get('spellcasting_ability', '') for c in classes if c.get('name').lower() == class_str.lower()][0]
		hero = Hero(id=h.get('id', 0), name=h.get('name', 'Hero'), level=h.get('level', 1), hp=h.get('hp', 10), max_hp=h.get('max_hp', 10),
					gold=h.get('gold', 0), xp=h.get('xp', 0), class_type=cls or ClassType.FIGHTER, race=race, armor=armor, weapon=weapon, shield=shield,
					abilities=abilities, spellcasting_ability=spellcasting_ability)
		if spellcasting_ability:
			hero.current_spell_slots = [0] * 10
			hero.max_spell_slots = [0] * 10
			allowed_spells = [s for s in spells if s.class_type == ClassType(class_str) and s.level == 1]
			hero.spells = sample(allowed_spells, min(randint(1, 2), len(allowed_spells)))
			base_slots = [c.get('base_spell_slots', 0) for c in classes if c.get('name').lower() == class_str.lower()]
			hero.current_spell_slots[0] = copy(base_slots[0])
			hero.max_spell_slots[0] = copy(base_slots[0])

		# print(h.get('name'), class_str, allowed_spells)
		party.append(hero)
	return party


def create_sample_monsters(monster_types: List[MonsterType], count: int = 3):
	"""Create sample monsters of different types"""
	monsters = []
	for i in range(count):
		# Select a random monster type
		monster_type = choice(monster_types)

		# Create monster with appropriate stats
		hp = monster_type.hit_dice.roll
		monster = Monster(id=i + 1, name=f"{monster_type.name}", level=monster_type.level, hp=hp, max_hp=hp, gold=randint(1, 10), xp=randint(5, 15) * (monster_type.level + 1), abilities=Abilities(strength=8 + monster_type.level, intelligence=8, dexterity=10 + monster_type.level, wisdom=10, charisma=10 + monster_type.level, constitution=10 + monster_type.level), type=monster_type, ac=monster_type.ac, damage=monster_type.damage)
		monsters.append(monster)

	return monsters


def calculate_initiative(party, monsters):
	# Create combatants list with initiative
	combatants = []

	# Add heroes to combatants
	for hero in party:
		initiative = hero.get_initiative()
		combatants.append(Combatant(hero, initiative))  # print(f"{hero.name} (Hero) - Initiative: {initiative}")

	# Add monsters to combatants
	for monster in monsters:
		initiative = monster.get_initiative()
		combatants.append(Combatant(monster, initiative))  # print(f"{monster.name} (Monster) - Initiative: {initiative}")

	# Sort combatants by initiative (highest first)
	combatants.sort(key=lambda c: c.initiative, reverse=True)
	return combatants


def party_stats_msg(party, num_combats, killed_monsters):
	# Display final stats
	print("=" * 100)
	print(f"STATS (Retour auberge tous les {BACK_TO_TOWN_FREQ} combats): {num_combats} victoires et {killed_monsters} monstres tués! {BattleSystem.spells_count} sorts lancés!")
	print("=" * 100)

	alive_chars = [c for c in party if c.hp > 0]
	print(f"Party Status: {len(alive_chars)}/{len(party)} ")
	if True or alive_chars:
		for hero in party:
			cls = getattr(hero, 'class_type', None)
			race = getattr(hero, 'race', None)
			cls_name = cls.value if isinstance(cls, Enum) else (cls if cls is not None else 'Unknown')
			race_name = 'Unknown'
			if isinstance(race, Race):
				if isinstance(race.type, Enum):
					race_name = race.type.value
				else:
					race_name = str(race.type)
			elif isinstance(getattr(hero, 'race', None), Enum):
				race_name = hero.race.value
			spell_slots = f', Spells slots: {hero.current_spell_slots}/{hero.max_spell_slots}' if hero.spells else ''
			# spell_slots = ''
			spells = '|'.join([f'{s.level}:{s.name}' for s in hero.spells])
			print(f"  {hero.name}: Lvl {hero.level} {cls_name} {race_name} (AC {hero.armor_class} - THACO {hero.thac0} - {hero.weapon}) "
			      f"- STR {hero.str} INT {hero.int} WIS {hero.wis} DEX {hero.dex} CON {hero.con} CHA {hero.cha} "
			      f"- HP {hero.hp}/{hero.max_hp} - {hero.condition.value.upper()}, XP {hero.xp}, {hero.gold} gp{spell_slots} - {spells}")
	else:
		print(f"All {len(party)} characters in party has died!")

def print_stats(killed_by_level, spells_cast):
	print("\nMonsters kill stats")
	for i, monsters in enumerate(killed_by_level):
		if monsters:
			print(f'Lvl {i+1}: {monsters}')
	print("\nSpells cast stats")
	for i, spells in enumerate(spells_cast):
		if spells:
			print(f'Lvl {i+1}: {spells}')

def monster_stats_msg(monsters):
	print("\nMonster Status:")
	for monster in monsters:
		print(f"  {monster.name} (Lvl {monster.level} - AC {monster.armor_class}): HP {monster.hp}/{monster.max_hp}")


def start_combat(party: List[Hero], monsters: List[Monster]) -> tuple[int, int]:
	"""Start a combat encounter using BattleSystem.combat_round for each action."""
	uprint("=" * 60)
	uprint("COMBAT BEGINS!")
	uprint("=" * 60)

	# # Display initial status
	# uprint("\nParty Status:")
	# for hero in party:
	# 	cls = getattr(hero, 'class_type', None)
	# 	race = getattr(hero, 'race', None)
	# 	cls_name = cls.value if isinstance(cls, Enum) else (cls if cls is not None else 'Unknown')
	# 	race_name = 'Unknown'
	# 	if isinstance(race, Race):
	# 		if isinstance(race.type, Enum):
	# 			race_name = race.type.value
	# 		else:
	# 			race_name = str(race.type)
	# 	elif isinstance(getattr(hero, 'race', None), Enum):
	# 		race_name = hero.race.value
	# 	uprint(f"  {hero.name}: {cls_name} {race_name} - HP {hero.hp}/{hero.max_hp}, XP {hero.xp}, Gold {hero.gold}")

	uprint("\nMonster Status:")
	for monster in monsters:
		uprint(f"  {monster.name}: HP {monster.hp}/{monster.max_hp}")

	# Combat loop
	round_num = 0
	total_xp = total_gp = 0
	while any(hero.hp > 0 for hero in party) and any(monster.hp > 0 for monster in monsters):
		round_num += 1
		for c in party:
			c.is_blessed = False
		uprint(f"\n--- ROUND {round_num} ---")

		alive_chars = [h for h in party if h.hp > 0]
		alive_monsters = [m for m in monsters if m.hp > 0]
		combatants = calculate_initiative(alive_chars, alive_monsters)

		# Process each combatant in initiative order
		for combatant in combatants:
			current_char = combatant.character

			# Find targets
			if isinstance(current_char, Hero):
				# Hero acts (spell or attack)
				alive_monsters = [m for m in monsters if m.hp > 0]
				if not alive_monsters:
					break
				target = max(monsters, key=lambda m: m.hp)
				# uprint(f"{current_char.name} acts against {target.name}!")

				# Use combat_round to handle spellcasting or normal attacks
				BattleSystem.combat(current_char, target, party)
				if target.is_dead:
					total_xp += target.xp
					total_gp += target.gold
					uprint(f"{target.name} is defeated!")
					alive_monsters.remove(target)
					# print(killed_by_level)
					killed_by_level[target.level - 1][target.name] += 1
					uprint(f"{combatant.character.name} gained {target.xp} XP and earned {target.gold} gp!")
			else:
				# Monster acts (spell or attack)
				if not alive_chars:
					break
				target = max(alive_chars, key=lambda m: m.hp)
				# uprint(f"{current_char.name} acts against {target.name}!")

				BattleSystem.combat(current_char, target, party)
				if target.is_dead:
					uprint(f"{target.name} is defeated!")
					alive_chars.remove(target)

			# Check if battle should end
			if not any(hero.hp > 0 for hero in party):
				uprint("All heroes have been defeated!")
				return 0, 0
			if not any(monster.hp > 0 for monster in monsters):
				uprint(f"*** VICTORY! *** Each member gained {total_xp} XP and earned {total_gp} gp")
				return total_xp, total_gp
		if not BATCH_MODE:
			input(f"End of round {round_num}. Press Enter to continue...")


def level_up(char, spells):
	char.level += 1
	hp_gained = randint(1, 10)
	char.max_hp += hp_gained
	char.hp += hp_gained
	max_spell_level = max(1, (min(20, char.level + 1) // 2))
	# print(max_spell_level)
	for i in range(max_spell_level):
		char.max_spell_slots[i] = min(char.max_spell_slots[i] + randint(1, 3), 9)
		char.current_spell_slots[i] = char.max_spell_slots[i]
	new_spells = [s for s in spells if s not in char.spells and s.level <= max_spell_level]
	if new_spells:
		# Application des règles selon la classe (Modèle standard 100% déterministe)
		if char.class_type == ClassType.WIZARD:
			# Le Wizard apprend toujours 2 sorts
			new_spells = sample(new_spells, min(2, len(new_spells)))

		elif char.class_type in [ClassType.SORCERER, ClassType.BARD, ClassType.RANGER]:
			# Ces classes apprennent généralement 1 sort par niveau
			new_spells = sample(new_spells, 1)
		if char.spells:
			char.spells += new_spells
		else:
			char.spells = new_spells

def uprint(msg: str = ''):
	if not BATCH_MODE:
		print(msg)


if __name__ == '__main__':
	# Load game data
	monster_types, spells, classes, races, weapons, armors, shields, heroes_data, spell_categories = load_game_data()
	# Build a random party from heroes_data
	party_size = 6
	party = build_party_from_heroes(heroes_data, spells, classes, races, weapons, armors, shields, spell_categories, party_size)

	BATCH_MODE = True
	end_game = False
	max_combats = 10000
	num_combats = 0
	max_monsters = 2
	killed_monsters = 0
	killed_by_level = [{m.name: 0 for m in monster_types if m.level == i + 1} for i in range(20)]
	spells_cast =  [{s.name: 0 for s in spells if s.level == i} for i in range(1, 10)]
	BACK_TO_TOWN_FREQ = 10
	party_stats_msg(party, num_combats, killed_monsters)
	while not end_game and num_combats < max_combats:
		for char in party:
			if char.xp // 500 >= char.level:
				allowed_spells = [s for s in spells if s.class_type == char.class_type]
				if char.level < 20:
					level_up(char, allowed_spells)
		num_combats += 1
		# Reposer et soigner le groupe (tous les 10 combats)
		if num_combats % BACK_TO_TOWN_FREQ == 0:
			for char in party:
				char.hp = char.max_hp
				for i in range(10):
					char.current_spell_slots[i] = char.max_spell_slots[i]
		party_level = sum([c.level for c in party]) / len(party)
		monster_types_selection = [m for m in monster_types if m.level <= party_level]
		monsters = create_sample_monsters(monster_types_selection, randint(1, max_monsters))
		total_xp, total_gp = start_combat(party, monsters)
		# Répartition des XP et Gold du combat sur personnages vivants
		alive_chars = [c for c in party if not c.is_dead]
		for char in alive_chars:
			char.xp += total_xp // len(alive_chars)
			char.gold += total_gp // len(alive_chars)
		# end_combat_msg(party, monsters)

		if all(c.is_dead for c in party):
			end_game = True
		# else:
		# 	msg = input("Voulez-vous continuer? (o/n)")
		# 	if msg in ('n', 'N'):
		# 		end_game = True
		killed_monsters += len(monsters)

	party_stats_msg(party, num_combats, killed_monsters)
	monster_stats_msg(monsters)
	print_stats(killed_by_level, spells_cast)
