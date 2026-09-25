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
## Fichier JSON data/spells.json: Grimoire Complet (6 classes x 10 niveaux)
Ce fichier respecte scrupuleusement la structure de vos données en l'adaptant à l'identité magique de chaque classe (Arcane pour Wizard/Sorcerer, Divine pour Cleric/Paladin, Nature pour Druid, et Mentale/Soutien pour Bard). Chaque classe possède 1 sort unique par niveau, du niveau 1 au niveau 10, soit 60 sorts au total.
