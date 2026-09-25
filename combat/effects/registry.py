from __future__ import annotations

from combat.effects.base import EffectHandler
from combat.effects.handlers import (
	BuffHandler,
	CleanseHandler,
	ConditionHandler,
	DamageHandler,
	FallbackHandler,
	HealHandler,
	ShieldHandler,
	SmiteHandler,
)
from combat.effects.specials import (
	DeathWardHandler,
	ForesightHandler,
	MindBlankHandler,
	MiracleHandler,
	ReviveHandler,
	ShieldSpellHandler,
	TimeStopHandler,
)
from models.spell import Spell


class EffectRegistry:
	"""Choisit le gestionnaire d'un sort.

	Ordre : nom de sort (traitement individuel), puis première catégorie
	dont `matches` réussit. Les smites sont enregistrés avant les dégâts,
	parce que leur `effect` JSON contient aussi « damage ».
	"""

	def __init__(self) -> None:
		self._by_name: dict[str, EffectHandler] = {}
		self._handlers: list[EffectHandler] = []
		self._fallback = FallbackHandler()

	def register(self, handler: EffectHandler) -> None:
		self._handlers.append(handler)

	def register_spell(self, spell_name: str, handler: EffectHandler) -> None:
		self._by_name[spell_name] = handler

	def resolve(self, spell: Spell) -> EffectHandler:
		named = self._by_name.get(spell.name)
		if named is not None:
			return named
		for handler in self._handlers:
			if handler.matches(spell):
				return handler
		return self._fallback


def build_registry() -> EffectRegistry:
	registry = EffectRegistry()

	shield_spell = ShieldSpellHandler()
	registry.register_spell('Shield', shield_spell)
	registry.register_spell('Shield Wild', shield_spell)

	death_ward = DeathWardHandler()
	registry.register_spell('Death Ward', death_ward)
	registry.register_spell('Death Ward Faith', death_ward)

	registry.register_spell('Time Stop', TimeStopHandler())
	registry.register_spell('Mind Blank', MindBlankHandler())

	foresight = ForesightHandler()
	registry.register_spell('Foresight', foresight)
	registry.register_spell('Foresight Nature', foresight)

	# Le JSON range ces sorts dans une autre catégorie que leur mécanique réelle.
	registry.register_spell('Fear', ConditionHandler(
		'frighten', 'frighten', 'is frightened', mental=True, priority=40,
	))
	registry.register_spell('Entangle', ConditionHandler(
		'restrained', 'restrained', 'is restrained', mental=False, priority=50,
	))
	registry.register_spell('Grasping Vine', ConditionHandler(
		'paralyze', 'paralyze', 'is seized and cannot act', mental=False, priority=10,
	))

	revive = ReviveHandler()
	registry.register_spell('Resurrection', revive)
	registry.register_spell('Revivify', revive)

	miracle = MiracleHandler()
	registry.register_spell('Wish Spell', miracle)
	registry.register_spell('Absolute Salvation', miracle)

	registry.register(SmiteHandler())
	registry.register(DamageHandler())
	registry.register(HealHandler())
	registry.register(BuffHandler())
	registry.register(ShieldHandler())
	registry.register(CleanseHandler())
	registry.register(ConditionHandler(
		'sleep', 'sleep', 'falls asleep', mental=True, priority=20,
	))
	registry.register(ConditionHandler(
		'blind', 'blind', 'is blinded', mental=True, priority=30,
	))
	registry.register(ConditionHandler(
		'paralyze', 'paralyze', 'is paralyzed and cannot act', mental=True, priority=10,
	))
	registry.register(ConditionHandler(
		'frighten', 'frighten', 'is frightened', mental=True, priority=40,
	))
	registry.register(ConditionHandler(
		'restrained', 'restrained', 'is restrained', mental=False, priority=50,
	))
	registry.register(ConditionHandler(
		'disadvantage', 'disadvantage', 'is hindered', mental=False, priority=60,
	))
	return registry


registry = build_registry()
