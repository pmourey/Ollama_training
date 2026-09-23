from dataclasses import dataclass

from models.enums import RaceType


@dataclass
class Race:
	type: RaceType

	@property
	def str_mod(self) -> int:
		return 2 if self.type == RaceType.DWARF else 0

	@property
	def int_mod(self) -> int:
		return 2 if self.type == RaceType.HUMAN else 0
