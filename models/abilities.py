from dataclasses import dataclass


@dataclass
class Abilities:
	"""Character abilities that affect combat and spellcasting."""
	strength: int = 10
	intelligence: int = 10
	dexterity: int = 10
	wisdom: int = 10
	charisma: int = 10
	constitution: int = 10

	def __post_init__(self) -> None:
		self.strength = max(3, min(20, self.strength))
		self.intelligence = max(3, min(20, self.intelligence))
		self.dexterity = max(3, min(20, self.dexterity))
		self.wisdom = max(3, min(20, self.wisdom))
		self.charisma = max(3, min(20, self.charisma))
		self.constitution = max(3, min(20, self.constitution))

	@property
	def str_mod(self) -> int:
		return (self.strength - 10) // 2

	@property
	def int_mod(self) -> int:
		return (self.intelligence - 10) // 2

	@property
	def dex_mod(self) -> int:
		return (self.dexterity - 10) // 2

	@property
	def wis_mod(self) -> int:
		return (self.wisdom - 10) // 2

	@property
	def con_mod(self) -> int:
		return (self.constitution - 10) // 2

	@property
	def cha_mod(self) -> int:
		return (self.charisma - 10) // 2
