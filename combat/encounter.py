from __future__ import annotations

from typing import List

from combat.battle import BattleSystem
from combat.combatant import Combatant
import game_state
from models.character import Hero
from models.enums import Condition
from models.monster import Monster

def monster_stats_msg(monsters: List[Monster]) -> None:
	game_state.uprint('\nMonster Status:')
	for monster in monsters:
		game_state.uprint(
			f'  {monster.name} (Lvl {monster.level} - AC {monster.armor_class}): '
			f'HP {monster.hp}/{monster.max_hp}'
		)

def calculate_initiative(party: list, monsters: list) -> list[Combatant]:
	combatants = [Combatant(hero, hero.get_initiative()) for hero in party]
	combatants += [Combatant(monster, monster.get_initiative()) for monster in monsters]
	combatants.sort(key=lambda c: c.initiative, reverse=True)
	return combatants


def start_combat(party: List[Hero], monsters: List[Monster]) -> tuple[int, int]:
	"""Start a combat encounter; returns (total_xp, total_gp)."""
	for hero in party:
		hero.clear_effects()

	game_state.uprint('=' * 60)
	game_state.uprint('COMBAT BEGINS!')
	game_state.uprint('=' * 60)
	game_state.uprint('\nMonster Status:')
	for monster in monsters:
		game_state.uprint(f'  {monster.name}: HP {monster.hp}/{monster.max_hp}')

	round_num = 0
	total_xp = total_gp = 0
	while any(hero.hp > 0 for hero in party) and any(monster.hp > 0 for monster in monsters):
		round_num += 1
		game_state.uprint(f'\n--- ROUND {round_num} ---')

		alive_chars = [h for h in party if h.hp > 0]
		alive_monsters = [m for m in monsters if m.hp > 0]
		combatants = calculate_initiative(alive_chars, alive_monsters)

		for combatant in combatants:
			current_char = combatant.character
			if current_char.hp <= 0:
				continue
			if current_char.condition in (Condition.PARALYZED, Condition.UNCONSCIOUS):
				game_state.uprint(f'{current_char.name} is {current_char.condition.value} and cannot act!')
				continue

			if isinstance(current_char, Hero):
				alive_monsters = [m for m in monsters if m.hp > 0]
				if not alive_monsters:
					break
				target = max(alive_monsters, key=lambda m: m.hp)
				BattleSystem.combat(current_char, target, party)
				if target.is_dead:
					total_xp += target.xp
					total_gp += target.gold
					game_state.uprint(f'{target.name} is defeated!')
					alive_monsters.remove(target)
					idx = target.level - 1
					if 0 <= idx < len(game_state.killed_by_level):
						bucket = game_state.killed_by_level[idx]
						bucket[target.name] = bucket.get(target.name, 0) + 1
					# game_state.uprint(f'{combatant.character.name} gained {target.xp} XP and earned {target.gold} gp!')
			else:
				if not alive_chars:
					break
				target = max(alive_chars, key=lambda m: m.hp)
				BattleSystem.combat(current_char, target, party)
				if target.is_dead:
					game_state.uprint(f'{target.name} is defeated!')
					alive_chars.remove(target)

			if not any(hero.hp > 0 for hero in party):
				game_state.uprint('All heroes have been defeated!')
				return 0, 0
			if not any(monster.hp > 0 for monster in monsters):
				game_state.uprint(f'*** VICTORY! *** Each member gained {total_xp} XP and earned {total_gp} gp')
				if not game_state.BATCH_MODE:
					input(f'Press Enter to continue...')
				return total_xp, total_gp

		for creature in [*party, *monsters]:
			for msg in creature.tick_effects():
				game_state.uprint(msg)

		if not game_state.BATCH_MODE:
			input(f'End of round {round_num}. Press Enter to continue...')

	return total_xp, total_gp
