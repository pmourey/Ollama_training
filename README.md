# 🎮 Résumé du Projet : Jeu de Combat Automatisé (RPG en mode batch)

Ce projet est un jeu de rôle (RPG) textuel automatisé, simulant des combats entre un groupe de héros (party) et des monstres. Le jeu est conçu pour fonctionner en mode batch, c'est-à-dire sans interface graphique, et peut être exécuté depuis la ligne de commande.

## 🔧 Fonctionnalités principales :

### 1. Génération de Party

Un groupe de héros est créé aléatoirement à partir de données stockées dans des fichiers JSON (`data/heroes.json`, `data/classes.json`, `data/races.json`, etc.).
Chaque héros possède :
- Classe (Fighter, Wizard, etc.)
- Race (Humain, Elfe, Nain, etc.)
- Attributs (Force, Dextérité, Intelligence, etc.)
- Arme, Armure, Bouclier
- Sorts (si applicable)
- Points de vie, XP, Or

### 2. Génération de Monstres

Des monstres sont générés aléatoirement à partir de types définis dans `data/monsters.json`. 
Le niveau des monstres est adapté au niveau moyen du groupe de héros.

Chaque monstre a :
- Un type (nom, niveau)
- Des statistiques (PV, CA, dégâts, XP, or)

### 3. Combat Automatisé

Les combats se déroulent en tour par tour, avec un ordre d'initiative basé sur les caractéristiques des personnages.
Les héros et monstres s'affrontent tour à tour :
- Attaques normales (avec arme)
- Sorts (si le personnage est un lanceur de sorts)
Les combats se terminent quand :
- Tous les héros sont morts → Défaite
- Tous les monstres sont morts → Victoire

### 4. Système de Niveau et d'Évolution

Les héros montent en niveau à mesure qu'ils gagnent de l'XP.
À chaque montée de niveau :
- Ils gagnent des PV
- Ils obtiennent de nouveaux sorts (selon leur classe)
- Ils reçoivent plus de fentes de sorts (spell slots)

### 5. Système de Sauvegarde et de Stats

À chaque 10 combats, le groupe se repose et se soigne (recharge des sorts, restauration des PV).
Des statistiques sont collectées :
- Nombre de monstres tués par niveau
- Sorts lancés
- XP et or gagnés

### 6. Mode Batch

Le jeu est conçu pour tourner en mode batch (sans interaction utilisateur pendant les combats). Un seul `input()` est utilisé à la fin de chaque round, si `BATCH_MODE = False`.

## 📁 Fichiers de données utilisés :
- `data/monsters.json` : Définitions des types de monstres
- `data/spells.json` : Sorts disponibles
- `data/classes.json` : Classes et règles de sorts
- `data/races.json` : Types de races
- `data/weapons.json`, `data/armors.json`, `data/shields.json` : Équipements
- `data/heroes.json` : Héros de départ

## 🧠 Objectif du Jeu :

Simuler un cycle de combats entre un groupe de héros et des monstres.
Observer l'évolution du groupe au fil des combats.
Collecter des statistiques de jeu pour analyser les performances et les tendances (ex : sorts utilisés, monstres tués par niveau, etc.)

## 🧪 Exemple de sortie :

```
====================================================================================================
DEBUG: 2024-06-23 09:20:00
====================================================================================================
Party Status: 6/6 
  Bilbo: Lvl 1 Rogue Hobbit (AC 14 - THACO 20 - Dagger 1d3) - STR 10 INT 12 WIS 12 DEX 14 CON 10 CHA 14 - HP 7/7 - OK, XP 0, 35 gp - 
  Aragorn: Lvl 1 Fighter Human (AC 14 - THACO 18 - Sword 1d6) - STR 14 INT 10 WIS 10 DEX 12 CON 13 CHA 14 - HP 10/10 - OK, XP 0, 100 gp - 
  Gimli: Lvl 1 Fighter Dwarf (AC 14 - THACO 16 - Axe 1d7) - STR 14 INT 10 WIS 10 DEX 12 CON 14 CHA 10 - HP 11/11 - OK, XP 0, 45 gp - 
  Lyra: Lvl 1 Bard Human (AC 12 - THACO 20 - Dagger 1d3) - STR 10 INT 12 WIS 12 DEX 14 CON 10 CHA 16 - HP 8/8 - OK, XP 0, 40 gp, Spells slots: [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]/[1, 0, 0, 0, 0, 0, 0, 0, 0, 0] - 1:Healing Word
  Gandalf: Lvl 1 Wizard Human (AC 11 - THACO 21 - Staff 1d4) - STR 8 INT 16 WIS 14 DEX 10 CON 12 CHA 15 - HP 8/8 - OK, XP 0, 50 gp, Spells slots: [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]/[3, 0, 0, 0, 0, 0, 0, 0, 0, 0] - 1:Shield
  Elrond: Lvl 1 Cleric Elf (AC 14 - THACO 19 - Mace 1d5) - STR 12 INT 12 WIS 15 DEX 10 CON 12 CHA 14 - HP 9/9 - OK, XP 0, 60 gp, Spells slots: [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]/[3, 0, 0, 0, 0, 0, 0, 0, 0, 0] - 1:Healing Word
====================================================================================================
STATS (Retour auberge tous les 10 combats): 675 victoires et 1026 monstres tués! 3352 sorts lancés!
====================================================================================================
Party Status: 0/6 
  Bilbo: Lvl 15 Rogue Hobbit (AC 14 - THACO 13 - Dagger 1d3) - STR 10 INT 12 WIS 12 DEX 14 CON 10 CHA 14 - HP -12/85 - OK, XP 7388, 681 gp - 
  Aragorn: Lvl 15 Fighter Human (AC 14 - THACO 4 - Sword 1d6) - STR 14 INT 10 WIS 10 DEX 12 CON 13 CHA 14 - HP -28/71 - OK, XP 7434, 748 gp - 
  Gimli: Lvl 15 Fighter Dwarf (AC 14 - THACO 2 - Axe 1d7) - STR 14 INT 10 WIS 10 DEX 12 CON 14 CHA 10 - HP -17/86 - OK, XP 7384, 692 gp - 
  Lyra: Lvl 15 Bard Human (AC 12 - THACO 13 - Dagger 1d3) - STR 10 INT 12 WIS 12 DEX 14 CON 10 CHA 16 - HP -8/70 - OK, XP 7404, 690 gp, Spells slots: [0, 9, 9, 9, 4, 0, 6, 0, 0, 0]/[9, 9, 9, 9, 9, 9, 6, 1, 0, 0] - 1:Healing Word|1:Dissonant Whispers|2:Calm Emotions|2:Shatter|2:Vicious Mockery|1:Sleep|4:Shout of Discord|4:Compulsive Dance|3:Hypnotic Pattern|3:Fear|6:Shout of Triumph|5:Synaptic Static|7:Ethereal Melody|4:Confusion|8:Feeblemind
  Gandalf: Lvl 15 Wizard Human (AC 11 - THACO 17 - Staff 1d4) - STR 8 INT 16 WIS 14 DEX 10 CON 12 CHA 15 - HP -16/78 - OK, XP 7449, 700 gp, Spells slots: [9, 9, 9, 9, 1, 0, 0, 0, 0, 0]/[9, 9, 9, 9, 9, 8, 6, 3, 0, 0] - 1:Shield|1:Fire Bolt|1:Magic Missile|2:Blindness|2:Scorching Ray|2:Acid Arrow|3:Lightning Bolt|3:Fireball|3:Slow|4:Blight|4:Ice Storm|4:Phantasmal Killer|5:Cone of Cold|5:Hold Monster|5:Cloudkill|6:Sunbeam|6:Disintegrate|6:Chain Lightning|7:Finger of Death|7:Delayed Blast Fireball|7:Prismatic Spray|8:Incendiary Cloud|8:Sunburst
  Elrond: Lvl 15 Cleric Elf (AC 14 - THACO 11 - Mace 1d5) - STR 12 INT 12 WIS 15 DEX 10 CON 12 CHA 14 - HP -11/75 - OK, XP 7347, 700 gp, Spells slots: [9, 9, 9, 3, 1, 0, 7, 2, 0, 0]/[9, 9, 9, 9, 9, 9, 7, 2, 0, 0] - 1:Healing Word|1:Cure Wounds|1:Guiding Bolt|2:Heal|2:Spiritual Weapon|2:Lesser Restoration|3:Greater Heal|3:Spirit Guardians|3:Bestow Curse|4:Sacred Radiance|4:Death Ward|4:Guardian of Faith|5:Mass Cure Wounds|5:Flame Strike|5:Insect Plague|6:Harm|6:Heal Divine|6:Blade Barrier|7:Divine Word|7:Resurrection|7:Fire of Judgment|8:Holy Aura|8:Earthquake|8:Unholy Blight

Monster Status:
  Storm Giant (Lvl 15 - AC 16): HP 42/185
  Purple Worm (Lvl 15 - AC 18): HP 32/304

Monsters kill stats
Lvl 1: {'Goblin': 81, 'Kobold': 93, 'Skeleton': 72, 'Giant Rat': 87}
Lvl 2: {'Orc': 60, 'Zombie': 37, 'Wizard': 40, 'Bandit': 49}
Lvl 3: {'Bugbear': 36, 'Dire Wolf': 31, 'Acolyte': 26, 'Imp': 28}
Lvl 4: {'Ogre': 21, 'Gargoyle': 23, 'Harpy': 17, 'Cult Fanatic': 23}
Lvl 5: {'Ghoul': 24, 'Griffon': 19, 'Basilisk': 15, 'Druid Apprentice': 20}
Lvl 6: {'Dragon Whelp': 11, 'Manticore': 10, 'Minotaur': 14, 'Mage': 16}
Lvl 7: {'Mummy': 7, 'Wyvern': 16, 'Owlbear': 11, 'Succubus': 13}
Lvl 8: {'Troll': 6, 'Green Hag': 12, 'Cyclops': 7, 'Werewolf': 6}
Lvl 9: {'Vampire Spawn': 8, 'Night Hag': 8, 'Chimera': 6, 'Flesh Golem': 8}
Lvl 10: {'Hill Giant': 2, 'Young White Dragon': 4, 'Mind Flayer': 7, 'Bone Devil': 4}
Lvl 11: {'Hydra': 1, 'Stone Golem': 3, 'Young Black Dragon': 2, 'Efreeti': 2}
Lvl 12: {'Frost Giant': 2, 'Young Blue Dragon': 4, 'Archmage': 3, 'Beholder': 2}
Lvl 13: {'Fire Giant': 2, 'Young Red Dragon': 2, 'Githyanki Supreme': 4, 'Nal feshnee Demon': 1}
Lvl 14: {'Iron Golem': 1, 'Adult White Dragon': 2, 'Ice Devil': 1, 'Rakshasa': 1}
Lvl 15: {'Adult Green Dragon': 0, 'Purple Worm': 0, 'Vampire Lord': 1, 'Storm Giant': 0}
Lvl 16: {'Adult Blue Dragon': 0, 'Marilith Demon': 0, 'Planetar Angel': 0, 'Mummy Lord': 0}
Lvl 17: {'Adult Red Dragon': 0, 'Goristro Demon': 0, 'Death Knight': 0, 'Androsphinx': 0}
Lvl 18: {'Lich': 0, 'Balor Demon': 0, 'Ancient White Dragon': 0, 'Pit Fiend Devil': 0}
Lvl 19: {'Ancient Blue Dragon': 0, 'Ancient Green Dragon': 0, 'Kraken': 0, 'Solar Angel': 0}
Lvl 20: {'Ancient Red Dragon': 0, 'Tarrasque': 0, 'Empyrean': 0, 'Ancient Gold Dragon': 0}

Spells cast stats
Lvl 1: {'Fire Bolt': 0, 'Magic Missile': 290, 'Shield': 0, 'Healing Word': 379, 'Cure Wounds': 180, 'Guiding Bolt': 110, 'Sleep': 0, 'Dissonant Whispers': 77, 'Ice Lance': 0, 'Entangle': 0, 'Burning Hands': 0, 'Shield Wild': 0, 'Bless': 0, 'Cure Wounds Light': 0, 'Searing Smite': 0}
Lvl 2: {'Scorching Ray': 7, 'Acid Arrow': 232, 'Blindness': 0, 'Heal': 177, 'Spiritual Weapon': 76, 'Lesser Restoration': 0, 'Vicious Mockery': 0, 'Shatter': 244, 'Calm Emotions': 0, 'Flame Blade': 0, 'Moonbeam': 0, 'Healing Spirit': 0, "Melf's Minute Meteors": 0, 'Divine Smite': 0, 'Thunderous Smite': 0, 'Shield of Faith': 0}
Lvl 3: {'Fireball': 0, 'Lightning Bolt': 248, 'Slow': 0, 'Greater Heal': 221, 'Spirit Guardians': 55, 'Bestow Curse': 0, 'Hypnotic Pattern': 0, 'Fear': 0, 'Stinking Cloud': 0, 'Call Lightning': 0, 'Erupting Earth': 0, 'Dispel Magic': 0, 'Fireball Wild': 0, 'Haste': 0, 'Blinding Smite': 0, 'Elemental Smite': 0, 'Revivify': 0}
Lvl 4: {'Ice Storm': 0, 'Blight': 176, 'Phantasmal Killer': 0, 'Sacred Radiance': 0, 'Death Ward': 121, 'Guardian of Faith': 0, 'Compulsive Dance': 0, 'Confusion': 0, 'Shout of Discord': 161, 'Grasping Vine': 0, 'Vitriolic Sphere': 0, 'Ice Storm Sorcery': 0, 'Blight Force': 0, 'Aura of Life': 0, 'Staggering Smite': 0, 'Death Ward Faith': 0}
Lvl 5: {'Cone of Cold': 91, 'Cloudkill': 0, 'Hold Monster': 0, 'Mass Cure Wounds': 103, 'Flame Strike': 0, 'Insect Plague': 4, 'Synaptic Static': 71, 'Wrath of Nature': 0, 'Antilife Shell': 0, 'Immolation': 0, 'Cone of Cold Sorcery': 0, 'Hold Monster Wild': 0, 'Destructive Wave': 0, 'Banishing Smite': 0, 'Holy Cure Wounds': 0}
Lvl 6: {'Disintegrate': 87, 'Chain Lightning': 0, 'Sunbeam': 0, 'Harm': 0, 'Heal Divine': 99, 'Blade Barrier': 0, 'Shout of Triumph': 87, 'Eyebite': 0, "Otto's Irresistible Dance": 0, 'Wall of Thorns': 0, 'Heal Nature': 0, 'Chain Lightning Sorcery': 0, 'Disintegrate Wild': 0, 'Sunbeam Wild': 0, 'Holy Cleave': 0, 'Aura of Devotion': 0, 'Chilling Smite': 0}
Lvl 7: {'Delayed Blast Fireball': 0, 'Finger of Death': 42, 'Prismatic Spray': 0, 'Divine Word': 0, 'Resurrection': 0, 'Fire of Judgment': 0, 'Power Word: Pain': 0, 'Ethereal Melody': 0, 'Regenerate': 0, 'Fire Storm': 0, 'Reverse Gravity': 0, 'Whirlwind': 0, 'Prismatic Spray Sorcery': 0, 'Delayed Fireball': 0, 'Finger of Ruin': 0, 'Shield of Valor': 0, 'Radiant Weapon': 0, 'Acidic Vow': 0}
Lvl 8: {'Sunburst': 0, 'Incendiary Cloud': 9, 'Mind Blank': 0, 'Holy Aura': 0, 'Earthquake': 2, 'Unholy Blight': 0, 'Feeblemind': 3, 'Power Word: Stun': 0, 'Animal Shapes': 0, 'Incendiary Cloud Sorcery': 0, 'Sunburst Wild': 0, 'Power Word Stun Sorcery': 0, 'Cleansing Touch': 0, 'Holy Bastion': 0, 'Necrotic Smite': 0}
Lvl 9: {'Meteor Swarm': 0, 'Time Stop': 0, 'Power Word Kill': 0, 'Mass Heal': 0, 'Gate': 0, 'Storm of Judgment': 0, 'Psychic Scream': 0, 'Foresight': 0, 'Storm of Vengeance': 0, 'Shapechange': 0, 'Foresight Nature': 0, 'Meteor Swarm Sorcery': 0, 'Wish Wild': 0, 'Power Word Kill Sorcery': 0, 'Righteous Verdict': 0, 'Aura of Supremacy': 0, 'Sonic Smite': 0}

```

## 📌 Conclusion :

C'est un simulateur de combat RPG en mode batch, parfait pour les tests automatisés, l'analyse statistique de gameplay ou l'expérimentation de mécaniques de jeu (classes, sorts, niveaux, etc.). Il est entièrement paramétrable via des fichiers JSON et peut être étendu facilement.
