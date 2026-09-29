from __future__ import annotations

import re

from copy import copy
from enum import Enum
import random as _stdlib_random
from random import randint, sample

# keep an internal reference to the stdlib random module for simulation logic
_random = _stdlib_random
# expose a callable 'random' at module level (so tests can monkeypatch simulation.random)
random = _random.random

from typing import List

import game_state
from combat.battle import BattleSystem
from combat.encounter import start_combat, monster_stats_msg
from loaders.game_data import load_game_data
from models.abilities import Abilities
from models.character import Hero
from models.dice import DamageDice
from models.enums import ClassType, RaceType
from models.equipment import Armor, Shield, Weapon, armor_to_item, shield_to_item, weapon_to_item
from models.monster import Monster, MonsterType
from models.race import Race
from models.spell import Spell

MELEE_CLASSES = {'Fighter', 'Paladin', 'Ranger', 'Rogue'}


def build_party_from_heroes(
	heroes_data,
	spells,
	classes,
	races,
	weapons,
	armors,
	shields,
	spell_categories,
	party_size: int = 6,
	party_level: int = 1
) -> List[Hero]:
	"""Build a party with 3 front-line melee and 3 back-line casters when possible.

	Assign class hit_dice and initial multi_attack according to class and level.
	"""
	if not heroes_data:
		return []
	melee_chars = [h for h in heroes_data if h.get('class') in MELEE_CLASSES]
	caster_chars = [h for h in heroes_data if h not in melee_chars]

	# Ensure 3 front-line melee and 3 back-line casters if possible
	front_needed = min(3, party_size)
	back_needed = min(party_size - front_needed, party_size)
	front_selection = _random.sample(melee_chars, min(front_needed, len(melee_chars)))
	back_selection = _random.sample(caster_chars, min(back_needed, len(caster_chars)))
	selection = front_selection + back_selection

	# If we still need members (not enough melee/casters), fill from remaining heroes
	remaining = [h for h in heroes_data if h not in selection]
	while len(selection) < party_size and remaining:
		selection.append(remaining.pop())

	party: List[Hero] = []
	for idx, h in enumerate(selection):
		class_str = h.get('class', 'Fighter')
		cls = getattr(ClassType, class_str.upper(), ClassType.FIGHTER)

		race_name = h.get('race', 'Human')
		try:
			race = Race(type=RaceType[race_name.upper()])
		except KeyError:
			race = Race(type=RaceType.HUMAN)

		ab = h.get('abilities', {})
		abilities = Abilities(
			**{
				k: ab.get(k, 10)
				for k in ['strength', 'intelligence', 'dexterity', 'wisdom', 'charisma', 'constitution']
			}
		)

		damage = next((w['damage'] for w in weapons if w['name'] == h.get('weapon')), 4)
		weapon = Weapon(name=h.get('weapon', 'Fists'), damage_dice=DamageDice(1, damage))
		armor = Armor(
			name=h.get('armor', 'Cloth'),
			bonus=next((a['bonus'] for a in armors if a['name'] == h.get('armor')), 0),
		)
		shield = Shield(
			name=h.get('shield', 'None'),
			bonus=next((s['bonus'] for s in shields if s['name'] == h.get('shield')), 0),
		)

		class_info = next(
			(c for c in classes if c.get('name', '').lower() == class_str.lower()),
			{},
		)
		spellcasting_ability = class_info.get('spellcasting_ability', '')
		hit_dice = class_info.get('hit_dice', 8)

		hero = Hero(
			id=h.get('id', 0),
			name=h.get('name', 'Hero'),
			level=h.get('level', 1),
			hp=h.get('hp', 10),
			max_hp=h.get('max_hp', 10),
			gold=h.get('gold', 0),
			xp=h.get('xp', 0),
			class_type=cls,
			race=race,
			armor=armor,
			weapon=weapon,
			shield=shield,
			abilities=abilities,
			spellcasting_ability=spellcasting_ability,
			hit_dice=hit_dice,
			position='front' if idx < front_needed else 'back',
		)

		# Bug fix: the weapon/armor/shield equipped at load time used to only
		# live as Hero attributes, invisible to the inventory (and therefore
		# to the GUI's equip/unequip/remove-item actions). Register the
		# starting gear as inventory records too, skipping bare defaults and
		# any malformed (None) names.
		if weapon.name and weapon.name != 'Fists':
			hero.inventory.append(weapon_to_item(weapon))
		if armor.name and armor.name not in ('Cloth', 'None'):
			hero.inventory.append(armor_to_item(armor))
		if shield.name and shield.name != 'None':
			hero.inventory.append(shield_to_item(shield))

		# set initial multi_attack based on class and level
		lvl = h.get('level', 1)
		# determine multi-attack progression
		if cls in [ClassType.FIGHTER, ClassType.RANGER, ClassType.PALADIN]:
			extra = 0
			if lvl >= 5:
				extra += 1
			if lvl >= 11:
				extra += 1
			if lvl >= 20:
				extra += 1
			hero.multi_attack = 1 + extra

		if spellcasting_ability:
			allowed = [s for s in spells if s.class_type == cls and s.level <= party_level // 2]
			hero.spells = _random.sample(allowed, min(_random.randint(1, 2), len(allowed))) if allowed else []
			base_slots = class_info.get('base_spell_slots', 0)
			hero.current_spell_slots = [0] * 10
			hero.max_spell_slots = [0] * 10
			hero.current_spell_slots[0] = copy(base_slots)
			hero.max_spell_slots[0] = copy(base_slots)
		else:
			allowed = []

		for _ in range(party_level - 1):
			level_up(hero, allowed)
		party.append(hero)
	return party


def create_sample_monsters(monster_types: List[MonsterType], count: int = 3) -> List[Monster]:
	monsters: List[Monster] = []
	if not monster_types:
		return monsters
	for i in range(count):
		monster_type = _random.choice(monster_types)
		hp = monster_type.hit_dice.roll
		level = monster_type.level
		monsters.append(
			Monster(
				id=i + 1,
				name=monster_type.name,
				level=level,
				hp=hp,
				max_hp=hp,
				gold=randint(1, 10),
				xp=randint(5, 15) * (level + 1),
				abilities=Abilities(
					strength=8 + level,
					intelligence=8,
					dexterity=10 + level,
					wisdom=10,
					charisma=10,
					constitution=10 + level,
				),
				type=monster_type,
				ac=monster_type.ac,
				damage=monster_type.damage,
			)
		)
	return monsters


def level_up(char: Hero, spells: List[Spell]) -> None:
	"""Increase level, gain HP based on class hit_dice and update spell slots and multi-attack."""
	char.level += 1
	# HP gain based on class hit die + CON modifier
	hit_die = getattr(char, 'hit_dice', 8) or 8
	con_mod = (char.abilities.constitution - 10) // 2
	hp_gained = randint(1, hit_die) + max(0, con_mod)
	char.max_hp += max(1, hp_gained)
	char.hp += max(1, hp_gained)

	# update spell slots (simple progression)
	max_spell_level = max(1, min(20, char.level + 1) // 2)
	for i in range(min(max_spell_level, len(char.max_spell_slots))):
		char.max_spell_slots[i] = min(char.max_spell_slots[i] + randint(1, 3), 9)
		char.current_spell_slots[i] = char.max_spell_slots[i]

	# update multi-attack progression for classes that gain it
	if char.class_type in [ClassType.FIGHTER, ClassType.RANGER, ClassType.PALADIN]:
		extra = 0
		if char.level >= 5:
			extra += 1
		if char.class_type == ClassType.FIGHTER:
			if char.level >= 11:
				extra += 1
			if char.level >= 20:
				extra += 1
		char.multi_attack = 1 + extra

	# learn new spells according to class
	new_spells = [s for s in spells if s not in char.spells and s.level <= max_spell_level]
	if not new_spells:
		return
	if char.class_type == ClassType.WIZARD:
		new_spells = sample(new_spells, min(2, len(new_spells)))
	elif char.class_type in [ClassType.SORCERER, ClassType.BARD, ClassType.RANGER]:
		new_spells = sample(new_spells, min(1, len(new_spells)))
	char.spells = (char.spells or []) + new_spells


def distribute_loot(monsters: List[Monster], survivors: List[Hero], weapons: list, armors: list, shields: list, magic_items: list) -> None:
	"""Distribute loot: non-magical equipment + chance for magic items with rarities.

	- Non-magical: small chance per defeated monster to find weapon/armor/shield
	- Magic items: rarer; use rarity drop probabilities
	- Auto-equip logic: if item is strictly better than current equipped, equip it
	"""
	# use random.random via the random module

	if not survivors:
		return

	# rarity drop probabilities (base per defeated monster) - prefer config if available
	config = globals().get('magic_config', None) or {}
	rarity_chances = config.get('rarity_chances', {
		'Legendary': 0.005,
		'Very rare': 0.01,
		'Rare': 0.03,
		'Uncommon': 0.08,
		'Common': 0.15,
	})
	per_level_scale = float(config.get('per_level_scale', 0.02))

	import re

	def parse_dice_str(dice: str) -> float:
		# Parse simple dice expressions like '1d8', '2d6+1' and return average expected damage
		m = re.match(r'(\d+)d(\d+)(?:\s*\+\s*(\d+))?', str(dice))
		if not m:
			return 4.0
		n, d, bonus = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
		# average of d-sided die is (d+1)/2
		return n * (d + 1) / 2.0 + bonus

	def weapon_power(w: dict) -> float:
		# heuristic: parse damage like "1d8" or numeric 'damage' or 'damage_str'
		if not w:
			return 4.0
		if 'damage' in w and isinstance(w.get('damage'), (int, float)):
			return float(w.get('damage'))
		if 'damage' in w and isinstance(w.get('damage'), str):
			return parse_dice_str(w.get('damage'))
		if 'damage_str' in w:
			return parse_dice_str(w.get('damage_str'))
		# try to extract dice from name or desc
		for field in ('name', 'desc'):
			val = w.get(field, '')
			m = re.search(r"(\d+d\d+(?:\+\d+)?)", str(val))
			if m:
				return parse_dice_str(m.group(1))
		# fallback
		return 4.0

	def parse_bonus_from_desc(item: dict) -> int:
		# extract '+N' patterns from desc or name
		for field in ('bonus', 'desc', 'name'):
			val = item.get(field)
			if isinstance(val, int):
				return int(val)
			if isinstance(val, str):
				m = re.search(r"\+\s*(\d+)", val)
				if m:
					return int(m.group(1))
		return 0

	# helper to auto-equip better items (must be defined before use).
	#
	# Note: this stays independent from Hero.equip_weapon/armor/shield (used by
	# the GUI) because distribute_loot must also work with lightweight
	# duck-typed heroes (see tests/test_distribute_loot_auto_equip.py) that
	# only expose plain attributes, not the full Hero API.
	def _try_auto_equip(hero: Hero, item: dict) -> None:
		it_type = item.get('type')
		name = item.get('name', 'Magic Item')
		if it_type == 'weapon':
			# compare expected damage if both sides have damage or dice
			cur = hero.weapon
			cur_power = weapon_power({'damage': getattr(cur.damage_dice, 'roll_dice', None) and f"1d{getattr(cur.damage_dice, 'roll_dice')}" or '1d4'})
			new_power = weapon_power(item)
			if new_power > cur_power:
				hero.weapon = Weapon(name=item.get('name', cur.name), damage_dice=DamageDice(1, int(item.get('damage', 4))))
				game_state.uprint(f'{hero.name} auto-equips {name} (weapon).')
		elif it_type == 'armor':
			cur_bonus = int(getattr(hero.armor, 'bonus', 0) or 0)
			# prefer explicit 'bonus' field, then 'ac', then parse from desc/name
			raw_new = item.get('bonus') if item.get('bonus') is not None else item.get('ac') if item.get('ac') is not None else parse_bonus_from_desc(item)
			try:
				new_bonus = int(raw_new or 0)
			except Exception:
				new_bonus = 0
			if new_bonus > cur_bonus:
				hero.armor = Armor(name=item.get('name', hero.armor.name), bonus=new_bonus)
				game_state.uprint(f'{hero.name} auto-equips {name} (armor).')
		elif it_type == 'shield':
			cur_bonus = int(getattr(hero.shield, 'bonus', 0) or 0)
			raw_new = item.get('bonus') if item.get('bonus') is not None else parse_bonus_from_desc(item)
			try:
				new_bonus = int(raw_new or 0)
			except Exception:
				new_bonus = 0
			if new_bonus > cur_bonus:
				hero.shield = Shield(name=item.get('name', hero.shield.name), bonus=new_bonus)
				game_state.uprint(f'{hero.name} auto-equips {name} (shield).')

	for m in monsters:
		if m.hp <= 0:
			# non-magical equipment drop
			if random() < 0.25:
				item_type = _random.choice([0, 1, 2])
				# prefer explicit monster loot if provided
				if getattr(m, 'loot', None):
					# assume loot is a list and pick first (tests set single-item loot)
					item = dict(m.loot[0])
				else:
					if item_type == 0 and weapons:
						item = dict(_random.choice(weapons))
						item.setdefault('type', 'weapon')
					elif item_type == 1 and armors:
						item = dict(_random.choice(armors))
						item.setdefault('type', 'armor')
					elif shields:
						item = dict(_random.choice(shields))
						item.setdefault('type', 'shield')
					else:
						item = None
				if item:
					# Skip malformed items with no name
					if not item.get('name'):
					    game_state.uprint(f'⚠️ Found malformed loot (no name) on {m.name}; skipping.')
					else:
					    owner = _random.choice(survivors)
					    owner.inventory.append(item)
					    name = item.get('name') or 'an item'
					    game_state.uprint(f'{owner.name} found {name} on {m.name}!')
					    # attempt to auto-equip non-magical equipment immediately
					    _try_auto_equip(owner, item)

			# magic item drop attempt based on rarity table
			r = random()
			cumulative = 0.0
			for rarity, chance in rarity_chances.items():
				cumulative += chance * (1 + (m.level or 0) * per_level_scale)
				if r < cumulative:
					# pick a magic item of this rarity if available
					candidates = [it for it in magic_items if it.get('rarity') == rarity]
					if candidates:
						mi = dict(_random.choice(candidates))
						# Skip malformed magic items without a name
						if not mi.get('name'):
						    game_state.uprint(f"⚠️ Found malformed magic loot (no name) on {m.name}; skipping.")
						else:
						    owner = _random.choice(survivors)
						    owner.inventory.append(mi)
						    name = mi.get('name') or 'magic item'
						    game_state.uprint(f'{owner.name} found magic item {name} (rarity {rarity}) on {m.name}!')
						    # auto-equip if beneficial
						    _try_auto_equip(owner, mi)
					break


def party_stats_msg(party: List[Hero], num_combats: int, killed_monsters: int, monsters=None) -> None:
	print('=' * 100)
	print(
		f'STATS (Retour auberge tous les {game_state.BACK_TO_TOWN_FREQ} combats): '
		f'{num_combats} victoires et {killed_monsters} monstres tués! '
		f'{BattleSystem.spells_count} sorts lancés!'
	)
	print('=' * 100)
	alive = [c for c in party if c.hp > 0]
	print(f'Party Status: {len(alive)}/{len(party)} ')
	for hero in party:
		cls = getattr(hero, 'class_type', None)
		race = getattr(hero, 'race', None)
		cls_name = cls.value if isinstance(cls, Enum) else (cls or 'Unknown')
		if isinstance(race, Race) and isinstance(race.type, Enum):
			race_name = race.type.value
		else:
			race_name = 'Unknown'
		spell_slots = (f', Spells slots: {hero.current_spell_slots}/{hero.max_spell_slots}' if hero.spells else '')
		spells = '|'.join(f'{s.level}:{s.name}' for s in hero.spells)
		print(
			f'  {hero.name}: Lvl {hero.level} {cls_name} {race_name} '
			f'(AC {hero.armor_class} - ATK+{hero.attack_bonus} - {hero.weapon} - {hero.armor.name}) '
			f'- STR {hero.str} INT {hero.int} WIS {hero.wis} DEX {hero.dex} '
			f'CON {hero.con} CHA {hero.cha} '
			f'- HP {hero.hp}/{hero.max_hp} - {hero.condition.value.upper()}, '
			f'XP {hero.xp}, {hero.gold} gp{spell_slots} - {spells}'
		)

	if monsters:
		print("\nMonsters:")
		for monster in monsters:
			print(f'  {monster.name} (Lvl {monster.level} - AC {monster.armor_class}): '
				f'HP {monster.hp}/{monster.max_hp}')


def print_stats(killed_by_level, spells_cast) -> None:
	print('\nMonsters kill stats')
	for i, monsters in enumerate(killed_by_level):
		# only show entries with kills > 0
		nonzero = {k: v for k, v in monsters.items() if v}
		if nonzero:
			print(f'Lvl {i + 1}: {nonzero}')
	print('\nSpells cast stats')
	for i, spells in enumerate(spells_cast):
		nonzero = {k: v for k, v in spells.items() if v}
		if nonzero:
			print(f'Lvl {i + 1}: {nonzero}')


def run(max_combats: int = 10000, party_size: int = 6, max_monsters: int = 2, batch_mode: bool = True, rest_freq: int = 30, party_level: int = 1) -> None:
	"""Boucle principale de simulation batch."""
	monster_types, spells, classes, races, weapons, armors, shields, heroes_data, spell_categories, magic_items, magic_config = (load_game_data())
	party = build_party_from_heroes(heroes_data, spells, classes, races, weapons, armors, shields, spell_categories, party_size, party_level)
	if not party:
		raise RuntimeError('Party vide : vérifie que data/heroes.json (et classes/armes/etc.) se chargent correctement.')

	game_state.BATCH_MODE = batch_mode
	game_state.BACK_TO_TOWN_FREQ = rest_freq
	# mutate lists in place so combat/encounter keeps the same references
	game_state.killed_by_level.clear()
	game_state.killed_by_level.extend([{m.name: 0 for m in monster_types if m.level == i + 1} for i in range(20)])
	max_spell_level = max((s.level for s in spells), default=9)
	game_state.spells_cast.clear()
	game_state.spells_cast.extend([{s.name: 0 for s in spells if s.level == i} for i in range(1, max_spell_level + 1)])
	BattleSystem.spells_count = 0

	end_game = False
	num_combats = 0
	killed_monsters = 0
	monsters: List[Monster] = []

	party_stats_msg(party, num_combats, killed_monsters)
	while not end_game and num_combats < max_combats:
		for char in party:
			if char.xp // 500 >= char.level and char.level < 20:
				allowed = [s for s in spells if s.class_type == char.class_type]
				level_up(char, allowed)

		num_combats += 1
		if num_combats % game_state.BACK_TO_TOWN_FREQ == 0:
			for char in party:
				char.hp = char.max_hp
				for i in range(len(char.current_spell_slots)):
					char.current_spell_slots[i] = char.max_spell_slots[i]

		party_level = sum(c.level for c in party) / len(party)
		selection = [m for m in monster_types if party_level - 1 < m.level <= party_level] or monster_types
		monsters = create_sample_monsters(selection, _random.randint(1, max_monsters))
		total_xp, total_gp = start_combat(party, monsters)

		alive = [c for c in party if not c.is_dead]
		if alive:
			share_xp = total_xp // len(alive)
			share_gp = total_gp // len(alive)
			for char in alive:
				char.xp += share_xp
				char.gold += share_gp
			# Distribute loot items among survivors (weapons/armors/shields + magic items)
			distribute_loot(monsters, alive, weapons, armors, shields, magic_items)

		if all(c.is_dead for c in party):
			end_game = True
		killed_monsters += len(monsters)

	for monster in monsters:
		print(f'  {monster.name}: HP {monster.hp}/{monster.max_hp}')

	party_stats_msg(party, num_combats, killed_monsters, monsters)
	print_stats(game_state.killed_by_level, game_state.spells_cast)
