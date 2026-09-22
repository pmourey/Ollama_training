🎮 Résumé du Projet : Jeu de Combat Automatisé (RPG en mode batch)

Ce projet est un jeu de rôle (RPG) textuel automatisé, simulant des combats entre un groupe de héros (party) et des monstres. Le jeu est conçu pour fonctionner en mode batch, c’est-à-dire sans interface graphique, et peut être exécuté depuis la ligne de commande.

🔧 Fonctionnalités principales :
1. Génération de Party
Un groupe de héros est créé aléatoirement à partir de données stockées dans des fichiers JSON (heroes.json, classes.json, races.json, etc.).
Chaque héros possède :
- Classe (Fighter, Wizard, etc.)
- Race (Humain, Elfe, Nain, etc.)
- Attributs (Force, Dextérité, Intelligence, etc.)
- Arme, Armure, Bouclier
- Sorts (si applicable)
- Points de vie, XP, Or

2. Génération de Monstres
Des monstres sont générés aléatoirement à partir de types définis dans monsters.json.
Le niveau des monstres est adapté au niveau moyen du groupe de héros.
Chaque monstre a :
- Un type (nom, niveau)
- Des statistiques (PV, CA, dégâts, XP, or)

3. Combat Automatisé
Les combats se déroulent en tour par tour, avec un ordre d'initiative basé sur les caractéristiques des personnages.
Les héros et monstres s’affrontent tour à tour :
- Attaques normales (avec arme)
- Sorts (si le personnage est un lanceur de sorts)
Les combats se terminent quand :
- Tous les héros sont morts → Défaite
- Tous les monstres sont morts → Victoire

4. Système de Niveau et d'Évolution
Les héros montent en niveau à mesure qu’ils gagnent de l’XP.
À chaque montée de niveau :
- Ils gagnent des PV
- Ils obtiennent de nouveaux sorts (selon leur classe)
- Ils reçoivent plus de fentes de sorts (spell slots)

5. Système de Sauvegarde et de Stats
À chaque 10 combats, le groupe se repose et se soigne (recharge des sorts, restauration des PV).
Des statistiques sont collectées :
- Nombre de monstres tués par niveau
- Sorts lancés
- XP et or gagnés

6. Mode Batch
Le jeu est conçu pour tourner en mode batch (sans interaction utilisateur pendant les combats).
Un seul input() est utilisé à la fin de chaque round, si BATCH_MODE = False.

📁 Fichiers de données utilisés :
- monsters.json : Définitions des types de monstres
- spells.json : Sorts disponibles
- classes.json : Classes et règles de sorts
- races.json : Types de races
- weapons.json, armors.json, shields.json : Équipements
- heroes.json : Héros de départ

🧠 Objectif du Jeu :

Simuler un cycle de combats entre un groupe de héros et des monstres.
Observer l’évolution du groupe au fil des combats.
Collecter des statistiques de jeu pour analyser les performances et les tendances (ex : sorts utilisés, monstres tués par niveau, etc.)

🧪 Exemple de sortie :

```COMBAT BEGINS!
------------------------------------------------------------
ROUND 1 ------------------
  Hero1: Lvl 3 Fighter Human - HP 20/20, XP 150, Gold 25
  Monster1: HP 12/12
VICTORY! Each member gained 30 XP and earned 15 gp
```

📌 Conclusion :
C’est un simulateur de combat RPG en mode batch, parfait pour les tests automatisés, l’analyse statistique de gameplay ou l’expérimentation de mécaniques de jeu (classes, sorts, niveaux, etc.). Il est entièrement paramétrable via des fichiers JSON et peut être étendu facilement.

Souhaitez-vous que je vous aide à ajouter des fonctionnalités, améliorer les performances, ou générer des rapports de statistiques ? SURTOUT PAS :-D