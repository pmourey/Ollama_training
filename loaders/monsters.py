from __future__ import annotations

import json
from typing import List

from models.dice import DamageDice
from models.monster import MonsterType


class MonsterTypeLoader:
	"""Handles loading monster types from JSON files."""

	@staticmethod
	def load_monster_types_from_file(filename: str) -> List[MonsterType]:
		try:
			with open(filename, 'r', encoding='utf-8') as f:
				monster_data = json.load(f)

			monster_types: List[MonsterType] = []
			for monster_dict in monster_data:
				hit = monster_dict['hit_dice']
				dmg = monster_dict['damage_dice']
				monster_types.append(
					MonsterType(
						name=monster_dict['name'],
						hit_dice=DamageDice(
							num_dice=hit['num_dice'],
							roll_dice=hit['roll_dice'],
							bonus=hit.get('bonus', 0),
						),
						ac=monster_dict['ac'],
						damage_dice=DamageDice(
							num_dice=dmg['num_dice'],
							roll_dice=dmg['roll_dice'],
							bonus=dmg.get('bonus', 0),
						),
						spellcasting=monster_dict.get('spellcasting', False),
					)
				)
			return monster_types
		except FileNotFoundError:
			print(f'Warning: Monster type file {filename} not found.')
			return []
		except json.JSONDecodeError:
			print(f'Warning: Invalid JSON in monster type file {filename}.')
			return []
