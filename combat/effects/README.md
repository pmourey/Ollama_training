# Module combat.effects — Résolution des effets de sorts

Le module combat.effects résout l'application des effets de sorts via un registry qui retourne un EffectHandler.

## Principe

- `registry.resolve(spell)` → `EffectHandler` (par nom ou par catégorie)
- Chaque handler expose `matches(spell)`, `apply(ctx, target)` et des métadonnées (`ai_role`, `ai_status`, `ai_priority`)
- Types fournis : `damage`, `heal`, `buff`, `shield`, `cleanse`, `smite`, `condition` et cas spéciaux (Shield, Death Ward, Time Stop, etc.)

## Intégration dans BattleSystem (`combat/battle.py`)

1) Importer le registry et `CastContext` (le code d'exemple ci-dessous utilise `BattleSystem.resolve_spell_effect` qui délègue déjà au registry) :

```py
from combat.effects import registry
from combat.effects.base import CastContext
```

2) Lorsqu'un héros lance un sort (depuis `main.py` / `encounter.py`), construire le contexte :

```py
ctx = CastContext(caster=hero, spell=spell)
```

3) Résoudre le handler et l'appliquer sur la cible :

```py
handler = registry.resolve(spell)
result_msg = handler.apply(ctx, target)
# gérer messages, logs et retours de combat
```

4) Respecter les effets actifs : certains handlers utilisent `target.has_effect`, `target.add_effect`, `target.cleanse_negative`, `target.receive_damage`, `target.saving_throw`. `BattleSystem` et `Hero.cast_spell` doivent déléguer à ces méthodes (les modèles `Character`/`Hero` fournissent déjà ces utilitaires).

5) IA / priorités : pour le choix des sorts, interroger `handler.ai_role` / `ai_priority` / `ai_status` pour trier et sélectionner les sorts adaptés.

## Implémentations de sorts par type d'effet

- Damage : gère jet de sauvegarde (`dc_type`/`dc_success`); ajuster pour sorts avec "save for half" ou effets élémentaires (psychic résiste à mind_blank).
- Heal : utilise `damage_dice` comme montant soigné.
- Buff/Shield : créent `ActiveEffect` avec durée calculée par `scaled_duration(level)`. Ajuster `magnitude`/`turns` pour sorts spéciaux en enregistrant un handler dédié dans `specials.py` et `registry.register_spell`.
- Smite : n'inflige pas immédiatement; ajoute un `ActiveEffect` "smite" consulté ensuite lors du calcul de dégâts d'attaque.
- Condition : appelle `resisted(ctx,target)` avant d'ajouter l'effet; pour effets mentaux vérifier `target.has_effect('mind_blank')`.
- Spécial : pour comportements non standard (revive, wish, time stop), ajouter une classe dans `specials.py` et appeler `registry.register_spell('Nom du sort', Handler())` dans `registry.build_registry()`.

## Ajustements individuels

- Pour modifier la mécanique d'un sort précis, créer/éditer un handler dans `specials.py` et enregistrer par nom.
- Pour variations mineures (magnitude, durée), modifier les paramètres d'`ActiveEffect` créés dans `handlers.py` ou `specials.py`.
- Tester via un appel depuis `encounter.py` : simuler `cast_spell` depuis `Hero` et vérifier l'état des `ActiveEffect` sur la cible après `apply()`.

## Exemple d'appel minimal dans `encounter.py` (pseudo)

```py
from combat.effects.base import CastContext
from combat.effects import registry

ctx = CastContext(caster=hero, spell=chosen_spell)
handler = registry.resolve(chosen_spell)
msg = handler.apply(ctx, target)
print(msg)
```

## Conclusion

Le module est conçu pour être extensible : ajout de handlers nommés pour exceptions et handlers génériques pour catégories. Utiliser la metadata (`ai_role`/`ai_priority`) pour l'intégration IA et respecter les méthodes utilitaires du modèle `Character` pour la cohérence des effets.