from __future__ import annotations

import json
from typing import List

from models.dice import DamageDice
from models.enums import ClassType
from models.spell import Spell


class SpellLoader:
	"""Handles loading spells from JSON files."""

	@staticmethod
	def load_spells_from_file(filename: str) -> List[Spell]:
		try:
			with open(filename, 'r', encoding='utf-8') as f:
				data = json.load(f)

			spells: List[Spell] = []
			for class_dict in data:
				class_str = class_dict.get('class')
				for spell_dict in class_dict.get('spells', []):
					dc = spell_dict.get('dc')
					dc_type = ''
					dc_success = ''
					if dc:
						dc_type = dc.get('dc_type', '')
						dc_success = dc.get('dc_success', '')
					dd = spell_dict.get('damage_dice') or {}
					damage_dice = (
						DamageDice(num_dice=dd['num_dice'], roll_dice=dd['roll_dice'], bonus=dd.get('bonus', 0))
						if dd
						else None
					)
					spells.append(
						Spell(
							name=spell_dict['name'],
							class_type=ClassType(class_str),
							level=spell_dict['level'],
							damage_dice=damage_dice,
							effect=spell_dict['effect'],
							dc_type=dc_type,
							dc_success=dc_success,
							description=spell_dict.get('description', ''),
						)
					)
			return spells
		except FileNotFoundError:
			print(f'Warning: Spell file {filename} not found.')
			return []
		except json.JSONDecodeError:
			print(f'Warning: Invalid JSON in spell file {filename}.')
			return []
