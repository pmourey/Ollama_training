"""Résolution modulaire des effets de sorts.

Le registre (`registry.resolve`) choisit un gestionnaire :
1. par nom de sort, pour un traitement individuel (`specials.py`) ;
2. sinon par catégorie `spell.effect` (`handlers.py`) ;
3. sinon un message générique.

Les dégâts élémentaires partagent `DamageHandler`. Les smites sont interceptés
avant, car leur champ `effect` contient aussi « damage ».
"""

from combat.effects.registry import registry

__all__ = ['registry']
