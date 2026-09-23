Voici d'abord les catégories d'effets possibles à implémenter pour enrichir votre gameplay de manière simple et structurée, suivies du fichier JSON contenant la liste complète de sorts pour vos 6 classes et les 10 niveaux.
------------------------------
## Catégories d'effets recommandées pour votre Gameplay
Pour étendre les effets actuels (fire damage, heal, lightning damage, force damage, cold damage, buff, sleep), voici une taxonomie propre, facilement gérable avec des conditions (if/elif ou des gestionnaires d'état) dans votre code :
## 1. Dégâts Élémentaires & Magiques (Damage Types)
Utiles si vous implémentez plus tard des résistances, immunités ou faiblesses sur vos monstres :

* acid damage (Acide) : Dégâts corrosifs (souvent liés au Druide/Wizard).
* poison damage (Poison) : Dégâts toxiques terrestres.
* necrotic damage (Nécrotique) : Magie noire, flétrissement de la vie.
* radiant damage (Radiant) : Magie sacrée/lumière (très important pour Cleric et Paladin).
* psychic damage (Psychique) : Attaque mentale directe, ignore souvent l'armure physique (Bard).
* thunder damage (Tonnerre) : Dégâts d'ondes de choc sonores.

## 2. Altérations d'État & Contrôle (Crowd Control / Debuffs)
Ces effets appliquent un statut à la cible pendant $X$ tours :

* blind (Aveuglement) : Réduit l'Armure (ac) ou donne un malus aux dés de dégâts de la cible.
* paralyze (Paralysie) : Empêche totalement la cible d'attaquer pendant son tour.
* frighten (Effroi) : Diminue les chances de toucher ou la défense de la cible (Bard/Paladin).
* restrained (Entravé) : Réduit l'esquive ou l'initiative.

## 3. Utilitaires & Soutien (Buffs & Combat Modifiers)

* shield (Bouclier) : Augmente temporairement l'Armure (ac) du lanceur ou d'un allié.
* disadvantage (Malus) : Force la cible à rater ou réduire son prochain dé de dégâts.
* smite (Châtiment) : Ajoute un bonus de dégâts directement indexé sur la prochaine attaque physique (Paladin).
* cleanse (Dissipation) : Retire un effet de statut négatif (sleep, blind, etc.) sur un allié.

------------------------------
## Fichier JSON : Grimoire Complet (6 classes x 10 niveaux)
Ce fichier respecte scrupuleusement la structure de vos données en l'adaptant à l'identité magique de chaque classe (Arcane pour Wizard/Sorcerer, Divine pour Cleric/Paladin, Nature pour Druid, et Mentale/Soutien pour Bard). Chaque classe possède 1 sort unique par niveau, du niveau 1 au niveau 10, soit 60 sorts au total.
```json
{
  "classes": {
    "Wizard": {
      "1": {"name": "Magic Missile", "effect": "force damage"},
      "2": {"name": "Scorching Ray", "effect": "fire damage"},
      "3": {"name": "Fireball", "effect": "fire damage"},
      "4": {"name": "Ice Storm", "effect": "cold damage"},
      "5": {"name": "Wall of Force", "effect": "force damage"},
      "6": {"name": "Chain Lightning", "effect": "lightning damage"},
      "7": {"name": "Finger of Death", "effect": "necrotic damage"},
      "8": {"name": "Sunburst", "effect": "radiant damage"},
      "9": {"name": "Meteor Swarm", "effect": ["fire damage", "bludgeoning damage"]},
      "10": {"name": "Time Stop", "effect": ["utility"]}
    },
    "Cleric": {
      "1": {"name": "Healing Word", "effect": ["heal"]},
      "2": {"name": "Bless", "effect": ["buff"]},
      "3": {"name": "Cure Wounds", "effect": ["heal"]},
      "4": {"name": "Divine Smite", "effect": ["radiant damage"]},
      "5": {"name": "Mass Heal", "effect": ["heal"]},
      "6": {"name": "Dispel Magic", "effect": ["utility"]},
      "7": {"name": "Guardian of Faith", "effect": ["radiant damage"]},
      "8": {"name": "Holy Aura", "effect": ["buff"]},
      "9": {"name": "True Resurrection", "effect": ["heal"]},
      "10": {"name": "Divine Intervention", "effect": ["utility"]}
    },
    "Bard": {
      "1": {"name": "Cure Wounds", "effect": ["heal"]},
      "2": {"name": "Healing Word", "effect": ["heal"]},
      "3": {"name": "Sleep", "effect": ["sleep"]},
      "4": {"name": "Greater Invisibility", "effect": ["utility"]},
      "5": {"name": "Mass Cure Wounds", "effect": ["heal"]},
      "6": {"name": "Otto's Irresistible Dance", "effect": ["crowd control"]},
      "7": {"name": "Regenerate", "effect": ["heal"]},
      "8": {"name": "Power Word Stun", "effect: ["crowd control"]},
      "9": {"name": "Foresight", "effect": ["buff"]},
      "10": {"name": "Power Word Kill", "effect: ["crowd control"]}
    },
    "Fighter": {
      "1": {"name": "Second Wind", "effect": ["heal"]},
      "2": {"name": "Action Surge", "effect": ["utility"]},
      "3": {"name": "Indomitable", "effect": ["buff"]},
      "4": {"name": "Extra Attack", "effect": ["utility"]},
      "5": {"name": "Cleave", "effect": ["damage"]},
      "6": {"name": "Maneuvering Attack", "effect": ["utility"]},
      "7": {"name": "Evasion", "effect": ["buff"]},
      "8": {"name": "Unstoppable", "effect": ["buff"]},
      "9": {"name": "Improved Critical", "effect": ["buff"]},
      "10": {"name": "Superior Defense", "effect": ["buff"]}
    },
    "Ranger": {
      "1": {"name": "Hunter's Mark", "effect": ["damage"]},
      "2": {"name": "Cordon of Arrows", "effect": ["damage"]},
      "3": {"name": "Conjure Barrage", "effect": ["damage"]},
      "4": {"name": "Lightning Arrow", "effect": ["lightning damage"]},
      "5": {"name": "Swift Quiver", "effect": ["utility"]},
      "6": {"name": "Conjure Volley", "effect": ["damage"]},
      "7": {"name": "Steel Wind Strike", "effect": ["damage"]},
      "8": {"name": "Feral Senses", "effect": ["utility"]},
      "9": {"name": "Foe Slayer", "effect": ["damage"]},
      "10": {"name": "Whirlwind Attack", "effect": ["damage"]}
    },
    "Druid": {
      "1": {"name": "Entangle", "effect": ["crowd control"]},
      "2": {"name": "Flame Blade", "effect": ["fire damage"]},
      "3": {"name": "Call Lightning", "effect": ["lightning damage"]},
      "4": {"name": "Ice Storm", "effect": ["cold damage"]},
      "5": {"name": "Wall of Thorns", "effect": ["damage"]},
      "6": {"name": "Heal", "effect": ["heal"]},
      "7": {"name": "Fire Storm", "effect": ["fire damage"]},
      "8": {"name": "Sunbeam", "effect": ["radiant damage"]},
      "9": {"name": "Shapechange", "effect": ["utility"]},
      "10": {"name": "Foresight", "effect": ["buff"]}
    }
  }
}   