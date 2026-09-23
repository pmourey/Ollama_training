from enum import Enum


class ClassType(Enum):
	WIZARD = 'Wizard'
	FIGHTER = 'Fighter'
	RANGER = 'Ranger'
	ROGUE = 'Rogue'
	CLERIC = 'Cleric'
	BARD = 'Bard'
	DRUID = 'Druid'
	SORCERER = 'Sorcerer'
	PALADIN = 'Paladin'


class RaceType(Enum):
	HUMAN = 'Human'
	DWARF = 'Dwarf'
	ELF = 'Elf'
	HOBBIT = 'Hobbit'


class Condition(Enum):
	# Les 15 conditions officielles de D&D 5e
	OK = 'ok'
	BLINDED = 'blinded'
	DEAFENED = 'deafened'
	RESTRAINED = 'restrained'
	GRAPPLED = 'grappled'
	PRONE = 'prone'
	CHARMED = 'charmed'
	FRIGHTENED = 'frightened'
	INCAPACITATED = 'incapacitated'
	PARALYZED = 'paralyzed'
	PETRIFIED = 'petrified'
	POISONED = 'poisoned'
	STUNNED = 'stunned'
	UNCONSCIOUS = 'unconscious'
	INVISIBLE = 'invisible'
	EXHAUSTION = 'exhaustion'
