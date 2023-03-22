import sys
import re
from PyQt5 import QtWidgets, Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QApplication, QAction, QStackedWidget, QMainWindow, QMenu, QToolButton, QLabel, \
    QScrollArea, QSizePolicy, QVBoxLayout, QHeaderView, QCheckBox, QLineEdit, QComboBox, QSpinBox, QTableView, \
    QSpacerItem, QAbstractItemView, QTreeView, QPushButton, QListView, QRadioButton
from PyQt5.Qt import QStandardItem, QStandardItemModel, QWidget
from PyQt5.QtCore import Qt, QModelIndex

import sqlite3
from queue import Queue
from time import time
import datetime
import math

# MAIN THINGS TODO:
#  Deck creation - done
#  Review system and displaying flashcards - cover HTML w/ daniel
#  Create ui windows to house this in the meantime, should prevent wasting any time in the session
#   (this being the main window for editing flashcards, and windows for setting up formats for templates

# STATS WINDOWS Important - but not key functionality - would certainly add to complexity due to aggregate functions,
# try to get this working asap

#  Templates ^ part of displaying the flashcards - done, some testing done but do so more thoroughly later
#      - will need to add a field to the cards table for format type, could remove template field, but could prove
#      useful.
#      - new formats table will need to reference a template, used when parsing user input to check for valid fields.
#      - for this should replace templates combo box with a format sub-menu that opens up in a new window and changes
#      the text on confirming a format in the sub-window

# Client server socketing - (needed) - consider, if not added make sure to justify thoroughly and explain implementation
#   - For this, it seems to be that whenever a signal is activated on the client side,
#   relevant data passed to functions should be passed and executed on the server side, and any necessary data used in
#   displaying sent back to the client
#    work out sync or async model

#  User Profiles and Following Tab - extra
#  Importing delimted files into decks - also extra but probably more important
#  Add salt values to SHA-256 hash func - low priority, but maybe important for justification
#       -other possilbe justification is to create a hash function where you know exactly what is going on, despite
#       possible security flaws

# TODO - whenever a card is added/deleted to a public deck, can update for all users by checking the user_cards table
#  to see if the connection exists for all users with a user_decks connection to that card's parent deck

# todo - browse window components, WHEN DECK CLICKED - NEW WINDOW: DISPLAYS deck name, description, (creator),
#  (+ratings), sample of cards, options to either add deck to library (no modification of cards
#  and updates in line with changes made by the creator) or copy the deck (allows for modification of cards) - stats
#  for each, comments/ratings section.
#  also for need a bunch of selection statement to ensure consistent logic when adding decks to your library

# todo - consider adding another table linked to templates which organises how templates are displayed
# this is referenced above


class User:
    def __init__(self, id, name):
        # store general settings here (preferences in anki)
        self.id = id
        self.name = name


class Deck(QStandardItem):
    # todo - a lot of this class is redundant, loading data and configs is used, everything else is redundant,
    #  should check add_card code to see if it is needed or can be deleted,
    def __init__(self, id, user, desc='', creator_access=False, font_size=13, set_bold=False):
        super().__init__()

        fnt = QFont()
        fnt.setPointSize(font_size)
        fnt.setBold(set_bold)

        self.setEditable(False)
        self.setFont(fnt)

        self.udid = id
        self.user = user

        self.fetchdata()
        self.setText(self.name)

        """SELECT ud.id, d.name, d.desc, u.username FROM decks d INNER JOIN user_decks ud ON d.id 
                        = ud.deck_id INNER JOIN users u ON d.created_uid = u.id WHERE d.isPublic = 1 AND isDeleted = 0 AND 
                        ud.uid = d.created_uid"""

    def review(self):
        review = Review(self.sr, self)
        review.review()

    def add_card(self):
        # todo when adding a card maybe add it for all other users with access to the deck in user_decks.
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("SELECT created_uid FROM decks WHERE id = ?", (self.id,))
        if self.user.id != cur.fetchone()[0]:
            print("You are not the creator of this deck")
            return
        cur.execute("SELECT id, name, fields FROM templates")
        templates = cur.fetchall()
        tids = []
        print("TEMPLATES")
        for template in templates:
            tids.append(template[0])
            print(f"{template[0]} - {template[1]} | Fields: {template[2].split(',')}")
        template_id = None
        print(tids)
        while template_id not in tids:
            template_id = int(input("select template id..."))
            if template_id not in tids:
                print("invalid input")
        cur.execute("""SELECT fields FROM templates WHERE id = ?""", [template_id])
        fields = cur.fetchone()[0]
        card_data = []
        print(fields.split(","))
        for field in fields.split(","):
            card_data.append(input(f"Input data for {field}:"))
        card_data = ",".join(card_data)
        print(card_data)
        cur.execute("""INSERT INTO cards (data, deck_id, template_id, modified, created_uid)
                VALUES (?, ?, ?, ?, ?) RETURNING id""", (card_data, self.id, template_id, time(), self.user.id))
        cid = cur.fetchone()[0]
        cur.execute("""INSERT INTO user_cards (uid, cid, ef, ivl, type, status, reps, lapses, odue)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (self.user.id, cid, self.base_ef, None, 0, 0, 0, 0, time()))
        # set left to no of deck learning steps
        con.commit()
        cur.close()
        con.close()

    def configure_review_settings(self):
        # steps for when a card is in the learning phase - allow user to have as many steps of whatever intervals as
        # desired, if fail - card resets to first interval, if easy, immediately graduated. Also options for
        # graduating interval and easy interval.
        # Card base ease factor (recommended to be kept at 250%). New cards/day, order in which they are shown
        # Max daily reviews,
        # Lapse settings (when again is hit) - lapse steps, lapse interval (of previous interval) - what good interval becomes
        # Min interval, (possibly leeches).
        # reviews - hard interval, max interval, interval modifier (scalar multiple in interval calcs)
        # Easy bonus - easy interval multiplier.
        # (Bury related cards, not sure how you would detect this?)
        # Allow users to configure settings presets, or have them change them individually for each deck?
        # Could utilise join queries and have tables: settings (id, user, decks? or decks_settings pair table, settings)
        # or for the latter, just a single settings table (id, deck_id, user, settings...)
        # options to change base ease factor, multiplier, etc.

        pass

    def fetchdata(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT d.name, d.id, d.desc, ud.config_id, d.isPublic, d.created_uid, d.isDeleted 
        FROM user_decks ud INNER JOIN decks d ON ud.deck_id = d.id WHERE ud.id = ?""", (self.udid,))
        fetch = cur.fetchone()
        self.name, self.did, self.desc, self.config_id, self.public, self.creator_id, self.isDeleted = fetch
        self.config = Config(self.config_id)
        cur.execute("""SELECT COUNT (c.id) FROM cards c INNER JOIN decks d ON c.deck_id = d.id WHERE d.id = ?""", (self.did,))
        self.cardcount = cur.fetchone()[0]
        cur.close()
        con.close()

    def save(self):
        if self.user.id == self.creator_id:
            con = sqlite3.connect(database)
            cur = con.cursor()
            cur.execute(f"""UPDATE decks
            SET name = ?,
            desc = ?,
            modified = {time()},
            isPublic = ?,
            isDeleted = ?
            WHERE id = {self.did}""", (self.name, self.desc, self.public, self.isDeleted))
            con.commit()
            cur.close()
            con.close()
        else:
            print("deck accessed by user who is not the creator")
            return


class Flashcard(QStandardItem):
    def __init__(self, id, font_size=13, set_bold=False):
        super().__init__()

        fnt = QFont()
        fnt.setPointSize(font_size)
        fnt.setBold(set_bold)

        self.setEditable(False)
        self.setFont(fnt)

        self.id = id
        self.cid = None
        self.zip = None
        self.fetch_attributes()

        sortFieldData = self.data[self.fields.index(self.sortfield)]
        self.setText(sortFieldData)

    def fetch_attributes(self):
        con = sqlite3.connect(database)
        cur = con.cursor()

        cur.execute("""SELECT
                    c.id,
                    c.data,
                    c.deck_id,
                    c.modified,
                    c.template_id,
                    c.created_uid,
                    u.ef,
                    u.ivl,
                    u.lapses,
                    u.left,                    
                    u.status,
                    u.reps,
                    u.type,                  
                    u.due,
                    u.odue
                FROM user_cards u INNER JOIN cards c ON u.cid = c.id
                WHERE u.id = ?
                """, (self.id,))

        self.cid, self.data, self.deck_id, self.modified, self.template, self.creator_id, self.ease_factor, self.interval, self.lapses, self.left, \
            self.status, self.reps, self.type, self.due, self.original_due = cur.fetchone()
        cur.execute("""SELECT fields, sortfield
                                FROM templates
                                WHERE id = ?
                                """, [self.template])
        self.fields, self.sortfield = cur.fetchone()

        self.fields = self.fields.split(",")
        self.data = self.data.split(",")

        # can you combine these 2 commands?

        self.zip = dict(zip(self.fields, self.data))
        cur.close()
        con.close()

    def update(self, uid):
        # better to pass objects instead of uid so 'user'
        con = sqlite3.connect(database)
        cur = con.cursor()

        cur.execute("""SELECT created_uid FROM CARDS WHERE id = ?""", (self.cid,))
        created_user = cur.fetchone()[0]
        data = (",").join(self.data)
        if created_user == uid:
            cur.execute("""UPDATE cards
                        SET
                        data = ?,
                        deck_id = ?,
                        modified = ?,
                        template_id = ?
                        WHERE id = ?
                        """, (data, self.deck_id, self.modified, self.template, self.cid))
        else:
            print("You are not the creator of this card")
        con.commit()
        cur.close()
        con.close()

    def delete(self):
        pass
        # todo - want to transfer data to a temporary deletion table before actually deleting

    def review_update(self, new_ivl, new_ef, new_due):
        con = sqlite3.connect(database)
        cur = con.cursor()
        self.interval = new_ivl
        self.ease_factor = new_ef
        self.due = new_due
        print(f"Next due: {datetime.datetime.fromtimestamp(self.due)}")
        cur.execute("""UPDATE user_cards SET 
               ivl = ?,
               ef = ?,
               status = ?,
               reps = ?,
               lapses = ?,
               left = ?,
               due = ? 
               WHERE id = ? """, (
            self.interval, self.ease_factor, self.status, self.reps, self.lapses, self.left, self.due, self.id))
        con.commit()
        cur.close()
        con.close()


class Config(QStandardItem):
    # todo add fetching of spaced repetition settings
    def __init__(self, configid, font_size=13, set_bold=False):
        super().__init__()
        """
        values: [0: id, 1: uid, 2: new_delays, 3: new_grad_ivls, 4: new_init_ef, 5:new_per_day, 
        6: rev_per_day, 7: rev_easy_factor, 8: rev_hard_factor, 9: max_ivl, 10: lapse_delays, 11: lapse_percent, 
        12: min_ivl, 13: leech_fails, 14: name]
        """

        self.id = configid
        self.loadvalues()

        fnt = QFont()
        fnt.setPointSize(font_size)
        fnt.setBold(set_bold)

        self.setEditable(False)
        self.setFont(fnt)
        self.setText(self.name)

    def loadvalues(self):
        con = sqlite3.connect(database)
        cur = con.cursor()

        cur.execute("SELECT * FROM configs WHERE id = ?", [self.id])
        values = cur.fetchone()

        self.id, self.uid, self.new_delays, self.new_grad_ivls, self.new_init_ef, self.new_per_day, self.rev_per_day, \
            self.rev_easy_factor, self.rev_hard_factor, self.max_ivl, self.lapse_delays, self.lapse_percent, self.min_ivl, \
            self.leech_fails, self.name = values

        cur.close()
        con.close()

    def save(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute(f"""UPDATE configs
        SET new_delays = ?,
        new_grad_ivls = ?,
        new_init_ef = ?,
        new_per_day = ?,
        rev_per_day = ?,
        rev_easy_factor = ?,
        rev_hard_factor = ?,
        max_ivl = ?,
        lapse_delays = ?,
        lapse_percent = ?,
        min_ivl = ?,
        leech_fails = ?,
        name = ?
        WHERE id = ?
        """, (self.new_delays, self.new_grad_ivls, self.new_init_ef, self.new_per_day, self.rev_per_day, \
            self.rev_easy_factor, self.rev_hard_factor, self.max_ivl, self.lapse_delays, self.lapse_percent, self.min_ivl, \
            self.leech_fails, self.name, self.id))
        con.commit()
        cur.close()
        con.close()


class Template(QStandardItem):
    def __init__(self, id):
        super().__init__()
        self.id = id
        self.fields = None
        self.sortfield = None
        self.styling = None
        self.back = None
        self.front = None
        self.name = None
        self.fields = None
        self.load()
        self.setText(self.name)

    def load(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT name, fields, sortfield, front_format, back_format, styling FROM templates WHERE id = ?""", (self.id,))
        self.name, self.fields, self.sortfield, self.front, self.back, self.styling = cur.fetchone()
        cur.close()
        con.close()

    def addfield(self, field_name):
        fields = self.fields.split(",")
        fields.append(field_name)
        self.fields = ",".join(fields)

    def renamefield(self, old_name, new_name):
        fields = self.fields.split(",")
        fields[fields.index(old_name)] = new_name
        self.fields = ",".join(fields)

    def repositionfield(self, old_index, new_index):
        fields = self.fields.split(",")
        fields = repositionitem(fields, old_index, new_index)
        self.fields = ",".join(fields)

    def removefield(self, delfield):
        fields = self.fields.split(",")
        fields = [field for field in fields if field != delfield]
        self.fields = ",".join(fields)

def repositionitem(list, old_index, new_index):
    if old_index == new_index:
        return list

    item = list[old_index]
    if new_index < old_index:
        # shift items down
        for i in range(old_index, new_index, -1):
            list[i] = list[i - 1]
        list[new_index] = item
    elif new_index > old_index:
        # shift items up
        for i in range(old_index, new_index, 1):
            list[i] = list[i + 1]
        list[new_index] = item
    return list


"""WINDOW CLASSES"""


class WelcomeScreen(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("welcome.ui", self)
        self.login.clicked.connect(self.gotologin)
        self.createaccount.clicked.connect(self.gotocreation)

    def gotologin(self):
        stack.setCurrentIndex(1)

    def gotocreation(self):
        stack.setCurrentIndex(2)


class Login(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("login.ui", self)
        self.user = None
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.login.clicked.connect(self.loginfunction)
        self.createaccount.clicked.connect(lambda: stack.setCurrentIndex(2))

    def emptyedits(self):
        # to be used later if logout enabled
        self.emailfield.setText("")
        self.passwordfield.setText("")

    def loginfunction(self):
        if self.user:
            # clear all other windows if logged in previously
            self.user = None
            for i in range(stack.count() - 3):
                widget = stack.widget(3)
                stack.removeWidget(widget)
                widget.deleteLater()
                print(f"removed {i + 1}")
            pass

        email = self.emailfield.text()
        password = self.passwordfield.text()
        pw_hash = sha_256(password)

        if len(email) == 0 or len(password) == 0:
            self.error.setText("Please input all fields")
        else:
            con = sqlite3.connect(database)
            cur = con.cursor()
            cur.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
            result = cur.fetchone()
            if result:
                result_hash = result[0]
                if result_hash != pw_hash:
                    print("here")
                    self.error.setText("Incorrect Password")
                    return
                cur.execute("SELECT username, id FROM users WHERE email = ?",
                            (email,))
                name, uid = cur.fetchone()
                self.user = User(uid, name)
                stack.widget(2).user = self.user

                decksmain = DecksMain(self.user)
                addcard = AddCard(self.user)
                cardsmain = CardsMain(self.user)
                stats = StatsPage(self.user)
                browse = Browse(self.user)
                stack.addWidget(decksmain)
                stack.addWidget(addcard)
                stack.addWidget(cardsmain)
                stack.addWidget(stats)
                stack.addWidget(browse)

                gotodecks()

            else:
                self.error.setText("Email is not registered")
            cur.close()
            con.close()


class CreateAccount(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("create_account.ui", self)
        self.user = None
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.register_.clicked.connect(self.registeracc)
        self.login.clicked.connect(lambda: stack.setCurrentIndex(1))

    def emptyedits(self):
        # to be used later if logout enabled
        self.usernamefield.setText("")
        self.emailfield.setText("")
        self.passwordfield.setText("")

    def registeracc(self):
        if self.user:
            # clear all other windows if logged in previously
            self.user = None
            for i in range(stack.count() - 3):
                widget = stack.widget(3)
                stack.removeWidget(widget)
                widget.deleteLater()
                print(f"removed {i + 1}")
            pass

        username = self.usernamefield.text()
        email = self.emailfield.text()
        password = self.passwordfield.text()

        if len(email) == 0 or len(password) == 0 or len(username) == 0:
            self.error.setText("Please input all fields")
        else:
            con = sqlite3.connect(database)
            cur = con.cursor()
            cur.execute("SELECT email, username FROM users WHERE email = ? OR username = ?", (email, username))
            fetch = cur.fetchone()
            if fetch:
                if email == fetch[0]:
                    self.error.setText("Email already in use, please login")
                elif username == fetch[1]:
                    self.error.setText("Username already in use, please login")
            else:
                pw_hash = sha_256(password)
                cur.execute("""INSERT INTO users (username, password_hash, email, doc, dom) 
                    VALUES (?, ?, ?, ?, ?) RETURNING id""", (username, pw_hash, email, time(), time())
                            )
                uid = cur.fetchone()[0]
                cur.execute("""INSERT INTO configs (
                                                name,
                                                lapse_delays,
                                                lapse_percent,
                                                leech_fails,
                                                max_ivl,
                                                min_ivl,
                                                new_delays,
                                                new_grad_ivls,
                                                new_init_ef,
                                                new_per_day,
                                                rev_easy_factor,
                                                rev_hard_factor,
                                                rev_per_day,
                                                uid)
                                            VALUES (
                                                'default',
                                                10,
                                                50,
                                                8,
                                                36500,
                                                1,
                                                '1,10',
                                                '1,4',
                                                250,
                                                10,
                                                130,
                                                120,
                                                200,
                                                ?)""", (uid,)
                            )
                con.commit()

                self.user = User(uid, username)
                stack.widget(1).user = self.user

                decksmain = DecksMain(self.user)
                addcard = AddCard(self.user)
                cardsmain = CardsMain(self.user)
                stats = StatsPage(self.user)
                browse = Browse(self.user)
                stack.addWidget(decksmain)
                stack.addWidget(addcard)
                stack.addWidget(cardsmain)
                stack.addWidget(stats)
                stack.addWidget(browse)
                gotodecks()

            cur.close()
            con.close()


class DecksMain(QMainWindow):
    def __init__(self, user):
        super().__init__()
        loadUi("decksmain.ui", self)
        self.adddeckwindow = None
        self.user = user

        connectmainbuttons(self)

        # initialising the tree model
        self.treeModel = QStandardItemModel(0, 4, self.decktree)
        self.treeModel.setHeaderData(0, Qt.Horizontal, "Deck")
        self.treeModel.setHeaderData(1, Qt.Horizontal, "Desc")
        self.treeModel.setHeaderData(2, Qt.Horizontal, "New")
        self.treeModel.setHeaderData(3, Qt.Horizontal, "Due")

        # assigning the tree model to the treeview and connecting the treeview
        self.decktree.setModel(self.treeModel)
        self.decktree.clicked.connect(self.opendeck)

        # configuring the treeview
        self.decktree.header().setSectionsMovable(False)
        self.decktree.setColumnWidth(2, 40)
        self.decktree.setColumnWidth(3, 40)
        self.decktree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.decktree.header().setSectionResizeMode(2, QHeaderView.Fixed)
        self.decktree.header().setSectionResizeMode(3, QHeaderView.Fixed)
        self.decktree.expandAll()

        self.adddeckbutton.clicked.connect(self.adddeck)
        self.refreshtree()

    def refresh(self):
        self.refreshtree()

    def adddeck(self):
        self.adddeckwindow = AddDeckWindow(self.user)
        self.adddeckwindow.show()
        self.adddeckwindow.createbutton.clicked.connect(self.adddeckfunc)

    def adddeckfunc(self):
        deckname = self.adddeckwindow.namelineedit.text()
        desc = self.adddeckwindow.desclineedit.text()
        config = self.adddeckwindow.configscombobox.itemData(self.adddeckwindow.configscombobox.currentIndex())
        if not deckname:
            self.adddeckwindow.emptylable.setText("You have not entered a name for the deck")
            return
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute(f"""INSERT INTO decks (name, desc, created, modified, created_uid, isPublic, isDeleted)
                    VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id""", (deckname, desc, time(), config.id, self.user.id, 0, 0))
        deckid = cur.fetchone()[0]
        cur.execute(f"""INSERT INTO user_decks (uid, deck_id, config_id) VALUES (?, ?, ?)""", (self.user.id, deckid, config.id))
        con.commit()
        cur.close()
        con.close()
        self.adddeckwindow = None
        refreshmainwindows()

    def refreshtree(self):
        self.treeModel.removeRows(0, self.treeModel.rowCount())
        rootnode = self.treeModel.invisibleRootItem()
        for deckname, desc, uid in self.fetch_decks():
            rootnode.appendRow([Deck(uid, self.user), QStandardItem(desc)])

        self.fetch_counts()

        # row_height = 25
        # self.decktree.setStyleSheet(f"""QTreeWidget::item{{height:{row_height}px;}}""")
        #
        # table_height = (self.treeModel.rowCount() * row_height)
        # print(table_height)
        # self.decktree.setMinimumHeight(table_height)


    def opendeck(self, val):
        deck = self.decktree.model().item(val.row())
        deckselect = DeckSelected(self.user, deck)
        stack.addWidget(deckselect)
        self.adddeckwindow = None
        stack.setCurrentIndex(8)


    def fetch_decks(self):
        # todo add id restrictions and decide on access method (id or name)
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute(
            "SELECT user_decks.id, decks.name, decks.desc FROM decks INNER JOIN user_decks ON user_decks.deck_id = decks.id WHERE user_decks.uid = ?",
            (self.user.id,))
        udids = []
        names = []
        descriptions = []

        for fetch in cur.fetchall():
            udids.append(fetch[0])
            names.append(fetch[1])
            descriptions.append(fetch[2])

        cur.close()
        con.close()

        return zip(names, descriptions, udids)

    def fetch_counts(self):
        con = sqlite3.connect(database)
        cur = con.cursor()

        for i in range(self.decktree.model().rowCount()):
            deck = self.decktree.model().item(i, 0)

            cur.execute(f"""SELECT COUNT (uc.id) FROM user_cards uc 
                        INNER JOIN cards c ON uc.cid = c.id 
                        INNER JOIN user_decks ud ON c.deck_id = ud.deck_id
                        WHERE ud.id = {deck.udid} AND uc.uid = {self.user.id}
                        AND (uc.status = 1 OR uc.status = 2 OR uc.status = 3)
                        AND uc.due <= {math.ceil(time() / 86400) * 86400}
                        """)

            duecount = cur.fetchone()[0]

            cur.execute(f"""SELECT COUNT (uc.id) FROM user_cards uc 
            INNER JOIN cards c ON uc.cid = c.id 
            INNER JOIN user_decks ud ON c.deck_id = ud.deck_id
            WHERE ud.id = {deck.udid} AND uc.uid = {self.user.id}
            AND uc.status = 0
            """)

            newcount = cur.fetchone()[0]

            if newcount >= deck.config.new_per_day:
                newcount = deck.config.new_per_day

            cur.execute(f"""SELECT COUNT (revlog.id) FROM revlog INNER JOIN user_cards uc ON revlog.ucid = uc.id 
            INNER JOIN cards c on uc.cid = c.id 
            INNER JOIN user_decks ud ON c.deck_id = ud.deck_id 
            WHERE ud.id = {deck.udid} 
            AND revlog.status = 0 
            AND (revlog.time >= {math.floor(time() / 86400) * 86400} 
            AND revlog.time <= {math.ceil(time() / 86400) * 86400})""")

            newreviewedtodaycount = cur.fetchone()[0]
            newcount -= newreviewedtodaycount

            index = self.decktree.model().index(i, 2)
            self.decktree.model().setData(index, newcount)
            index = self.decktree.model().index(i, 3)
            self.decktree.model().setData(index, duecount)


class AddDeckWindow(QWidget):
    def __init__(self, user):
        super().__init__()
        loadUi("adddeckwindow.ui", self)
        self.user = user
        self.fetchconfigs()

    def fetchconfigs(self):
        self.configs = []
        self.configscombobox.clear()
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("SELECT id FROM configs WHERE uid = ?", [self.user.id])
        configs_values = cur.fetchall()
        for values in configs_values:
            configid = values[0]
            self.configs.append(Config(configid))
        self.fillconfigsbox()
        cur.close()
        con.close()

    def fillconfigsbox(self):
        for config in self.configs:
            try:
                self.configscombobox.addItem(config.name, config)
            except Exception as e:
                print(e)


class DeckSelected(QMainWindow):
    def __init__(self, user, deck):
        self.user = user
        self.deck = deck
        super().__init__()
        loadUi("deckselected.ui", self)
        connectmainbuttons(self)

        self.deckname.setText(deck.name)
        # self.backbutton.clicked.connect(self.back)
        self.deckoptionsbutton.clicked.connect(self.deckoptions)
        self.studybutton.clicked.connect(self.study)

    def deckoptions(self):
        self.optionswindow = DeckOptions(self.user, self.deck)
        self.optionswindow.show()

    def study(self):
        self.study = Study(self.user, self.deck)


# maybe create a study class that handles both front and back and switches between the two

class Study:
    def __init__(self, user, deck):
        self.user = user
        self.deck = deck
        self.card = None
        self.starttime = None
        self.endtime = None

        self.studyfront = StudyFront()
        self.studyfront.flipbutton.clicked.connect(self.flip)
        stack.addWidget(self.studyfront)

        self.studyback = StudyBack()
        self.studyback.againbutton.clicked.connect(lambda: self.review(0))
        self.studyback.hardbutton.clicked.connect(lambda: self.review(1))
        self.studyback.goodbutton.clicked.connect(lambda: self.review(2))
        self.studyback.easybutton.clicked.connect(lambda: self.review(3))
        stack.addWidget(self.studyback)

        self.showfront()

    def showfront(self):
        self.loadcard()
        self.starttime = time()
        stack.setCurrentIndex(9)

    def loadcard(self):
        return

    def flip(self):
        stack.setCurrentIndex(10)
        self.showback()

    def showback(self):
        return

    def review(self, ease):
        self.endtime = time()
        stack.setCurrentIndex(9)


class StudyFront(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("studyfront.ui", self)


class StudyBack(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("studyback.ui", self)


class DeckOptions(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    # todo connect combo box with deck config settings - done todo - either add a save button to confirm changes to
    #  configs or individually connect each lineedit, save button is likely to be a lot easier will have to change
    #  the objects properties when line edits are changed, and then connect the save button to inserting and
    #  commiting to the database configs now hold changes but need to add a save button do confirm changing config
    #  for the deck and update all changes made to the configs - add a save method to the config class

    def __init__(self, user, deck=None):
        super().__init__()
        self.cfgnamewindow = None
        self.user = user
        self.deck = deck
        loadUi("deckoptions.ui", self)
        self.configs = []
        self.configscombobox.activated.connect(self.configchange)
        self.fetchconfigs()
        if deck:
            for config in self.configs:
                if config.id == self.deck.config_id:
                    idx = self.configs.index(config)
            self.configscombobox.setCurrentIndex(idx)
        self.configchange(self.configscombobox.currentIndex())
        self.constructmanagetoolmenu()
        self.connectvaluecontainers()
        self.savebutton.clicked.connect(self.save)

    def configchange(self, index):
        self.current_config = self.configscombobox.itemData(index)
        self.__fillnewcardstab()
        self.__fillreviewstab()
        self.__filllapsestab()

    def save(self):
        self.deck.config_id = self.current_config.id
        self.deck.config = self.current_config

        # could either save here or create a method in the deck class for this, will keep here for now since it only
        # involves the user decks table

        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute(f"""UPDATE user_decks
                    SET config_id = ?
                    where id = ?
                    """, (self.deck.config_id, self.deck.udid))

        con.commit()
        cur.close()
        con.close()

        for config in self.configs:
            config.save()

        self.hide()


    def __fillnewcardstab(self):
        new_delays = re.sub(",", " ", self.current_config.new_delays)
        grad_ivls = self.current_config.new_grad_ivls.split(",")
        grad_ivls = [int(x) for x in grad_ivls]
        self.newdelaysedit.setText(str(new_delays))
        self.newperdaybox.setValue(self.current_config.new_per_day)
        self.gradivlbox.setValue(grad_ivls[0])
        self.easyivlbox.setValue(grad_ivls[1])
        self.startingeasebox.setValue(self.current_config.new_init_ef)

    def __fillreviewstab(self):
        self.maxdailyrevbox.setValue(self.current_config.rev_per_day)
        self.easybonusbox.setValue(self.current_config.rev_easy_factor)
        self.hardivlbox.setValue(self.current_config.rev_hard_factor)
        self.maxivlbox.setValue(self.current_config.max_ivl)

    def __filllapsestab(self):
        lapse_delays = re.sub(",", " ", self.current_config.lapse_delays)
        self.lapsedelaysedit.setText(lapse_delays)
        self.lapsepenaltybox.setValue(self.current_config.lapse_percent)
        self.minivlbox.setValue(self.current_config.min_ivl)
        self.leechthresholdbox.setValue(self.current_config.leech_fails)

    def fetchconfigs(self):
        self.configs = []
        self.configscombobox.clear()
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("SELECT id FROM configs WHERE uid = ?", [self.user.id])
        configs_values = cur.fetchall()
        for values in configs_values:
            configid = values[0]
            self.configs.append(Config(configid))
        self.fillconfigsbox()
        cur.close()
        con.close()

    def fillconfigsbox(self):
        for config in self.configs:
            try:
                self.configscombobox.addItem(config.name, config)
            except Exception as e:
                print(e)

    def constructmanagetoolmenu(self):
        self.manageMenu = QMenu()
        self.addconfig = QAction("Add", self.managetool)
        self.cloneconfig = QAction("Clone", self.managetool)
        self.renameconfig = QAction("Rename", self.managetool)
        self.deleteconfig = QAction("Delete", self.managetool)

        self.manageMenu.addActions([self.addconfig, self.cloneconfig, self.renameconfig, self.deleteconfig])
        self.managetool.setMenu(self.manageMenu)
        self.managetool.setPopupMode(QToolButton.InstantPopup)

        self.addconfig.triggered.connect(self.add)
        self.cloneconfig.triggered.connect(self.clone)
        self.renameconfig.triggered.connect(self.rename)
        self.deleteconfig.triggered.connect(self.delete)

    def connectvaluecontainers(self):
        for widget in self.newcards.children() + self.reviews.children() + self.lapses.children():
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.updateconfig)
            if isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self.updateconfig)

    def updateconfig(self):
        try:
            # New tab
            # reminder in testing to demonstrate inputs mixed with strings of letters to show regex removing this.
            # if wanted to improve at a later date then can add in mixed units for time such as mins, hours and days
            new_delays = re.findall(r'\d+', self.newdelaysedit.text())
            new_delays = ",".join(new_delays)
            self.current_config.new_delays = new_delays

            self.current_config.new_per_day = self.newperdaybox.value()
            grad_ivls = str(self.gradivlbox.value()) + "," + str(self.easyivlbox.value())
            self.current_config.new_grad_ivls = grad_ivls
            self.current_config.new_init_ef = self.startingeasebox.value()

            # Reviews tab
            self.current_config.rev_per_day = self.maxdailyrevbox.value()
            self.current_config.rev_easy_factor = self.easybonusbox.value()
            self.current_config.rev_hard_factor = self.hardivlbox.value()
            self.current_config.max_ivl = self.maxivlbox.value()

            # Lapse tab
            lapse_delays = re.findall(r'\d+', self.lapsedelaysedit.text())
            lapse_delays = ",".join(lapse_delays)
            self.current_config.lapse_delays = lapse_delays

            self.current_config.lapse_percent = self.lapsepenaltybox.value()
            self.current_config.min_ivl = self.minivlbox.value()
            self.current_config.max_ivl = self.maxivlbox.value()

        except Exception as e:
            self.errorlabel.setText(str(e))
            return

        print(vars(self.current_config))

    def add(self):
        # add now working
        self.cfgnamewindow = CFGNameWindow()
        self.cfgnamewindow.show()
        self.cfgnamewindow.confirmbutton.clicked.connect(self.addfunc)

    def addfunc(self):
        self.cfgnamewindow.name = self.cfgnamewindow.namelineedit.text()
        if self.cfgnamewindow.name:
            con = sqlite3.connect(database)
            cur = con.cursor()
            cur.execute("""INSERT INTO configs (
                        name,
                        lapse_delays,
                        lapse_percent,
                        leech_fails,
                        max_ivl,
                        min_ivl,
                        new_delays,
                        new_grad_ivls,
                        new_init_ef,
                        new_per_day,
                        rev_easy_factor,
                        rev_hard_factor,
                        rev_per_day,
                        uid)
                    VALUES (
                        ?,
                        10,
                        50,
                        8,
                        36500,
                        1,
                        '1,10',
                        '1,4',
                        250,
                        10,
                        130,
                        120,
                        200,
                        ?)""", (self.cfgnamewindow.name, self.user.id,))
            con.commit()
            cur.close()
            con.close()
            self.cfgnamewindow.hide()
            self.fetchconfigs()

        else:
            self.cfgnamewindow.emptylabel.setText("You have not entered a name for the config")

    def clone(self):
        # clone working, should integrate with everything to be added
        self.cfgnamewindow = CFGNameWindow()
        self.cfgnamewindow.show()
        self.cfgnamewindow.confirmbutton.clicked.connect(self.clonefunc)
        self.cfgnamewindow.namelineedit.setText(f"{self.current_config.name} - clone")

    def clonefunc(self):
        self.cfgnamewindow.name = self.cfgnamewindow.namelineedit.text()
        if self.cfgnamewindow.name:
            con = sqlite3.connect(database)
            cur = con.cursor()
            cur.execute("""INSERT INTO configs (
                        name,
                        lapse_delays,
                        lapse_percent,
                        leech_fails,
                        max_ivl,
                        min_ivl,
                        new_delays,
                        new_grad_ivls,
                        new_init_ef,
                        new_per_day,
                        rev_easy_factor,
                        rev_hard_factor,
                        rev_per_day,
                        uid)
                    VALUES (
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?)
                        RETURNING id""", (self.cfgnamewindow.name, self.current_config.lapse_delays,
                                          self.current_config.lapse_percent, self.current_config.leech_fails,
                                          self.current_config.max_ivl, self.current_config.min_ivl,
                                          self.current_config.new_delays, self.current_config.new_grad_ivls,
                                          self.current_config.new_init_ef, self.current_config.new_per_day,
                                          self.current_config.rev_easy_factor, self.current_config.rev_hard_factor,
                                          self.current_config.rev_per_day, self.user.id,))
            cfgid = cur.fetchone()[0]
            con.commit()
            cur.close()
            con.close()
            self.cfgnamewindow.hide()
            config = Config(cfgid)
            self.configs.append(config)
            self.configscombobox.addItem(config.name, config)
            self.configscombobox.setCurrentIndex(self.configscombobox.count() - 1)
        else:
            self.cfgnamewindow.emptylabel.setText("You have not entered a name for the config")

    def rename(self):
        self.cfgnamewindow = CFGNameWindow(rename=True)
        self.cfgnamewindow.show()
        self.cfgnamewindow.confirmbutton.clicked.connect(self.renamefunc)
        self.cfgnamewindow.namelineedit.setText(f"{self.current_config.name}")

    def renamefunc(self):
        self.cfgnamewindow.name = self.cfgnamewindow.namelineedit.text()

        if self.cfgnamewindow.name:
            self.current_config.name = self.cfgnamewindow.name
            con = sqlite3.connect(database)
            cur = con.cursor()
            # remove this execute statement once save button functionality is added
            cur.execute("""UPDATE configs
            SET name = ?
            WHERE id = ?
            """, (self.current_config.name, self.current_config.id))
            idx = self.configscombobox.currentIndex()
            self.configscombobox.clear()
            self.fillconfigsbox()
            self.configscombobox.setCurrentIndex(idx)
            self.cfgnamewindow.hide()
            con.commit()
            cur.close()
            con.close()
        else:
            self.cfgnamewindow.emptylabel.setText("You have not entered a name for the config")

    def delete(self):
        # delete function working, need to add a clause that prevents the deault config from being deleted (maybe by
        # checking for the min idx of a config tied to the user, and also handle decks which were using the deleted
        # config, perhaps also by setting their config to the default.
        # todo also rework this so that the config is
        #  only truly deleted on save being clicked, perhaps add another column to the db, or a deleted attribute to
        #  the class that can be used just for the purpose of editing configs

        # reminder when testing to reference an error where if a config was deleted that a deck was using and not
        # changed to another value, the program would crash upon trying to load said deck's config
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT MIN(id) FROM configs
                    WHERE uid = ?""", (self.user.id,))
        defaultcfgid = cur.fetchone()[0]
        if self.current_config.id == defaultcfgid:
            self.errorlabel.setText("The default config cannot be deleted")
            return

        delidx = self.configscombobox.currentIndex()
        tempidx = delidx - 1
        if tempidx == -1:
            tempidx = 0

        cur.execute(f"""UPDATE user_decks
                    SET config_id = ? WHERE config_id = ? AND uid = ?""",
                    (defaultcfgid, self.current_config.id, self.user.id))
        cur.execute(f"""DELETE FROM configs where id = {self.current_config.id}""")
        self.configscombobox.setCurrentIndex(tempidx)
        self.configscombobox.removeItem(delidx)
        print(len(self.configs))
        del self.configs[delidx]
        print(len(self.configs))
        print("deleting")
        con.commit()
        cur.close()
        con.close()


class CFGNameWindow(QWidget):
    def __init__(self, rename=False):
        super().__init__()
        loadUi("cfgnamewindow.ui", self)
        self.create = False
        self.name = None
        if rename:
            self.confirmbutton.setText("Confirm")


class CardsMain(QMainWindow):
    # todo get filters working
    # make sure a general search matches against all card data, not just sortfield, also best to split before matching
    def __init__(self, user):
        self.user = user
        super().__init__()
        loadUi("cardsmain.ui", self)
        connectmainbuttons(self)
        self.searchbutton.clicked.connect(self.search)

        # setting up filter button
        self.filterMenu = QMenu()

        self.filterWholeCollection = QAction("Whole Collection", self.filtertool)
        self.filterCurrentDeck = QAction("Current Deck", self.filtertool)
        self.filterStudiedLast = QMenu("Studied in the last", self.filterMenu)
        self.filterStatus = QMenu("Status", self.filterMenu)

        self.statusNew = QAction("New", self.filterStatus)
        self.statusLearning = QAction("Learning", self.filterStatus)
        self.statusReview = QAction("Review", self.filterStatus)
        self.statusRelearning = QAction("Relearning", self.filterStatus)

        self.statusNew.triggered.connect(lambda: self.filterstatusfunc(self.statusNew.text()))
        self.statusLearning.triggered.connect(lambda: self.filterstatusfunc(self.statusLearning.text()))
        self.statusReview.triggered.connect(lambda: self.filterstatusfunc(self.statusReview.text()))
        self.statusRelearning.triggered.connect(lambda: self.filterstatusfunc(self.statusRelearning.text()))

        self.filterStatus.addActions([self.statusNew, self.statusLearning, self.statusReview, self.statusRelearning])
        self.filterMenu.addActions([self.filterWholeCollection, self.filterCurrentDeck])

        self.filterMenu.addMenu(self.filterStudiedLast)
        self.filterMenu.addMenu(self.filterStatus)

        self.filtertool.setMenu(self.filterMenu)
        self.filtertool.setPopupMode(QToolButton.InstantPopup)

        # setting up cards tree
        self.cards = QStandardItemModel(0, 4, self.cardstree)
        self.cards.setHeaderData(0, Qt.Horizontal, "Sort Field")
        self.cards.setHeaderData(1, Qt.Horizontal, "Card")
        self.cards.setHeaderData(2, Qt.Horizontal, "Due")
        self.cards.setHeaderData(3, Qt.Horizontal, "Deck")
        self.rootNode = self.cards.invisibleRootItem()

        self.cardstree.setModel(self.cards)
        self.cardstree.expandAll()
        self.cardstree.setIndentation(0)

        self.cardstree.selectionModel().selectionChanged.connect(lambda: self.editcard(self.cardstree.currentIndex()))

        # constructing decks list
        self.deckslistmodel = QStandardItemModel(0, 1, self.deckslist)
        self.deckslistmodel.setHeaderData(0, Qt.Horizontal, "Decks")
        self.deckslist.setModel(self.deckslistmodel)
        self.deckslist.clicked.connect(self.filterondeck)
        self.filldeckslist()

        # contstructing scroll area
        self.scrollWidgetContents_layout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollWidgetContents_layout.setContentsMargins(0, 0, 0, 0)
        self.scrollWidgetContents_layout.setAlignment(Qt.AlignTop)

        self.scrollAreaWidgetContents.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll.setWidget(self.scrollAreaWidgetContents)
        self.scroll.setWidgetResizable(True)

        self.search()

    def refresh(self):
        q = QTreeView()
        q.currentIndex()
        self.filldeckslist()
        self.search(refresh=True)
        # beware of issues here down the line with refresh

    def filterstatusfunc(self, status):
        self.filterinput.setText(f"Status: {status}")
        self.search()

    def search(self, refresh=False):
        fetch = self.fetch_cards()
        self.fillcards(fetch, refresh)

    def fetch_cards(self):
        # todo - change this function so it only displays cards in active decks, or has an option to NOTE: this might
        #  cause issues when changing windows with the clause to retain edits so might be easier just to reset the
        #  selection
        filterText = self.filterinput.text()
        # regex expressions
        # should have filters of:
        # status, time when last reviewed, last ease in review, reps, lapses, interval,
        # maybe allow for searching of other user's cards in library but not editing
        # todo might need to save and retain the current sort state of the table when updating
        # todo current issue where selecting a card, searching, then editing does not update the displayed item text
        """
        "deck:([^":]+\s?)*"$ - for "deck:abc"
        deck:current - self explanatory

        """

        # check if falls under predifined filter formats, else iterate through card data to see if it contains a
        # regex match

        # todo also should rewrite this later so if the card is from someone else's deck it can't be edited,
        #  and user_cards which aren't connected to a user_deck pair shouldn't be shown, but can still be stored.

        con = sqlite3.connect(database)
        cur = con.cursor()

        cur.execute("""SELECT uc.id, d.name FROM user_cards uc INNER JOIN cards c ON uc.cid = c.id
         INNER JOIN decks d ON c.deck_id = d.id 
         WHERE uc.uid = ? """, (self.user.id,))

        fetch = [(row[0], row[1]) for row in cur.fetchall()]
        cur.close()
        con.close()

        return fetch

    def fillcards(self, fetch, refresh):
        # need to sort out card types

        self.rootNode.removeRows(0, self.rootNode.rowCount())
        # i = 0
        for cid, deckname in fetch:
            card = Flashcard(cid)

            try:
                due = str(datetime.datetime.fromtimestamp(card.due).isoformat(' ', 'seconds'))
            except Exception as e:
                due = ''

            self.rootNode.appendRow([card, QStandardItem(), QStandardItem(due), QStandardItem(deckname)])
            # if card == self.editingcard:
            #     i = self.rootNode.rowCount()
        #
        # return i

    def editcard(self, idx):
        if idx.row() == -1:  # prevents crashing if search is used whilst a card is selected
            return

        self.editingcard = self.rootNode.child(idx.row())
        if self.editingcard.creator_id != self.user.id:
            editable = False
        else:
            editable = True

        for i in reversed(range(self.scrollWidgetContents_layout.count())):
            self.scrollWidgetContents_layout.itemAt(i).widget().deleteLater()

        self.line_edits = []
        font = QFont()
        font.setPointSize(14)
        font.setWeight(50)

        if not editable:
            label = QtWidgets.QLabel(f"You cannot edit this card as you are not the creator")
            label.setStyleSheet("color:red;")
            self.scrollWidgetContents_layout.addWidget(label)

        for i in range(len(self.editingcard.fields)):
            label = QtWidgets.QLabel(f"{self.editingcard.fields[i]}")
            label.setFont(font)
            line_edit = QtWidgets.QLineEdit()
            line_edit.setMinimumHeight(41)
            line_edit.setMaximumHeight(41)
            line_edit.setFont(font)
            line_edit.setPlaceholderText("")
            if self.editingcard.data[i]:
                line_edit.setText(self.editingcard.data[i])
            else:
                line_edit.setText("")

            if not editable:
                line_edit.setReadOnly(True)

            self.scrollWidgetContents_layout.addWidget(label)
            self.scrollWidgetContents_layout.addWidget(line_edit)
            line_edit.editingFinished.connect(lambda le=line_edit, idx=i: self.saveedit(le, idx, self.editingcard))
            self.line_edits.append(line_edit)

    def saveedit(self, le, idx, card):
        text = le.text()
        card.data[idx] = text
        card.setText(card.data[card.fields.index(card.sortfield)])
        try:
            card.update(self.user.id)
        except Exception as e:
            print(e)

    def filldeckslist(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        self.deckslistmodel.removeRows(0, self.deckslistmodel.rowCount())

        cur.execute("""SELECT ud.id FROM decks d INNER JOIN user_decks ud ON d.id = ud.deck_id INNER JOIN 
        users u on ud.uid = u.id WHERE u.id = ?""", (self.user.id,))
        udids = [row[0] for row in cur.fetchall()]

        for i in range(len(udids)):
            self.deckslistmodel.appendRow(Deck(udids[i], self.user))

        cur.close()
        con.close()

    def filterondeck(self, idx):
        deck = self.deckslistmodel.item(idx.row(), 0)
        self.filterinput.setText(f'"deck:{deck.name}"')
        self.search()


class AddCard(QMainWindow):
    def __init__(self, user):
        self.user = user
        super().__init__()
        loadUi("addcard.ui", self)

        connectmainbuttons(self)

        self.scrollWidgetContents_layout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollWidgetContents_layout.setContentsMargins(0, 0, 0, 0)
        self.scrollWidgetContents_layout.setAlignment(Qt.AlignTop)

        self.scrollAreaWidgetContents.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.scroll.setWidget(self.scrollAreaWidgetContents)
        self.scroll.setWidgetResizable(True)

        self.templatesbutton.clicked.connect(self.viewtemplates)

        self.fill_decks_box()

        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("SELECT MIN (id) FROM templates WHERE created_uid = ?", (self.user.id,))
        self.template = Template(cur.fetchone()[0])
        cur.close()
        con.close()
        self.applytemplate()
        self.templateswindow = None

        self.addcard.clicked.connect(self.add_card)


    def applytemplate(self):
        self.templatesbutton.setText(self.template.name)

        for i in reversed(range(self.scrollWidgetContents_layout.count())):
            self.scrollWidgetContents_layout.itemAt(i).widget().deleteLater()

        split = self.template.fields.split(",")
        self.line_edits = []
        font = QFont()
        font.setPointSize(15)
        font.setWeight(50)

        for field in split:
            label = QtWidgets.QLabel(f"{field}")
            label.setFont(font)
            line_edit = QtWidgets.QLineEdit()
            line_edit.setMinimumHeight(41)
            line_edit.setMaximumHeight(41)
            line_edit.setFont(font)
            line_edit.setPlaceholderText("")
            self.scrollWidgetContents_layout.addWidget(label)
            self.scrollWidgetContents_layout.addWidget(line_edit)
            self.line_edits.append(line_edit)

    def viewtemplates(self):
        self.templateswindow = TemplatesWindow(self.user, self.template)
        self.templateswindow.show()
        self.templateswindow.selectbutton.clicked.connect(self.settemplate)

    def settemplate(self):
        self.template = self.templateswindow.templatesmodel.item(self.templateswindow.templateslist.currentIndex().row(), 0)
        if self.template:
            self.applytemplate()
            self.templateswindow.hide()
        else:
            pass

    def fill_decks_box(self):
        self.decksbox.clear()
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT d.id, d.name FROM decks d INNER JOIN users u on d.created_uid = 
                    u.id WHERE u.id = ?""", (self.user.id,))
        try:
            self.d_ids, self.d_names = zip(*[(row[0], row[1]) for row in cur.fetchall()])
        except:
            self.d_ids = []
            self.d_names = []

        for name in self.d_names:
            self.decksbox.addItem(name)

    def refresh(self):
        self.fill_decks_box()
        # self.fill_templates_box()

    def add_card(self):
        card_data = []
        empty = True
        for line in self.line_edits:
            data = line.text()
            if data:
                empty = False
            card_data.append(data)

        if not empty:
            con = sqlite3.connect(database)
            cur = con.cursor()

            card_data = ','.join(card_data)

            d_idx = self.d_names.index(self.decksbox.currentText())
            deck_id = self.d_ids[d_idx]
            cur.execute("""INSERT INTO cards (data, deck_id, template_id, modified, created_uid)
                            VALUES (?, ?, ?, ?, ?) RETURNING id""",
                        (card_data, deck_id, self.template.id, time(), self.user.id))
            cid = cur.fetchone()[0]
            cur.execute("""INSERT INTO user_cards (uid, cid, ivl, type, status, reps, lapses, odue)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (self.user.id, cid, None, 0, 0, 0, 0, time()))

            try:
                con.commit()
            except Exception as e:
                print(e)
            cur.close()
            con.close()

            for line in self.line_edits:
                line.setText("")

        else:
            try:
                self.error.setText("Card has no data")
            except Exception as e:
                print(e)


class TemplatesWindow(QWidget):
    # todo add counts to each template text showing how many cards use the template
    def __init__(self, user, template):
        super().__init__()
        loadUi("templates.ui", self)
        self.user = user
        self.initialtemplate = template
        self.templatesmodel = QStandardItemModel()
        self.loadtemplates()
        self.backbutton.clicked.connect(self.hide)
        self.addbutton.clicked.connect(self.addwindow)
        self.renamebutton.clicked.connect(self.renamewindow)
        self.fieldsbutton.clicked.connect(self.managefields)

    def loadtemplates(self):
        self.templatesmodel.clear()
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("SELECT id FROM templates WHERE created_uid = ?", (self.user.id,))
        for fetch in cur.fetchall():
            template = Template(fetch[0])
            self.templatesmodel.appendRow(template)
            # if template.id == self.initialtemplate.id:
            #     print("here")
            #     i = self.templatesmodel.rowCount()
            #     print(i)
            #     self.templateslist.selectionModel().setCurrentIndex(i)
        cur.close()
        con.close()
        self.templateslist.setModel(self.templatesmodel)

    def addwindow(self):
        self.addtemplatewindow = AddTemplate(self.user)
        self.addtemplatewindow.addbutton.clicked.connect(self.addtemplate)
        self.addtemplatewindow.show()

    def addtemplate(self):
        template = self.addtemplatewindow.optionsmodel.item(self.addtemplatewindow.optionslist.currentIndex().row(), 0)
        if not template:
            # button doesnt do anything
            return

        self.addtemplatewindow.hide()
        # to work out below
        # self.setWindowFlag(Qt.WindowDoesNotAcceptFocus)
        # self.setWindowState(Qt.Window)
        self.templatenamewindow = NameWindow()
        # can rewrite to use regex matching for more generalisation
        if template.text() == "Add: Basic":
            self.templatenamewindow.namelineedit.setText("Basic")
        else:
            self.templatenamewindow.namelineedit.setText(f"{template.name} copy")
        self.templatenamewindow.cancelbutton.clicked.connect(lambda: self.cancel(self.templatenamewindow))
        self.templatenamewindow.okbutton.clicked.connect(self.completeadd)
        self.templatenamewindow.show()

    def completeadd(self):
        template = self.addtemplatewindow.optionsmodel.item(self.addtemplatewindow.optionslist.currentIndex().row(), 0)
        name = self.templatenamewindow.namelineedit.text()
        if template.text() == "Add: Basic":
            addbasictemplate(self.user, name=name)
        else:
            con = sqlite3.connect(database)
            cur = con.cursor()
            cur.execute("""INSERT INTO templates (name, fields, sortfield, modified, created_uid) VALUES
               (?, ?, ?, ?, ?)""", (name, template.fields, template.sortfield, time(), self.user.id))
            # self.setWindowState(Qt.WindowActive)
            con.commit()
            cur.close()
            con.close()
        self.templatenamewindow.deleteLater()
        self.loadtemplates()

    def renamewindow(self):
        template = self.templatesmodel.item(self.templateslist.currentIndex().row(), 0)
        if not template:
            return

        self.renametemplatewindow = NameWindow()
        self.renametemplatewindow.template = template
        self.renametemplatewindow.okbutton.clicked.connect(self.rename)
        self.renametemplatewindow.cancelbutton.clicked.connect(lambda: self.cancel(self.renametemplatewindow))
        self.renametemplatewindow.namelineedit.setText(template.name)
        self.renametemplatewindow.show()

    def rename(self):
        new_name = self.renametemplatewindow.namelineedit.text()
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""UPDATE templates SET name = ? WHERE id = ?""", (new_name, self.renametemplatewindow.template.id))
        con.commit()
        cur.close()
        con.close()
        self.renametemplatewindow.deleteLater()
        self.loadtemplates()

    def cancel(self, window):
        window.deleteLater()
        self.loadtemplates()
        # self.setWindowState(Qt.WindowActive)

    def managefields(self):
        template = self.templatesmodel.item(self.templateslist.currentIndex().row(), 0)
        if not template:
            return
        self.templatefieldswindow = TemplateFieldsWindow(template)
        self.templatefieldswindow.savebutton.clicked.connect(self.savetemplatefields)
        self.templatefieldswindow.cancelbutton.clicked.connect(lambda: self.cancel (self.templatefieldswindow))
        self.templatefieldswindow.show()
        pass

    def savetemplatefields(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        # utilising a FIFO queue data structure here to handle all the executions after saving, could not do so in
        # the other class as this would require changes being commited before the save button was actually clicked,
        # due to the potential for needing to change the cards' data fields
        for instruction, params in zip(self.templatefieldswindow.instructions, self.templatefieldswindow.params):
            if instruction == "CARD_ADD_FIELD":
                print("adding field")
                cid, index = params
                cur.execute("SELECT data FROM cards WHERE id = ?", (cid,))
                data = cur.fetchone()[0]
                data = data.split(",")
                data.append(",")
                data = ",".join(data)
                # print(cid, data)
                cur.execute("""UPDATE cards SET data = ? WHERE id = ?""", (data, cid))
            elif instruction == "CARD_DELETE_FIELD":
                cid, delindex = params
                cur.execute("SELECT data FROM cards WHERE id = ?", (cid,))
                data = cur.fetchone()[0]
                data = data.split(",")
                del data[delindex]
                data = ",".join(data)
                # print(cid, data)
                cur.execute("""UPDATE cards SET data = ? WHERE id = ?""", (data, cid))
            elif instruction == "CARD_REPOS_FIELD":
                print("repositioning field")
                cid, old_index, new_index = params
                cur.execute("SELECT data FROM cards WHERE id = ?", (cid,))
                data = cur.fetchone()[0]
                data = data.split(",")
                repositionitem(data, old_index, new_index)
                data = ",".join(data)
                # print(cid, data)
                cur.execute("""UPDATE cards SET data = ? WHERE id = ?""", (data, cid))
            else:
                print("executing")
                print(instruction, params)
                cur.execute(instruction, params)

            # TODO handle these if... elif ... else execute as SQL
            # todo here, allow fields to be added and deleted,
            #  when this happens will want to update all cards that are connected to the template, and update the data of
            #  any changed fields, if indexes change, will want to change the index of data, etc.
            #  Delete -> Delete Data and field
            #  Add -> Add field and empty data slot - Also need to check field name not in use
            #  Reposition -> Change position/index of field and data
            #  Rename -> Change field name
            #  Sort by this field -> change sortfield, make sure this changes with the ui aswell
            #  Should be sufficient (obviously cancel and save to discard/commit changes) - to cancel just call load
            #  template again

        con.commit()
        cur.close()
        con.close()
        self.templatefieldswindow.deleteLater()
        self.loadtemplates()


class NameWindow(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("namewindow.ui", self)
        self.template = None
        self.cancelbutton.clicked.connect(self.deleteLater)


class TemplateFieldsWindow(QWidget):
    # todo add delete functionality, add a prompt (alert box) on pressing delete notifying the user of how many cards
    #  the deletion affects, (iterate through cards with the template to check if they have dat in that index)
    def __init__(self, template):
        super().__init__()
        loadUi("templatefields.ui", self)
        self.template = template

        self.fieldsmodel = QStandardItemModel()
        self.fieldslist.setModel(self.fieldsmodel)
        self.fieldslist.selectionModel().selectionChanged.connect(self.fieldselected)


        self.sortfieldradio.clicked.connect(self.changesortfield)
        self.addbutton.clicked.connect(self.addwindow)
        self.renamebutton.clicked.connect(self.renamewindow)
        self.reposbutton.clicked.connect(self.repositionwindow)
        self.deletebutton.clicked.connect(self.deletefield)

        # idx = self.fieldsmodel.index(0, 0)
        # self.fieldslist.selectionModel().setCurrentIndex(idx, self.fieldslist.selectionModel().SelectionFlags())
        # self.fieldslist.setCurrentIndex(idx)

        self.fillfields()
        self.selectedfield = self.fieldsmodel.item(self.fieldslist.currentIndex().row(), 0)

        self.instructions = []
        self.params = []

    def fillfields(self):
        self.fieldsmodel.clear()
        i = 1
        for field in self.template.fields.split(","):
            self.fieldsmodel.appendRow(QStandardItem(f"{i}: {field}"))
            i += 1

    def fieldselected(self):
        self.selectedfield = new_string = re.sub(r"^\d+: ", "", self.fieldsmodel.item(self.fieldslist.currentIndex().row(), 0).text())
        if self.selectedfield == self.template.sortfield:
            self.sortfieldradio.setChecked(True)
        else:
            self.sortfieldradio.setChecked(False)

    def changesortfield(self):
        self.template.sortfield = self.selectedfield
        self.instructions.append("""UPDATE templates SET sortfield = ? WHERE id = ?""")
        self.params.append((self.template.sortfield, self.template.id))

    def addwindow(self):
        self.namewindow = NameWindow()
        self.namewindow.okbutton.clicked.connect(self.addfield)
        self.namewindow.show()

    def addfield(self):
        field_name = self.namewindow.namelineedit.text()
        if not field_name:
            self.namewindow.errorlabel.setText("Field must have a name")
            return
        elif field_name in self.template.fields.split(","):
            self.namewindow.errorlabel.setText("Field name already in use")
            return
        self.template.addfield(field_name)
        self.instructions.append("""UPDATE templates SET fields = ? WHERE id = ?""")
        self.params.append((self.template.fields, self.template.id))

        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT id FROM cards WHERE template_id = ?""", (self.template.id,))
        field_pos = self.template.fields.split(",").index(field_name)
        for fetch in cur.fetchall():
            cid = fetch[0]
            self.instructions.append("CARD_ADD_FIELD")
            # work out a function to handle this
            # field pos might not be necessary
            self.params.append((cid, field_pos))
        cur.close()
        con.close()
        self.fillfields()
        self.namewindow.deleteLater()

    def renamewindow(self):
        if not self.selectedfield:
            # output message?
            return
        old_name = self.selectedfield
        self.namewindow = NameWindow()
        self.namewindow.okbutton.clicked.connect(lambda: self.renamefield(old_name))
        self.namewindow.show()
        self.namewindow.namelineedit.setText(self.selectedfield)

    def renamefield(self, old_name):
        new_name = self.namewindow.namelineedit.text()
        if new_name == old_name:
            self.namewindow.deleteLater()
            self.loadtemplates()
            return
        if not new_name:
            self.namewindow.errorlabel.setText("Field must have a name")
            return
        elif new_name in self.template.fields.split(","):
            self.namewindow.errorlabel.setText("Field name already in use")
            return
        self.template.renamefield(old_name, new_name)
        self.instructions.append("""UPDATE templates SET fields = ? WHERE id = ?""")
        self.params.append((self.template.fields, self.template.id))
        self.namewindow.deleteLater()
        self.fillfields()

    def repositionwindow(self):
        if not self.selectedfield:
            # output message?
            return
        old_index = self.template.fields.split(",").index(self.selectedfield)
        self.reposwindow = RepositionFieldWindow(self.template)
        self.reposwindow.okbutton.clicked.connect(lambda: self.repositionfield(old_index))
        self.reposwindow.show()

    def repositionfield(self, old_index):
        new_index = self.reposwindow.namelineedit.text()
        if not new_index:
            self.reposwindow.errorlabel.setText("Please enter a position")
            return
        try:
            new_index = int(new_index) - 1
            if not 0 <= new_index <= self.reposwindow.count - 1:
                self.reposwindow.errorlabel.setText("Please enter a value within the range")
                return
        except ValueError:
            self.reposwindow.errorlabel.setText("Please enter an integer value")
            return
        self.template.repositionfield(old_index, new_index)
        self.instructions.append("""UPDATE templates SET fields = ? WHERE id = ?""")
        self.params.append((self.template.fields, self.template.id))

        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT id FROM cards WHERE template_id = ?""", (self.template.id,))
        for fetch in cur.fetchall():
            cid = fetch[0]
            self.instructions.append("CARD_REPOS_FIELD")
            # work out a function to handle this
            # field pos might not be necessary
            self.params.append((cid, old_index, new_index))
        cur.close()
        con.close()

        self.reposwindow.deleteLater()
        self.fillfields()

    def deletefield(self):
        if not self.selectedfield:
            return
        deletewindow = DeleteFieldWindow(self, self.template, self.selectedfield)
        deletewindow.buttonBox.accepted.connect(self.delete)
        deletewindow.exec()

    def delete(self):
        delfield = self.selectedfield
        field_pos = self.template.fields.split(",").index(delfield)
        self.template.removefield(delfield)

        self.instructions.append("""UPDATE templates SET fields = ? WHERE id = ?""")
        self.params.append((self.template.fields, self.template.id))

        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT id FROM cards WHERE template_id = ?""", (self.template.id,))
        for fetch in cur.fetchall():
            cid = fetch[0]
            self.instructions.append("CARD_DELETE_FIELD")
            # work out a function to handle this
            # field pos might not be necessary
            self.params.append((cid, field_pos))
        cur.close()
        con.close()
        self.fillfields()

    def cancel(self):
        self.deleteLater()


class RepositionFieldWindow(QWidget):
    def __init__(self, template):
        super().__init__()
        loadUi("namewindow.ui", self)
        # repurposing same file but changing text
        self.count = len(template.fields.split(','))
        self.label.setText(f"Enter New Position ({1} - {self.count}):")
        self.cancelbutton.clicked.connect(self.deleteLater)


class DeleteFieldWindow(QDialog):
    def __init__(self, parent_wnd, template, field):
        super().__init__(parent_wnd)
        loadUi("deletetemplate.ui", self)
        self.setFixedSize(400, 200)
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT COUNT (id) FROM cards WHERE template_id = ?""", (template.id,))
        totalcount = cur.fetchone()[0]
        cur.execute("""SELECT c.data, d.isPublic FROM cards c INNER JOIN decks d ON c.deck_id = d.id WHERE 
        template_id = ?""", (template.id,))
        affected_idx = template.fields.split(',').index(field)
        affectspublic = False
        # affectedcount = 0
        for fetch in cur.fetchall():
            data = fetch[0].split(",")
            public = fetch[1]
            # try:
            #     if data[affected_idx]:
            #         affectedcount += 1
            # except IndexError:
            #     # is passing here ok, should I just delete the section? ...
            #     pass
            if public:
                affectspublic = True

        self.totalnoteslabel.setText(f"Delete field '{field}' from {totalcount} notes")
        # self.noteswithdatalabel.setText(f"Of which {affectedcount} contain data in this field")
        if affectspublic:
            self.warninglabel.setText("Deleting this field will affect decks which you have published!")
        self.buttonBox.rejected.connect(self.deleteLater)


def addbasictemplate(user, name="Basic"):
    # todo - come back and include formatting when done
    print("adding basic")
    con = sqlite3.connect(database)
    cur = con.cursor()
    cur.execute("""INSERT INTO templates (name, fields, sortfield, modified, created_uid) VALUES
    (?, ?, ?, ?, ?)""", (name, "Front,Back", "Front", time(), user.id))
    cur.close()
    con.commit()
    con.close()


class AddTemplate(QWidget):
    def __init__(self, user):
        super().__init__()
        loadUi("addtemplate.ui", self)
        self.user = user
        self.optionsmodel = QStandardItemModel()
        self.backbutton.clicked.connect(self.hide)
        self.filloptions()

    def filloptions(self):
        self.optionsmodel.clear()
        self.optionsmodel.appendRow(QStandardItem("Add: Basic"))
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("SELECT id FROM templates WHERE created_uid = ?", (self.user.id,))
        for fetch in cur.fetchall():
            template = Template(fetch[0])
            template.setText(f"Clone: {template.name}")
            self.optionsmodel.appendRow(template)
        self.optionslist.setModel(self.optionsmodel)
        cur.close()
        con.close()


class StatsPage(QMainWindow):
    def __init__(self, user):
        self.user = user
        super().__init__()
        loadUi("statspage.ui", self)
        connectmainbuttons(self)

    def refresh(self):
        pass


class Browse(QMainWindow):
    # todo card data will automatically update with changes made by the creator, could add an option that allow
    #  creator to allow/disallow copies being made
    # also maybe open another window if the creator is accessing a deck, for now will just no connect the button
    # also need to refactor to avoid using 2 duplicate containers for decks
    def __init__(self, user):
        self.user = user
        super().__init__()
        loadUi("browse.ui", self)
        connectmainbuttons(self)

        # Could later check for updates on a deck allowing the user to keep their current version or sync changes. For
        # now will just ignore this and have 1 time deck copying in the current state of the deck.

        public_decks_model = QStandardItemModel(0, 5,
                                                self.deckstreeview)  # Deck, Description, Cards No, Creator, Date Updated
        public_decks_model.setHeaderData(0, Qt.Horizontal, "Name")
        public_decks_model.setHeaderData(1, Qt.Horizontal, "Description")
        public_decks_model.setHeaderData(2, Qt.Horizontal, "Creator")
        public_decks_model.setHeaderData(3, Qt.Horizontal, "Cards")
        public_decks_model.setHeaderData(4, Qt.Horizontal, "Date Updated")

        self.publicdecksrootnode = public_decks_model.invisibleRootItem()
        self.deckstreeview.setModel(public_decks_model)
        self.deckstreeview.clicked.connect(self.selectdeck)
        self.fillpublicdecks()

        # constructing the "My Decks" list
        self.deckslistmodel = QStandardItemModel(0, 2, self.mydeckslist)
        self.deckslistmodel.setHeaderData(0, Qt.Horizontal, "Decks")
        self.deckslistmodel.setHeaderData(1, Qt.Horizontal, "Public")
        self.deckslistmodel.itemChanged.connect(self.togglepublic)
        self.mydeckslist.setModel(self.deckslistmodel)
        self.fillmydeckslist()

        self.searchbutton.clicked.connect(self.fillpublicdecks)

    def regexp(self, expr, item):
        """
        A function to be used in filtering and retrieving published decks, matching the user's input to fields in the database
        :param expr: the input to be used when filtering
        :param item: the field which is being checked for a match with the expression
        :return: returns True if a match is found and re.search() returns a match item
        """
        return re.search(expr, item, re.IGNORECASE) is not None

    def fetchpublicdecks(self, searchfilter):
        con = sqlite3.connect(database)
        cur = con.cursor()
        con.create_function("REGEXP", 2, self.regexp)
        if searchfilter:
            try:
                cur.execute("""SELECT ud.id, d.name, d.desc, u.username FROM decks d INNER JOIN user_decks ud ON d.id 
                = ud.deck_id INNER JOIN users u ON d.created_uid = u.id WHERE d.isPublic = 1 AND isDeleted = 0 AND 
                ud.uid = d.created_uid AND (d.name REGEXP ? OR d.desc REGEXP ? OR u.username REGEXP ?)""", (searchfilter,
                                                                                                            searchfilter,
                                                                                                            searchfilter))
            except Exception as e:
                # todo - add error text at the bottom to show message
                print("No public decks match your search")
                print(e)
                return
        else:
            try:
                cur.execute("""SELECT ud.id, d.name, d.desc, u.username FROM decks d INNER JOIN user_decks ud ON d.id 
                = ud.deck_id INNER JOIN users u ON d.created_uid = u.id WHERE d.isPublic = 1 AND isDeleted = 0 AND 
                ud.uid = d.created_uid""")
            except:
                print("No public decks right now")
                return
        # dids, names, descs, users = zip(*[(row[0], row[1], row[2], row[3]) for row in cur.fetchall()])
        data = [[row[0], row[1], row[2], row[3]] for row in cur.fetchall()]
        card_counts = []
        for i in range(len(data)):
            cur.execute("""SELECT COUNT(*) FROM cards WHERE deck_id = ?""", (data[i][0],))
            count = cur.fetchone()[0]
            card_counts.append(count)
            data[i].append(count)
        return data

    def fillpublicdecks(self):
        searchfilter = self.browsefilter.text()
        self.publicdecksrootnode.removeRows(0, self.publicdecksrootnode.rowCount())
        decks = self.fetchpublicdecks(searchfilter)
        if decks:
            for id, name, desc, creator, cardcount in decks:
                self.publicdecksrootnode.appendRow(
                    [Deck(id, self.user), QStandardItem(desc), QStandardItem(creator), QStandardItem(cardcount)])

    def fillmydeckslist(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        self.deckslistmodel.removeRows(0, self.deckslistmodel.rowCount())
        self.decks = []
        self.checkboxes = []

        cur.execute("""SELECT ud.id, d.name FROM decks d INNER JOIN user_decks ud ON ud.deck_id = d.id WHERE 
        d.created_uid = ? AND ud.uid = ?""", (self.user.id, self.user.id))
        try:
            dids, names = zip(*[(row[0], row[1]) for row in cur.fetchall()])
        except:
            dids = []
            names = []

        for i in range(len(dids)):
            deck = Deck(dids[i], self.user)
            self.decks.append(deck)
            check = QStandardItem()
            check.setCheckable(True)
            if deck.public == 1:
                check.setCheckState(2)
            else:
                check.setCheckState(0)
            self.checkboxes.append(check)
            self.deckslistmodel.appendRow([self.decks[i], check])

        cur.close()
        con.close()

    def togglepublic(self, check):
        deckpos = self.checkboxes.index(check)
        deck = self.decks[deckpos]
        if check.checkState() == 2:
            deck.public = 1
        else:
            deck.public = 0
        deck.save()
        self.fillpublicdecks()
        # print(deck.name, deck.public)

    def selectdeck(self, idx):

        deck = self.deckstreeview.model().item(idx.row(), 0)
        if deck.creator_id == self.user.id:
            return
        self.publicdeckview = PublicDeckView(deck, self.user)
        self.publicdeckview.show()

    def refresh(self):
        self.fillpublicdecks()
        self.fillmydeckslist()


class PublicDeckView(QWidget):
    def __init__(self, deck, user):
        super().__init__()
        loadUi("publicdeckview.ui", self)
        self.deck = deck
        self.user = user
        self.descriptionlabel.setText(f"{deck.desc}")
        self.decknamelabel.setText(f"{deck.name}")
        self.samplefromxcards.setText(self.samplefromxcards.text().replace("x", f"{self.deck.cardcount}"))
        self.loadsamples()
        self.addbutton.clicked.connect(self.toggledeckadded)
        if self.checkifinlibrary():
            self.addbutton.setText("Remove")
        else:
            self.addbutton.setText("Add")

    def loadsamples(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT t.fields, c.data FROM cards c INNER JOIN templates t ON c.template_id = t.id WHERE deck_id = ? ORDER BY RANDOM () LIMIT 3""", (self.deck.did,))
        samples = cur.fetchall()
        self.vlayout = QVBoxLayout(self.samplescrollareacontents)

        for sample in samples:
            tablemodel = QStandardItemModel()
            fields = sample[0].split(",")
            data = sample[1].split(",")
            for i in range(len(fields)):
                tablemodel.appendRow([QStandardItem(fields[i]), QStandardItem(data[i])])
            table = QTableView()
            table.setModel(tablemodel)
            table.horizontalHeader().hide()
            table.verticalHeader().hide()

            table.horizontalHeader().setSectionsMovable(False)
            table.setColumnWidth(0, 160)
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table.horizontalHeader().setStretchLastSection(True)

            row_height = table.verticalHeader().sectionSize(0)

            print(tablemodel.rowCount())
            table_height = (tablemodel.rowCount() * row_height) + 2
            table.setMinimumHeight(table_height)
            table.setMaximumHeight(table_height)

            table.setSelectionMode(QAbstractItemView.NoSelection)
            table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            table.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

            self.vlayout.addWidget(table)
        self.vlayout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def toggledeckadded(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        if not self.checkifinlibrary():
            cur.execute("""SELECT MIN(id) FROM configs
                    WHERE uid = ?""", (self.user.id,))
            cfgid = cur.fetchone()[0]
            cur.execute("""INSERT INTO user_decks (deck_id, uid, config_id) VALUES (?, ?, ?)""", (self.deck.did, self.user.id, cfgid))
            cur.execute("""SELECT c.id FROM cards c WHERE c.deck_id = ?""", (self.deck.did,))
            cids = cur.fetchall()
            for cid in cids:
                cid = cid[0]
                cur.execute("""SELECT id FROM user_cards WHERE cid = ? AND uid = ?""", (cid, self.user.id))
                if not cur.fetchone():
                    cur.execute("""INSERT INTO user_cards (uid, cid, ef, ivl, type, status, reps, lapses, odue)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (self.user.id, cid, self.deck.config.new_init_ef, None, 0, 0, 0, 0, time()))
            self.addbutton.setText("Remove")

        else:
            self.addbutton.setText("Add")
            cur.execute("""DELETE FROM user_decks WHERE deck_id = ? AND uid = ?""", (self.deck.did, self.user.id))

        con.commit()
        cur.close()
        con.close()
        # todo call refresh function here, or other system


    def checkifinlibrary(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT id FROM user_decks ud WHERE ud.uid = ? AND ud.deck_id = ?""", (self.user.id, self.deck.did))
        exists = cur.fetchone() is not None
        return exists


#############################


def resetstack():
    """
    used after navigating away from any of the main 5 pages
    """
    for i in range(stack.count() - 8):
        widget = stack.widget(8)
        stack.removeWidget(widget)
        widget.deleteLater()


def gotodecks():
    stack.setCurrentIndex(3)
    resetstack()
    refreshmainwindows()


def gotoadd():
    stack.setCurrentIndex(4)
    resetstack()
    refreshmainwindows()


def gotocards():
    stack.setCurrentIndex(5)
    resetstack()
    refreshmainwindows()


def gotostats():
    stack.setCurrentIndex(6)
    resetstack()
    refreshmainwindows()


def gotobrowse():
    stack.setCurrentIndex(7)
    resetstack()
    refreshmainwindows()


def connectmainbuttons(window):
    window.decks.clicked.connect(gotodecks)
    window.add.clicked.connect(gotoadd)
    window.cards.clicked.connect(gotocards)
    window.stats.clicked.connect(gotostats)
    window.browse.clicked.connect(gotobrowse)


def refreshmainwindows():
    """
    stack widgets [3,4,5,6,7] = [DecksMain, AddCard, CardsMain, StatsPage, Browse]
    """
    stack.widget(3).refresh()
    stack.widget(4).refresh()
    stack.widget(5).refresh()
    stack.widget(6).refresh()
    stack.widget(7).refresh()


def sha_256(message):
    # Initialize hash values: (first 32 bits of the fractional parts of the square roots of the first 8 primes 2..19):
    h0 = 0x6a09e667
    h1 = 0xbb67ae85
    h2 = 0x3c6ef372
    h3 = 0xa54ff53a
    h4 = 0x510e527f
    h5 = 0x9b05688c
    h6 = 0x1f83d9ab
    h7 = 0x5be0cd19

    k = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
         0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
         0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
         0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
         0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
         0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
         0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
         0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]

    if isinstance(message, str):
        message = message.encode('UTF-8')
    elif isinstance(message, bytes):
        pass

    L = len(message) * 8
    message += b'\x80'  # adds a single 1 bit to the end of the message (and then 7 0 bits)
    K = (512 - ((
                        L + 1 + 64) % 512))  # 512 - remainder from L + 1 + 64 / 512, note a value of K = 512
    # shouldn't be possible here
    if K == 512:
        K = 0
    message += b'\x00' * (K // 8)
    message += L.to_bytes(8,
                          'big')  # appends the value of L and pads it to 8 bytes or 64 bits (hence the +1 used earlier)

    assert (len(message) * 8) % 512 == 0, "Padding did not complete properly!"

    # splitting up the bytecode string into 512 bit chunks

    chunks = []
    for i in range(0, len(message), 64):  # 64 bytes = 512 bits
        chunks.append(message[i:i + 64])

    for chunk in chunks:
        # Create a list of the block's words
        w = [0] * 64

        # Copy chunk into first 16 words w[0..15] of the message schedule array
        for i in range(16):
            w[i] = int.from_bytes(chunk[i * 4:(i + 1) * 4], byteorder='big')

        # Extend the first 16 words into the remaining 48 words w[16..63] of the message schedule array:
        for i in range(16, 64):
            s0 = (right_rotate(w[i - 15], 7) ^ (right_rotate(w[i - 15], 18)) ^ (
                    w[i - 15] >> 3))  # rightshifts here was the error...
            s1 = (right_rotate(w[i - 2], 17) ^ right_rotate(w[i - 2], 19) ^ (w[i - 2] >> 10))
            w[i] = (w[i - 16] + s0 + w[i - 7] + s1) & 0xffffffff

        # Initialize working variables to current hash value
        a = h0
        b = h1
        c = h2
        d = h3
        e = h4
        f = h5
        g = h6
        h = h7

        # compression function main loop
        for i in range(64):
            S1 = right_rotate(e, 6) ^ right_rotate(e, 11) ^ right_rotate(e, 25)
            ch = (e & f) ^ (~e & g)
            temp1 = (h + S1 + ch + k[i] + w[i]) & 0xffffffff
            S0 = right_rotate(a, 2) ^ right_rotate(a, 13) ^ right_rotate(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (S0 + maj) & 0xffffffff

            h = g
            g = f
            f = e
            e = (d + temp1) & 0xffffffff
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xffffffff

        # add the compressed chunk to the current hash value
        h0 = (h0 + a) & 0xffffffff
        h1 = (h1 + b) & 0xffffffff
        h2 = (h2 + c) & 0xffffffff
        h3 = (h3 + d) & 0xffffffff
        h4 = (h4 + e) & 0xffffffff
        h5 = (h5 + f) & 0xffffffff
        h6 = (h6 + g) & 0xffffffff
        h7 = (h7 + h) & 0xffffffff

    # any time a bitwise AND is performed on a value with 0xffffffff this to make sure any value is at most 32 bits

    digest = h0.to_bytes(4, 'big') + h1.to_bytes(4, 'big') + h2.to_bytes(4, 'big') + h3.to_bytes(4,
                                                                                                 'big') + h4.to_bytes(4,
                                                                                                                      'big') + h5.to_bytes(
        4, 'big') + h6.to_bytes(4, 'big') + h7.to_bytes(4, 'big')

    return digest.hex()


def right_rotate(num, shift, size=32):
    return (num >> shift) | (num << size - shift)


"""
REDUNDANT CODE BELOW!!!! NEEDS TO BE MIGRATED TO GUI.
"""


# todo - migrate card review and spaced repetition algorithm/handling


class SpacedRepetition:
    def __init__(self, user, deck):
        self.user = user
        self.deck = deck

        # self.load_deck_parameters()

    def load_deck_parameters(self):
        # could be handled here or in deck class (loading config for a deck)
        pass

    def save_deck_parameters(self):
        pass
        # todo

    def calculate_interval_new(self, card, ease, start, end):
        start = start
        end = end
        # default values in case they aren't changed:
        new_ivl = card.interval
        new_ef = card.ease_factor
        new_due = card.due

        con = sqlite3.connect(database)
        cur = con.cursor()

        colConf = {
            'newSpread': 0,
            'collapseTime': 1200,
        }

        card.reps += 1

        # learning_steps = [60, 600]
        # relearning_steps = 60
        # collapse_time = 1200

        # need to add config record
        status_log = card.status

        if card.status == 0:
            cur.execute(
                """SELECT configs.new_delays FROM configs INNER JOIN user_decks ON user_decks.config_id = config_id""")
            new_delays = cur.fetchone()[0]
            new_delays = [int(x) for x in new_delays.split(',')]
            card.left = len(new_delays)
            print("status: new")
            card.status = 1

        if card.status == 1:
            print("status: learning")
            cur.execute(
                """SELECT configs.new_delays, configs.new_grad_ivls FROM configs INNER JOIN user_decks ON user_decks.config_id = config_id""")
            new_delays, new_grad_ivls = cur.fetchone()
            new_delays = [int(x) * 60 for x in new_delays.split(',')]
            new_grad_ivls = [int(x) for x in new_grad_ivls.split(',')]
            # might want to replace this with temp values then return and assign to cards, in order to be able to log old/new ivls etc
            if ease == 0:
                card.left = len(new_delays)
                new_ivl = new_delays[0]
                new_due = time() + new_ivl

            elif ease == 1:
                if card.left != 1:
                    new_ivl = (new_delays[-card.left] + new_delays[-card.left + 1]) / 2
                    new_due = time() + new_ivl
                    # return stuff and log
                if card.left == 1:
                    new_ivl = new_delays[-card.left]
                    new_due = time() + new_ivl
                    # return stuff and log

            elif ease == 2:
                card.left -= 1
                if card.left == 0:
                    card.status = 2
                    new_ivl = new_grad_ivls[0] * 86400
                    new_due = time() + new_ivl
                    # return stuff and log
                else:
                    new_ivl = new_delays[-card.left]
                    new_due = time() + new_ivl
                    # return stuff and log

            elif ease == 3:
                card.status = 2
                card.left = 0
                new_ivl = new_grad_ivls[1] * 86400
                new_due = time() + new_ivl
                # return stuff and log

        elif card.status == 2:
            print("status: review")
            cur.execute(
                """SELECT configs.rev_easy_factor, configs.rev_hard_factor, configs.max_ivl, configs.min_ivl, leech_fails, lapse_delays,
        lapse_percent FROM configs INNER JOIN user_decks ON user_decks.config_id = config_id""")
            easy_factor, hard_factor, max_ivl, min_ivl, leech_fails, lapse_delays, lapse_percent = cur.fetchone()
            lapse_delays = [int(x) * 60 for x in lapse_delays.split(',')]
            min_ivl *= 86400
            max_ivl *= 86400
            if ease == 0:
                card.lapses += 1
                new_ef = card.ease_factor - 20
                card.status = 3
                card.left = len(lapse_delays)
                new_ivl = card.interval * lapse_percent / 100
                if new_ivl < min_ivl:
                    new_ivl = min_ivl
                new_due = time() + lapse_delays[0]
                # return stuff and log

            elif ease == 1:
                new_ivl = card.interval * hard_factor / 100
                new_ef = card.ease_factor - 15
                new_due = time() + new_ivl
                # return stuff and log

            elif ease == 2:
                if math.ceil(card.due / 86400) * 86400 < math.ceil(time() / 86400) * 86400:
                    bonus = (math.ceil(time() / 86400) * 86400 - math.ceil(card.due / 86400) * 86400) / 2
                else:
                    bonus = 0
                new_ivl = (card.interval + bonus) * card.ease_factor / 100
                new_due = time() + new_ivl
                # return stuff and log

            elif ease == 3:
                if math.ceil(card.due / 86400) * 86400 < math.ceil(time() / 86400) * 86400:
                    bonus = (math.ceil(time() / 86400) * 86400 - math.ceil(card.due / 86400) * 86400)
                else:
                    bonus = 0
                new_ivl = (card.interval + bonus) * (card.ease_factor / 100) * (easy_factor / 100)
                new_due = time() + new_ivl
                new_ef = card.ease_factor + 20
                # return stuff and log

        elif card.status == 3:
            print("status: relearning")
            cur.execute(
                """SELECT configs.min_ivl, lapse_delays, lapse_percent FROM configs INNER JOIN user_decks ON user_decks.config_id = config_id""")
            min_ivl, lapse_delays, lapse_percent = cur.fetchone()
            lapse_delays = [int(x) for x in lapse_delays.split(',')]

            if ease == 0:
                card.left = len(lapse_delays)
                new_ivl = card.interval * lapse_percent / 100
                new_due = time() + lapse_delays[0]

            # DON'T CHANGE INTERVALS HERE
            elif ease == 1:
                if card.left != 1:
                    new_due = time() + (lapse_percent[-card.left] + lapse_percent[-card.left + 1]) / 2
                    # return stuff and log
                if card.left == 1:
                    new_due = time() + lapse_delays[-card.left]
                    # return stuff and log

            elif ease == 2:
                card.left -= 1
                if card.left == 0:
                    card.status = 2
                    new_due = time() + card.interval
                    # return stuff and log
                else:
                    new_due = time() + lapse_delays[-card.left]
                    # return stuff and log

            elif ease == 3:
                card.status = 2
                card.left = 0
                new_due = time() + card.interval
                # return stuff and log
        else:
            assert 0

        # todo fix this
        cur.close()
        con.close()
        self.log_review(card, ease, status_log, start, end, new_ivl, new_ef)
        card.review_update(new_ivl, new_ef, new_due)

    def log_review(self, card, ease, status_log, start, end, new_ivl, new_ef):
        # something wrong here
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT time from revlog WHERE ucid = ? ORDER BY time DESC""", (card.id,))
        try:
            last_time = cur.fetchone()[0]
        except:
            last_time = None
        # need to have else = None?
        cur.execute("""INSERT INTO revlog (
                    ucid,
                    ease,
                    ivl,
                    lastivl,
                    ef,
                    lastef,
                    status,
                    reps,
                    lapses,
                    time,
                    lasttime,
                    start,
                    end) VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            card.id, ease, new_ivl, card.interval, new_ef, card.ease_factor, status_log, card.reps,
            card.lapses, time(), last_time, start, end))
        con.commit()
        cur.close()
        con.close()


class Review:
    def __init__(self, spaced_repetition, deck):
        self.sr = spaced_repetition
        self.deck = deck
        self.queues = [Queue()] * 4
        self.learnlimit = 1000
        self.newlimit = 10
        self.reviewlimit = 200
        self.collapsetime = 1200
        self.reps = 0

    def reset_queue(self, no):
        self.queues[no] = Queue()

    def fill_learn(self):
        # need to store and track cards added to queue and last update time for resetting over new days filling with
        # all cards at once might present issues for inserting cards with smaller intervals, so maybe will have to
        # retrieve one at a time? And use another method for presenting total number of cards to be learnt that means
        # it can be displayed to the user
        if not self.queues[1].empty():
            return True
        con = sqlite3.connect(database)
        cur = con.cursor()
        cutoff = time() + self.collapsetime
        cur.execute(
            "SELECT u.id FROM user_cards u INNER JOIN cards ON u.cid = cards.id WHERE cards.deck_id = ? AND (u.status = 1 OR u.status = 3) AND u.due <= ? AND u.uid = ? ORDER BY due ASC LIMIT ?",
            (self.deck.id, cutoff, self.deck.user.id, self.learnlimit,))
        # order by ASC here is arbitrary for deterministic ordering (old)
        # order by due should get the earliest cards first but still suffers from the same issue as above
        for ucid in cur.fetchall():
            self.queues[1].put(Flashcard(ucid[0]))
            self.queues[1] = self.queues[1]
        cur.close()
        con.close()
        if not self.queues[1].empty():
            return True

    def fill_new(self):
        if not self.queues[0].empty():
            return True
        con = sqlite3.connect(database)
        cur = con.cursor()
        # this assumes that card id is the same as order for cards to be learnt, might want to assign a deck_idx to
        # user_cards with status 0 that can be changed and allows for custom learning orders
        cur.execute(
            "SELECT u.id FROM user_cards u INNER JOIN cards ON u.cid = cards.id WHERE cards.deck_id = ? AND u.status = 0 AND u.uid = ? ORDER BY cards.id ASC LIMIT ?",
            (self.deck.id, self.deck.user.id, self.newlimit))
        for ucid in cur.fetchall():
            self.queues[0].put(Flashcard(ucid[0]))
        # need to store and track cards added to queue and last update time for resetting over new days. IMPORTANT HERE
        # so that more and more new cards don't keep getting added
        cur.close()
        con.close()
        if not self.queues[0].empty():
            return True

    def fill_review(self):
        if not self.queues[2].empty():
            return True
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute(
            "SELECT u.id FROM user_cards u INNER JOIN cards ON u.cid = cards.id WHERE cards.deck_id = ? AND u.status = 2 AND u.due <= ? AND u.uid = ? ORDER BY u.due ASC LIMIT ?",
            (self.deck.id, math.ceil(time() / 86400) * 86400, self.deck.user.id, self.reviewlimit))
        for ucid in cur.fetchall():
            self.queues[2].put(Flashcard(ucid[0]))
        cur.close()
        con.close()
        # again need to ensure limit is tracked and updated in database
        # should retrieve all due cards then shuffle and limit number based on settings
        if not self.queues[2].empty():
            return True

    def review(self):
        print("Type 'exit' at any point to exit review mode")
        empty = False
        while not empty:
            exit = self.review_card()
            if exit == 'exit':
                break
            elif exit:
                print("No more cards to review")
                empty = True

    # done - allow review of as many cards as desired and exit at any time
    # todo - allow for custom review

    def get_card(self):
        card = self._get_card()
        if card:
            self.reps += 1
            return card

    def _get_card(self):
        "Return the next due card or None."

        # learning card due?
        c = self.get_learn_card()
        if c:
            return c

        # new first, or time for one?
        if self.time_for_new_card():
            c = self.get_new_card()
            if c:
                return c

        # card due for review?
        c = self.get_review_card()
        if c:
            return c

        # new cards left?
        c = self.get_new_card()
        if c:
            return c

        # collapse or finish
        return self.get_learn_card(collapse=True)

    def get_learn_card(self, collapse=False):
        if self.fill_learn():
            return self.queues[1].get()
        else:
            return None

    def get_new_card(self):
        if self.fill_new():
            return self.queues[0].get()

    def get_review_card(self):
        if self.fill_review():
            return self.queues[2].get()

    def time_for_new_card(self):
        # determines if a new card should be shown (in relation to the review cards)
        return True

    def review_card(self):
        # messy way for early exit but should work for now
        card = self.get_card()
        if not card:
            return True
        self.show_card(card)
        start = time()
        temp = input("Press the Enter key to flip...")
        if temp == 'exit':
            return 'exit'
        self.flip_card(card)
        graded = False
        # need to change for more advanced algorithm
        while not graded:
            try:
                ease = input("How easy (0-3) was the card to recall...")
                ease = int(ease)
                graded = True
                end = time()
                self.sr.calculate_interval_new(card, ease, start, end)
                return False
            except Exception as e:
                if ease == 'exit':
                    return 'exit'
                else:
                    print(f'Error Occurred: {e}')

    def show_card(self, card):
        # need to add some functionality to cards to filter front and back sides
        # for now will just define front/back and print cards
        print(card.zip["front"])
        # todo - fetch front fields and display once gui incorporated

    def flip_card(self, card):
        print(card.zip["back"])
        # todo - as above


class Main:
    def __init__(self):
        self.user = None
        self.login()

    # todo add updation of user dom table on actions

    # login done
    # deck selection done
    # todo - migrate deck and template creation
    # todo - migrate flashcard moving
    # todo - migrate public deck adding to library + add checking for duplication

    def create_deck(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        name = input("Deck name...")
        existing = cur.fetchall()
        while name in existing:
            name = input("Name already exists, please enter a new name...")
        description = input("Description...")
        cur.execute("""INSERT INTO decks (name, desc, created, modified, created_uid, total_cards, isPublic, isDeleted)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                    (name, description, time(), time(), self.user.id, 0, 0, 0))
        deck_id = cur.fetchone()[0]
        cur.execute("SELECT id, name, new_init_ef FROM configs where uid = ?", (self.user.id,))

        cur.execute("SELECT id, name FROM configs where uid = ?", (self.user.id,))
        ids, names = zip(*[(row[0], row[1]) for row in cur.fetchall()])

        # should instead print 1-n and then retrieve id of that index.
        for i in range(len(ids)):
            print(f"{ids[i]} - {names[i]}")
        if not ids:
            print("you do not have any configs setup")
        while True:
            config = int(input("\nEnter a valid config id or 'exit' to return"))
            if config == 'exit':
                return
            elif config in ids:
                break
            else:
                print("invalid input")

        while True:
            try:

                cur.execute("""INSERT INTO user_decks (uid, deck_id, config_id) VALUES (?, ?, ?)""",
                            (self.user.id, deck_id, config))
                break
            except:
                print("invalid id")
        print(f"Deck {name} created")
        con.commit()
        cur.close()
        con.close()
        self.menu()

    def create_template(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        name = input("Template name...")
        existing = cur.fetchall()
        while name in existing:
            name = input("Name already exists, please enter a new name...")
        fields = []
        print("Enter as many fields as desired, and hit return when finished")
        while True:
            field = input("Enter field...")
            if field == "":
                break
            fields.append(field)
        sortfield = fields[0]
        cur.execute("""INSERT INTO templates (name, fields, sortfield, modified, created_uid)
                            VALUES (?, ?, ?, ?, ?)""", (name, ",".join(fields), sortfield, time(), self.user.id))
        print(f"Template {name} created")
        con.commit()
        cur.close()
        con.close()
        self.menu()

    def edit_template(self):
        print("Can't you read? I said todo")
        self.menu()

    def move_flashcards(self):
        # testing: invalid inputs for everything, selecting empty decks, same decks etc. (although not really necessary until finalised with GUI)
        con = sqlite3.connect(database)
        cur = con.cursor()
        while True:
            empty = True
            while empty:
                dids = []
                names = []
                cur.execute("SELECT id, name FROM decks")
                for fetch in cur.fetchall():
                    dids.append(fetch[0])
                    names.append(fetch[1])
                print("DECKS:")
                for i in range(len(dids)):
                    print(f"{dids[i]} - {names[i]}")
                deckfrom = None
                while deckfrom not in dids:
                    deckfrom = int(input("Enter id of deck to move from..."))
                    if not deckfrom in dids:
                        print("Invalid deck ID\n")
                print(f"Deck selected: {names[dids.index(deckfrom)]}")

                cur.execute("SELECT id, data FROM cards WHERE deck_id = ?", [deckfrom])
                cids = []
                datas = []
                # todo add checking for if deck is empty
                for fetch in cur.fetchall():
                    cids.append(fetch[0])
                    datas.append(fetch[1])
                    empty = False  # only sets empty to false if deck contains cards
                if empty:
                    print("Selected deck is empty\n")

            print("CARDS:")
            for i in range(len(cids)):
                print(f"{cids[i]}: {datas[i]}")

            cid = None
            while cid not in cids:
                cid = int(input("Enter id of card to move..."))

            print("DECKS:")
            for i in range(len(dids)):
                print(f"{dids[i]} - {names[i]}")
            deckto = None
            while deckto not in dids:
                deckto = int(input("Enter id of deck to move to..."))
                if deckto == deckfrom:
                    print("Same deck selected")
                    deckto = None
            print(f"Deck selected: {names[dids.index(deckto)]}")

            while True:
                confirm = input("confirm move? (no:0, yes:1) ")
                if confirm in ['0', '1']:
                    break
                print("invalid input")

            if confirm == '1':
                break
            else:
                print("\nmove cancelled")
                while True:
                    exit = input("enter 1 to continue, 0 to exit")
                    if exit in ['0', '1']:
                        break
                    print("invalid input")
                if exit == '1':
                    break
                elif exit == '0':
                    self.menu()

        cur.execute("""UPDATE cards SET
        deck_id = ?,
        modified = ?
        WHERE id = ?""", (deckto, time(), cid))

        print(f"Move complete from {names[dids.index(deckfrom)]} -> {names[dids.index(deckto)]}")
        con.commit()
        cur.close()
        con.close()
        self.menu()

    def browse_decks(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        try:
            cur.execute("""SELECT d.id, d.name, d.desc, u.username FROM decks d INNER JOIN users u on d.created_uid = 
            u.id WHERE d.isPublic = 1 AND isDeleted = 0""")
        except:
            print("No public decks right now")
            return
        dids, names, descs, users = zip(*[(row[0], row[1], row[2], row[3]) for row in cur.fetchall()])
        card_counts = []
        for i in range(len(dids)):
            cur.execute("""SELECT COUNT(*) FROM cards WHERE deck_id = ?""", (dids[i],))
            card_counts.append(cur.fetchone()[0])
            print(f"{names[i]}: {descs[i]} | Creator - {users[i]} | Cards - {card_counts[i]} | id - {dids[i]}")
        while True:
            o = int(input("\nEnter the id of deck you would like to add or type 'exit' to return"))
            if o == 'exit':
                return
            elif o in dids:
                self._copy_deck(o, cur, con, names[dids.index(o)])
                cur.close()
                con.close()
                return
            else:
                print("invalid input")

    def _copy_deck(self, did, cur, con, deckname):
        cur.execute("SELECT id, name, new_init_ef FROM configs where uid = ?", (self.user.id,))
        ids, names, efs = zip(*[(row[0], row[1], row[2]) for row in cur.fetchall()])
        for i in range(len(ids)):
            print(f"{ids[i]} - {names[i]}")
        if not ids:
            print("you do not have any configs setup")
        while True:
            config = int(input("\nEnter a valid config id or 'exit' to return"))
            if config == 'exit':
                return
            elif config in ids:
                break
            else:
                print("invalid input")

        cur.execute("""INSERT INTO user_decks (uid, deck_id, config_id) VALUES (?, ?, ?)""",
                    (self.user.id, did, config))
        ef = efs[ids.index(config)]
        self._copy_cards(did, cur, con, ef)
        print(f"Deck {deckname} successfully added to your library")

    def _copy_cards(self, did, cur, con, ef):
        cur.execute("SELECT * FROM configs")
        cur.execute("""SELECT id FROM cards WHERE deck_id = ?""", (did,))
        cids = [row[0] for row in cur.fetchall()]
        for cid in cids:
            cur.execute("""INSERT INTO user_cards (uid, cid, ef, ivl, type, status, reps, lapses, odue)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (self.user.id, cid, ef, None, 0, 0, 0, 0, time()))

        con.commit()


"""
PROGRAM EXECUTION:
"""

database = 'data/newdb.db'

app = QApplication(sys.argv)
# app.setStyle("windows")
stack = QStackedWidget()

welcome = WelcomeScreen()
stack.addWidget(welcome)
login = Login()
stack.addWidget(login)
create = CreateAccount()
stack.addWidget(create)

# temporary while ui is not scalable
# stack.sizeHint().setHeight(900)
# stack.sizeHint().setWidth(1600)
stack.resize(1600, 900)
# stack.updateGeometry()
stack.show()

try:
    sys.exit(app.exec_())
except:
    print("Exiting")
