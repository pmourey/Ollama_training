from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loaders.monsters import MonsterTypeLoader
from loaders.spells import SpellLoader

# Racine du projet (parent de loaders/), indépendant du cwd
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = _PROJECT_ROOT / 'data'


def _data_path(filename: str) -> Path:
	return DATA_DIR / filename


def _load_json(filename: str, default: Any) -> Any:
	path = _data_path(filename)
	if not path.exists():
		print(f'Warning: {path} not found.')
		return default
	try:
		with open(path, 'r', encoding='utf-8') as f:
			return json.load(f)
	except Exception:
		print(f'Warning: failed to load {path}')
		return default


def load_game_data():
	"""Load monster types, spells, classes, races, and equipment from data/*.json."""
	monster_types = MonsterTypeLoader.load_monster_types_from_file(str(_data_path('monsters.json')))
	spells = SpellLoader.load_spells_from_file(str(_data_path('spells.json')))
	classes = _load_json('classes.json', [])
	races = _load_json('races.json', [])
	weapons = _load_json('weapons.json', [])
	armors = _load_json('armors.json', [])
	shields = _load_json('shields.json', [])
	heroes_data = _load_json('heroes.json', [])
	spell_categories = _load_json('spell_categories.json', {})
	return monster_types, spells, classes, races, weapons, armors, shields, heroes_data, spell_categories
