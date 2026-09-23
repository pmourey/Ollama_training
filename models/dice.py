from dataclasses import dataclass
from random import randint


@dataclass
class DamageDice:
	num_dice: int
	roll_dice: int
	bonus: int = 0

	@property
	def roll(self) -> int:
		return sum(randint(1, self.roll_dice) for _ in range(self.num_dice)) + self.bonus

	def __repr__(self) -> str:
		bonus = f'+{self.bonus}' if self.bonus else ''
		return f'{self.num_dice}d{self.roll_dice}{bonus}'
