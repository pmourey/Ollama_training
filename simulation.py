from __future__ import annotations

from copy import copy
from enum import Enum
from random import choice, randint, sample
from typing import List

import game_state
from combat.battle import BattleSystem
from combat.encounter import start_combat
from loaders.game_data import load_game_data
from models.abilities import Abilities
from models.character import Hero
from models.dice import DamageDice
from models.enums import ClassType, RaceType
from models.equipment import Armor, Shield, Weapon
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
) -> List[Hero]:
	if not heroes_data:
		return []
	melee_chars = [h for h in heroes_data if h.get('class') in MELEE_CLASSES]
	caster_chars = [h for h in heroes_data if h not in melee_chars]
	half = party_size // 2
	selection = sample(melee_chars, min(half, len(melee_chars))) + sample(
		caster_chars, min(half, len(caster_chars))
	)

	party: List[Hero] = []
	for h in selection:
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
		)

		if spellcasting_ability:
			allowed = [s for s in spells if s.class_type == cls and s.level == 1]
			hero.spells = sample(allowed, min(randint(1, 2), len(allowed))) if allowed else []
			base_slots = class_info.get('base_spell_slots', 0)
			hero.current_spell_slots = [0] * 10
			hero.max_spell_slots = [0] * 10
			hero.current_spell_slots[0] = copy(base_slots)
			hero.max_spell_slots[0] = copy(base_slots)

		party.append(hero)
	return party


def create_sample_monsters(monster_types: List[MonsterType], count: int = 3) -> List[Monster]:
	monsters: List[Monster] = []
	if not monster_types:
		return monsters
	for i in range(count):
		monster_type = choice(monster_types)
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
	char.level += 1
	hp_gained = randint(1, 10)
	char.max_hp += hp_gained
	char.hp += hp_gained
	max_spell_level = max(1, min(20, char.level + 1) // 2)
	for i in range(min(max_spell_level, len(char.max_spell_slots))):
		char.max_spell_slots[i] = min(char.max_spell_slots[i] + randint(1, 3), 9)
		char.current_spell_slots[i] = char.max_spell_slots[i]
	new_spells = [s for s in spells if s not in char.spells and s.level <= max_spell_level]
	if not new_spells:
		return
	if char.class_type == ClassType.WIZARD:
		new_spells = sample(new_spells, min(2, len(new_spells)))
	elif char.class_type in [ClassType.SORCERER, ClassType.BARD, ClassType.RANGER]:
		new_spells = sample(new_spells, min(1, len(new_spells)))
	char.spells = (char.spells or []) + new_spells


def party_stats_msg(party: List[Hero], num_combats: int, killed_monsters: int) -> None:
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
		spell_slots = (
			f', Spells slots: {hero.current_spell_slots}/{hero.max_spell_slots}' if hero.spells else ''
		)
		spells = '|'.join(f'{s.level}:{s.name}' for s in hero.spells)
		print(
			f'  {hero.name}: Lvl {hero.level} {cls_name} {race_name} '
			f'(AC {hero.armor_class} - ATK+{hero.attack_bonus} - {hero.weapon}) '
			f'- STR {hero.str} INT {hero.int} WIS {hero.wis} DEX {hero.dex} '
			f'CON {hero.con} CHA {hero.cha} '
			f'- HP {hero.hp}/{hero.max_hp} - {hero.condition.value.upper()}, '
			f'XP {hero.xp}, {hero.gold} gp{spell_slots} - {spells}'
		)


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


def monster_stats_msg(monsters: List[Monster]) -> None:
	print('\nMonster Status:')
	for monster in monsters:
		print(
			f'  {monster.name} (Lvl {monster.level} - AC {monster.armor_class}): '
			f'HP {monster.hp}/{monster.max_hp}'
		)


def run(max_combats: int = 10000, party_size: int = 6, max_monsters: int = 2) -> None:
	"""Boucle principale de simulation batch."""
	monster_types, spells, classes, races, weapons, armors, shields, heroes_data, spell_categories = (
		load_game_data()
	)
	party = build_party_from_heroes(
		heroes_data, spells, classes, races, weapons, armors, shields, spell_categories, party_size
	)
	if not party:
		raise RuntimeError(
			'Party vide : vérifie que data/heroes.json (et classes/armes/etc.) se chargent correctement.'
		)

	game_state.BATCH_MODE = True
	game_state.BACK_TO_TOWN_FREQ = 10
	# mutate lists in place so combat/encounter keeps the same references
	game_state.killed_by_level.clear()
	game_state.killed_by_level.extend(
		[{m.name: 0 for m in monster_types if m.level == i + 1} for i in range(20)]
	)
	max_spell_level = max((s.level for s in spells), default=9)
	game_state.spells_cast.clear()
	game_state.spells_cast.extend(
		[{s.name: 0 for s in spells if s.level == i} for i in range(1, max_spell_level + 1)]
	)
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
		selection = [m for m in monster_types if m.level <= party_level] or monster_types
		monsters = create_sample_monsters(selection, randint(1, max_monsters))
		total_xp, total_gp = start_combat(party, monsters)

		alive = [c for c in party if not c.is_dead]
		if alive:
			share_xp = total_xp // len(alive)
			share_gp = total_gp // len(alive)
			for char in alive:
				char.xp += share_xp
				char.gold += share_gp

		if all(c.is_dead for c in party):
			end_game = True
		killed_monsters += len(monsters)

	party_stats_msg(party, num_combats, killed_monsters)
	if monsters:
		monster_stats_msg(monsters)
	print_stats(game_state.killed_by_level, game_state.spells_cast)
