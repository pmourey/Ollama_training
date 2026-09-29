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
    QListWidgetItem, QTextBrowser, QComboBox
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
            # Spell points (only for casters)
            has_spell_slots = any(getattr(character, 'max_spell_slots', []) or []) or bool(getattr(character, 'spells', None))
            if has_spell_slots:
                sp_total = sum(getattr(character, 'current_spell_slots', []) or [])
                self.sp_label = QLabel(str(sp_total))
                self.overview_form.addRow('Spell Points:', self.sp_label)
            else:
                self.sp_label = None
            self.overview_form.addRow('Arme équipée:', self.weapon_label)
            self.overview_form.addRow('Armure équipée:', self.armor_label)
            self.overview_form.addRow('Bouclier équipé:', self.shield_label)
            # Gold and XP
            self.gold_label = QLabel(str(getattr(character, 'gold', 0)))
            self.xp_label = QLabel(str(getattr(character, 'xp', 0)))
            self.overview_form.addRow('Gold:', self.gold_label)
            self.overview_form.addRow('XP:', self.xp_label)
            # Worn items (rings, wondrous)
            worn_txt = '\n'.join([w.get('name') for w in getattr(character, 'worn', [])]) or '—'
            self.worn_label = QLabel(worn_txt)
            self.worn_label.setWordWrap(True)
            self.overview_form.addRow('Équipements portés:', self.worn_label)
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
            # update spell points only if label exists (caster)
            if getattr(self, 'sp_label', None) is not None:
                sp_total = sum(getattr(character, 'current_spell_slots', []) or [])
                self.sp_label.setText(str(sp_total))
            # update gold/xp
            if getattr(self, 'gold_label', None) is not None:
                self.gold_label.setText(str(getattr(character, 'gold', 0)))
            if getattr(self, 'xp_label', None) is not None:
                self.xp_label.setText(str(getattr(character, 'xp', 0)))
            worn_txt = '\n'.join([w.get('name') for w in getattr(character, 'worn', [])]) or '—'
            self.worn_label.setText(worn_txt)

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
            self.btn_use = QPushButton('🧪 Utiliser')
            self.btn_use.setEnabled(False)
            self.btn_use.clicked.connect(self._on_use_clicked)
            btn_row.addWidget(self.btn_use)
            # Single contextual unequip button: enabled when selected item is currently equipped/worn
            self.btn_unequip = QPushButton('🔄 Déséquiper')
            self.btn_unequip.setEnabled(False)
            self.btn_unequip.clicked.connect(self._on_unequip_selected)
            btn_row.addWidget(self.btn_unequip)
            inv_layout.addLayout(btn_row)

            # Transfer controls: choose recipient and transfer selected (non-equipped) item
            transfer_row = QHBoxLayout()
            self.transfer_recipient = QComboBox()
            # populate with other party members' names
            # parent may be the main CombatWindow; guard if not available
            p = self.parent()
            others = [h for h in getattr(p, 'party', []) if h is not self.character]
            for h in others:
                self.transfer_recipient.addItem(h.name, h)
            transfer_row.addWidget(QLabel('Transférer à:'))
            transfer_row.addWidget(self.transfer_recipient)
            self.btn_transfer = QPushButton('➡️ Transférer')
            self.btn_transfer.clicked.connect(self._on_transfer_clicked)
            transfer_row.addWidget(self.btn_transfer)
            inv_layout.addLayout(transfer_row)

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
            # tooltip shows description when hovering
            desc = item.get('desc') or item.get('description') or ''
            if desc:
                list_item.setToolTip(desc)
            self.inv_list.addItem(list_item)
        # enable/disable Use/Unequip button when selection changes
        self.inv_list.currentItemChanged.connect(self._on_inv_selection_changed)
        # ensure initial state
        self._on_inv_selection_changed()

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

    def _on_inv_selection_changed(self, current=None, previous=None):
        item = self._selected_item()
        if not item:
            if hasattr(self, 'btn_use'):
                self.btn_use.setEnabled(False)
            if hasattr(self, 'btn_unequip'):
                self.btn_unequip.setEnabled(False)
            if hasattr(self, 'btn_transfer'):
                self.btn_transfer.setEnabled(False)
            return
        # Enable Use for potions only
        if hasattr(self, 'btn_use'):
            self.btn_use.setEnabled(item.get('type') == 'potion')
        # Enable unequip if selected item is equipped/worn
        if hasattr(self, 'btn_unequip'):
            is_equipped = False
            # check hero slots
            if self.is_hero:
                itype = item.get('type')
                if itype in ('weapon', 'armor', 'shield'):
                    is_equipped = self.character._is_equipped(item)
                elif itype in ('ring', 'wondrous'):
                    is_equipped = any(w.get('name') == item.get('name') for w in getattr(self.character, 'worn', []))
            self.btn_unequip.setEnabled(is_equipped)
        # Enable transfer only for non-equipped items
        if hasattr(self, 'btn_transfer'):
            can_transfer = not self.character._is_equipped(item) if self.is_hero else False
            self.btn_transfer.setEnabled(can_transfer)

    def _on_equip_clicked(self):
        item = self._selected_item()
        if item is None:
            self.status_label.setText('Sélectionnez un objet à équiper.')
            return
        if item.get('type') not in ('weapon', 'armor', 'shield', 'ring', 'wondrous'):
            self.status_label.setText(f"{item.get('name', 'Objet')} ne peut pas être équipé.")
            return
        msg = self.character.equip_item(item)
        self.status_label.setText(msg)
        self._refresh_overview()
        self._refresh_inventory_list()

    # Unified unequip handler for selected item (weapon/armor/shield/ring/wondrous)
    def _on_unequip_selected(self):
        item = self._selected_item()
        if item is None:
            # if nothing selected, try to unequip nothing
            self.status_label.setText('Sélectionnez un objet équipé à déséquiper.')
            return
        itype = item.get('type')
        if itype == 'weapon':
            self.status_label.setText(self.character.unequip_weapon())
        elif itype == 'armor':
            self.status_label.setText(self.character.unequip_armor())
        elif itype == 'shield':
            self.status_label.setText(self.character.unequip_shield())
        elif itype in ('ring', 'wondrous'):
            # remove from worn by name
            name = item.get('name')
            self.status_label.setText(self.character.unequip_worn(name))
        else:
            self.status_label.setText(f"{item.get('name','Objet')} ne peut pas être déséquipé.")
        self._refresh_overview()
        self._refresh_inventory_list()

    def save_game(self):
        """Save minimal hero state to both JSON and (optionally) pickle for fidelity.
        NOTE: pickle is binary and should only be used locally; loading pickle executes code.
        Includes killed_monsters and total_kills so stats persist between sessions.
        """
        try:
            import json, os, pickle
            data = {'heroes': []}
            for h in self.party:
                data['heroes'].append({
                    'name': h.name,
                    'hp': h.hp,
                    'position': getattr(h, 'position', 'front'),
                    'inventory': getattr(h, 'inventory', []),
                    'worn': getattr(h, 'worn', [])
                })
            # include killed monsters stats
            data['killed_monsters'] = getattr(self, 'killed_monsters', {})
            data['total_kills'] = getattr(self, 'total_kills', 0)
            # write JSON (human-readable)
            with open('savegame.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # write pickle for a more complete snapshot (protocol highest)
            try:
                with open('savegame.pkl', 'wb') as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception as e:
                # non-fatal
                self.log_message(f"⚠️ Échec de l'écriture pickle: {e}")
            self.log_message('💾 Partie sauvegardée (savegame.json + savegame.pkl)')
        except Exception as e:
            self.log_message(f'⚠️ Échec de la sauvegarde: {e}')

    def show_killed_monsters(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('Monstres tués')
        dlg.resize(420, 360)
        layout = QVBoxLayout(dlg)
        total = getattr(self, 'total_kills', 0)
        lbl = QLabel(f'Total tués: {total}')
        layout.addWidget(lbl)
        listw = QListWidget()
        items = sorted(getattr(self, 'killed_monsters', {}).items(), key=lambda kv: kv[1], reverse=True)
        if not items:
            listw.addItem("Aucun monstre tué pour l'instant.")
        for name, count in items:
            listw.addItem(f"{name}: {count}")
        layout.addWidget(listw)
        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        dlg.exec()

    def _on_remove_clicked(self):
        item = self._selected_item()
        if item is None:
            self.status_label.setText('Sélectionnez un objet à supprimer.')
            return
        msg = self.character.remove_from_inventory(item)
        self.status_label.setText(msg)
        self._refresh_overview()
        self._refresh_inventory_list()

    def _on_transfer_clicked(self):
        item = self._selected_item()
        if item is None:
            self.status_label.setText('Sélectionnez un objet à transférer.')
            return
        # cannot transfer equipped items
        if self.character._is_equipped(item):
            self.status_label.setText("Impossible de transférer un objet équipé. Déséquipez-le d'abord.")
            return
        recipient = None
        if hasattr(self, 'transfer_recipient'):
            recipient = self.transfer_recipient.currentData()
        if recipient is None:
            self.status_label.setText('Sélectionnez un destinataire valide.')
            return
        # perform transfer: remove from current inventory (by identity) and append to recipient
        idx = self.character._find_inventory_index(item)
        if idx is None:
            self.status_label.setText('Objet introuvable pour transfert.')
            return
        transferred = self.character.inventory.pop(idx)
        recipient.inventory.append(transferred)
        self.status_label.setText(f"{transferred.get('name','Objet')} transféré à {recipient.name}.")
        # refresh both dialogs/cards
        self._refresh_inventory_list()
        parent = self.parent()
        try:
            # refresh recipient card if present
            if hasattr(parent, 'hero_cards') and recipient.id in parent.hero_cards:
                parent.hero_cards[recipient.id].refresh()
        except Exception:
            pass
        # autosave
        try:
            self.save_game()
        except Exception:
            pass

    def _on_use_clicked(self):
        item = self._selected_item()
        if item is None:
            self.status_label.setText('Sélectionnez un objet à utiliser.')
            return
        # Delegate full gameplay effect to Hero.use_item
        msg = self.character.use_item(item)
        self.status_label.setText(msg)
        # if item is consumable, remove it from inventory
        if item.get('type') in ('potion', 'consumable'):
            self.character.remove_from_inventory(item)
        self._refresh_overview()
        self._refresh_inventory_list()
        # autosave after using an item
        try:
            self.save_game()
        except Exception:
            pass

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
        # track monsters killed by party this session
        # killed_monsters_counts maps monster name -> count
        self.killed_monsters: dict = {}
        self.total_kills: int = 0
        self._killed_names: set = set()
        # attempt to auto-load save file (prefer pickle for fidelity, fallback to json)
        try:
            import os, json, pickle
            save_pkl = os.path.join('.', 'savegame.pkl')
            save_json = os.path.join('.', 'savegame.json')
            if os.path.exists(save_pkl):
                # WARNING: loading pickle can execute arbitrary code. Only load trusted files.
                try:
                    with open(save_pkl, 'rb') as f:
                        data = pickle.load(f)
                    # expected structure: {'heroes': [hero_state_dicts...], 'killed_monsters': {...}, 'total_kills': N}
                    for hs in data.get('heroes', []):
                        for hero in self.party:
                            if hero.name == hs.get('name'):
                                # apply attributes that are safe/expected
                                hero.hp = hs.get('hp', hero.hp)
                                hero.position = hs.get('position', hero.position)
                                if 'worn' in hs:
                                    hero.worn = hs.get('worn', hero.worn)
                                if 'inventory' in hs:
                                    hero.inventory = hs.get('inventory', hero.inventory)
                    # restore killed stats if present
                    if 'killed_monsters' in data:
                        try:
                            self.killed_monsters = dict(data.get('killed_monsters') or {})
                            self.total_kills = int(data.get('total_kills', 0))
                        except Exception:
                            pass
                    if hasattr(self, 'log_message'):
                        self.log_message('🔄 Partie chargée depuis savegame.pkl (pickle)')
                    else:
                        print('🔄 Partie chargée depuis savegame.pkl (pickle)')
                except Exception as ex:
                    # on failure, fall back to json
                    print(f'⚠️ Échec du chargement pickle: {ex}')
            elif os.path.exists(save_json):
                with open(save_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # apply saved state to party by matching names
                for hs in data.get('heroes', []):
                    for hero in self.party:
                        if hero.name == hs.get('name'):
                            hero.hp = hs.get('hp', hero.hp)
                            hero.position = hs.get('position', hero.position)
                            # restore worn and inventory if present
                            if 'worn' in hs:
                                hero.worn = hs.get('worn', hero.worn)
                            if 'inventory' in hs:
                                hero.inventory = hs.get('inventory', hero.inventory)
                # restore killed stats from json if present
                if 'killed_monsters' in data:
                    try:
                        self.killed_monsters = dict(data.get('killed_monsters') or {})
                        self.total_kills = int(data.get('total_kills', 0))
                    except Exception:
                        pass
                # log if UI ready, otherwise print
                if hasattr(self, 'log_message'):
                    try:
                        self.log_message('🔄 Partie chargée depuis savegame.json')
                    except Exception:
                        print('🔄 Partie chargée depuis savegame.json')
                else:
                    print('🔄 Partie chargée depuis savegame.json')
        except Exception as e:
            if hasattr(self, 'log_message'):
                try:
                    self.log_message(f'⚠️ Échec du chargement de la sauvegarde: {e}')
                except Exception:
                    print(f'⚠️ Échec du chargement de la sauvegarde: {e}')
            else:
                print(f'⚠️ Échec du chargement de la sauvegarde: {e}')
        # keep originals to restore on close
        # Additional: ensure XP and gold from savegame.json (if any) are applied to heroes
        try:
            import os, json
            if os.path.exists('savegame.json'):
                with open('savegame.json', 'r', encoding='utf-8') as _f:
                    _data = json.load(_f)
                for hs in _data.get('heroes', []):
                    for hero in self.party:
                        if hero.name == hs.get('name'):
                            try:
                                hero.xp = hs.get('xp', getattr(hero, 'xp', 0))
                            except Exception:
                                pass
                            try:
                                hero.gold = hs.get('gold', getattr(hero, 'gold', 0))
                            except Exception:
                                pass
        except Exception:
            pass

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
        # Save/Load buttons
        self.btn_save = QPushButton('💾 Sauvegarder')
        self.btn_save.clicked.connect(self.save_game)
        controls.addWidget(self.btn_save)
        self.btn_show_kills = QPushButton('🗡️ Monstres tués')
        self.btn_show_kills.clicked.connect(self.show_killed_monsters)
        controls.addWidget(self.btn_show_kills)
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
        """Append a message to GUI log if available; fallback to print before UI ready."""
        for line in str(msg).splitlines() or ['']:
            try:
                if hasattr(self, 'log') and self.log is not None:
                    self.log.append(line)
                else:
                    print(line)
            except Exception:
                # Final fallback
                try:
                    print(line)
                except Exception:
                    pass
        try:
            if hasattr(self, 'log') and self.log is not None:
                bar = self.log.verticalScrollBar()
                bar.setValue(bar.maximum())
        except Exception:
            pass

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
        # note: do NOT clear killed_monsters here so the list accumulates across encounters
        # (clearing was causing previously recorded kills to be lost each victory)
        # self.killed_monsters.clear()

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
            # Equip/unequip/actions performed in the dialog change AC/weapon/worn;
            # refresh the on-screen card so the party panel stays in sync.
            if isinstance(character, Hero) and character.id in self.hero_cards:
                self.hero_cards[character.id].refresh()
            self.refresh_all_cards()
            self.update_action_buttons()
            # auto-save after changes to character sheet
            try:
                self.save_game()
            except Exception:
                pass

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
        # If monster died during combat resolution, record it for stats
        if monster.hp <= 0:
            # record kill via helper to avoid duplicates
            try:
                self._record_kill(monster)
            except Exception:
                pass

    def _record_kill(self, monster: Monster):
        """Record a monster kill: increment per-type counts and total.
        Uses name as key; duplicates are allowed and counted (multiple same-name kills).
        """
        try:
            name = monster.name or 'Unknown'
            lvl = getattr(monster, 'level', None)
            # increment count for this monster type
            self.killed_monsters[name] = self.killed_monsters.get(name, 0) + 1
            self.total_kills = getattr(self, 'total_kills', 0) + 1
            # also keep _killed_names for previously-seen types (not strictly required now)
            self._killed_names.add(name)
        except Exception:
            pass

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
            # ensure any newly-dead monsters are recorded
            for m in self.monsters:
                if m.hp <= 0:
                    self._record_kill(m)
            # Compute XP/GP totals like encounter.start_combat and distribute to survivors
            try:
                total_xp = sum((m.xp or 0) for m in self.monsters if m.hp <= 0)
                total_gp = sum((m.gold or 0) for m in self.monsters if m.hp <= 0)
                survivors = [h for h in self.party if h.hp > 0]
                if survivors and (total_xp > 0 or total_gp > 0):
                    per_xp = total_xp // len(survivors)
                    extra_xp = total_xp - per_xp * len(survivors)
                    per_gp = total_gp // len(survivors)
                    extra_gp = total_gp - per_gp * len(survivors)
                    for i, h in enumerate(survivors):
                        add_xp = per_xp + (extra_xp if i == 0 else 0)
                        add_gp = per_gp + (extra_gp if i == 0 else 0)
                        try:
                            h.xp = getattr(h, 'xp', 0) + add_xp
                            h.gold = getattr(h, 'gold', 0) + add_gp
                        except Exception:
                            pass
                        self.log_message(f'🏅 {h.name} reçoit {add_xp} XP et {add_gp} gp')
                # Distribute loot like console simulation
                from simulation import distribute_loot
                # Use weapons/armors/shields/magic_items loaded at start
                distribute_loot(self.monsters, survivors, self.weapons, self.armors, self.shields, self.magic_items)
                self.log_message('🧰 Loot distribué aux survivants.')
                # Refresh hero cards to show new equipment/inventory
                for card in self.hero_cards.values():
                    card.refresh()
                # autosave stats and hero state after victory so killed_monsters persist
                try:
                    self.save_game()
                except Exception:
                    pass
            except Exception as e:
                self.log_message(f'⚠️ Erreur lors de la distribution du butin/XP: {e}')
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
            # if target died from this attack, announce and record
            if target.hp <= 0:
                try:
                    self.log_message(f'{target.name} est vaincu !')
                except Exception:
                    pass
                try:
                    self._record_kill(target)
                except Exception:
                    pass
                break
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
        # after spells, check for defeated targets to announce and record
        for t in targets:
            if getattr(t, 'hp', 1) <= 0:
                try:
                    self.log_message(f'{t.name} est vaincu !')
                except Exception:
                    pass
                try:
                    self._record_kill(t)
                except Exception:
                    pass
        self.finish_hero_action()

    def finish_hero_action(self):
        self.turn_index += 1
        self.selected_target = None
        self.refresh_all_cards()
        if self.check_combat_end():
            return
        self.advance()

    # Persistence: save/load minimal hero state
    def save_game(self):
        """Save minimal hero state to both JSON and (optionally) pickle for fidelity.
        NOTE: pickle is binary and should only be used locally; loading pickle executes code.
        Includes killed_monsters and total_kills so stats persist between sessions.
        """
        try:
            import json, os, pickle
            data = {'heroes': []}
            for h in self.party:
                data['heroes'].append({
                    'name': h.name,
                    'hp': h.hp,
                    'position': getattr(h, 'position', 'front'),
                    'inventory': getattr(h, 'inventory', []),
                    'worn': getattr(h, 'worn', [])
                })
            # include killed monsters stats
            data['killed_monsters'] = getattr(self, 'killed_monsters', {})
            data['total_kills'] = getattr(self, 'total_kills', 0)
            # write JSON (human-readable)
            with open('savegame.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # try to write pickle for fidelity; ignore failure
            try:
                with open('savegame.pkl', 'wb') as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception as e:
                self.log_message(f"⚠️ Échec de l'écriture pickle: {e}")
            self.log_message('💾 Partie sauvegardée (savegame.json + savegame.pkl)')
        except Exception as e:
            self.log_message(f'⚠️ Échec de la sauvegarde: {e}')

    def show_killed_monsters(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('Monstres tués')
        dlg.resize(420, 360)
        layout = QVBoxLayout(dlg)
        total = getattr(self, 'total_kills', 0)
        lbl = QLabel(f'Total tués: {total}')
        layout.addWidget(lbl)
        listw = QListWidget()
        items = sorted(getattr(self, 'killed_monsters', {}).items(), key=lambda kv: kv[1], reverse=True)
        if not items:
            listw.addItem("Aucun monstre tué pour l'instant.")
        for name, count in items:
            listw.addItem(f"{name}: {count}")
        layout.addWidget(listw)
        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        dlg.exec()


if __name__ == '__main__':
    # Install global excepthook to capture unexpected exceptions to a log file
    import traceback, os
    def _log_exception(exc_type, exc_value, exc_tb):
        try:
            tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
            with open('debug_startup.log', 'a', encoding='utf-8') as f:
                f.write(tb)
            # also print to stderr for consoles
            print(tb, file=sys.stderr)
        except Exception:
            pass
    sys.excepthook = _log_exception

    try:
        app = QApplication(sys.argv)
        window = CombatWindow(party_level=3)
        window.show()
        ret = app.exec()
        # normal exit
        sys.exit(ret)
    except Exception as e:
        # log startup exception to file for inspection
        try:
            with open('debug_startup.log', 'a', encoding='utf-8') as f:
                f.write('=== Startup exception ===\n')
                traceback.print_exc(file=f)
                f.write('\n')
        except Exception:
            pass
        # re-raise so IDE shows the error as well
        raise
