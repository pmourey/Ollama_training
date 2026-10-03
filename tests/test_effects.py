import pytest
import json
from loaders.game_data import load_game_data
from models.spell import Spell
from models.enums import ClassType
from models.character import Hero
from combat.effects import registry
from combat.effects.base import CastContext
from unittest.mock import MagicMock

def test_all_spells_have_handlers():
    _, spells, _, _, _, _, _, _, _, _, _ = load_game_data()

    unhandled_spells = []

    for spell in spells:
        handler = registry.resolve(spell)
        if type(handler).__name__ == "FallbackHandler":
            unhandled_spells.append(spell.name)

    assert not unhandled_spells, f"Found spells without specific handlers: {unhandled_spells}"

def test_spell_effects_categories():
    _, spells, _, _, _, _, _, _, _, _, _ = load_game_data()

    effect_to_handler_type = {
        'acid damage': 'DamageHandler',
        'blind': 'ConditionHandler',
        'buff': ('BuffHandler', 'DeathWardHandler', 'TimeStopHandler', 'MindBlankHandler', 'ForesightHandler'),
        'cleanse': 'CleanseHandler',
        'cold damage': 'DamageHandler',
        'disadvantage': 'ConditionHandler',
        'fire damage': 'DamageHandler',
        'force damage': 'DamageHandler',
        'heal': 'HealHandler',
        'lightning damage': 'DamageHandler',
        'necrotic damage': 'DamageHandler',
        'paralyze': 'ConditionHandler',
        'poison damage': 'DamageHandler',
        'psychic damage': 'DamageHandler',
        'radiant damage': 'DamageHandler',
        'shield': ('ShieldHandler', 'ShieldSpellHandler', 'ForesightHandler'),
        'sleep': 'ConditionHandler',
        'thunder damage': 'DamageHandler',
    }

    mismatched = []

    for spell in spells:
        handler = registry.resolve(spell)
        handler_name = type(handler).__name__

        # Exceptions allowed by specials.py and SmiteHandler logic:
        if 'smite' in spell.name.lower() and handler_name == 'SmiteHandler':
            continue

        expected = effect_to_handler_type.get(spell.effect)
        if expected:
            if isinstance(expected, tuple):
                if handler_name not in expected:
                    mismatched.append(f"{spell.name} ({spell.effect}) -> {handler_name}, expected one of {expected}")
            else:
                if handler_name != expected:
                    if spell.effect == 'cleanse' and handler_name in ('ReviveHandler', 'MiracleHandler'):
                         continue # acceptable
                    if spell.effect == 'buff' and handler_name == 'MiracleHandler':
                         continue
                    mismatched.append(f"{spell.name} ({spell.effect}) -> {handler_name}, expected {expected}")

    assert not mismatched, f"Found spells with mismatched handlers: {mismatched}"

def test_smite_handler_logic():
    from combat.effects.handlers import SmiteHandler

    handler = SmiteHandler()
    spell1 = Spell(name="Searing Smite", level=1, class_type=ClassType.PALADIN, dc_type="", dc_success="", description="", effect="fire damage", damage_dice=None)
    spell2 = Spell(name="Fireball", level=3, class_type=ClassType.WIZARD, dc_type="", dc_success="", description="", effect="fire damage", damage_dice=None)

    assert handler.matches(spell1) == True
    assert handler.matches(spell2) == False

def test_spell_effects_application():
    from models.enums import RaceType, ClassType
    from models.race import Race
    from models.abilities import Abilities
    from models.equipment import Weapon, DamageDice

    _, spells, _, _, _, _, _, _, _, _, _ = load_game_data()

    # Create dummy heroes to test spell application
    caster = Hero(
        id=1, name="Caster", level=20, hp=100, max_hp=100,
        class_type=ClassType.WIZARD, race=Race(type=RaceType.HUMAN),
        abilities=Abilities(strength=10, dexterity=10, constitution=10, intelligence=20, wisdom=10, charisma=10),
        spellcasting_ability='intelligence', gold=0, xp=0, armor=None, weapon=None, shield=None
    )

    target = Hero(
        id=2, name="Target", level=20, hp=100, max_hp=100,
        class_type=ClassType.FIGHTER, race=Race(type=RaceType.HUMAN),
        abilities=Abilities(strength=20, dexterity=10, constitution=10, intelligence=10, wisdom=10, charisma=10), gold=0, xp=0, armor=None, weapon=None, shield=None
    )

    failed_applications = []

    for spell in spells:
        # Reset target state
        target.hp = target.max_hp
        target.clear_effects()

        ctx = CastContext(caster=caster, spell=spell)
        handler = registry.resolve(spell)

        try:
            msg = handler.apply(ctx, target)
            if not msg:
                failed_applications.append(f"{spell.name}: No message returned from apply()")
        except Exception as e:
            failed_applications.append(f"{spell.name}: Raised exception during apply() - {str(e)}")

    assert not failed_applications, f"Found spells that failed to apply: {failed_applications}"
