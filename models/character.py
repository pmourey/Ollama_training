from __future__ import annotations

from dataclasses import dataclass, field
from random import randint
from typing import List

from models.abilities import Abilities
from models.enums import ClassType, Condition
from models.equipment import Armor, Equipment, Shield, Weapon
from models.race import Race
from models.spell import Spell


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
		return self.abilities.str_mod + proficiency_bonus

	def saving_throw(self, dc_type: str, dc: int) -> bool:
		roll = randint(1, 20)
		modifiers = {
			'str': self.abilities.str_mod,
			'int': self.abilities.int_mod,
			'wis': self.abilities.wis_mod,
			'dex': self.abilities.dex_mod,
			'con': self.abilities.con_mod,
		}
		return roll + modifiers[dc_type] >= dc

	def take_damage(self, damage: int) -> int:
		"""Applique les dégâts bruts (pas de réduction d'armure en 5e)."""
		actual_damage = max(0, damage)
		self.hp -= actual_damage
		return actual_damage

	def get_initiative(self) -> int:
		return randint(1, 20) + self.abilities.dex_mod


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

	def can_cast_spell(self, spell: Spell) -> bool:
		return self.current_spell_slots[spell.level - 1] > 0

	def cast_spell(self, spell: Spell, targets: list[Character]) -> None:
		"""Cast a spell; delegates effect resolution to BattleSystem."""
		from combat.battle import BattleSystem
		from game_state import spells_cast, uprint

		if self.current_spell_slots[spell.level - 1] <= 0:
			uprint(f'[Spell] {self.name} cannot cast {spell.name} (insufficient slots)!')
			return

		self.current_spell_slots[spell.level - 1] -= 1
		level_idx = spell.level - 1
		while len(spells_cast) <= level_idx:
			spells_cast.append({})
		spells_cast[level_idx][spell.name] = spells_cast[level_idx].get(spell.name, 0) + 1
		BattleSystem.spells_inc()
		BattleSystem.resolve_spell_effect(self, targets, spell)

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
			return 10 + armor_bonus + shield_bonus
		if 'hide' in armor_name or 'scale' in armor_name:
			return 10 + armor_bonus + min(2, dex_mod) + shield_bonus
		return 10 + armor_bonus + dex_mod + shield_bonus

	@property
	def attack_bonus(self) -> int:
		"""Bonus d'attaque 5e : maîtrise + attribut selon la classe."""
		proficiency_bonus = 2 + ((self.level - 1) // 4)
		if self.class_type in [ClassType.RANGER, ClassType.ROGUE]:
			return self.abilities.dex_mod + proficiency_bonus
		if self.class_type == ClassType.WIZARD:
			return self.abilities.int_mod + proficiency_bonus
		return self.abilities.str_mod + proficiency_bonus

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
