# This is a sample Python script.
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from random import randint, choice
from typing import List, Dict, Any


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
	damage: int


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
	agility: int = 10
	constitution: int = 10

	def __post_init__(self):
		# Ensure abilities are within valid range (3-20)
		self.strength = max(3, min(20, self.strength))
		self.intelligence = max(3, min(20, self.intelligence))
		self.dexterity = max(3, min(20, self.dexterity))
		self.wisdom = max(3, min(20, self.wisdom))
		self.agility = max(3, min(20, self.agility))
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


@dataclass
class Spell:
	"""A spell that can be cast by spellcasters"""
	name: str
	level: int
	damage_dice: Dict[str, int]  # e.g., {"num_dice": 1, "roll_dice": 6}
	effect: str  # e.g., "fire damage", "heal"
	save_dc: int  # Difficulty class for saving throws
	description: str


class SpellCaster:
	"""Mixin class for characters that can cast spells"""

	def __init__(self, spells=None, max_spell_slots=None, current_spell_slots=None):
		self.spells: List[Spell] = spells or []
		self.max_spell_slots: list[int] = max_spell_slots or [0] * 10
		self.current_spell_slots: list[int] = current_spell_slots or [0] * 10

	def can_cast_spell(self, spell: Spell) -> bool:
		"""Check if the spellcaster can cast a spell of given level"""
		return self.current_spell_slots[spell.level - 1] > 0

	def cast_spell(self, spell: Spell, target: Character) -> str:
		"""Cast a spell, reduce slots, and return the BattleSystem message.
		Delegates effect resolution to BattleSystem.resolve_spell_effect which also updates target HP."""
		if self.current_spell_slots[spell.level - 1] == 0:
			return f"[Spell] {self.name} cannot cast {spell.name} (insufficient slots)!"

		# Reduce spell slots
		self.current_spell_slots[spell.level - 1] -= 1
		spells_cast[spell.name] += 1
		BattleSystem.spells_inc()

		# Use BattleSystem to resolve effect (it will apply HP changes) and return its message
		return BattleSystem.resolve_spell_effect(self, target, spell)


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
	def armor_class(self) -> int:
		"""Classe d'armure par défaut (sans armure)"""
		return 10 + self.abilities.dex_mod

	@property
	def attack_bonus(self) -> int:
		"""Bonus d'attaque de base (Maîtrise + Force par défaut)"""
		proficiency_bonus = 2 + ((self.level - 1) // 4)
		return self.abilities.str_mod + proficiency_bonus


class Hero(SpellCaster, Character):
	"""Hero character combining Character dataclass with SpellCaster mixin"""

	def __init__(self, id: int, name: str, level: int, hp: int, max_hp: int, gold: int, xp: int, *, class_type: ClassType, race: Race, armor: Armor, weapon: Weapon, shield: Shield, inventory: List[Equipment] | None = None, abilities: Abilities | None = None, spells: List[Spell] | None = None, max_spell_slots: int = 0, current_spell_slots: int = 0):
		# Initialize dataclass part
		if abilities is None:
			abilities = Abilities()
		Character.__init__(self, id=id, name=name, level=level, hp=hp, max_hp=max_hp, gold=gold, xp=xp, condition=Condition.OK, abilities=abilities)
		# Initialize spellcaster mixin
		SpellCaster.__init__(self, spells=spells, max_spell_slots=max_spell_slots, current_spell_slots=current_spell_slots)

		# Hero-specific attributes
		self.class_type: ClassType = class_type
		self.race: Race = race
		self.armor: Armor = armor
		self.weapon: Weapon = weapon
		self.shield: Shield = shield
		self.inventory: List[Equipment] = inventory or []

	def allowed_spells(self, spell_categories: dict, spells: list[Spell]) -> list[Spell]:
		# spells: if explicit list provided use it; otherwise infer by class categories
		allowed_spells = spell_categories.get(self.class_type.value, [])
		return [s for s in spells if s.name in allowed_spells]

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
		# Calculate base damage
		damage = self.weapon.damage

		# Add ability modifiers
		if self.class_type == ClassType.FIGHTER:
			damage += self.abilities.str_mod
		elif self.class_type == ClassType.RANGER or self.class_type == ClassType.ROGUE:
			damage += self.abilities.dex_mod
		elif self.class_type == ClassType.WIZARD:
			damage += self.abilities.int_mod

		# Roll damage
		damage += randint(1, damage)

		# Apply target's armor
		armor_bonus = target.armor.bonus if hasattr(target, 'armor') else 0
		damage_dealt = max(1, damage - armor_bonus)

		return damage_dealt

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

	def saving_throw(self, dc: int) -> bool:
		"""Perform a saving throw against a spell or effect"""
		# Simple saving throw based on wisdom modifier
		roll = randint(1, 20)
		return roll + self.abilities.wis_mod >= dc


@dataclass
class DamageDice:
	num_dice: int
	roll_dice: int
	bonus: int

	@property
	def roll(self):
		return sum(randint(1, self.roll_dice) for _ in range(self.num_dice)) + self.bonus


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
		return self.damage_dice.num_dice

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

	def saving_throw(self, dc: int) -> bool:
		"""Perform a saving throw against a spell or effect"""
		# Monster saving throw based on wisdom modifier
		roll = randint(1, 20)
		return roll + self.abilities.wis_mod >= dc


class SpellLoader:
	"""Handles loading spells from JSON files"""

	@staticmethod
	def load_spells_from_file(filename: str) -> List[Spell]:
		"""Load spells from a JSON file"""
		try:
			with open(filename, 'r') as f:
				spell_data = json.load(f)

			spells = []
			for spell_dict in spell_data:
				spell = Spell(name=spell_dict['name'], level=spell_dict['level'], damage_dice=spell_dict.get('damage_dice', {}), effect=spell_dict['effect'], save_dc=spell_dict['save_dc'], description=spell_dict.get('description', ''))
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
	def resolve_spell_effect(caster: SpellCaster, target: Character, spell: Spell) -> str:
		"""Resolve the effect of a spell on the target"""
		if spell.effect == "heal":
			# Healing spell
			heal_amount = sum(randint(1, spell.damage_dice["roll_dice"]) for _ in range(spell.damage_dice["num_dice"]))
			heal_amount += spell.damage_dice.get("bonus", 0)
			target.hp = min(target.max_hp, target.hp + heal_amount)
			return f"[Spell] {caster.name} heals {target.name} for {heal_amount} HP!"

		elif spell.effect == "buff":
			# Logique du sort Bless
			for t in party:
				t.is_blessed = True
			return f"[Spell] {caster.name} bless all party members!"

		elif spell.effect in ["fire damage", "lightning damage", "force damage", "cold damage"]:
			# Damage spell
			damage = sum(randint(1, spell.damage_dice["roll_dice"]) for _ in range(spell.damage_dice["num_dice"]))
			damage += spell.damage_dice.get("bonus", 0)

			# Check if target makes saving throw (any character with saving_throw)
			if hasattr(target, 'saving_throw') and target.saving_throw(spell.save_dc):
				half = max(1, damage // 2)
				target.hp -= half
				return f"[Spell] {target.name} saves against {spell.name} and takes half damage ({half} HP)!"
			else:
				target.hp -= damage
				return f"[Spell] {caster.name} casts {spell.name} and deals {damage} damage to {target.name}!"

		elif spell.effect == "sleep":
			# Sleep spell - requires saving throw
			if hasattr(target, 'saving_throw') and target.saving_throw(spell.save_dc):
				return f"[Spell] {target.name} saves against {spell.name} and remains awake!"
			else:
				target.condition = Condition.UNCONSCIOUS
				return f"[Spell] {target.name} falls asleep due to {spell.name}!"

		return f"[Spell] {caster.name} casts {spell.name} on {target.name}!"

	@staticmethod
	def resolve_attack(attacker: Character, defender: Character) -> str:
		"""Résout une attaque en utilisant un jet de 1d20 et gère les échecs critiques."""
		# 1. Gestion des cibles sans défense
		if hasattr(defender, 'condition') and defender.condition in [Condition.UNCONSCIOUS, Condition.PARALYZED]:
			damage = BattleSystem._roll_damage(attacker, defender, is_critical=True)
			defender.hp -= damage
			return f"[Weapon] {attacker.name} touche AUTOMATIQUEMENT {defender.name} (sans défense) pour un COUP CRITIQUE de {damage} dégâts !"

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
			return status_msg

		# 3. Réussite Critique (20 naturel)
		if d20_roll == 20:
			damage = BattleSystem._roll_damage(attacker, defender, is_critical=True)
			defender.hp -= damage
			return f"[Weapon] 🎯 COUP CRITIQUE ! {attacker.name} fait un 20 naturel et inflige {damage} dégâts à {defender.name} !"

		# 4. Jet normal contre Classe d'Armure (CA)
		if total_attack >= ac:
			damage = BattleSystem._roll_damage(attacker, defender, is_critical=False)
			defender.hp -= damage
			return f"[Weapon] {attacker.name} (jet: {d20_roll} + {attack_bonus} = {total_attack}) TOUCHE {defender.name} (CA: {ac}) pour {damage} dégâts !"
		else:
			return f"[Weapon] {attacker.name} (jet: {d20_roll} + {attack_bonus} = {total_attack}) RATE {defender.name} (CA: {ac}) !"

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
		if hasattr(attacker, 'attack') and callable(getattr(attacker, 'attack')):
			base_damage = attacker.attack(defender)
		else:
			base_damage = getattr(attacker, 'damage', 1)

		if attacker.is_blessed:
			d4 = randint(1, 4)
			base_damage += d4
			uprint(f"✨ Bless s'applique ! +{d4} au jet d'attaque.")

		if is_critical:
			base_damage *= 2

		return max(1, base_damage)

	@staticmethod
	def combat(attacker: Character, defender: Character, party: List[Hero]) -> str:
		"""Execute a single combat round"""
		# Determine if attacker is a spellcaster
		if isinstance(attacker, SpellCaster) and attacker.spells:
			# Filter spells to only those allowed for the class and affordable by slots
			usable_spells = [s for s in attacker.spells if attacker.can_cast_spell(s)]

			# Smart selection: prefer healing when any ally is below 40% HP and spell heals; else prefer highest-level damaging spell
			if usable_spells:
				if not all(t.is_blessed for t in party):
					buffs = [s for s in usable_spells if s.effect == 'buff']
					if buffs:
						attacker.cast_spell = buffs[0]
				# If attacker is allied party member, attempt to heal allies
				healing_spells = [s for s in usable_spells if s.effect == 'heal']
				if attacker in party and healing_spells:
					# cast heal on the low ally if found
					allies = [a for a in party if 0 < a.hp < a.max_hp and a is not attacker]
					allies_to_heal = [a for a in allies if a.hp / a.max_hp <= 0.4]
					if allies_to_heal:
						spell = max(healing_spells, key=lambda x: x.level)
						low_ally = min(allies_to_heal, key=lambda a: a.hp)
						#print(low_ally, spell)
						try:
							return attacker.cast_spell(spell, low_ally)
						except TypeError:
							pass

				# otherwise pick highest-level damaging spell and best target
				damage_spells = [s for s in usable_spells if s.effect not in ('heal', 'buff')]
				if damage_spells:
					spell = max(damage_spells, key=lambda x: x.level)
					# prefer target with highest hp among defenders (to finish big ones)
					return attacker.cast_spell(spell, defender)

		# Regular attack
		return BattleSystem.resolve_attack(attacker, defender)


def load_game_data():
	"""Load monster types, spells, classes, races, and equipment from JSON files"""
	monster_types = MonsterTypeLoader.load_monster_types_from_file("monster_types.json")
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


def create_sample_party(spells: List[Spell] | None = None, classes: list | None = None, races: list | None = None, weapons: list | None = None, armors: list | None = None, shields: list | None = None):
	"""Create a sample party of heroes. If spells list is provided, assign to wizards.
	Uses classes, races and equipment data if available to set defaults."""
	spells = spells or []
	classes = classes or []
	races = races or []
	weapons = weapons or []
	armors = armors or []
	shields = shields or []

	# Helper to find class data
	def get_class(name: str):
		for c in classes:
			if c.get('name', '').lower() == name.lower():
				return c
		return None

	# Helper to find race data
	def get_race(name: str):
		for r in races:
			if r.get('name', '').lower() == name.lower():
				return r
		return None

	# Helper to pick equipment by name
	def pick_weapon(name: str):
		for w in weapons:
			if w.get('name', '').lower() == name.lower():
				return Weapon(name=w['name'], damage=w['damage'])
		return Weapon(name='Fists', damage=1)

	def pick_armor(name: str):
		for a in armors:
			if a.get('name', '').lower() == name.lower():
				return Armor(name=a['name'], bonus=a['bonus'])
		return Armor(name='Cloth', bonus=0)

	def pick_shield(name: str):
		for s in shields:
			if s.get('name', '').lower() == name.lower():
				return Shield(name=s['name'], bonus=s['bonus'])
		return Shield(name='None', bonus=0)

	# Construct heroes using equipment JSON when available
	aragorn_weapon = pick_weapon('Sword')
	aragorn_armor = pick_armor('Leather Armor')
	aragorn_shield = pick_shield('Wooden Shield')

	gandalf_weapon = pick_weapon('Staff')
	gandalf_armor = pick_armor('Robe')
	gandalf_shield = pick_shield('None')

	gandalf_class = get_class('Wizard')
	gandalf_slots = gandalf_class.get('base_spell_slots', 3) if gandalf_class else 3

	return [Hero(id=1, name="Aragorn", level=1, hp=10, max_hp=10, gold=100, xp=0, class_type=ClassType.FIGHTER, race=Race(type=RaceType.HUMAN), armor=aragorn_armor, weapon=aragorn_weapon, shield=aragorn_shield, abilities=Abilities(strength=14, intelligence=10, dexterity=12, wisdom=10, agility=12, constitution=13), spells=[]), Hero(id=2, name="Gandalf", level=1, hp=8, max_hp=8, gold=50, xp=0, class_type=ClassType.WIZARD, race=Race(type=RaceType.HUMAN), armor=gandalf_armor, weapon=gandalf_weapon, shield=gandalf_shield, abilities=Abilities(strength=8, intelligence=16, dexterity=10, wisdom=14, agility=10, constitution=12), spells=spells, max_spell_slots=gandalf_slots, current_spell_slots=gandalf_slots),
		Hero(id=3, name="Legolas", level=1, hp=9, max_hp=9, gold=75, xp=0, class_type=ClassType.RANGER, race=Race(type=RaceType.ELF), armor=Armor(name="Leather Armor", bonus=2), weapon=Weapon(name="Bow", damage=6), shield=Shield(name="None", bonus=0), abilities=Abilities(strength=12, intelligence=12, dexterity=16, wisdom=12, agility=14, constitution=12), spells=[]),  # Ranger has no spells
		Hero(id=4, name="Frodo", level=1, hp=7, max_hp=7, gold=30, xp=0, class_type=ClassType.ROGUE, race=Race(type=RaceType.HOBBIT), armor=Armor(name="Leather Armor", bonus=2), weapon=Weapon(name="Dagger", damage=4), shield=Shield(name="None", bonus=0), abilities=Abilities(strength=10, intelligence=12, dexterity=14, wisdom=12, agility=14, constitution=10), spells=[]),  # Rogue has no spells
		Hero(id=5, name="Boromir", level=1, hp=10, max_hp=10, gold=80, xp=0, class_type=ClassType.FIGHTER, race=Race(type=RaceType.HUMAN), armor=Armor(name="Chainmail", bonus=3), weapon=Weapon(name="Sword", damage=6), shield=Shield(name="Wooden Shield", bonus=1), abilities=Abilities(strength=14, intelligence=10, dexterity=12, wisdom=10, agility=12, constitution=13), spells=[]),  # Fighter has no spells
	]


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
		abilities = Abilities(**{k: ab.get(k, 10) for k in ['strength', 'intelligence', 'dexterity', 'wisdom', 'agility', 'constitution']})

		weapon = Weapon(name=h.get('weapon', 'Fists'), damage=next((w['damage'] for w in weapons if w['name'] == h.get('weapon')), 1))
		armor = Armor(name=h.get('armor', 'Cloth'), bonus=next((a['bonus'] for a in armors if a['name'] == h.get('armor')), 0))
		shield = Shield(name=h.get('shield', 'None'), bonus=next((s['bonus'] for s in shields if s['name'] == h.get('shield')), 0))

		# determine spell slots
		hero = Hero(id=h.get('id', 0), name=h.get('name', 'Hero'), level=h.get('level', 1), hp=h.get('hp', 10), max_hp=h.get('max_hp', 10), gold=h.get('gold', 0), xp=h.get('xp', 0), class_type=cls or ClassType.FIGHTER, race=race, armor=armor, weapon=weapon, shield=shield, abilities=abilities)
		allowed_spells = hero.allowed_spells(spell_categories, spells)
		# print(h.get('name'), class_str, allowed_spells)
		hero.spells = sample(allowed_spells, min(randint(1, 2), len(allowed_spells)))
		# print(h.get('name'), class_str, hero.spells)
		base_slots = [c.get('base_spell_slots', 0) for c in classes if c.get('name').lower() == class_str.lower()]
		hero.current_spell_slots[0] = hero.max_spell_slots[0] = base_slots[0]
		party.append(hero)
	return party


def create_sample_monsters(monster_types: List[MonsterType], count: int = 3):
	"""Create sample monsters of different types"""
	monsters = []
	for i in range(count):
		# Select a random monster type
		monster_type = choice(monster_types)

		# Create monster with appropriate stats
		monster = Monster(id=i + 1, name=f"{monster_type.name}", level=monster_type.level, hp=monster_type.hit_dice.roll, max_hp=monster_type.hit_dice.roll, gold=randint(1, 10), xp=randint(5, 15) * (monster_type.level + 1), abilities=Abilities(strength=8 + monster_type.level, intelligence=8, dexterity=10 + monster_type.level, wisdom=10, agility=10 + monster_type.level, constitution=10 + monster_type.level), type=monster_type, ac=monster_type.ac, damage=monster_type.damage)
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


def end_combat_msg(party, monsters, num_combats, killed_monsters):
	# Display final stats
	print("=" * 50)
	print(f"FINAL STATS : {num_combats} victoires et {killed_monsters} monstres tués! {BattleSystem.spells_count} sorts lancés!")
	print("=" * 50)

	alive_chars = [c for c in party if c.hp > 0]
	print(f"Party Status: {len(alive_chars)}/{len(party)} ")
	if alive_chars:
		for hero in alive_chars:
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
			print(f"  {hero.name}: Lvl {hero.level} {cls_name} {race_name} (AC {hero.armor_class} - THACO: {hero.thac0}) "
			      f"- STR: {hero.str} INT: {hero.int} DEX: {hero.dex} CON: {hero.con} WIS: {hero.wis} "
			      f"- HP {hero.hp}/{hero.max_hp} - {hero.condition.value.upper()}, XP {hero.xp}, Gold {hero.gold}{spell_slots}")
	else:
		print(f"All {len(party)} characters in party has died!")

	print("\nMonster Status:")
	for monster in monsters:
		# print(f"  {monster.name}: HP {monster.hp}/{monster.max_hp}")
		if monster.is_dead:
			print(f"  {monster.name}: {monster.condition.value}")
		else:
			print(f"  {monster.name}: HP {monster.hp}/{monster.max_hp}")


def start_combat(party: List[Hero], monsters: List[Monster]):
	"""Start a combat encounter using BattleSystem.combat_round for each action."""
	uprint("=" * 60)
	uprint("COMBAT BEGINS!")
	uprint("=" * 60)

	# Display initial status
	uprint("\nParty Status:")
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
		uprint(f"  {hero.name}: {cls_name} {race_name} - HP {hero.hp}/{hero.max_hp}, XP {hero.xp}, Gold {hero.gold}")

	uprint("\nMonster Status:")
	for monster in monsters:
		uprint(f"  {monster.name}: HP {monster.hp}/{monster.max_hp}")

	# Combat loop
	round_num = 0
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
				uprint(f"{current_char.name} acts against {target.name}!")

				# Use combat_round to handle spellcasting or normal attacks
				result = BattleSystem.combat(current_char, target, party)
				uprint(result)
				if target.is_dead:
					combatant.character.xp += target.xp
					combatant.character.gold += target.gold
					uprint(f"{target.name} is defeated!")
					alive_monsters.remove(target)
					killed_by_level[target.name] += 1
					uprint(f"{combatant.character.name} gained {target.xp} XP and earned {target.gold} gp!")
			else:
				# Monster acts (spell or attack)
				if not alive_chars:
					break
				target = max(party, key=lambda m: m.hp)
				uprint(f"{current_char.name} acts against {target.name}!")

				result = BattleSystem.combat(current_char, target, party)
				uprint(result)
				if target.is_dead:
					uprint(f"{target.name} is defeated!")
					alive_chars.remove(target)

			uprint()

			# Check if battle should end
			if not any(hero.hp > 0 for hero in party):
				uprint("All heroes have been defeated!")
				break
			if not any(monster.hp > 0 for monster in monsters):
				uprint("All monsters have been defeated!")
				break
		if not BATCH_MODE:
			input(f"End of round {round_num}. Press Enter to continue...")


def level_up(party):
	for char in party:
		if char.is_dead:
			continue
		if char.xp // 500 >= char.level:
			char.level += 1
			hp_gained = randint(1, 10)
			char.max_hp += hp_gained
			char.hp += hp_gained
			if char.spells:
				for i in range(10):
					if i <= char.level // 2:
						char.max_spell_slots[i] = min(char.max_spell_slots[i] + randint(1, 3), 9)
						char.current_spell_slots[i] = char.max_spell_slots[i]


def uprint(msg: str = ''):
	if not BATCH_MODE:
		print(msg)


if __name__ == '__main__':
	# Load game data
	monster_types, spells, classes, races, weapons, armors, shields, heroes_data, spell_categories = load_game_data()
	# Build a random party from heroes_data if present
	party_size = 6
	if heroes_data:
		party = build_party_from_heroes(heroes_data, spells, classes, races, weapons, armors, shields, spell_categories, party_size)
	else:
		party = create_sample_party(spells, classes, races, weapons, armors, shields)

	BATCH_MODE = True
	end_game = False
	max_combats = 100
	num_combats = 0
	max_monsters = 3
	killed_monsters = 0
	killed_by_level = {m.name: 0 for m in monster_types}
	spells_cast = {s.name: 0 for s in spells}
	while not end_game and num_combats < max_combats:
		level_up(party)
		num_combats += 1
		if num_combats % 50 == 0:
			for char in party:
				char.hp = char.max_hp
				for i in range(10):
					char.current_spell_slots[i] = char.max_spell_slots[i]
		party_level = sum([c.level for c in party]) / len(party)
		monster_types_selection = [m for m in monster_types if m.level <= party_level]
		monsters = create_sample_monsters(monster_types_selection, randint(1, max_monsters))
		start_combat(party, monsters)
		# end_combat_msg(party, monsters)

		if all(c.is_dead for c in party):
			end_game = True
		# else:
		# 	msg = input("Voulez-vous continuer? (o/n)")
		# 	if msg in ('n', 'N'):
		# 		end_game = True
		killed_monsters += len(monsters)

	end_combat_msg(party, monsters, num_combats, killed_monsters)
	print("killed: ", killed_by_level)
	print("spells: ", spells_cast)

