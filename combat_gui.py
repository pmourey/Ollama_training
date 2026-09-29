"""GUI PySide6 pour la gestion interactive des combats.

Intègre le moteur de jeu existant (data/heroes.json, data/monsters.json,
models.character.Hero, models.monster.Monster, combat.battle.BattleSystem)
et laisse l'utilisateur jouer chaque tour de héros en choisissant une
action (Melee Attack ou Cast Spell) via des composants cliquables
(cartes de personnages/monstres, boutons de sorts) plutôt que des listes
déroulantes.
"""
from __future__ import annotations

import random as pyrandom
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QScrollArea,
    QSizePolicy, QTextEdit, QVBoxLayout, QWidget,
)

import game_state
from combat.battle import BattleSystem
from combat.combatant import Combatant
from combat.encounter import calculate_initiative
from loaders.game_data import load_game_data
from models.character import Hero
from models.enums import Condition
from models.monster import Monster
from models.spell import Spell
from simulation import build_party_from_heroes, create_sample_monsters

BENEFICIAL_EFFECTS = {'heal', 'buff', 'shield'}


def is_beneficial(spell: Spell) -> bool:
    """Sorts qui doivent viser un allié plutôt qu'un monstre."""
    return spell.effect in BENEFICIAL_EFFECTS


class CharacterCard(QFrame):
    """Carte cliquable représentant un héros ou un monstre (cible d'action)."""

    clicked = Signal(object)
    double_clicked = Signal(object)

    def __init__(self, character, subtitle_fn, extra_fn=None):
        super().__init__()
        self.character = character
        self._subtitle_fn = subtitle_fn
        self._extra_fn = extra_fn
        self.selected = False
        self.is_turn = False

        self.setFixedSize(175, 112)
        self.setCursor(Qt.PointingHandCursor)
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        self.name_label = QLabel()
        # Force a high-contrast text color so names remain readable on light backgrounds
        self.name_label.setStyleSheet('font-weight: bold; font-size: 13px; color: #111;')
        layout.addWidget(self.name_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setStyleSheet('color: #444; font-size: 10px;')
        layout.addWidget(self.subtitle_label)

        self.hp_bar = QProgressBar()
        self.hp_bar.setFixedHeight(15)
        self.hp_bar.setTextVisible(True)
        layout.addWidget(self.hp_bar)

        self.extra_label = QLabel()
        self.extra_label.setStyleSheet('font-size: 10px; color: #333;')
        self.extra_label.setWordWrap(True)
        layout.addWidget(self.extra_label)

        self.refresh()

    def mousePressEvent(self, event):
        if self.character.hp > 0:
            self.clicked.emit(self.character)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        # Emit a dedicated double-click signal to open detailed sheet dialogs.
        if self.character.hp > 0:
            self.double_clicked.emit(self.character)
        super().mouseDoubleClickEvent(event)

    def set_selected(self, value: bool):
        self.selected = value
        self._apply_style()

    def set_is_turn(self, value: bool):
        self.is_turn = value
        self._apply_style()

    def _apply_style(self):
        if self.selected:
            border = '3px solid #2b7de9'
        elif self.is_turn:
            border = '3px solid #e9a62b'
        else:
            border = '1px solid #999999'
        bg = '#f7f7f7' if self.character.hp > 0 else '#dddddd'
        self.setStyleSheet(f'CharacterCard {{ border: {border}; border-radius: 8px; background: {bg}; }}')

    def refresh(self):
        c = self.character
        self.name_label.setText(c.name)
        self.subtitle_label.setText(self._subtitle_fn(c))

        max_hp = max(1, c.max_hp)
        self.hp_bar.setMaximum(max_hp)
        self.hp_bar.setValue(max(0, c.hp))
        pct = max(0, c.hp) / max_hp
        color = '#4caf50' if pct > 0.5 else ('#ff9800' if pct > 0.2 else '#f44336')
        self.hp_bar.setStyleSheet(f'QProgressBar::chunk {{ background-color: {color}; }}')
        self.hp_bar.setFormat('💀 Mort' if c.hp <= 0 else f'{max(0, c.hp)}/{c.max_hp} PV')

        self.extra_label.setText(self._extra_fn(c) if self._extra_fn else '')
        self._apply_style()


from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QTabWidget, QFormLayout, QListWidget,
    QListWidgetItem, QTextBrowser,
)


class CharacterSheetDialog(QDialog):
    """Dialog modal tabbed affichant fiche, inventaire et sorts d'un héros/monstre.

    Pour les héros, l'onglet Inventaire permet d'équiper/déséquiper des armes,
    armures et boucliers, et de supprimer des objets de l'inventaire.
    """

    def __init__(self, parent, character):
        super().__init__(parent)
        self.character = character
        self.is_hero = isinstance(character, Hero)
        self.setWindowTitle(f"Fiche de {getattr(character, 'name', 'Personnage')}")
        self.resize(560, 460)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        self._build_overview_tab()
        self._build_inventory_tab()
        self._build_spells_tab()

        layout.addWidget(self.tabs)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    # ------------------------------------------------------------ Overview
    def _build_overview_tab(self):
        character = self.character
        overview = QWidget()
        self.overview_form = QFormLayout(overview)
        self.overview_form.addRow('Nom:', QLabel(getattr(character, 'name', '—')))
        self.overview_form.addRow('Niveau:', QLabel(str(getattr(character, 'level', '—'))))
        if self.is_hero:
            self.overview_form.addRow('Classe:', QLabel(str(character.class_type.value)))
            self.overview_form.addRow('Race:', QLabel(str(character.race.type.value)))
        self.overview_form.addRow('HP:', QLabel(f"{getattr(character, 'hp', '—')}/{getattr(character, 'max_hp', '—')}"))
        self.ac_label = QLabel(str(getattr(character, 'armor_class', '—')))
        self.overview_form.addRow('AC:', self.ac_label)
        if self.is_hero:
            self.weapon_label = QLabel(str(character.weapon))
            self.armor_label = QLabel(str(character.armor.name))
            self.shield_label = QLabel(str(character.shield.name))
            self.overview_form.addRow('Arme équipée:', self.weapon_label)
            self.overview_form.addRow('Armure équipée:', self.armor_label)
            self.overview_form.addRow('Bouclier équipé:', self.shield_label)
        self.overview_form.addRow('Strength:', QLabel(str(character.str)))
        self.overview_form.addRow('Dexterity:', QLabel(str(character.dex)))
        self.overview_form.addRow('Constitution:', QLabel(str(character.con)))
        self.overview_form.addRow('Intelligence:', QLabel(str(character.int)))
        self.overview_form.addRow('Wisdom:', QLabel(str(character.wis)))
        self.overview_form.addRow('Charisme:', QLabel(str(character.cha)))
        self.tabs.addTab(overview, 'Aperçu')

    def _refresh_overview(self):
        character = self.character
        self.ac_label.setText(str(getattr(character, 'armor_class', '—')))
        if self.is_hero:
            self.weapon_label.setText(str(character.weapon))
            self.armor_label.setText(str(character.armor.name))
            self.shield_label.setText(str(character.shield.name))

    # ------------------------------------------------------------ Inventory
    def _build_inventory_tab(self):
        character = self.character
        inv = QWidget()
        inv_layout = QVBoxLayout(inv)
        self.inv_list = QListWidget()
        inv_layout.addWidget(self.inv_list)

        if self.is_hero:
            self.status_label = QLabel('')
            self.status_label.setStyleSheet('color: #2b7de9;')
            inv_layout.addWidget(self.status_label)

            btn_row = QHBoxLayout()
            self.btn_equip = QPushButton('✅ Équiper')
            self.btn_equip.clicked.connect(self._on_equip_clicked)
            btn_row.addWidget(self.btn_equip)
            self.btn_unequip_weapon = QPushButton('🗡️ Déséquiper arme')
            self.btn_unequip_weapon.clicked.connect(self._on_unequip_weapon)
            btn_row.addWidget(self.btn_unequip_weapon)
            self.btn_unequip_armor = QPushButton('🛡️ Déséquiper armure')
            self.btn_unequip_armor.clicked.connect(self._on_unequip_armor)
            btn_row.addWidget(self.btn_unequip_armor)
            self.btn_unequip_shield = QPushButton('🔰 Déséquiper bouclier')
            self.btn_unequip_shield.clicked.connect(self._on_unequip_shield)
            btn_row.addWidget(self.btn_unequip_shield)
            inv_layout.addLayout(btn_row)

            btn_row2 = QHBoxLayout()
            self.btn_remove = QPushButton('🗑️ Supprimer de l\'inventaire')
            self.btn_remove.clicked.connect(self._on_remove_clicked)
            btn_row2.addWidget(self.btn_remove)
            inv_layout.addLayout(btn_row2)

        self.tabs.addTab(inv, 'Inventaire')
        self._refresh_inventory_list()

    def _refresh_inventory_list(self):
        self.inv_list.clear()
        for item in getattr(self.character, 'inventory', []) or []:
            equipped = self.is_hero and self.character._is_equipped(item)
            label = self._format_item(item) + (' (équipé)' if equipped else '')
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.UserRole, item)
            self.inv_list.addItem(list_item)

    @staticmethod
    def _format_item(item: dict) -> str:
        name = item.get('name', 'Objet')
        kind = item.get('type', '')
        if kind == 'weapon':
            return f"{name} (arme, dégâts 1d{item.get('damage', 4)})"
        if kind == 'armor':
            return f"{name} (armure, bonus +{item.get('bonus', 0)})"
        if kind == 'shield':
            return f"{name} (bouclier, bonus +{item.get('bonus', 0)})"
        rarity = item.get('rarity')
        suffix = f" ({rarity})" if rarity else ''
        return f"{name}{suffix}"

    def _selected_item(self) -> dict | None:
        list_item = self.inv_list.currentItem()
        if list_item is None:
            return None
        return list_item.data(Qt.UserRole)

    def _on_equip_clicked(self):
        item = self._selected_item()
        if item is None:
            self.status_label.setText('Sélectionnez un objet à équiper.')
            return
        if item.get('type') not in ('weapon', 'armor', 'shield'):
            self.status_label.setText(f"{item.get('name', 'Objet')} ne peut pas être équipé.")
            return
        msg = self.character.equip_item(item)
        self.status_label.setText(msg)
        self._refresh_overview()
        self._refresh_inventory_list()

    def _on_unequip_weapon(self):
        self.status_label.setText(self.character.unequip_weapon())
        self._refresh_overview()
        self._refresh_inventory_list()

    def _on_unequip_armor(self):
        self.status_label.setText(self.character.unequip_armor())
        self._refresh_overview()
        self._refresh_inventory_list()

    def _on_unequip_shield(self):
        self.status_label.setText(self.character.unequip_shield())
        self._refresh_overview()
        self._refresh_inventory_list()

    def _on_remove_clicked(self):
        item = self._selected_item()
        if item is None:
            self.status_label.setText('Sélectionnez un objet à supprimer.')
            return
        msg = self.character.remove_from_inventory(item)
        self.status_label.setText(msg)
        self._refresh_overview()
        self._refresh_inventory_list()

    # --------------------------------------------------------------- Spells
    def _build_spells_tab(self):
        character = self.character
        spells = QWidget()
        spells_layout = QVBoxLayout(spells)
        tb = QTextBrowser()
        spells_list = getattr(character, 'spells', None)
        if spells_list:
            lines = []
            for s in spells_list:
                # handle Spell-like objects or dicts
                name = getattr(s, 'name', s.get('name') if isinstance(s, dict) else str(s))
                lvl = getattr(s, 'level', s.get('level') if isinstance(s, dict) else '?')
                desc = getattr(s, 'description', s.get('description') if isinstance(s, dict) else '')
                lines.append(f"Niv.{lvl} {name}: {desc}")
            tb.setText('\n\n'.join(lines))
        else:
            tb.setText('Aucun sort connu.')
        spells_layout.addWidget(tb)
        self.tabs.addTab(spells, 'Sorts')

    def open(self):
        return super().exec()


def hero_subtitle(h: Hero) -> str:
    return f'{h.class_type.value} • {h.race.type.value} • Niv.{h.level} • AC.{h.armor_class}'


def hero_extra(h: Hero) -> str:
    parts = [
        f'Lv{i + 1}: {cur}/{mx}'
        for i, (cur, mx) in enumerate(zip(h.current_spell_slots, h.max_spell_slots))
        if mx > 0
    ]
    slots = ' | '.join(parts) if parts else '—'
    status = '' if h.condition == Condition.OK else f' ⚠ {h.condition.value}'
    return f'PS: {slots}{status}'


def monster_subtitle(m: Monster) -> str:
    return f'CA {m.armor_class} • Niv.{m.level}'


def monster_extra(m: Monster) -> str:
    return '' if m.condition == Condition.OK else f'⚠ {m.condition.value}'


class EmittingStream:
    """File-like object that redirects writes to a callable (GUI log)."""

    def __init__(self, write_callable):
        self.write_callable = write_callable

    def write(self, text):
        # ignore empty writes
        if text and not text.isspace():
            # Ensure newline separation
            for line in str(text).splitlines():
                try:
                    self.write_callable(line)
                except Exception:
                    pass

    def flush(self):
        pass


class CombatWindow(QMainWindow):
    def __init__(self, party_level=1):
        super().__init__()
        self.setWindowTitle('Gestion des Combats - Prototype')
        self.resize(1180, 760)

        (self.monster_types, self.spells, self.classes, self.races, self.weapons,
         self.armors, self.shields, self.heroes_data, self.spell_categories,
         self.magic_items, self.magic_config) = load_game_data()

        self.party: list[Hero] = build_party_from_heroes(
            self.heroes_data, self.spells, self.classes, self.races,
            self.weapons, self.armors, self.shields, self.spell_categories,
            party_size=6, party_level=party_level
        )
        # keep originals to restore on close
        import sys as _sys
        self._orig_stdout = _sys.stdout
        self._orig_stderr = _sys.stderr
        # Redirect stdout/stderr to GUI log
        _sys.stdout = EmittingStream(self.log_message)
        _sys.stderr = EmittingStream(self.log_message)
        self.monsters: list[Monster] = []

        self.order: list[Combatant] = []
        self.turn_index = 0
        self.current_hero: Hero | None = None
        self.selected_target = None
        self.combat_over = True
        self.round_num = 0

        self.hero_cards: dict[int, CharacterCard] = {}
        self.monster_cards: list[CharacterCard] = []
        self.spell_buttons: list[QPushButton] = []

        self._build_ui()

        # Redirige les messages du moteur de jeu vers la console de log.
        game_state.uprint = self.log_message

        self.new_encounter()

    def closeEvent(self, event):
        # restore stdout/stderr
        try:
            import sys as _sys
            if hasattr(self, '_orig_stdout') and _sys.stdout is not self._orig_stdout:
                _sys.stdout = self._orig_stdout
            if hasattr(self, '_orig_stderr') and _sys.stderr is not self._orig_stderr:
                _sys.stderr = self._orig_stderr
        except Exception:
            pass
        super().closeEvent(event)

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        left = QVBoxLayout()
        root.addLayout(left, 3)

        # Monsters panel
        monsters_group = QGroupBox('Monstres')
        self.monsters_layout = QHBoxLayout()
        self.monsters_layout.addStretch()
        monsters_group.setLayout(self.monsters_layout)
        left.addWidget(monsters_group)

        # Turn indicator
        self.turn_label = QLabel('—')
        self.turn_label.setStyleSheet('font-size: 15px; font-weight: bold; padding: 4px;')
        left.addWidget(self.turn_label)

        # Actions panel
        actions_group = QGroupBox('Actions')
        actions_layout = QVBoxLayout()
        actions_group.setLayout(actions_layout)

        melee_row = QHBoxLayout()
        self.btn_melee = QPushButton('⚔️  Melee Attack')
        self.btn_melee.setMinimumHeight(36)
        self.btn_melee.clicked.connect(self.on_melee)
        melee_row.addWidget(self.btn_melee)
        actions_layout.addLayout(melee_row)

        actions_layout.addWidget(QLabel('Sorts disponibles (clic = lancer sur la cible sélectionnée) :'))
        self.spells_container = QWidget()
        self.spells_layout = QHBoxLayout(self.spells_container)
        self.spells_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(90)
        scroll.setWidget(self.spells_container)
        actions_layout.addWidget(scroll)

        left.addWidget(actions_group)

        # Party panel
        party_group = QGroupBox("Groupe d'aventuriers")
        self.party_layout = QGridLayout()
        party_group.setLayout(self.party_layout)
        left.addWidget(party_group)

        # Bottom controls
        controls = QHBoxLayout()
        self.btn_new_encounter = QPushButton('🐉 Nouvelle Rencontre')
        self.btn_new_encounter.clicked.connect(self.new_encounter)
        controls.addWidget(self.btn_new_encounter)
        self.btn_rest = QPushButton('🏕️ Repos complet')
        self.btn_rest.clicked.connect(self.on_rest)
        controls.addWidget(self.btn_rest)
        left.addLayout(controls)

        # Log panel
        right = QVBoxLayout()
        root.addLayout(right, 2)
        right.addWidget(QLabel('Journal de combat'))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        right.addWidget(self.log)

        # Static party cards (6 slots, 3 columns x 2 rows)
        for idx, hero in enumerate(self.party):
            card = CharacterCard(hero, hero_subtitle, hero_extra)
            card.clicked.connect(self.on_target_clicked)
            card.double_clicked.connect(self.show_character_sheet)
            self.hero_cards[hero.id] = card
            self.party_layout.addWidget(card, idx // 3, idx % 3)

    # --------------------------------------------------------------- Log
    def log_message(self, msg: str = ''):
        for line in str(msg).splitlines() or ['']:
            self.log.append(line)
        bar = self.log.verticalScrollBar()
        bar.setValue(bar.maximum())

    # ---------------------------------------------------------- Encounter
    def new_encounter(self):
        if not any(h.hp > 0 for h in self.party):
            QMessageBox.warning(self, 'Groupe anéanti', "Tout le groupe est mort. Utilisez 'Repos complet' pour recommencer.")
            return
        count = pyrandom.randint(2, 4)
        alive_heroes = [h for h in self.party if h.hp > 0]
        party_level = sum(h.level for h in alive_heroes) / len(alive_heroes) if alive_heroes else 1
        selection = [m for m in self.monster_types if party_level - 1 < m.level <= party_level] or self.monster_types
        self.monsters = create_sample_monsters(selection, count)

        # Rebuild monster cards
        for card in self.monster_cards:
            self.monsters_layout.removeWidget(card)
            card.deleteLater()
        self.monster_cards = []
        self.monsters_layout.takeAt(self.monsters_layout.count() - 1)  # remove stretch
        for monster in self.monsters:
            card = CharacterCard(monster, monster_subtitle, monster_extra)
            card.clicked.connect(self.on_target_clicked)
            # monsters can also show a sheet on double-click (read-only)
            card.double_clicked.connect(self.show_character_sheet)
            self.monster_cards.append(card)
            self.monsters_layout.addWidget(card)
        self.monsters_layout.addStretch()

        for hero in self.party:
            hero.clear_effects()

        self.combat_over = False
        self.selected_target = None
        self.round_num = 0
        self.log_message('=' * 60)
        self.log_message('NOUVELLE RENCONTRE !')
        self.log_message('=' * 60)
        self.start_round()

    def show_character_sheet(self, character):
        """Open the modal character sheet dialog for a Hero/Monster."""
        try:
            dlg = CharacterSheetDialog(self, character)
            dlg.open()
        except Exception as e:
            # Fallback quick message if dialog construction fails
            QMessageBox.information(self, 'Fiche', f"{getattr(character, 'name', repr(character))}\n{e}")
        finally:
            # Equip/unequip actions performed in the dialog change AC/weapon;
            # refresh the on-screen card so the party panel stays in sync.
            if isinstance(character, Hero) and character.id in self.hero_cards:
                self.hero_cards[character.id].refresh()
            self.refresh_all_cards()
            self.update_action_buttons()

    def on_rest(self):
        for hero in self.party:
            hero.hp = hero.max_hp
            hero.clear_effects()
            for i in range(len(hero.current_spell_slots)):
                hero.current_spell_slots[i] = hero.max_spell_slots[i]
        for card in self.hero_cards.values():
            card.refresh()
        self.log_message('🏕️ Le groupe se repose : PV et emplacements de sorts restaurés.')
        self.new_encounter()

    # --------------------------------------------------------------- Turn
    def start_round(self):
        self.round_num += 1
        self.log_message(f'\n--- ROUND {self.round_num} ---')
        alive_heroes = [h for h in self.party if h.hp > 0]
        alive_monsters = [m for m in self.monsters if m.hp > 0]
        self.order = calculate_initiative(alive_heroes, alive_monsters)
        self.turn_index = 0
        self.advance()

    def advance(self):
        while self.turn_index < len(self.order):
            char = self.order[self.turn_index].character
            if char.hp <= 0:
                self.turn_index += 1
                continue
            if char.condition in (Condition.PARALYZED, Condition.UNCONSCIOUS):
                self.log_message(f'{char.name} est {char.condition.value} et ne peut pas agir !')
                self.turn_index += 1
                continue

            if isinstance(char, Hero):
                self.current_hero = char
                self.selected_target = None
                self.update_turn_ui()
                return  # attend l'action du joueur

            # Tour d'un monstre : résolu automatiquement.
            self.resolve_monster_turn(char)
            self.turn_index += 1
            self.refresh_all_cards()
            if self.check_combat_end():
                return

        # Fin de round : effets, puis round suivant.
        for creature in [*self.party, *self.monsters]:
            for msg in creature.tick_effects():
                self.log_message(msg)
        if self.check_combat_end():
            return
        self.start_round()

    def resolve_monster_turn(self, monster: Monster):
        alive_heroes = [h for h in self.party if h.hp > 0]
        if not alive_heroes:
            return
        front = [h for h in alive_heroes if getattr(h, 'position', 'front') == 'front']
        pool = front or alive_heroes
        target = max(pool, key=lambda h: h.hp)
        BattleSystem.combat(monster, target, self.party)
        if target.is_dead:
            self.log_message(f'{target.name} est tombé au combat !')

    def check_combat_end(self) -> bool:
        # Victory: all monsters dead
        if all(m.hp <= 0 for m in self.monsters):
            self.log_message('*** VICTOIRE ! ***')
            self.combat_over = True
            self.current_hero = None
            self.turn_label.setText('🏆 Victoire ! Lancez une nouvelle rencontre.')
            self.clear_spell_buttons()
            self.refresh_all_cards()
            self.update_action_buttons()
            # Distribute loot like console simulation
            try:
                from simulation import distribute_loot
                survivors = [h for h in self.party if h.hp > 0]
                # Use weapons/armors/shields/magic_items loaded at start
                distribute_loot(self.monsters, survivors, self.weapons, self.armors, self.shields, self.magic_items)
                self.log_message('🧰 Loot distribué aux survivants.')
                # Refresh hero cards to show new equipment/inventory
                for card in self.hero_cards.values():
                    card.refresh()
            except Exception as e:
                self.log_message(f'⚠️ Erreur lors de la distribution du butin: {e}')
            return True

        # Defeat: all heroes dead
        if all(h.hp <= 0 for h in self.party):
            self.log_message('*** DÉFAITE... tout le groupe est tombé. ***')
            self.combat_over = True
            self.current_hero = None
            self.turn_label.setText('💀 Défaite. Reposez le groupe pour recommencer.')
            self.clear_spell_buttons()
            self.refresh_all_cards()
            self.update_action_buttons()
            return True
        return False

    def update_turn_ui(self):
        self.turn_label.setText(f'🎯 Tour de : {self.current_hero.name} ({self.current_hero.class_type.value})')
        self.rebuild_spell_buttons()
        self.refresh_all_cards()
        self.update_action_buttons()

    # ------------------------------------------------------------ Targets
    def on_target_clicked(self, character):
        if self.combat_over or self.current_hero is None:
            return
        self.selected_target = character
        self.refresh_all_cards()
        self.update_action_buttons()

    def refresh_all_cards(self):
        for hero_id, card in self.hero_cards.items():
            card.refresh()
            card.set_selected(card.character is self.selected_target)
            card.set_is_turn(self.current_hero is not None and card.character is self.current_hero)
        for card in self.monster_cards:
            card.refresh()
            card.set_selected(card.character is self.selected_target)

    # ------------------------------------------------------------ Actions
    def update_action_buttons(self):
        can_act = not self.combat_over and self.current_hero is not None
        target_is_monster = isinstance(self.selected_target, Monster) and self.selected_target.hp > 0
        self.btn_melee.setEnabled(can_act and target_is_monster)

        for btn, spell in self.spell_buttons:
            slots_left = self.current_hero.current_spell_slots[spell.level - 1] if self.current_hero else 0
            ok_target = spell.multi_target or self._target_matches(spell)
            btn.setEnabled(can_act and slots_left > 0 and ok_target)

    def _target_matches(self, spell: Spell) -> bool:
        if self.selected_target is None or self.selected_target.hp <= 0:
            return False
        if is_beneficial(spell):
            return isinstance(self.selected_target, Hero)
        return isinstance(self.selected_target, Monster)

    def clear_spell_buttons(self):
        for btn, _ in self.spell_buttons:
            self.spells_layout.removeWidget(btn)
            btn.deleteLater()
        self.spell_buttons = []

    def rebuild_spell_buttons(self):
        self.clear_spell_buttons()
        if not self.current_hero:
            return
        for spell in self.current_hero.spells:
            slots_left = self.current_hero.current_spell_slots[spell.level - 1]
            slots_max = self.current_hero.max_spell_slots[spell.level - 1]
            icon = '💚' if is_beneficial(spell) else '🔥'
            label = f'{icon} {spell.name}\nNiv.{spell.level} ({slots_left}/{slots_max})'
            btn = QPushButton(label)
            btn.setMinimumSize(140, 70)
            btn.setToolTip(spell.description)
            btn.clicked.connect(lambda checked=False, s=spell: self.on_cast_spell(s))
            self.spells_layout.addWidget(btn)
            self.spell_buttons.append((btn, spell))

    def on_melee(self):
        hero = self.current_hero
        target = self.selected_target
        if not hero or not isinstance(target, Monster) or target.hp <= 0:
            return
        attacks = max(1, getattr(hero, 'multi_attack', 1))
        for _ in range(attacks):
            if hero.hp <= 0 or target.hp <= 0:
                break
            BattleSystem.melee_attack(hero, [target])
        self.finish_hero_action()

    def on_cast_spell(self, spell: Spell):
        hero = self.current_hero
        if not hero:
            return
        beneficial = is_beneficial(spell)
        pool = [h for h in self.party if h.hp > 0] if beneficial else [m for m in self.monsters if m.hp > 0]

        if spell.multi_target:
            targets = pool
        else:
            if self.selected_target in pool:
                targets = [self.selected_target]
            else:
                side = 'un allié' if beneficial else 'un monstre'
                self.log_message(f'⚠️ Sélectionnez {side} comme cible pour {spell.name}.')
                return

        hero.cast_spell(spell, targets)
        self.finish_hero_action()

    def finish_hero_action(self):
        self.turn_index += 1
        self.selected_target = None
        self.refresh_all_cards()
        if self.check_combat_end():
            return
        self.advance()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CombatWindow(party_level=20)
    window.show()
    sys.exit(app.exec())
