import decimal
import random
import sys

import mplcursors
from PyQt5 import QtWidgets, Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QApplication, QAction, QStackedWidget, QMainWindow, QMenu, QToolButton, QLabel, \
    QSizePolicy, QVBoxLayout, QHeaderView, QLineEdit, QSpinBox, QTableView, QSpacerItem, QAbstractItemView, QTreeView, \
    QRadioButton, QGridLayout, QHBoxLayout, QMenuBar, QComboBox, QButtonGroup
from PyQt5.Qt import QStandardItem, QStandardItemModel, QWidget
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtWebEngineWidgets import QWebEngineView

import sqlite3
from queue import Queue
from time import time, mktime
import re
import datetime
import math
import numpy as np
import matplotlib.patches as mpatches
import pandas as pd
from matplotlib import ticker
import matplotlib.colors as mcolors
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

# todo maybe add descriptions to graphs
# MAIN THINGS TODO:
# issues with review of shared decks, need to check what cards are being fetched in each statement

#  Deck creation - done
#  Review system and displaying flashcards - covered
#  todo - storing html and escaped fields, what do i need to have. how to enable a dark mode for the html page,
#   + how to go about storing sound and image files in a database or somewhere else and referencing them
#  need to write some kind of interpreter for html where fields are converted into their data.
# mainly done ^ still could try to work out how to use dark mode.


# note todo - include collapse condition when showing counts for learning/relearning cards
# todo - determine whether deleting fields affects template functionality (as inclusion of fields is only controlled
#  when manging templates, maybe just need to check for front and back format and delete {{field}} when it appears)

# todo consider allowing the editing of decks descriptions

#  Templates ^ part of displaying the flashcards - done, some testing done but do so more thoroughly later
#      - will need to add a field to the cards table for format type, could remove template field, but could prove
#      useful. - changed, formats part of template, no multiple note format types as of now
#      - new formats table will need to reference a template, used when parsing user input to check for valid fields.
#      - for this should replace templates combo box with a format sub-menu that opens up in a new window and changes
#      the text on confirming a format in the sub-window - ignore
#

# Client server socketing - consider, if not added make sure to justify thoroughly and explain implementation
#   - For this, it seems to be that whenever a signal is activated on the client side,
#   relevant data passed to functions should be passed and executed on the server side, and any necessary data used in
#   displaying sent back to the client
#    work out sync or async model

#  User Profiles and Following Tab - extra
#  Importing delimted files into decks - also extra but probably more important
#  Add salt values to SHA-256 hash func - low priority, but maybe important for justification
#       -other possilbe justification is to create a hash function where you know exactly what is going on, despite
#       possible security flaws
# USING python secrets module to generate salt values to be stored with passwords
# secrets.token_hex(nbytes = 32)


# TODO - whenever a card is added/deleted to a public deck, can update for all users by checking the user_cards table
#  to see if the connection exists for all users with a user_decks connection to that card's parent deck

# todo - browse window components, WHEN DECK CLICKED - NEW WINDOW: DISPLAYS deck name, description, (creator),
#  (+ratings), sample of cards, options to either add deck to library (no modification of cards
#  and updates in line with changes made by the creator) or copy the deck (allows for modification of cards) - stats
#  for each, comments/ratings section.
#  also for need a bunch of selection statement to ensure consistent logic when adding decks to your library

# todo - consider adding another table linked to templates which organises how templates are displayed
# this is referenced above

"""
Current Progress with sections of the program

# possibly connect a menu bar to access templates, configs options from anywhere, could add other menubar options for
# card window to handle moving cards etc or just right click.

DECKS:
- implemented:
-- adding decks, selecting configs for review
- todo:
-- deletion, renaming
-- add counts onto deckselected page + a indicator for when there are no cards to review (+ disconnect button)

CARDS:
- implemented:
-- adding, editing and browsing cards
- todo:
-- deletion, deck (and possibly template) migration, filters when browsing, integration of multimedia (imgs, audio)

Configs:
- implemented:
-- Addition, cloning, renaming and deletion, configuration of all settings currently in use.
- todo:
-- nothing I can think of as of now, maybe consider more settings for configuration down the line (possibly new order)

Templates:
- implemented:
-- Addition, renaming, deletion. 
-- Adding, renaming, deletion and repositioning of fields + selection of sortfield.
-- Editing and styling of formats, validity checking (of fields and syntax) and rendering/displaying a preview as HTML in the ui
-- Parsing of templates when displaying flashcards in review section
- todo
-- again, handling of multimedia once storage and integration of this is worked out

Browsing/Public Decks:
- implemented:
-- publishing of decks, and the ability for other users to view and add published decks to their library, aswell 
    as filter public dekcs via a text input
- todo:
-- check functionality when reviewing a shared deck (done?), and potentially add optional syncronisation if the creator makes changes
-- also potentially add an option to allow users to copy a deck (which adds it to their library as if they created it), and the functionality behind this

Login + Account Creation:
- implemented:
-- user account creation, password hashing and storing of details in database to allow for future login, 
-- input checking and error handling in these window
- todo:
-- possibly add regex validity checking for emails, currently accepts any string

Study/Review Of Flashcards:
- implemented:
-- displaying of text based flashcard fields
-- queue formation, interval calculation and updating of various fields pertaining to spaced the spaced repetition algorithm
-- logging of reviews to be utilised when fetching statistics
- todo:
-- again intergrate multimedia content
-- also thoroughly bug test this section, as of writing it seems as though there might be an error with queue formation
-- issue should be fixed now ^

Statistics:
- todo:
-- decide on what statistics to display and how to go about doing this within the ui

Other Features to be Considered once Minimum Completion reached:
- Importing of delimited files into flashcards
- Client Server Socketing
- User Profiles and some kind of Social System
- Adding salt values to password hashing

"""

basictemplate_front = """{{Front}}"""
basictemplate_back = """{{FrontSide}}
<hr>
{{Back}}"""
basictemplate_styling = """.card {
  font-family: arial;
  font-size: 20px;
  text-align: center;
  color: white;
  background-color: rgb(50,50,50);
}}
"""
basictemplate_fields = 'Front,Back'
basictemplate_sort = 'Front'


def addbasictemplate(uid, cur):
    cur.execute(
        """INSERT INTO templates (fields, sortfield, modified, created_uid, front_format, back_format, styling, name) VALUES 
        (?, ?, ?, ?, ?, ?, ?, ?)""", (basictemplate_fields, basictemplate_sort, time(), uid, basictemplate_front,
                                      basictemplate_back, basictemplate_styling, 'Basic'))


default_config_insert = """INSERT INTO configs (
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
                                                ?)"""


class User:
    def __init__(self, id, name):
        # store general settings here (preferences in anki)
        self.id = id
        self.name = name
        self.collapsetime = None
        self.neworder = None # (0 = new first, 1 = new last, [2 = spread out])
        self.fetchpreferences()

    def fetchpreferences(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT collapsetime, neworder FROM users WHERE id = ?""", (self.id,))
        self.collapsetime, self.neworder = cur.fetchone()

        cur.close()
        con.close()


class Deck(QStandardItem):
    def __init__(self, id, user, font_size=13, set_bold=False):
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

    def fetchdata(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT d.name, d.id, d.desc, ud.config_id, d.isPublic, d.created_uid, d.isDeleted 
        FROM user_decks ud INNER JOIN decks d ON ud.deck_id = d.id WHERE ud.id = ?""", (self.udid,))
        fetch = cur.fetchone()
        self.name, self.did, self.desc, self.config_id, self.public, self.creator_id, self.isDeleted = fetch
        self.config = Config(self.config_id)
        cur.execute("""SELECT COUNT (c.id) FROM cards c INNER JOIN decks d ON c.deck_id = d.id WHERE d.id = ?""",
                    (self.did,))
        try:
            self.cardcount = cur.fetchone()[0]
        except:
            self.cardcount = 0
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

        self.cid, self.data, self.deck_id, self.modified, self.template_id, self.creator_id, self.ease_factor, self.interval, self.lapses, self.left, \
            self.status, self.reps, self.type, self.due, self.original_due = cur.fetchone()

        cur.execute("""SELECT fields, sortfield
                                FROM templates
                                WHERE id = ?
                                """, [self.template_id])
        self.fields, self.sortfield = cur.fetchone()

        self.fields = self.fields.split(",")
        self.data = self.data.split(",")

        self.zip = dict(zip(self.fields, self.data))

        # can you combine these 2 commands?
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
                        """, (data, self.deck_id, self.modified, self.template_id, self.cid))
        else:
            print("You are not the creator of this card")
        con.commit()
        cur.close()
        con.close()

    def review_update(self, new_ivl, new_ef, new_due):
        con = sqlite3.connect(database)
        cur = con.cursor()
        self.interval = new_ivl
        self.ease_factor = new_ef
        self.due = new_due
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
              self.rev_easy_factor, self.rev_hard_factor, self.max_ivl, self.lapse_delays, self.lapse_percent,
              self.min_ivl, \
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
        cur.execute(
            """SELECT name, fields, sortfield, front_format, back_format, styling FROM templates WHERE id = ?""",
            (self.id,))
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user = None

        self.menubar = QMenuBar(self)
        # create menu items and add them to the menu bar
        omo_menu = self.menubar.addMenu("Omo")
        # Preceding spaces used when naming actions because they are reserved keywords on macOS
        # (and for indentation purposes)
        omo_menu.addAction(" Preferences")
        omo_menu.addAction(" Sign Out")
        omo_menu.addSeparator()

        quit_action = QAction(" Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        omo_menu.addAction(quit_action)

        # connect preferences action and disable initially
        preferences_action = omo_menu.actions()[0]
        preferences_action.setObjectName("Preferences")
        preferences_action.triggered.connect(self.openpreferences)
        preferences_action.setEnabled(False)

        # connect signout action and disable initially
        signout_action = omo_menu.actions()[1]
        signout_action.setObjectName("Signout")
        signout_action.triggered.connect(self.signout)
        signout_action.setEnabled(False)

        # set the QMenuBar for the main window
        self.setMenuBar(self.menubar)

        # create a QStackedWidget to manage the views
        self.stack = QStackedWidget()
        self.stack.addWidget(WelcomeScreen(self.stack, self))
        self.stack.addWidget(Login(self.stack, self))
        self.stack.addWidget(CreateAccount(self.stack, self))

        # set the QStackedWidget as the central widget of the main window
        self.setCentralWidget(self.stack)

    def signout(self):
        # clear user
        self.user = None

        # clear all widgets in the stack besides the welcome screen
        while self.stack.count() > 1:
            self.stack.removeWidget(self.stack.widget(1))

        # disable the "Preferences" and "Sign Out" actions
        preferences_action = self.menubar.findChild(QAction, "Preferences")
        signout_action = self.menubar.findChild(QAction, "Signout")
        preferences_action.setEnabled(False)
        signout_action.setEnabled(False)

        # add new login and account creation windows (to clear text inputted text)
        self.stack.addWidget(Login(self.stack, self))
        self.stack.addWidget(CreateAccount(self.stack, self))

        # show the welcome screen
        self.stack.setCurrentIndex(0)

    def openpreferences(self):
        if not self.user:
            return

        self.preferenceswindow = PreferencesWindow(self.user)
        self.preferenceswindow.buttonBox.accepted.connect(self.savepreferences)
        self.preferenceswindow.exec()

    def savepreferences(self):
        self.user.collapsetime = self.preferenceswindow.collapsetimebox.value() * 60
        self.user.neworder = self.preferenceswindow.neworderbox.currentData()

        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""UPDATE users SET
         collapsetime = ?,
         neworder = ?
         WHERE id = ?""", (self.user.collapsetime, self.user.neworder, self.user.id))
        con.commit()
        cur.close()
        con.close()

        self.preferenceswindow.deleteLater()


class PreferencesWindow(QDialog):
    def __init__(self, user):
        super().__init__()
        loadUi("preferenceswindow.ui", self)
        self.user = user
        self.collapsetimebox.setValue(self.user.collapsetime / 60)
        self.neworderbox.addItem("Show new cards after reviews", 0)
        self.neworderbox.addItem("Show new cards before reviews", 1)
        # self.neworderbox.addItem(QStandardItem("Show new cards mixed in with reviews"), 2)

        self.neworderbox.setCurrentIndex(self.user.neworder)


class WelcomeScreen(QDialog):
    def __init__(self, stack, mainwindow):
        super().__init__()
        loadUi("welcome.ui", self)
        self.stack = stack
        self.mainwindow = mainwindow
        self.login.clicked.connect(self.gotologin)
        self.createaccount.clicked.connect(self.gotocreation)

    def gotologin(self):
        self.stack.setCurrentIndex(1)

    def gotocreation(self):
        self.stack.setCurrentIndex(2)


class Login(QDialog):
    def __init__(self, stack, mainwindow):
        super().__init__()
        loadUi("login.ui", self)
        self.user = None
        self.stack = stack
        self.mainwindow = mainwindow
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.login.clicked.connect(self.loginfunction)
        self.createaccount.clicked.connect(lambda: self.stack.setCurrentIndex(2))

    def emptyedits(self):
        # to be used later if logout enabled
        self.emailfield.setText("")
        self.passwordfield.setText("")

    def loginfunction(self):
        if self.user:
            # clear all other windows if logged in previously
            self.user = None
            for i in range(self.stack.count() - 3):
                widget = self.stack.widget(3)
                self.stack.removeWidget(widget)
                widget.deleteLater()
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
                    self.error.setText("Incorrect Password")
                    return
                cur.execute("SELECT username, id FROM users WHERE email = ?",
                            (email,))
                name, uid = cur.fetchone()
                self.user = User(uid, name)
                self.stack.widget(2).user = self.user

                decksmain = DecksMain(self.user, self.stack)
                addcard = AddCard(self.user, self.stack)
                cardsmain = CardsMain(self.user, self.stack)
                stats = StatsPage(self.user, self.stack)
                browse = Browse(self.user, self.stack)
                self.stack.addWidget(decksmain)
                self.stack.addWidget(addcard)
                self.stack.addWidget(cardsmain)
                self.stack.addWidget(stats)
                self.stack.addWidget(browse)

                self.mainwindow.user = self.user

                preferences = self.mainwindow.menubar.findChild(QAction, "Preferences")
                preferences.setEnabled(True)
                signout = self.mainwindow.menubar.findChild(QAction, "Signout")
                signout.setEnabled(True)

                gotodecks(self.stack)

            else:
                self.error.setText("Email is not registered")
            cur.close()
            con.close()


class CreateAccount(QDialog):
    def __init__(self, stack, mainwindow):
        super().__init__(parent=mainwindow)
        loadUi("create_account.ui", self)
        self.user = None
        self.stack = stack
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.register_.clicked.connect(self.registeracc)
        self.login.clicked.connect(lambda: self.stack.setCurrentIndex(1))

    def emptyedits(self):
        # to be used later if logout enabled
        self.usernamefield.setText("")
        self.emailfield.setText("")
        self.passwordfield.setText("")

    def registeracc(self):
        if self.user:
            # clear all other windows if logged in previously
            self.user = None
            for i in range(self.stack.count() - 3):
                widget = self.stack.widget(3)
                self.stack.removeWidget(widget)
                widget.deleteLater()
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
                # creating user
                cur.execute("""INSERT INTO users (username, password_hash, email, doc, dom) 
                    VALUES (?, ?, ?, ?, ?) RETURNING id""", (username, pw_hash, email, time(), time())
                            )
                uid = cur.fetchone()[0]
                # adding basic config
                cur.execute(default_config_insert, (uid,))
                # adding basic template
                addbasictemplate(uid, cur)
                con.commit()

                self.user = User(uid, username)
                self.stack.widget(1).user = self.user

                decksmain = DecksMain(self.user, self.stack)
                addcard = AddCard(self.user, self.stack)
                cardsmain = CardsMain(self.user, self.stack)
                stats = StatsPage(self.user, self.stack)
                browse = Browse(self.user, self.stack)
                self.stack.addWidget(decksmain)
                self.stack.addWidget(addcard)
                self.stack.addWidget(cardsmain)
                self.stack.addWidget(stats)
                self.stack.addWidget(browse)

                self.mainwindow.user = self.user

                preferences = self.mainwindow.menubar.findChild(QAction, "Preferences")
                preferences.setEnabled(True)
                signout = self.mainwindow.menubar.findChild(QAction, "Signout")
                signout.setEnabled(True)

                gotodecks(self.stack)

            cur.close()
            con.close()


class DecksMain(QWidget):
    def __init__(self, user, stack):
        super().__init__()
        loadUi("decksmain.ui", self)
        self.adddeckwindow = None
        self.user = user
        self.stack = stack

        connectmainbuttons(self, self.stack)

        # initialising the tree model
        self.treeModel = QStandardItemModel(0, 4, self.decktree)
        self.treeModel.setHeaderData(0, Qt.Horizontal, "Deck")
        self.treeModel.setHeaderData(1, Qt.Horizontal, "Description")
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

        self.decktree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.decktree.customContextMenuRequested.connect(self.deckmenu)

        self.adddeckbutton.clicked.connect(self.adddeck)
        self.refreshtree()

    def refresh(self):
        self.refreshtree()
        self.alertlabel.setText("")

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
                    VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                    (deckname, desc, time(), config.id, self.user.id, 0, 0))
        deckid = cur.fetchone()[0]
        cur.execute(f"""INSERT INTO user_decks (uid, deck_id, config_id) VALUES (?, ?, ?)""",
                    (self.user.id, deckid, config.id))
        con.commit()
        cur.close()
        con.close()
        self.adddeckwindow = None
        self.refresh()

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
        deckselect = DeckSelected(self.user, deck, self.stack)
        self.stack.addWidget(deckselect)
        self.adddeckwindow = None
        self.stack.setCurrentIndex(8)

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

            # might be better to split counts into 3 types then add together + pass values to selected window?

            cur.execute(f"""SELECT COUNT (uc.id) FROM user_cards uc 
                        INNER JOIN cards c ON uc.cid = c.id 
                        INNER JOIN user_decks ud ON c.deck_id = ud.deck_id
                        WHERE ud.id = {deck.udid} 
                        AND uc.uid = {self.user.id}
                        AND (uc.status = 1 OR uc.status = 2 OR uc.status = 3)
                        AND uc.due <= {math.ceil(time() / 86400) * 86400}
                        """)

            duecount = cur.fetchone()[0]

            cur.execute(f"""SELECT COUNT (DISTINCT revlog.ucid) FROM revlog INNER JOIN user_cards uc ON revlog.ucid = uc.id 
                        INNER JOIN cards c on uc.cid = c.id 
                        INNER JOIN user_decks ud ON c.deck_id = ud.deck_id 
                        WHERE ud.id = {deck.udid}
                        AND ud.uid = {self.user.id}
                        AND (revlog.time >= {math.floor(time() / 86400) * 86400} 
                        AND revlog.time <= {math.ceil(time() / 86400) * 86400})""")

            reviewedtodaycount = cur.fetchone()[0]

            cur.execute(f"""SELECT COUNT (DISTINCT revlog.ucid) FROM revlog 
                    INNER JOIN user_cards uc ON revlog.ucid = uc.id 
                    INNER JOIN cards c on uc.cid = c.id 
                    INNER JOIN user_decks ud ON c.deck_id = ud.deck_id 
                    WHERE ud.id = {deck.udid}
                    AND ud.uid = {self.user.id}
                    AND (revlog.time >= {math.floor(time() / 86400) * 86400} 
                    AND revlog.time <= {math.ceil(time() / 86400) * 86400}
                    AND uc.due <= {math.ceil(time() / 86400) * 86400})""")

            stillinqueuecount = cur.fetchone()[0]

            if duecount >= deck.config.rev_per_day:
                duecount = deck.config.rev_per_day - reviewedtodaycount + stillinqueuecount

            cur.execute(f"""SELECT COUNT (uc.id) FROM user_cards uc 
            INNER JOIN cards c ON uc.cid = c.id 
            INNER JOIN user_decks ud ON c.deck_id = ud.deck_id
            WHERE ud.id = {deck.udid} AND uc.status = 0 AND uc.uid = {self.user.id}
            """)

            newcount = cur.fetchone()[0]

            cur.execute(f"""SELECT COUNT (DISTINCT revlog.ucid) FROM revlog
            INNER JOIN user_cards uc ON revlog.ucid = uc.id
            INNER JOIN cards c ON uc.cid = c.id
            INNER JOIN user_decks ud ON c.deck_id = ud.deck_id
            WHERE ud.id = {deck.udid}
            AND ud.uid = {self.user.id}
            AND revlog.status = 0
            AND (revlog.time >= {math.floor(time() / 86400) * 86400}
            AND revlog.time <= {math.ceil(time() / 86400) * 86400})""")

            newreviewedtodaycount = cur.fetchone()[0]

            if newcount + newreviewedtodaycount >= deck.config.new_per_day:
                newcount = deck.config.new_per_day - newreviewedtodaycount

            if newcount + duecount > deck.config.rev_per_day:
                newcount = deck.config.rev_per_day - duecount

            index = self.decktree.model().index(i, 2)
            self.decktree.model().setData(index, newcount)
            index = self.decktree.model().index(i, 3)
            self.decktree.model().setData(index, duecount)

    def deckmenu(self, position):
        menu = QMenu()
        rename = QAction(self.tr("Rename"), menu)
        rename.triggered.connect(self.rename)
        delete = QAction(self.tr("Delete"), menu)
        delete.triggered.connect(self.delete)
        menu.addActions([rename, delete])
        menu.exec_(self.decktree.viewport().mapToGlobal(position))

    def rename(self):
        deck = self.decktree.model().item(self.decktree.currentIndex().row())
        if deck.creator_id != self.user.id:
            self.alertlabel.setText("You are not the creator of this deck")
            return
        self.renamewindow = NameWindow()
        self.renamewindow.okbutton.clicked.connect(lambda: self.confirmrename(deck))
        self.renamewindow.namelineedit.setText(deck.name)
        self.renamewindow.show()

    def confirmrename(self, deck):
        newname = self.renamewindow.namelineedit.text()
        deck.name = newname
        deck.save()
        self.renamewindow.deleteLater()
        self.refresh()

    def delete(self):
        deck = self.decktree.model().item(self.decktree.currentIndex().row())
        deletedialog = DeleteDeckDialog(deck, self.user)
        if deletedialog.allowdeletion:
            deletedialog.buttonBox.accepted.connect(lambda: self.confirmdelete(deck))
        deletedialog.exec()

    def confirmdelete(self, deck):
        # difference between deleting and removing of a public deck is that deleting also deletes all cards,
        # removing keeps card progress

        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT uc.id FROM user_cards uc 
        INNER JOIN cards c ON uc.cid = c.id
        INNER JOIN decks d on c.deck_id = d.id
        WHERE uc.uid = ?
        AND d.id = ?""", (self.user.id, deck.did))

        for fetch in cur.fetchall():
            ucid = fetch[0]
            cur.execute("""DELETE FROM user_cards WHERE id = ?""", (ucid,))

        cur.execute("""DELETE FROM user_decks
        WHERE deck_id = ?
        AND uid = ?""", (deck.did, self.user.id))

        # checks if other users have access to the deck
        cur.execute("""SELECT id FROM user_decks
        WHERE deck_id = ?""", (deck.did,))

        # deletes the deck and associated cards if no other users have access
        if not cur.fetchone():
            cur.execute("""DELETE FROM cards WHERE deck_id = ?""", (deck.did,))
            cur.execute("""DELETE FROM decks WHERE id = ?""", (deck.did,))

        con.commit()
        cur.close()
        con.close()
        self.refresh()


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


class DeleteDeckDialog(QDialog):
    def __init__(self, deck, user):
        super().__init__()
        self.deck = deck
        self.user = user
        loadUi("deletedeck.ui", self)
        self.settext()

    def settext(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT isPublic FROM decks WHERE id = ?""", (self.deck.did,))
        deckpublic = cur.fetchone()[0]
        if deckpublic == 1 and (self.deck.creator_id == self.user):
            self.allowdeletion = False
            self.label.setText("""The deck is currently public, please delist it before deleting this deck""")
        else:
            self.allowdeletion = True
            cur.execute("""SELECT COUNT (id) FROM cards WHERE deck_id = ?""", (self.deck.did,))
            cardcount = cur.fetchone()[0]
            self.label.setText(f"""Delete {self.deck.name} and {cardcount} cards associated with it?""")
        cur.close()
        con.close()


class DeckSelected(QWidget):
    def __init__(self, user, deck, stack):
        self.user = user
        self.deck = deck
        self.stack = stack
        super().__init__()
        loadUi("deckselected.ui", self)
        connectmainbuttons(self, self.stack)

        self.fetchcounts()

        self.deckname.setText(deck.name)
        # self.backbutton.clicked.connect(self.back)
        self.deckoptionsbutton.clicked.connect(self.deckoptions)

    def deckoptions(self):
        self.optionswindow = DeckOptions(self.user, self.deck)
        self.optionswindow.show()

    def study(self):
        self.study = Study(self.user, self.deck, self.stack)

    def fetchcounts(self):
        tempstudywindow = Study(self.user, self.deck, self.stack, counts=True)
        newcount, learningcount, reviewcount = tempstudywindow.fetchcounts()
        if not newcount == learningcount == reviewcount == 0:
            self.newcount.setText(f"{newcount}")
            self.learningcount.setText(f"{learningcount}")
            self.reviewcount.setText(f"{reviewcount}")
            self.studybutton.clicked.connect(self.study)
        else:
            self.clearlayout(self.countslayout)
            label = QLabel("Congratulations! You have finished studying this deck for now.")
            label.setAlignment(Qt.AlignHCenter)
            font = QFont()
            font.setPointSize(22)
            label.setFont(font)
            self.countslayout.addWidget(label)

    def clearlayout(self, layout):
        # recursive function to clear all the layouts and widgets within the layout passed as a parameter
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearlayout(item.layout())


# maybe create a study class that handles both front and back and switches between the two

class Study:
    def __init__(self, user, deck, stack, counts=False):
        self.user = user
        self.deck = deck
        self.stack = stack
        self.card = None
        self.template = None
        self.starttime = None
        self.endtime = None

        #########################

        self.queues = [Queue(), Queue(), Queue()]
        # could rewrite to have 3 seperate queues

        # todo add configuration for these 2 in user preferences, hard code rn ^
        self.reps = 0  # not used rn

        ##################

        if counts:
            return

        self.studyfront = StudyFront(self.stack)
        self.studyfront.flipbutton.clicked.connect(self.flip)
        self.stack.addWidget(self.studyfront)

        self.studyback = StudyBack(self.stack)
        self.studyback.againbutton.clicked.connect(lambda: self.review(0))
        self.studyback.hardbutton.clicked.connect(lambda: self.review(1))
        self.studyback.goodbutton.clicked.connect(lambda: self.review(2))
        self.studyback.easybutton.clicked.connect(lambda: self.review(3))
        self.stack.addWidget(self.studyback)

        self.startreview()
        """ 
        todo:
        Study sequence/loop:
        initialise queues once? Do i need to use a queue data structure here or would an artificial queue using the sql 
        database work? - using queue data strucutures is probably feasible sticking to what is outlined below, storing 
        all potential cards for review would prevent lots of repeated database connections <---- potential justification
        
        loop:
        - fetch next card
        - filter through queues in fixed preferential order for now, can add configuration later
        - show the front
        - flip input
        - show back
        - user inputs ease
        - calculate interval
        - log review
        - if using dynamic queue data strucutures, will need to check due, then add card back to appropriate queue if 
        necessary
        - check for more cards in queue
        - if yes loop
        """

    def fetchcounts(self):
        self.fill_new()
        self.fill_learn(collapse=True)
        self.fill_review()
        newcount = len(list(self.queues[0].queue))
        learncount = len(list(self.queues[1].queue))
        reviewcount = len(list(self.queues[2].queue))
        return newcount, learncount, reviewcount

    def startreview(self):
        self.loadcard()
        if not self.card:
            return
        self.template = Template(self.card.template_id)
        self.starttime = time()
        self.showfront()

    def showfront(self):
        front = self.fillfront()
        self.studyfront.htmlview.setHtml(
            f"""<head><style>{self.template.styling}</style></head> <body class='card'>{front}</body>""")
        self.stack.setCurrentIndex(9)

    def fillfront(self):
        front = re.sub(r"\n", "", self.template.front)
        match = True
        while match:
            match = re.search(r"\{\{(.+?)}}", front)
            if match:
                match = match.group(0)
                field = match[2:-2]
                front = re.sub(match, f"{self.card.zip[field]}", front)
        return front

    def fillback(self):
        back = re.sub(r"\n", "", self.template.back)
        match = True
        while match:
            match = re.search(r"\{\{(.+?)}}", back)
            if match:
                match = match.group(0)
                field = match[2:-2]
                if field == "FrontSide":
                    front = self.fillfront()
                    back = re.sub(match, f"{front}", back)
                else:
                    back = re.sub(match, f"{self.card.zip[field]}", back)
        return back

    def loadcard(self):
        self.card = self.get_card()
        if not self.card:
            print("GO BACK TO DECK SELECTED PAGE")
            for i in range(self.stack.count() - 9):
                widget = self.stack.widget(9)
                self.stack.removeWidget(widget)
                widget.deleteLater()
                self.stack.setCurrentIndex(8)
                self.stack.widget(8).fetchcounts()
            return

    def flip(self):
        self.stack.setCurrentIndex(10)
        self.showback()

    def showback(self):
        back = self.fillback()
        # error because of == 0 or 1
        if self.card.status == 0 or self.card.status == 1:
            self.new_ivls, self.due_ivls = self.calculateintervals1()
        elif self.card.status == 2:
            self.new_ivls, self.due_ivls = self.calculateintervals2()
        elif self.card.status == 3:
            self.new_ivls, self.due_ivls = self.calculateintervals3()

        self.studyback.againivllabel.setText(converttime(self.due_ivls[0]))
        self.studyback.hardivllabel.setText(converttime(self.due_ivls[1]))
        self.studyback.goodivllabel.setText(converttime(self.due_ivls[2]))
        self.studyback.easyivllabel.setText(converttime(self.due_ivls[3]))

        self.studyback.htmlview.setHtml(
            f"""<head><style>{self.template.styling}</style></head> <body class='card'>{back}</body>""")
        self.stack.setCurrentIndex(10)

    def review(self, ease):
        self.endtime = time()
        # print(f"ease = {ease}")
        self.update_interval(ease)
        self.startreview()

    def update_interval(self, ease):
        # NOTE FOR WRITEUP, CAN FIND OLD VERSION OF THIS FUNCTION ON GOOGLE DRIVE TO DEMONSTRATE HOW IT HAS
        # BEEN REFACTORED - WILL DEFINITELY ALLOW FOR EASIER EXPLANATION

        new_ef = self.card.ease_factor  # (for convenience if not changed)

        # only changes in left and EF handled here
        self.card.reps += 1
        status_log = self.card.status

        if self.card.status == 0:
            new_delays = [int(x) for x in self.deck.config.new_delays.split(',')]
            self.card.left = len(new_delays)
            # print(f"set left = {self.card.left}")
            new_ef = self.deck.config.new_init_ef
            self.card.status = 1

        if self.card.status == 1:
            new_delays = [int(x) * 60 for x in self.deck.config.new_delays.split(',')]
            if ease == 0:
                self.card.left = len(new_delays)
            elif ease == 2:
                self.card.left -= 1

                if self.card.left == 0:
                    self.card.status = 2
                # print(f"{self.card.left} - left")
                # print(f"{self.card.status} - status")

            elif ease == 3:
                self.card.status = 2
                self.card.left = 0

        elif self.card.status == 2:
            # todo add in leech fails/flagging?
            lapse_delays = [int(x) * 60 for x in self.deck.config.lapse_delays.split(',')]
            if ease == 0:
                self.card.lapses += 1
                new_ef = self.card.ease_factor - 20
                self.card.status = 3
                self.card.left = len(lapse_delays)
            elif ease == 1:
                new_ef = self.card.ease_factor - 15
            elif ease == 3:
                new_ef = self.card.ease_factor + 20

            if new_ef < 130:
                new_ef = 130

        elif self.card.status == 3:
            # todo add in min ivl checking
            lapse_delays = [int(x) for x in self.deck.config.lapse_delays.split(',')]
            min_ivl = self.deck.config.min_ivl * 86400

            if ease == 0:
                self.card.left = len(lapse_delays)

            elif ease == 2:
                self.card.left -= 1
                if self.card.left == 0:
                    self.card.status = 2

            elif ease == 3:
                self.card.status = 2
                self.card.left = 0

        else:
            assert 0

        new_due = time() + self.due_ivls[ease]
        new_ivl = self.new_ivls[ease]

        self.log_review(ease, status_log, new_ivl, new_ef)
        self.card.review_update(new_ivl, new_ef, new_due)
        return ease, status_log, new_ivl, new_ef,

    def calculateintervals1(self):
        # calculations for status = 0 and 1

        new_delays = [int(x) * 60 for x in self.deck.config.new_delays.split(',')]
        new_grad_ivls = [int(x) for x in self.deck.config.new_grad_ivls.split(',')]
        # might want to replace this with temp values then return and assign to self.cards,
        # in order to be able to log old/new ivls etc. - done

        due_ivls = [0] * 4
        new_ivls = [0] * 4

        # print(new_delays)

        new_ivls[0] = new_delays[0]
        due_ivls[0] = new_ivls[0]

        if self.card.status == 0:
            left = len(new_delays)
        else:
            left = self.card.left

        if left != 1:
            new_ivls[1] = (new_delays[-left] + new_delays[-left + 1]) / 2
            due_ivls[1] = new_ivls[1]
        elif left == 1:
            new_ivls[1] = new_delays[-left]
            due_ivls[1] = new_ivls[1]

        if left - 1 == 0:
            new_ivls[2] = new_grad_ivls[0] * 86400
            due_ivls[2] = new_ivls[2]
        else:
            new_ivls[2] = new_delays[-(left - 1)]
            due_ivls[2] = new_ivls[2]

        new_ivls[3] = new_grad_ivls[1] * 86400
        due_ivls[3] = new_ivls[3]

        return new_ivls, due_ivls

    def calculateintervals2(self):
        # for status = 2 (review)
        due_ivls = [0] * 4
        new_ivls = [0] * 4

        lapse_delays = [int(x) * 60 for x in self.deck.config.lapse_delays.split(',')]
        min_ivl = self.deck.config.min_ivl * 86400
        max_ivl = self.deck.config.max_ivl * 86400

        # interval is changed here, but because the card has been failed, interval is not taken as the next due time
        # since the card enters the relearning state
        new_ivls[0] = self.card.interval * self.deck.config.lapse_percent / 100
        if new_ivls[0] < min_ivl:
            new_ivls[0] = min_ivl
        due_ivls[0] = lapse_delays[0]

        new_ivls[1] = self.card.interval * self.deck.config.rev_hard_factor / 100
        due_ivls[1] = new_ivls[1]

        if math.ceil(self.card.due / 86400) * 86400 < math.ceil(time() / 86400) * 86400:
            bonus = (math.ceil(time() / 86400) * 86400 - math.ceil(self.card.due / 86400) * 86400) / 2
        else:
            bonus = 0
        new_ivls[2] = (self.card.interval + bonus) * self.card.ease_factor / 100
        due_ivls[2] = new_ivls[2]

        if math.ceil(self.card.due / 86400) * 86400 < math.ceil(time() / 86400) * 86400:
            bonus = (math.ceil(time() / 86400) * 86400 - math.ceil(self.card.due / 86400) * 86400)
        else:
            bonus = 0
        new_ivls[3] = (self.card.interval + bonus) * (self.card.ease_factor / 100) * (
                self.deck.config.rev_easy_factor / 100)
        due_ivls[3] = new_ivls[3]

        # maybe error here in calculating easy ivl

        return new_ivls, due_ivls

    def calculateintervals3(self):
        # for status 3 (relearning)
        # print("status: relearning")
        lapse_delays = [int(x) * 60 for x in self.deck.config.lapse_delays.split(',')]
        min_ivl = self.deck.config.min_ivl * 86400

        due_ivls = [0] * 4
        new_ivls = [0] * 4

        new_ivls[0] = self.card.interval * self.deck.config.lapse_percent / 100
        if new_ivls[0] < min_ivl:
            new_ivls[0] = min_ivl
        due_ivls[0] = lapse_delays[0]

        # DON'T CHANGE INTERVALS HERE
        if self.card.left != 1:
            due_ivls[1] = time() + (self.deck.config.lapse_percent[-self.card.left] + self.deck.config.lapse_percent[
                -self.card.left + 1]) / 2
        if self.card.left == 1:
            due_ivls[1] = lapse_delays[-self.card.left]
        new_ivls[1] = self.card.interval

        if self.card.left - 1 == 0:
            due_ivls[2] = self.card.interval
        else:
            due_ivls[2] = lapse_delays[-(self.card.left - 1)]
        new_ivls[2] = self.card.interval

        due_ivls[3] = self.card.interval
        new_ivls[3] = self.card.interval

        return new_ivls, due_ivls

    def log_review(self, ease, status_log, new_ivl, new_ef):
        # something wrong here??
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT time from revlog WHERE ucid = ? ORDER BY time DESC""", (self.card.id,))
        try:
            last_time = cur.fetchone()[0]
        except:
            last_time = None

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
            self.card.id, ease, new_ivl, self.card.interval, new_ef, self.card.ease_factor, status_log, self.card.reps,
            self.card.lapses, time(), last_time, self.starttime, self.endtime))
        con.commit()
        cur.close()
        con.close()

    def fill_learn(self, collapse=False):
        # need to store and track cards added to queue and last update time for resetting over new days filling with
        # all cards at once might present issues for inserting cards with smaller intervals, so maybe will have to
        # retrieve one at a time? And use another method for presenting total number of cards to be learnt that means
        # it can be displayed to the user
        if not self.queues[1].empty():
            return True

        con = sqlite3.connect(database)
        cur = con.cursor()
        if not collapse:
            cutoff = time()
        else:
            cutoff = time() + self.user.collapsetime

        # todo consider how to integrate review per day count into here, review and new sections, could possibly use
        #  some variable to track fetches, or might work out due to how queue formation works sequentially.

        cur.execute(
            """SELECT uc.id FROM user_cards uc 
            INNER JOIN cards c ON uc.cid = c.id 
            INNER JOIN decks d ON c.deck_id = d.id 
            WHERE d.id = ? 
            AND (uc.status = 1 OR uc.status = 3) 
            AND uc.due <= ? 
            AND uc.uid = ? 
            ORDER BY uc.id ASC LIMIT ?""",
            (self.deck.did, cutoff, self.user.id, self.deck.config.rev_per_day))
        # need to change rework rev_per_day filter
        # order by id ASC here is arbitrary for deterministic ordering (old)
        # order by due should get the earliest cards first but still suffers from the same issue as above
        for ucid in cur.fetchall():
            self.queues[1].put(Flashcard(ucid[0]))
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

        cur.execute(f"""SELECT COUNT (DISTINCT revlog.ucid) FROM revlog
            INNER JOIN user_cards uc ON revlog.ucid = uc.id 
            INNER JOIN cards c on uc.cid = c.id 
            INNER JOIN user_decks ud ON c.deck_id = ud.deck_id 
            WHERE ud.id = {self.deck.udid}
            AND ud.uid = {self.user.id}
            AND revlog.status = 0 
            AND (revlog.time >= {math.floor(time() / 86400) * 86400} 
            AND revlog.time <= {math.ceil(time() / 86400) * 86400})""")

        newreviewedcount = cur.fetchone()[0]

        cur.execute(
            """SELECT uc.id FROM user_cards uc 
            INNER JOIN cards c ON uc.cid = c.id 
            INNER JOIN decks d ON c.deck_id = d.id 
            WHERE d.id = ? 
            AND uc.uid = ?
            AND uc.status = 0 
            ORDER BY uc.id ASC LIMIT ?""",
            (self.deck.did, self.user.id, self.deck.config.new_per_day - newreviewedcount))
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

        # todo, see earlier in fill_learn()

        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute(
            """SELECT uc.id FROM user_cards uc
             INNER JOIN cards c ON uc.cid = c.id 
             INNER JOIN decks d ON c.deck_id = d.id
             INNER JOIN user_decks ud ON ud.deck_id = d.id 
             WHERE ud.id = ? 
             AND uc.status = 2 
             AND uc.due <= ? 
             AND uc.uid = ? ORDER BY uc.due ASC LIMIT ?""",
            (self.deck.udid, math.ceil(time() / 86400) * 86400, self.user.id, self.deck.config.rev_per_day))
        for ucid in cur.fetchall():
            self.queues[2].put(Flashcard(ucid[0]))
        cur.close()
        con.close()

        # again need to ensure limit is tracked and updated in database
        # should retrieve all due cards then shuffle and limit number based on settings?

        if not self.queues[2].empty():
            return True

    def get_card(self):
        card = self._get_card()
        if card:
            self.reps += 1  # currently not used
        return card

    def _get_card(self):
        "Return the next due card or None."

        # learning card due?
        c = self.get_learn_card()
        if c:
            return c

        # new first, or time for one? (to be implemented in review settings, either new first, last [or mixed])
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
        if self.fill_learn(collapse):
            print("getting learn card")
            return self.queues[1].get()
        else:
            return None

    def get_new_card(self):
        if self.fill_new():
            print("getting new card")
            return self.queues[0].get()

    def get_review_card(self):
        if self.fill_review():
            print("getting review card")
            return self.queues[2].get()

    def time_for_new_card(self):
        # determines if a new card should be shown (in relation to the review cards)
        # placeholder right now
        if self.user.neworder == 0:
            return False
        elif self.user.neworder == 1:
            return True
        elif self.user.neworder == 2:
            # need some other function to manage spread of new cards within other reviews
            pass

    def review_card(self):
        card = self.get_card()
        if not card:
            # call back to deck page and set text to show all cards are reviewed
            return True
        self.show_card(card)
        start = time()
        temp = input("Press the Enter key to flip...")
        self.flip_card(card)
        graded = False
        # need to change for more advanced algorithm
        # on ease button clicked
        # self.calculate_interval_new(card, ease, start, end)


class StudyFront(QWidget):
    def __init__(self, stack):
        super().__init__()
        loadUi("studyfront.ui", self)
        connectmainbuttons(self, stack)

        self.htmlview = QWebEngineView()

        self.mainvlayout.insertWidget(2, self.htmlview, 1)


class StudyBack(QWidget):
    def __init__(self, stack):
        super().__init__()
        loadUi("studyback.ui", self)
        connectmainbuttons(self, stack)

        self.htmlview = QWebEngineView()

        self.mainvlayout.insertWidget(2, self.htmlview, 0)
        self.mainvlayout.setStretch(0, 0)
        self.mainvlayout.setStretch(1, 0)
        self.mainvlayout.setStretch(2, 1)
        self.mainvlayout.setStretch(3, 0)


class DeckOptions(QWidget):

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
        del self.configs[delidx]
        # print(len(self.configs))
        # print("deleting")
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


class CardsMain(QWidget):
    # todo get filters working
    # make sure a general search matches against all card data, not just sortfield, also best to split before matching
    def __init__(self, user, stack):
        self.user = user
        super().__init__()
        loadUi("cardsmain.ui", self)
        connectmainbuttons(self, stack)
        self.searchbutton.clicked.connect(self.search)

        # setting up filter button
        self.filterMenu = QMenu()

        self.filterWholeCollection = QAction("Whole Collection", self.filtertool)
        self.filterLastStudied = QMenu("Studied", self.filterMenu)
        self.filterStatus = QMenu("Status", self.filterMenu)

        self.statusNew = QAction("New", self.filterStatus)
        self.statusLearning = QAction("Learning", self.filterStatus)
        self.statusReview = QAction("Review", self.filterStatus)
        self.statusRelearning = QAction("Relearning", self.filterStatus)

        self.studiedToday = QAction("Today", self.filterLastStudied)
        self.studiedLastWeek = QAction("In the last week", self.filterLastStudied)
        self.studiedLastMonth = QAction("In the last month", self.filterLastStudied)
        self.studiedLastYear = QAction("In the last year", self.filterLastStudied)

        self.filterLastStudied.addActions(
            [self.studiedToday, self.studiedLastWeek, self.studiedLastMonth, self.studiedLastYear])

        self.statusNew.triggered.connect(lambda: self.filterstatusfunc(self.statusNew.text()))
        self.statusLearning.triggered.connect(lambda: self.filterstatusfunc(self.statusLearning.text()))
        self.statusReview.triggered.connect(lambda: self.filterstatusfunc(self.statusReview.text()))
        self.statusRelearning.triggered.connect(lambda: self.filterstatusfunc(self.statusRelearning.text()))

        self.studiedToday.triggered.connect(lambda: self.filterlaststudiedfunc(0))
        self.studiedLastWeek.triggered.connect(lambda: self.filterlaststudiedfunc(7))
        self.studiedLastMonth.triggered.connect(lambda: self.filterlaststudiedfunc(30))
        self.studiedLastYear.triggered.connect(lambda: self.filterlaststudiedfunc(365))

        self.filterWholeCollection.triggered.connect(self._filterwholecollection)

        self.filterStatus.addActions([self.statusNew, self.statusLearning, self.statusReview, self.statusRelearning])
        self.filterMenu.addAction(self.filterWholeCollection)

        self.filterMenu.addMenu(self.filterLastStudied)
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

        self.cardstree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cardstree.customContextMenuRequested.connect(self.cardsmenu)

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
        self.search()
        self.alertlabel.setText("")
        # beware of issues here down the line with refresh

    def filterlaststudiedfunc(self, days):
        self.filterinput.setText(f"studied:{days}")
        self.search()

    def filterstatusfunc(self, status):
        self.filterinput.setText(f"status:{status.lower()}")
        self.search()

    def _filterwholecollection(self):
        self.filterinput.setText("")
        self.search()

    def search(self):
        fetch = self.fetch_cards()
        self.fillcards(fetch)

    def fetch_cards(self):
        # todo - change this function so it only displays cards in active decks (ie with a user_deck field),
        #  or has an option to NOTE: this might cause issues when changing windows with the clause to
        #  retain edits so might be easier just to reset the selection
        filtertext = self.filterinput.text()

        """
        can have:
        status:{new, learning, etc}
        studied:x
        deck:abc
        """
        # regex expressions
        # should have filters of:
        # status, time when last reviewed, last ease in review, reps, lapses, interval,
        # studied in the last week/month/year
        # maybe allow for searching of other user's cards in library but not editing
        # todo might need to save and retain the current sort state of the table when updating

        con = sqlite3.connect(database)
        cur = con.cursor()
        con.create_function("REGEXP", 2, regexp)

        expression = r"^(status|deck):[a-zA-Z]+|(studied):\d+$"
        match = re.search(expression, filtertext)
        if match:
            if "status:" in match.group(0):
                statusints = {"new": 0, "learning": 1, "review": 2, "relearning": 3}
                status = match.group(0)[7:]
                if status in statusints:
                    cur.execute("""SELECT uc.id, d.name FROM user_cards uc INNER JOIN cards c ON uc.cid = c.id
                             INNER JOIN decks d ON c.deck_id = d.id 
                             WHERE uc.uid = ?
                             AND uc.status = ?""", (self.user.id, statusints[status]))
            elif "deck:" in match.group(0):
                deckname = match.group(0)[5:]
                cur.execute("""SELECT uc.id, d.name FROM user_cards uc INNER JOIN cards c ON uc.cid = c.id
                         INNER JOIN decks d ON c.deck_id = d.id 
                         WHERE uc.uid = ? AND d.name REGEXP ? """, (self.user.id, deckname))
            elif "studied:" in match.group(0):
                days = int(match.group(0)[8:])
                today = datetime.date.today()
                timestamp = int(mktime(today.timetuple()))
                cutoff = timestamp - (86400 * days)
                cur.execute("""SELECT DISTINCT uc.id, d.name FROM user_cards uc INNER JOIN cards c ON uc.cid = c.id
                         INNER JOIN decks d ON c.deck_id = d.id 
                         INNER JOIN revlog r ON r.ucid = uc.id
                         WHERE r.time >= ?
                         AND uc.uid = ? """, (cutoff, self.user.id))
        else:
            cur.execute("""SELECT uc.id, d.name FROM user_cards uc INNER JOIN cards c ON uc.cid = c.id
                     INNER JOIN decks d ON c.deck_id = d.id
                     WHERE uc.uid = ? AND c.data REGEXP ?""", (self.user.id, filtertext))
            # cur.execute("""SELECT uc.id, d.name FROM user_cards uc INNER JOIN cards c ON uc.cid = c.id
            #          INNER JOIN decks d ON c.deck_id = d.id
            #          WHERE uc.uid = ?""", (self.user.id,))

        # check if falls under predifined filter formats, else iterate through card data to see if it contains a
        # regex match

        # consider whether user_cards which aren't connected to a user_deck pair shouldn't be shown, but can still be
        # stored

        fetch = [(row[0], row[1]) for row in cur.fetchall()]
        cur.close()
        con.close()

        return fetch

    def fillcards(self, fetch):
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

    def editcard(self, idx):
        if idx.row() == -1:  # prevents crashing if search is used whilst a card is selected
            return

        self.editingcard = self.rootNode.child(idx.row())
        if self.editingcard.creator_id != self.user.id:
            editable = False
        else:
            editable = True

        for i in reversed(range(self.scrollWidgetContents_layout.count())):
            self.scrollWidgetContents_layout.takeAt(i).widget().deleteLater()  # was using itemAt() which was wrong

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
        self.filterinput.setText(f'deck:{deck.name}')
        self.search()

    def cardsmenu(self, position):
        menu = QMenu()
        changedeck = QAction(self.tr("Change Deck"), menu)
        changedeck.triggered.connect(self.changedeck)
        # won't allow moving cards from public decks
        changedue = QAction(self.tr("Change Due Date"), menu)
        changedue.triggered.connect(self.changedue)
        forget = QAction(self.tr("Forget"), menu)
        forget.triggered.connect(self.forget)
        delete = QAction(self.tr("Delete"), menu)
        delete.triggered.connect(self.delete)
        menu.addActions([changedeck, changedue, forget, delete])
        menu.exec_(self.cardstree.viewport().mapToGlobal(position))

    def changedeck(self):
        # could allow selection of multiple cards
        card = self.cardstree.model().item(self.cardstree.currentIndex().row())
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT isPublic FROM decks WHERE id = ?""", (card.deck_id,))
        public = cur.fetchone()[0]
        if card.creator_id != self.user.id and public:
            # todo - maybe change this to a dialog box
            self.alertlabel.setText("This card is part of a public deck and cannot be moved")
        else:
            self.movewindow = MoveCard(self.user)
            self.movewindow.movebutton.clicked.connect(lambda: self.move(card))
            self.movewindow.exec()

    def move(self, card):
        deck = self.movewindow.decksmodel.item(self.movewindow.deckslist.currentIndex().row(), 0)
        if not deck:
            return
        card.deck_id = deck.did
        card.update(self.user.id)
        self.movewindow.deleteLater()
        self.refresh()

    def changedue(self):
        card = self.cardstree.model().item(self.cardstree.currentIndex().row())
        self.reschedulewindow = RescheduleWindow()
        self.reschedulewindow.buttonBox.accepted.connect(lambda: self.reschedule(card))
        self.reschedulewindow.exec()

    def reschedule(self, card):
        pattern = r"\d+(?:-\d+)?(?:!)?"
        # this regex pattern matches to x-y!, x-y, x!, or x [with x,y being integers]
        string = self.reschedulewindow.lineedit.text()
        match = re.search(pattern, string)

        if not match:
            self.alertlabel.setText("Please enter numbers in a valid format")
            self.reschedulewindow.deleteLater()

        con = sqlite3.connect(database)
        cur = con.cursor()
        match = match.group(0)
        if "-" in match and '!' in match:
            # Handle the x-y! case
            x, y = match.split("-")
            y = y[:-1]
            x, y = map(int, [x, y])
            try:
                days_ivl = random.randint(x, y)
            except:
                days_ivl = random.randint(y, x)
            ivl = days_ivl * 86400
            # max() ensures ivl isnt less than 1 day
            cur.execute("""UPDATE user_cards SET status = ?, due = ?, ivl = ? WHERE id = ?""",
                        (2, time() + ivl, max(ivl, 86400), card.id))
            print("x-y!")
        elif "-" in match:
            # Handle the x-y case
            x, y = map(int, match.split("-"))
            try:
                days_ivl = random.randint(x, y)
            except:
                days_ivl = random.randint(y, x)
            ivl = days_ivl * 86400
            cur.execute("""UPDATE user_cards SET status = ? due = ? WHERE id = ?""", (2, time() + ivl, card.id))
            print("x-y")
        elif "!" in match:
            # Handle the x! case
            x = int(match[:-1])
            ivl = x * 86400
            # max() ensures ivl isnt less than 1 day
            cur.execute("""UPDATE user_cards SET status = ?, due = ?, ivl = ? WHERE id = ?""",
                        (2, time() + ivl, max(ivl, 86400), card.id))
            print("x!")
        else:
            # Handle the x case
            x = int(match)
            ivl = x * 86400
            cur.execute("""UPDATE user_cards SET status = ?, due = ? WHERE id = ?""", (2, time() + ivl, card.id))

        con.commit()
        cur.close()
        con.close()
        self.reschedulewindow.deleteLater()
        self.refresh()

    def forget(self):
        card = self.cardstree.model().item(self.cardstree.currentIndex().row())
        self.forgetwindow = ForgetWindow()
        self.forgetwindow.buttonBox.accepted.connect(lambda: self.confirmforget(card))
        self.forgetwindow.exec()

    def confirmforget(self, card):
        con = sqlite3.connect(database)
        cur = con.cursor()
        if self.forgetwindow.resetcountscheck.isChecked():
            cur.execute("""UPDATE user_cards SET 
                        ef = ?,
                        ivl = ?,
                        status = ?,
                        reps = ?,
                        lapses = ?,
                        due = ?,
                        left = ?
                        WHERE id = ?""", (None, None, 0, 0, 0, None, 0, card.id))
        else:
            cur.execute("""UPDATE user_cards SET 
                        ef = ?,
                        ivl = ?,
                        status = ?,
                        due = ?,
                        left = ?
                        WHERE id = ?""", (None, None, 0, None, 0, card.id))

        con.commit()
        cur.close()
        con.close()
        self.forgetwindow.deleteLater()

    def delete(self):
        card = self.cardstree.model().item(self.cardstree.currentIndex().row())
        self.deletewindow = DeleteCard()
        self.deletewindow.buttonBox.accepted.connect(lambda: self.confirmdelete(card))
        self.deletewindow.exec()

    def confirmdelete(self, card):
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""DELETE FROM user_cards WHERE cid = ?""", (card.cid,))
        cur.execute("""DELETE FROM cards WHERE id = ?""", (card.cid,))
        con.commit()
        cur.close()
        con.close()
        self.deletewindow.deleteLater()
        self.refresh()


class MoveCard(QDialog):
    def __init__(self, user):
        super().__init__()
        loadUi("movecard.ui", self)
        self.user = user
        self.decksmodel = QStandardItemModel()
        self.loaddecks()
        self.cancelbutton.clicked.connect(self.deleteLater)

    def loaddecks(self):
        self.decksmodel.clear()
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("SELECT ud.id FROM user_decks ud INNER JOIN decks d ON ud.deck_id = d.id "
                    "WHERE ud.uid = ? AND d.created_uid = ?", (self.user.id, self.user.id))
        for fetch in cur.fetchall():
            deck = Deck(fetch[0], self.user)
            self.decksmodel.appendRow(deck)
        cur.close()
        con.close()
        self.deckslist.setModel(self.decksmodel)


class RescheduleWindow(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("reschedule.ui", self)
        self.buttonBox.rejected.connect(self.deleteLater)


class ForgetWindow(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("forgetwindow.ui", self)
        self.buttonBox.rejected.connect(self.deleteLater)


class DeleteCard(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("deletecard.ui", self)
        self.buttonBox.rejected.connect(self.deleteLater)


class AddCard(QWidget):
    def __init__(self, user, stack):
        self.user = user
        super().__init__()
        loadUi("addcard.ui", self)

        connectmainbuttons(self, stack)

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
        self.template = self.templateswindow.templatesmodel.item(
            self.templateswindow.templateslist.currentIndex().row(), 0)
        if self.template:
            self.applytemplate()
            self.templateswindow.hide()
        else:
            pass

    def fill_decks_box(self):
        self.decksbox.clear()
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT ud.id, d.name FROM decks d INNER JOIN user_decks ud ON ud.deck_id = d.id INNER JOIN users         
        u on d.created_uid = u.id WHERE u.id = ?""", (self.user.id,))
        try:
            self.ud_ids, self.d_names = zip(*[(row[0], row[1]) for row in cur.fetchall()])
        except:
            self.ud_ids = []
            self.d_names = []

        for name in self.d_names:
            self.decksbox.addItem(name)

    def refresh(self):
        self.fill_decks_box()
        # self.fill_templates_box()

    def add_card(self):
        # bad code?
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
            if not self.decksbox.currentText():
                self.error.setText("No deck selected")
                return
            ud_idx = self.d_names.index(self.decksbox.currentText())
            udeck_id = self.ud_ids[ud_idx]
            deck = Deck(udeck_id, self.user)
            cur.execute("""INSERT INTO cards (data, deck_id, template_id, modified, created_uid)
                            VALUES (?, ?, ?, ?, ?) RETURNING id""",
                        (card_data, deck.did, self.template.id, time(), self.user.id))
            cid = cur.fetchone()[0]
            cur.execute("""INSERT INTO user_cards (uid, cid, ivl, type, status, reps, lapses, odue, left)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (self.user.id, cid, None, 0, 0, 0, 0, time(), 0))

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
    # also todo connect delete, when deleting dont allow basic to be deleted using min id fetch for the user!!
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
        self.layoutbutton.clicked.connect(self.editlayout)

    def loadtemplates(self):
        self.templatesmodel.clear()
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("SELECT id FROM templates WHERE created_uid = ?", (self.user.id,))
        for fetch in cur.fetchall():
            template = Template(fetch[0])
            cur.execute(f"""SELECT COUNT (id) FROM cards WHERE template_id = {template.id}""")
            cardcount = cur.fetchone()[0]
            template.setText(f"{template.name} [{cardcount} cards]")
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
        con = sqlite3.connect(database)
        cur = con.cursor()
        if template.text() == "Add: Basic":
            addbasictemplate(self.user.id, cur)
        else:
            cur.execute("""INSERT INTO templates (fields, sortfield, modified, created_uid, front_format, back_format,
             styling, name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (template.fields, template.sortfield, time(), self.user.id,
                         template.front, template.back, template.styling, name))
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
        self.templatefieldswindow.cancelbutton.clicked.connect(lambda: self.cancel(self.templatefieldswindow))
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

            """
            CAN USE THIS IN WRITEUP
            handle these if... elif ... else execute as SQL
             here, allow fields to be added and deleted,
             when this happens will want to update all cards that are connected to the template, and update the data of
             any changed fields, if indexes change, will want to change the index of data, etc.
             Delete -> Delete Data and field
             Add -> Add field and empty data slot - Also need to check field name not in use
             Reposition -> Change position/index of field and data
             Rename -> Change field name
             Sort by this field -> change sortfield, make sure this changes with the ui aswell
             Should be sufficient (obviously cancel and save to discard/commit changes) - to cancel just call load
             template again
            """

        con.commit()
        cur.close()
        con.close()
        self.templatefieldswindow.deleteLater()
        self.loadtemplates()

    def editlayout(self):
        template = self.templatesmodel.item(self.templateslist.currentIndex().row(), 0)
        if not template:
            return
        self.layoutwindow = LayoutWindow(template)
        self.layoutwindow.savebutton.clicked.connect(self.savetemplatelayout)
        self.layoutwindow.cancelbutton.clicked.connect(lambda: self.cancel(self.layoutwindow))
        self.layoutwindow.show()

    def savetemplatelayout(self):
        # todo need to check if the layouts are valid, if not have to create dialog prompt alerting them and preventing
        #  saving - return from this function, parent should be self.layoutwindow in init
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""UPDATE templates SET front_format = ?, back_format = ?, styling = ? WHERE id = ?""",
                    (self.layoutwindow.template.front, self.layoutwindow.template.back,
                     self.layoutwindow.template.styling, self.layoutwindow.template.id))
        con.commit()
        cur.close()
        con.close()
        self.layoutwindow.deleteLater()
        self.loadtemplates()

    def delete(self):
        template = self.templatesmodel.item(self.templateslist.currentIndex().row(), 0)
        if not template:
            return

        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT MIN(id) FROM templates
                            WHERE created_uid = ?""", (self.user.id,))
        defaulttemplate = cur.fetchone()[0]

        if template.id == defaulttemplate:
            # todo dialog box to say default template can't be deleted
            return

        # trigger dialog box to show how many cards are affected
        # connect ok button to confirm delete function

        cur.close()
        con.close()
        self.loadtemplates()


class LayoutWindow(QWidget):
    def __init__(self, template):
        # do I want to load the two widgets separately and add them to the layout if there is an issue with the
        # layout text (e.g. {{ missing }} or field doesn't exist, update preview to show this, use a flag variable to
        # check for errors and if save clicked with an error - open up a dialog to prompt the user to change the
        # template
        super().__init__()
        loadUi("templatelayout.ui", self)
        self.preview = QWebEngineView()
        self.previewwidget.layout().addWidget(self.preview, 2)
        self.template = template

        self.formatfrontbutton.toggle()
        self.changeediting()

        self.formatfrontbutton.clicked.connect(self.changeediting)
        self.formatbackbutton.clicked.connect(self.changeediting)
        self.formatstylingbutton.clicked.connect(self.changeediting)
        self.frontpreviewbutton.clicked.connect(self.showpreview)
        self.backpreviewbutton.clicked.connect(self.showpreview)
        self.formattextedit.textChanged.connect(self.update)

    def changeediting(self):

        self.formattextedit.blockSignals(True)
        if self.formatfrontbutton.isChecked():
            if not self.frontpreviewbutton.isChecked():
                self.frontpreviewbutton.setChecked(True)
            self.formattextedit.setPlainText(f"{self.template.front or ''}")

        elif self.formatbackbutton.isChecked():
            if not self.backpreviewbutton.isChecked():
                self.backpreviewbutton.setChecked(True)

            self.formattextedit.setPlainText(f"{self.template.back or ''}")

        else:
            self.formattextedit.setPlainText(f"{self.template.styling or ''}")
        self.formattextedit.blockSignals(False)
        self.update()

    def update(self):
        if self.formatfrontbutton.isChecked():
            self.template.front = self.formattextedit.toPlainText()
        elif self.formatbackbutton.isChecked():
            self.template.back = self.formattextedit.toPlainText()
        else:
            self.template.styling = self.formattextedit.toPlainText()
        self.showpreview()

    def showpreview(self):

        # check for {{
        # except no }}, set html to show an error
        # except field doesn't exist to show error
        # parse field as html
        # move selection to processpreview
        if self.frontpreviewbutton.isChecked():
            preview = self.processpreview(1)
            self.preview.setHtml(preview)

        elif self.backpreviewbutton.isChecked():
            preview = self.processpreview(0)
            self.preview.setHtml(preview)

    def processpreview(self, side):
        if side:
            field_error, missing_brackets_error, front = self.extractfields(1)
            if field_error:
                # could pass the field as field error
                preview = "Field Doesn't exist"
            elif missing_brackets_error:
                preview = "'{{' is missing closing '}}'"
            else:
                preview = f"<head><style>{self.template.styling}</style></head> <body class='card'>{front}</body>"
                print(preview)
            return preview
        else:
            field_error, missing_brackets_error, back = self.extractfields(0)
            if field_error:
                # could pass the field as field error
                preview = "Field Doesn't exist"
            elif missing_brackets_error:
                preview = "'{{' is missing closing '}}'"

            else:
                preview = preview = f"<head><style>{self.template.styling}</style></head> <body class='card'>{back}</body>"
                print(preview)

            return preview
        pass

    def extractfields(self, side):
        field_error = False
        missing_brackets_error = False
        if side:
            front = re.sub(r"\n", "", self.template.front)
            match = True

            while match:
                # print(f"front: {front}")
                match = re.search(r"\{\{(.+?)\}\}", front)
                # print(match)
                if match:
                    match = match.group(0)
                    # print(f"match: ({match[2:-2]})")
                    if match[2:-2] not in self.template.fields.split(","):
                        # print(match[2:-2])

                        field_error = True
                        return field_error, missing_brackets_error, front
                    else:
                        front = re.sub(match, f"({match[2:-2]})", front)

            match = re.search(r"\{\{", front)
            if match:
                missing_brackets_error = True
                return field_error, missing_brackets_error, front
            return field_error, missing_brackets_error, front

        else:
            back = re.sub(r"\n", "", self.template.back)
            match = True

            while match:
                # print(f"back: {back}")
                match = re.search(r"\{\{(.+?)\}\}", back)
                # print(match)
                if match:
                    match = match.group(0)
                    # print(f"match: ({match[2:-2]})")
                    if match[2:-2] == "FrontSide":
                        # recursion
                        field_error, missing_brackets_error, front = self.extractfields(1)
                        back = re.sub(match, f"{front}", back)
                    elif match[2:-2] not in self.template.fields.split(","):

                        field_error = True
                        return field_error, missing_brackets_error, back
                    else:

                        back = re.sub(match, f"({match[2:-2]})", back)

            match = re.search(r"\{\{", back)
            if match:
                missing_brackets_error = True
                return field_error, missing_brackets_error, back
            return field_error, missing_brackets_error, back


class NameWindow(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("namewindow.ui", self)
        self.template = None
        self.cancelbutton.clicked.connect(self.deleteLater)


class TemplateFieldsWindow(QWidget):
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
        self.selectedfield = new_string = re.sub(r"^\d+: ", "",
                                                 self.fieldsmodel.item(self.fieldslist.currentIndex().row(), 0).text())
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


# STATS WINDOWS Important - would add to complexity due to aggregate functions,
# try to get this working asap
# IDEAS:
# statistics by deck and whole collection
# - no of cards studied today, total time spent studying, avg time, counts for each difficulty and %
# correct answers on mature cards (i.e. hard, good or easy on cards with previous intervals of > 21/30 days)
# cards due in the future, plot by days ahead and no
# [work out way to show historic reviews (number on each day)] - matplotlib imshow(z)? - low priority
# ^ breakdown of these past reviews on whether cards were young, mature, learning, relearning, new etc.
# [both time spent and no of reviews] ^
# Pie chart breakdown of cards in the deck - done this, todo should add text and percentages
# Plot of card intervals
# bar chart of card ease factors
# Success rate breakdown by hours over a given time frame
# Answer buttons pressed for each card type - (re+)learning, young, mature
# When cards were added? Not sure how this would be done or if it serves mutch purpose
# also want session statistics maybe?
# be open to any other ideas or suggestions


class StatsPage(QWidget):
    def __init__(self, user, stack):
        self.statuscolours = ['#6BAED6', '#DF8C50', '#CF6A52', '#84C685', '#48A461']
        self.answercolours = ['#8F0B29', '#D5A365', '#9DBE69', '#0B5E37']

        self.user = user
        self.deck = None
        super().__init__()
        loadUi("statspage.ui", self)
        connectmainbuttons(self, stack)
        labelfont = QFont()
        labelfont.setPointSize(18)

        layout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)

        # should really clear widgets and just refresh the graphs

        self.scrollarea.setWidget(self.scrollAreaWidgetContents)
        self.scrollarea.setWidgetResizable(True)
        self.scrollAreaWidgetContents.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scrollAreaWidgetContents.setLayout(layout)
        self.scrollAreaWidgetContents.layout().setAlignment(Qt.AlignTop)

        self.allcardsbutton.clicked.connect(self.allcardstoggled)
        self.deckbutton.clicked.connect(self.deckbuttontoggled)
        self.decksbox.currentIndexChanged.connect(self.changedeck)

        self.decksbox.currentIndexChanged.connect(self.refreshgraphs)

        self.allcardsbutton.setChecked(True)
        self.decksbox.setEnabled(False)
        self.deck = None
        self.createstatswidgets()
        self.refresh()

    def refresh(self):
        self.filldecksbox()
        self.refreshgraphs()

    def createstatswidgets(self):
        buttonfont = QFont()
        buttonfont.setPointSize(16)

        todaywidget = TodayStatsWidget()
        self.scrollAreaWidgetContents.layout().addWidget(todaywidget)

        # Creating future due housing widget and elements
        futuredue = GraphWidget()
        futuredue.titlelabel.setText("Future Due")

        buttonswidget = QWidget(futuredue.frame)
        buttonswidget.setObjectName("buttonswidget")
        buttonslayout = QHBoxLayout()

        onemonth = QRadioButton("1 month", buttonswidget)
        threemonths = QRadioButton("3 months", buttonswidget)
        oneyear = QRadioButton("1 year", buttonswidget)
        all = QRadioButton("all", buttonswidget)

        onemonth.setFont(buttonfont)
        threemonths.setFont(buttonfont)
        oneyear.setFont(buttonfont)
        all.setFont(buttonfont)

        onemonth.setObjectName("onemonth")
        threemonths.setObjectName("threemonths")
        oneyear.setObjectName("oneyear")
        all.setObjectName("all")

        onemonth.clicked.connect(self.refreshfuturereviews)
        threemonths.clicked.connect(self.refreshfuturereviews)
        oneyear.clicked.connect(self.refreshfuturereviews)
        all.clicked.connect(self.refreshfuturereviews)

        futurebuttongroup = QButtonGroup()
        futurebuttongroup.addButton(onemonth)
        futurebuttongroup.addButton(threemonths)
        futurebuttongroup.addButton(oneyear)
        futurebuttongroup.addButton(all)

        # Set the default checked button
        onemonth.setChecked(True)

        buttonslayout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        buttonslayout.addWidget(onemonth)
        buttonslayout.addWidget(threemonths)
        buttonslayout.addWidget(oneyear)
        buttonslayout.addWidget(all)
        buttonslayout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))

        buttonswidget.setLayout(buttonslayout)
        futuredue.frame.layout().addWidget(buttonswidget)

        self.scrollAreaWidgetContents.layout().addWidget(futuredue)

        # Past reviews housing widget and elements
        pastreviews = GraphWidget()
        pastreviews.titlelabel.setText("Past Reviews")

        buttonswidget = QWidget(futuredue.frame)
        buttonswidget.setObjectName("buttonswidget")
        buttonslayout = QHBoxLayout()

        onemonth = QRadioButton("1 month", buttonswidget)
        threemonths = QRadioButton("3 months", buttonswidget)
        oneyear = QRadioButton("1 year", buttonswidget)

        onemonth.setFont(buttonfont)
        threemonths.setFont(buttonfont)
        oneyear.setFont(buttonfont)

        onemonth.setObjectName("onemonth")
        threemonths.setObjectName("threemonths")
        oneyear.setObjectName("oneyear")

        onemonth.clicked.connect(self.refreshpastreviews)
        threemonths.clicked.connect(self.refreshpastreviews)
        oneyear.clicked.connect(self.refreshpastreviews)

        pastbuttongroup = QButtonGroup()
        pastbuttongroup.addButton(onemonth)
        pastbuttongroup.addButton(threemonths)
        pastbuttongroup.addButton(oneyear)
        pastbuttongroup.setExclusive(True)

        onemonth.setChecked(True)

        buttonslayout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        buttonslayout.addWidget(onemonth)
        buttonslayout.addWidget(threemonths)
        buttonslayout.addWidget(oneyear)
        buttonslayout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))

        buttonswidget.setLayout(buttonslayout)
        pastreviews.frame.layout().addWidget(buttonswidget)

        self.scrollAreaWidgetContents.layout().addWidget(pastreviews)

        # Cards breakdown

        piewidget = GraphWidget()
        piewidget.titlelabel.setText("Cards By Status")
        self.scrollAreaWidgetContents.layout().addWidget(piewidget)

        # ivls widget

        ivlswidget = GraphWidget()
        ivlswidget.titlelabel.setText("Review Intervals")

        buttonswidget = QWidget(ivlswidget.frame)
        buttonswidget.setObjectName("buttonswidget")
        buttonslayout = QHBoxLayout()

        onemonth = QRadioButton("1 month", buttonswidget)
        half = QRadioButton("50%", buttonswidget)
        ninety = QRadioButton("90%", buttonswidget)
        all = QRadioButton("all", buttonswidget)

        onemonth.setFont(buttonfont)
        half.setFont(buttonfont)
        ninety.setFont(buttonfont)
        all.setFont(buttonfont)

        onemonth.setObjectName("onemonth")
        half.setObjectName("half")
        ninety.setObjectName("ninety")
        all.setObjectName("all")

        onemonth.setChecked(True)

        ivlsbuttongroup = QButtonGroup()
        ivlsbuttongroup.addButton(onemonth)
        ivlsbuttongroup.addButton(half)
        ivlsbuttongroup.addButton(ninety)
        ivlsbuttongroup.addButton(all)
        ivlsbuttongroup.setExclusive(True)

        onemonth.clicked.connect(self.refreshivlswidget)
        half.clicked.connect(self.refreshivlswidget)
        ninety.clicked.connect(self.refreshivlswidget)
        all.clicked.connect(self.refreshivlswidget)

        buttonslayout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        buttonslayout.addWidget(onemonth)
        buttonslayout.addWidget(half)
        buttonslayout.addWidget(ninety)
        buttonslayout.addWidget(all)
        buttonslayout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))

        buttonswidget.setLayout(buttonslayout)
        ivlswidget.frame.layout().addWidget(buttonswidget)

        self.scrollAreaWidgetContents.layout().addWidget(ivlswidget)

        easewidget = GraphWidget()
        easewidget.titlelabel.setText("Card Ease")
        self.scrollAreaWidgetContents.layout().addWidget(easewidget)

        # Answer buttons widget

        answerswidget = GraphWidget()
        answerswidget.titlelabel.setText("Answer Buttons")

        buttonswidget = QWidget(answerswidget.frame)
        buttonswidget.setObjectName("buttonswidget")
        buttonslayout = QHBoxLayout()

        onemonth = QRadioButton("1 month", buttonswidget)
        threemonths = QRadioButton("3 months", buttonswidget)
        oneyear = QRadioButton("1 year", buttonswidget)
        all = QRadioButton("all", buttonswidget)

        onemonth.setFont(buttonfont)
        threemonths.setFont(buttonfont)
        oneyear.setFont(buttonfont)
        all.setFont(buttonfont)

        onemonth.setObjectName("onemonth")
        threemonths.setObjectName("threemonths")
        oneyear.setObjectName("oneyear")
        all.setObjectName("all")

        all.setChecked(True)

        answersbuttongroup = QButtonGroup()
        answersbuttongroup.addButton(onemonth)
        answersbuttongroup.addButton(threemonths)
        answersbuttongroup.addButton(oneyear)
        answersbuttongroup.addButton(all)
        answersbuttongroup.setExclusive(True)

        onemonth.clicked.connect(self.refreshanswerwidget)
        threemonths.clicked.connect(self.refreshanswerwidget)
        oneyear.clicked.connect(self.refreshanswerwidget)
        all.clicked.connect(self.refreshanswerwidget)


        buttonslayout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        buttonslayout.addWidget(onemonth)
        buttonslayout.addWidget(threemonths)
        buttonslayout.addWidget(oneyear)
        buttonslayout.addWidget(all)
        buttonslayout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))

        buttonswidget.setLayout(buttonslayout)
        answerswidget.frame.layout().addWidget(buttonswidget)

        self.scrollAreaWidgetContents.layout().addWidget(answerswidget)

        # break

        self.scrollAreaWidgetContents.layout().addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding))

        self.scrollAreaWidgetContents.layout().setContentsMargins(0, 0, 0, 0)

    def refreshgraphs(self):
        self.updatetodaywidget(self.scrollAreaWidgetContents.layout().itemAt(0).widget())  # .widget()?
        self.refreshfuturereviews()
        self.refreshpastreviews()
        self.refreshstatuswidget()
        self.refreshivlswidget()
        self.refresheasewidget()
        self.refreshanswerwidget()

    def refreshfuturereviews(self):
        futurewidget = self.scrollAreaWidgetContents.layout().itemAt(1).widget()
        buttonswidget = futurewidget.frame.findChild(QWidget, "buttonswidget")

        daysrange = None  # Default value if none of the radio buttons are checked
        if buttonswidget.findChild(QRadioButton, "onemonth").isChecked():
            daysrange = 30
        elif buttonswidget.findChild(QRadioButton, "threemonths").isChecked():
            daysrange = 90
        elif buttonswidget.findChild(QRadioButton, "oneyear").isChecked():
            daysrange = 365

        futuresubwidget = self.createfuturereviewsbar(daysrange)
        if futurewidget.frame.layout().count() > 3:
            futurewidget.frame.layout().itemAt(3).widget().deleteLater()

        futurewidget.frame.layout().addWidget(futuresubwidget)

    def refreshpastreviews(self):
        pastwidget = self.scrollAreaWidgetContents.layout().itemAt(2).widget()

        buttonswidget = pastwidget.frame.findChild(QWidget, "buttonswidget")
        daysrange = None  # Default value if none of the radio buttons are checked
        if buttonswidget.findChild(QRadioButton, "onemonth").isChecked():
            daysrange = 30
        elif buttonswidget.findChild(QRadioButton, "threemonths").isChecked():
            daysrange = 90
        elif buttonswidget.findChild(QRadioButton, "oneyear").isChecked():
            daysrange = 365

        pastsubwidget = self.createpastreviewsbar(daysrange)
        if pastwidget.frame.layout().count() > 3:
            pastwidget.frame.layout().itemAt(3).widget().deleteLater()

        pastwidget.frame.layout().addWidget(pastsubwidget)

    def refreshstatuswidget(self):
        statuswidget = self.scrollAreaWidgetContents.layout().itemAt(3).widget()
        statussubwidget = self.createstatuspie()

        if statuswidget.frame.layout().count() > 2:
            statuswidget.frame.layout().itemAt(2).widget().deleteLater()

        statuswidget.frame.layout().addWidget(statussubwidget)

    def refreshivlswidget(self):
        ivlswidget = self.scrollAreaWidgetContents.layout().itemAt(4).widget()

        buttonswidget = ivlswidget.frame.findChild(QWidget, "buttonswidget")
        maxivl = None  # Default value if none of the radio buttons are checked
        percentage = None
        if buttonswidget.findChild(QRadioButton, "onemonth").isChecked():
            maxivl = 31
        elif buttonswidget.findChild(QRadioButton, "half").isChecked():
            percentage = 0.5
        elif buttonswidget.findChild(QRadioButton, "ninety").isChecked():
            percentage = 0.9

        ivlsubwidget = self.createintervalsbar(maxivl, percentage)

        if ivlswidget.frame.layout().count() > 3:
            ivlswidget.frame.layout().itemAt(3).widget().deleteLater()

        ivlswidget.frame.layout().addWidget(ivlsubwidget)

    def refresheasewidget(self):
        easewidget = self.scrollAreaWidgetContents.layout().itemAt(5).widget()

        easesubwidget = self.createeasefactorbar()
        if easewidget.frame.layout().count() > 2:
            easewidget.frame.layout().itemAt(2).widget().deleteLater()

        easewidget.frame.layout().addWidget(easesubwidget)

    def refreshanswerwidget(self):
        answerwidget = self.scrollAreaWidgetContents.layout().itemAt(6).widget()

        buttonswidget = answerwidget.frame.findChild(QWidget, "buttonswidget")
        daysrange = None  # Default value if none of the radio buttons are checked
        if buttonswidget.findChild(QRadioButton, "onemonth").isChecked():
            daysrange = 30
        elif buttonswidget.findChild(QRadioButton, "threemonths").isChecked():
            daysrange = 90
        elif buttonswidget.findChild(QRadioButton, "oneyear").isChecked():
            daysrange = 365

        answerbar = self.createanswerbuttonsbar(daysrange)

        if answerwidget.frame.layout().count() > 3:
            answerwidget.frame.layout().itemAt(3).widget().deleteLater()

        answerwidget.frame.layout().addWidget(answerbar)

    def allcardstoggled(self):
        if not self.allcardsbutton.isChecked():
            return
        self.decksbox.setEnabled(False)
        self.deck = None
        self.refreshgraphs()
        # call a refresh graphs

    def deckbuttontoggled(self):
        if not self.deckbutton.isChecked():
            return
        self.decksbox.setEnabled(True)
        self.deck = self.decksbox.currentData()
        self.refreshgraphs()
        # call a refresh graphs

    def filldecksbox(self):
        prevdeck = self.decksbox.currentData()

        self.decksbox.blockSignals(True)
        self.decksbox.clear()
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT ud.id FROM user_decks ud WHERE ud.uid = ?""", (self.user.id,))
        try:
            udids = cur.fetchall()
        except:
            udids = []
            print("no decks exist")

        for udid in udids:
            deck = Deck(udid[0], self.user)
            self.decksbox.addItem(deck.name, deck)
            try:
                if deck.udid == prevdeck.udid:
                    self.decksbox.setCurrentIndex(self.decksbox.count() - 1)
            except AttributeError:
                pass
        self.decksbox.blockSignals(False)

    def changedeck(self):
        if not self.deckbutton.isChecked():
            return
        self.deck = self.decksbox.currentData()

    def updatetodaywidget(self, widget):
        todaywidget = widget
        con = sqlite3.connect(database)
        cur = con.cursor()
        # self.deck = self.decksbox.currentData()
        # print(self.deck.name)
        if self.deck:
            cur.execute(f"""SELECT COUNT (r.id) FROM revlog r
            INNER JOIN user_cards uc ON r.ucid = uc.id
            INNER JOIN cards c on uc.cid = c.id
            WHERE uc.uid = ? 
            AND c.deck_id = ? 
            AND (r.time >= {math.floor(time() / 86400) * 86400}
            AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id, self.deck.did))
            totalcount = cur.fetchone()[0]

            cur.execute(f"""SELECT SUM (r.start), SUM (r.end) FROM revlog r
            INNER JOIN user_cards uc ON r.ucid = uc.id
            INNER JOIN cards c on uc.cid = c.id
            WHERE uc.uid = ? 
            AND c.deck_id = ? 
            AND (r.time >= {math.floor(time() / 86400) * 86400}
            AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id, self.deck.did))
            times = cur.fetchone()

            try:
                totaltime = times[1] - times[0]
            except:
                totaltime = 0

            cur.execute(f"""SELECT COUNT (r.id) FROM revlog r
                        INNER JOIN user_cards uc ON r.ucid = uc.id
                        INNER JOIN cards c on uc.cid = c.id
                        WHERE uc.uid = ? 
                        AND c.deck_id = ?
                        AND r.ease = 0
                        AND (r.time >= {math.floor(time() / 86400) * 86400}
                        AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id, self.deck.did))

            againcount = cur.fetchone()[0]

            newcount = self.statuscount(0, cur)
            learncount = self.statuscount(1, cur)
            reviewcount = self.statuscount(2, cur)
            relearncount = self.statuscount(3, cur)

            cur.execute(f"""SELECT COUNT (r.id) FROM revlog r
                            INNER JOIN user_cards uc ON r.ucid = uc.id
                            INNER JOIN cards c on uc.cid = c.id
                            WHERE uc.uid = ? 
                            AND c.deck_id = ?
                            AND r.status = 2
                            AND r.lastivl >= {86400 * 30}
                            AND (r.time >= {math.floor(time() / 86400) * 86400}
                            AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id, self.deck.did))

            totalmaturecount = cur.fetchone()[0]

            cur.execute(f"""SELECT COUNT (r.id) FROM revlog r
                            INNER JOIN user_cards uc ON r.ucid = uc.id
                            INNER JOIN cards c on uc.cid = c.id
                            WHERE uc.uid = ? 
                            AND c.deck_id = ?
                            AND r.lastivl >= {86400 * 30}
                            AND r.status = 2
                            AND (r.ease = 1 OR r.ease = 2 OR r.ease = 3)
                            AND (r.time >= {math.floor(time() / 86400) * 86400}
                            AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id, self.deck.did))

            correctmaturecount = cur.fetchone()[0]

        else:
            cur.execute(f"""SELECT COUNT (r.id) FROM revlog r
            INNER JOIN user_cards uc ON r.ucid = uc.id
            WHERE uc.uid = ? 
            AND (r.time >= {math.floor(time() / 86400) * 86400}
            AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id,))
            totalcount = cur.fetchone()[0]

            cur.execute(f"""SELECT SUM (r.start), SUM (r.end) FROM revlog r
            INNER JOIN user_cards uc ON r.ucid = uc.id
            WHERE uc.uid = ? 
            AND (r.time >= {math.floor(time() / 86400) * 86400}
            AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id,))
            times = cur.fetchone()
            try:
                totaltime = times[1] - times[0]
            except:
                totaltime = 0

            cur.execute(f"""SELECT COUNT (r.id) FROM revlog r
                        INNER JOIN user_cards uc ON r.ucid = uc.id
                        WHERE uc.uid = ? 
                        AND r.ease = 0
                        AND (r.time >= {math.floor(time() / 86400) * 86400}
                        AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id,))

            againcount = cur.fetchone()[0]

            newcount = self.statuscount(0, cur)
            learncount = self.statuscount(1, cur)
            reviewcount = self.statuscount(2, cur)
            relearncount = self.statuscount(3, cur)

            cur.execute(f"""SELECT COUNT (r.id) FROM revlog r
                            INNER JOIN user_cards uc ON r.ucid = uc.id
                            WHERE uc.uid = ? 
                            AND r.lastivl >= {86400 * 30}
                            AND r.status = 2
                            AND (r.time >= {math.floor(time() / 86400) * 86400}
                            AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id,))

            totalmaturecount = cur.fetchone()[0]

            cur.execute(f"""SELECT COUNT (r.id) FROM revlog r
                            INNER JOIN user_cards uc ON r.ucid = uc.id
                            WHERE uc.uid = ? 
                            AND r.lastivl >= {86400 * 30}
                            AND r.status = 2
                            AND (r.ease = 1 OR r.ease = 2 OR r.ease = 3)
                            AND (r.time >= {math.floor(time() / 86400) * 86400}
                            AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id,))

            correctmaturecount = cur.fetchone()[0]

        if totalcount == 0:
            todaywidget.overallcardsstudied.setText("No cards have been studied today")
            todaywidget.againcountlabel.setText("")
            todaywidget.breakdownlabel.setText("")
            todaywidget.maturecardslabel.setText("")

        else:
            # todo, format times here better, i.e. minutes for total time if > 60 etc.
            todaywidget.overallcardsstudied.setText(
                f"""Studied {totalcount} cards in {round(totaltime, 1)} seconds ({round(totaltime / totalcount, 1)}s/card)""")
            todaywidget.againcountlabel.setText(
                f"""Again count: {againcount} ({'{:,.1%}'.format((totalcount - againcount) / totalcount)} correct)""")
            todaywidget.breakdownlabel.setText(
                f"""Learn: {learncount}, Review {reviewcount}, Relearn: {relearncount}, New: {newcount}""")
            if totalmaturecount:
                todaywidget.maturecardslabel.setText(
                    f"""Correct answers on mature cards: {correctmaturecount}/{totalmaturecount} ({'{:,.1%}'.format(correctmaturecount / totalmaturecount)})""")
            else:
                todaywidget.maturecardslabel.setText(f"""No mature cards have been studied today""")

        return todaywidget

    def createfuturereviewsbar(self, daysrange):
        # todo configuration of this - perhaps allow for showing overdue if they exist.
        today = datetime.date.today()
        todayend = int(mktime(today.timetuple())) + 86400

        con = sqlite3.connect(database)
        cur = con.cursor()

        if self.deck:
            if daysrange:
                cur.execute(f"""SELECT uc.id, uc.due FROM user_cards uc
                INNER JOIN cards c ON uc.cid = c.id
                INNER JOIN decks d on c.deck_id = d.id
                WHERE uc.uid = ?
                AND d.id = ?
                AND uc.due <= ?""",
                            (self.user.id, self.deck.did, todayend + daysrange * 86400))
            else:
                cur.execute(f"""SELECT uc.id, uc.due FROM user_cards uc
                                INNER JOIN cards c ON uc.cid = c.id
                                INNER JOIN decks d on c.deck_id = d.id
                                WHERE uc.uid = ?
                                AND d.id = ?""",
                            (self.user.id, self.deck.did))

        else:
            if daysrange:
                cur.execute(f"""SELECT uc.id, uc.due FROM user_cards uc
                                INNER JOIN cards c ON uc.cid = c.id
                                INNER JOIN decks d on c.deck_id = d.id
                                WHERE uc.uid = ?
                                AND uc.due <= ?""",
                            (self.user.id, todayend + daysrange * 86400))
            else:
                cur.execute(f"""SELECT uc.id, uc.due FROM user_cards uc
                                            INNER JOIN cards c ON uc.cid = c.id
                                            INNER JOIN decks d on c.deck_id = d.id
                                            WHERE uc.uid = ?""",
                            (self.user.id,))

        duesdf = pd.DataFrame(cur.fetchall(), columns=['id', 'due'])

        if duesdf['due'].empty:
            nodata = QLabel("No Data")
            font = QFont()
            font.setPointSize(24)
            nodata.setFont(font)
            nodata.setStyleSheet("color:#8c8c8c;")
            nodata.setAlignment(Qt.AlignCenter)
            nodata.setMinimumSize(0, 300)
            return nodata


        cur.close()
        con.close()

        today = datetime.date.today()
        today_datetime = datetime.datetime.combine(today, datetime.datetime.min.time())

        duesdf['due'] = pd.to_datetime(duesdf['due'], unit='s', origin='unix')
        duesdf['due'] = duesdf['due'].dt.date
        duesdf['due'] = pd.to_datetime(duesdf['due'])
        duesdf['due'] = (duesdf['due'] - today_datetime).dt.days

        canvas = MplCanvas(self, width=5, height=4, dpi=100)
        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        due_counts = duesdf.groupby(['due']).size().reset_index(name='count')
        due_counts['due'] = due_counts['due'].astype(int)

        if daysrange:
            for i in range(daysrange + 1):
                count = due_counts.loc[due_counts['due'] == i]
                if count.empty:
                    due_counts.loc[len(due_counts)] = [i, 0]
        else:
            for i in range(max(due_counts['due']) + 1):
                count = due_counts.loc[due_counts['due'] == i]
                if count.empty:
                    due_counts.loc[len(due_counts)] = [i, 0]

        due_counts = due_counts[due_counts['due'] >= 0]
        due_counts = due_counts.sort_values(by=['due']).reset_index(drop=True)

        canvas.axes.bar(due_counts['due'], due_counts['count'], color=self.statuscolours[3], alpha=1)
        canvas.axes.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        # canvas.axes.set_xlabel('Due')
        ax2 = canvas.axes.twinx()

        ax2.plot(due_counts['due'], due_counts['count'].cumsum(), c='#a6a6a6', lw=0.2)
        ax2.fill_between(due_counts['due'], due_counts['count'].cumsum(), 0, alpha=0.1, color='#8C8C8C')
        ax2.set_ylim(0, max(due_counts['count'].cumsum()))
        ax2.set_ylim(bottom=0)
        ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        if daysrange:
            canvas.axes.set_xlim(right=daysrange + 0.5, left=-0.5)
        else:
            canvas.axes.set_xlim(right=max(due_counts['due'] + 0.5), left=-0.5)

        ax3 = canvas.axes.twinx()

        ax3.bar(range(max(due_counts['due']) + 1), max(due_counts['count']), color='white', alpha=0)
        ax3.get_yaxis().set_ticks([])

        canvas.axes.spines[['top']].set_visible(False)
        ax2.spines[['top', 'bottom', 'left', 'right']].set_visible(False)
        ax3.spines[['top', 'left', 'bottom', 'right']].set_visible(False)

        canvas.axes.spines[['left', 'bottom', 'right']].set_color('#8C8C8C')

        canvas.axes.tick_params(colors='#8C8C8C')
        ax2.tick_params(colors='#8C8C8C')
        ax3.tick_params(colors='#8C8C8C')

        canvas.axes.set_facecolor('#363636')
        canvas.fig.set_facecolor('#363636')

        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        cursor = mplcursors.cursor(ax3, hover=mplcursors.HoverMode.Transient)

        @cursor.connect("add")
        def on_add(sel):
            sel.annotation.get_bbox_patch().set(fc="white")
            sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=0)
            sel.annotation.set_fontsize(9)
            index = sel.index
            days = due_counts.iloc[index]["due"]
            if days == 0:
                daystext = "Today"
            elif days == 1:
                daystext = "Tomorrow"
            else:
                daystext = f"In {days} days:"
            count = due_counts.iloc[index]["count"]
            if count == 1:
                cardsdue = f"{count} card due"
            else:
                cardsdue = f"{count} cards due"
            cumulative = due_counts['count'].cumsum()[index]

            sel.annotation.set_text(f"{daystext}\n{cardsdue}\nRunning Total: {cumulative}")
            x, y, width, height = sel.artist[sel.index].get_bbox().bounds
            sel.annotation.xy = (x + width / 2, y + height)
            sel.artist[sel.index].set_alpha(0.1)

        @cursor.connect("remove")
        def on_remove(sel):
            sel.artist[sel.index].set_alpha(0)
            for sel in cursor.selections:
                sel.artist[sel.index].set_alpha(0.1)

        font = QFont()
        font.setPointSize(15)

        # total, avg, due tmrw
        textwidget = QWidget()
        textlayout = QGridLayout()
        textwidget.setLayout(textlayout)

        totalreviewslabel = QLabel("Total:")
        totalreviewslabel.setAlignment(Qt.AlignRight)
        totalreviewslabel.setFont(font)

        totalreviewsstat = QLabel(f"{sum(due_counts['count'])} reviews")
        totalreviewsstat.setAlignment(Qt.AlignLeft)
        totalreviewsstat.setFont(font)

        avglabel = QLabel("Average:")
        avglabel.setAlignment(Qt.AlignRight)
        avglabel.setFont(font)

        avgstat = QLabel(f"{int(round(sum(due_counts['count']) / (max(due_counts['due']) + 1), 0))} reviews/day")
        avgstat.setAlignment(Qt.AlignLeft)
        avgstat.setFont(font)

        tmrwlabel = QLabel("Due Tomorrow:")
        tmrwlabel.setAlignment(Qt.AlignRight)
        tmrwlabel.setFont(font)

        tmrwstat = QLabel(f"{due_counts.iloc[1]['count']} reviews")
        tmrwstat.setAlignment(Qt.AlignLeft)
        tmrwstat.setFont(font)

        textlayout.addWidget(totalreviewslabel, 0, 0)
        textlayout.addWidget(totalreviewsstat, 0, 1)
        textlayout.addWidget(avglabel, 1, 0)
        textlayout.addWidget(avgstat, 1, 1)
        textlayout.addWidget(tmrwlabel, 2, 0)
        textlayout.addWidget(tmrwstat, 2, 1)

        subwidget = QWidget()
        sublayout = QVBoxLayout()
        subwidget.setLayout(sublayout)
        sublayout.addWidget(canvas)
        sublayout.addWidget(textwidget)

        return subwidget

    def createpastreviewsbar(self, daysrange):
        group_size = math.ceil(daysrange / 90)
        num_groups = math.ceil(daysrange / group_size)

        today = datetime.date.today()
        todaytimestamp = int(mktime(today.timetuple()))
        daystarts = [todaytimestamp]
        days_x = [0]
        for i in range(daysrange):
            daystart = todaytimestamp - (i + 1) * 86400
            daystarts.append(daystart)
            days_x.append(-(i + 1))

        # results in a whole number of groups
        while len(daystarts) % group_size != 0:
            daystarts.append(min(daystarts) - 86400)
            days_x.append(min(days_x) - 1)
            pass

        daystarts.reverse()
        days_x.reverse()

        con = sqlite3.connect(database)
        cur = con.cursor()

        mature = []
        young = []
        learning = []
        relearning = []
        new = []

        for daystart in daystarts:
            if self.deck:
                cur.execute("""SELECT r.status, r.lastivl FROM revlog r 
                            INNER JOIN user_cards uc ON r.ucid = uc.id
                            INNER JOIN cards c ON uc.cid = c.id
                            INNER JOIN decks d ON c.deck_id = d.id
                            WHERE r.time >= ? 
                            AND r.time < ? 
                            AND uc.uid = ?
                            AND d.id = ?""", (daystart, daystart + 86400, self.user.id, self.deck.did))
            else:
                cur.execute("""SELECT r.status, r.lastivl FROM revlog r 
                            INNER JOIN user_cards uc ON r.ucid = uc.id
                            WHERE r.time >= ? 
                            AND r.time < ? 
                            AND uc.uid = ?""", (daystart, daystart + 86400, self.user.id))

            reviews = cur.fetchall()
            maturecount = youngcount = learningcount = relearningcount = newcount = 0
            try:
                statuses, lastivls = zip(*reviews)
                for i in range(len(statuses)):
                    if statuses[i] == 0:
                        newcount += 1
                    elif statuses[i] == 1:
                        learningcount += 1
                    elif statuses[i] == 2:
                        if lastivls[i] >= 30 * 86400:
                            maturecount += 1
                        else:
                            youngcount += 1
                    elif statuses[i] == 3:
                        relearningcount += 1
                    else:
                        assert 0
            except ValueError:
                # no reviews for this day
                pass

            mature.append(maturecount)
            young.append(youngcount)
            learning.append(learningcount)
            relearning.append(relearningcount)
            new.append(newcount)

        if all(x == 0 for x in mature + young + learning + relearning + new):
            nodata = QLabel("No Data")
            font = QFont()
            font.setPointSize(24)
            nodata.setFont(font)
            nodata.setStyleSheet("color:#8c8c8c;")
            nodata.setAlignment(Qt.AlignCenter)
            nodata.setMinimumSize(0, 300)
            return nodata

        cur.close()
        con.close()

        days_x.reverse()
        mature.reverse()
        young.reverse()
        learning.reverse()
        relearning.reverse()
        new.reverse()

        groups = [days_x[i] - group_size for i in range(0, daysrange + 1, group_size)]
        mature = [sum(mature[i:i+group_size]) for i in range(0, daysrange + 1, group_size)]
        young = [sum(young[i:i+group_size]) for i in range(0, daysrange + 1, group_size)]
        learning = [sum(learning[i:i+group_size]) for i in range(0, daysrange + 1, group_size)]
        relearning = [sum(relearning[i:i+group_size]) for i in range(0, daysrange + 1, group_size)]
        new = [sum(new[i:i+group_size]) for i in range(0, daysrange + 1, group_size)]

        canvas = MplCanvas(self, width=5, height=4, dpi=100)

        canvas.axes.bar(groups, mature, color=self.statuscolours[4], label='Mature', width=group_size * 0.9,
                        align='edge')
        canvas.axes.bar(groups, young, color=self.statuscolours[3], bottom=mature, label='Young',
                        width=group_size * 0.9, align='edge')
        canvas.axes.bar(groups, relearning, color=self.statuscolours[2], align='edge',
                        bottom=[i + j for i, j in zip(young, mature)], label='relearning', width=group_size * 0.9)
        canvas.axes.bar(groups, learning, color=self.statuscolours[1], align='edge',
                        bottom=[i + j + k for i, j, k in zip(young, mature, relearning)],
                        label='learning', width=group_size * 0.9)
        canvas.axes.bar(groups, new, color=self.statuscolours[0], align='edge',
                        bottom=[i + j + k + l for i, j, k, l in zip(young, mature, relearning, learning)],
                        label='new', width=group_size * 0.9)

        canvas.axes.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        revsum = np.array([sum(i) for i in zip(mature, young, relearning, learning, new)])
        revsum = np.flip(revsum)
        cumulative = np.cumsum(revsum)

        reversed_groups = [groups[i] for i in reversed(range(len(groups)))]
        ax2 = canvas.axes.twinx()
        ax2.plot([x + group_size/2 for x in reversed_groups], cumulative, c='#a6a6a6', lw=0.2)
        ax2.fill_between([x + group_size/2 for x in reversed_groups], cumulative, 0, alpha=0.1, color='#8C8C8C')
        ax2.set_ylim(bottom=0)
        ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        canvas.axes.set_xlim(right=0, left=min(groups))

        ax3 = canvas.axes.twinx()

        ax3.bar(groups, max(revsum), color='white', alpha=0, width=group_size * 0.9, align='edge')
        ax3.get_yaxis().set_ticks([])

        canvas.axes.spines[['top']].set_visible(False)
        ax2.spines[['top', 'bottom', 'left', 'right']].set_visible(False)
        ax3.spines[['top', 'left', 'bottom', 'right']].set_visible(False)

        canvas.axes.spines[['left', 'bottom', 'right']].set_color('#8C8C8C')

        canvas.axes.tick_params(colors='#8C8C8C')
        ax2.tick_params(colors='#8C8C8C')
        ax3.tick_params(colors='#8C8C8C')

        cursor = mplcursors.cursor(ax3, hover=mplcursors.HoverMode.Transient)

        @cursor.connect("add")
        def on_add(sel):
            sel.annotation.get_bbox_patch().set(fc="white")
            sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=0)
            sel.annotation.set_fontsize(9)
            index = sel.index
            mature_val = mature[index]
            young_val = young[index]
            relearning_val = relearning[index]
            learning_val = learning[index]
            new_val = new[index]
            running_val = cumulative[len(cumulative) - 1 - index]

            if group_size == 1:
                days_ago = -groups[index] - group_size
                if days_ago == 0:
                    daystext = f"Today"
                elif days_ago == 1:
                    daystext = f"Yesterday"
                else:
                    daystext = f"{days_ago} days ago"
            else:
                earliest = -groups[index] - group_size
                latest = -groups[index] - 1
                daystext = f"{earliest}-{latest} days ago"

            sel.annotation.set_text(
                f"{daystext}\nMature: {mature_val}\nYoung: {young_val}\nRelearning: {relearning_val}\nLearning: {learning_val}\nNew: {new_val}\nRunning Total: {running_val}")
            x, y, width, height = sel.artist[sel.index].get_bbox().bounds
            sel.annotation.xy = (x + width / 2, y + height)
            sel.artist[sel.index].set_alpha(0.1)

        @cursor.connect("remove")
        def on_remove(sel):
            sel.artist[sel.index].set_alpha(0)
            for sel in cursor.selections:
                sel.artist[sel.index].set_alpha(0.1)

        # Add a legend
        # canvas.axes.legend()

        canvas.axes.set_facecolor('#363636')
        canvas.fig.set_facecolor('#363636')

        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        font = QFont()
        font.setPointSize(15)
        # adding stats for days studied, total reviews, avg for days studied, avg over period.
        textwidget = QWidget()
        textlayout = QGridLayout()
        textwidget.setLayout(textlayout)

        daysstudied = np.count_nonzero(revsum)
        daysstudiedlabel = QLabel("Days Studied:")
        daysstudiedlabel.setAlignment(Qt.AlignRight)
        daysstudiedlabel.setFont(font)

        daysstudiedstat = QLabel(
            f"{daysstudied} of {daysrange + 1} ({'{:,.0%}'.format(daysstudied / (daysrange + 1))})")
        daysstudiedstat.setAlignment(Qt.AlignLeft)
        daysstudiedstat.setFont(font)

        totalreviewslabel = QLabel("Total:")
        totalreviewslabel.setAlignment(Qt.AlignRight)
        totalreviewslabel.setFont(font)

        totalreviewsstat = QLabel(f"{sum(revsum)} reviews")
        totalreviewsstat.setAlignment(Qt.AlignLeft)
        totalreviewsstat.setFont(font)

        avgdaysstudiedlabel = QLabel("Average for days studied:")
        avgdaysstudiedlabel.setAlignment(Qt.AlignRight)
        avgdaysstudiedlabel.setFont(font)

        avgdaysstudiedstat = QLabel(f"{int(round(sum(revsum) / daysstudied, 0))} reviews/day")
        avgdaysstudiedstat.setAlignment(Qt.AlignLeft)
        avgdaysstudiedstat.setFont(font)

        avgperiodlabel = QLabel("Average over period:")
        avgperiodlabel.setAlignment(Qt.AlignRight)
        avgperiodlabel.setFont(font)

        avgperiodstat = QLabel(f"{int(round(sum(revsum) / (daysrange + 1), 0))} reviews/day")
        avgperiodstat.setAlignment(Qt.AlignLeft)
        avgperiodstat.setFont(font)

        textlayout.addWidget(daysstudiedlabel, 0, 0)
        textlayout.addWidget(daysstudiedstat, 0, 1)
        textlayout.addWidget(totalreviewslabel, 1, 0)
        textlayout.addWidget(totalreviewsstat, 1, 1)
        textlayout.addWidget(avgdaysstudiedlabel, 2, 0)
        textlayout.addWidget(avgdaysstudiedstat, 2, 1)
        textlayout.addWidget(avgperiodlabel, 3, 0)
        textlayout.addWidget(avgperiodstat, 3, 1)

        # todo - will need to create widget outside of the scope of this function in order to use time frame buttons,
        #  and just regenerate graph/text

        subwidget = QWidget()
        sublayout = QVBoxLayout()
        subwidget.setLayout(sublayout)
        sublayout.addWidget(canvas)
        sublayout.addWidget(textwidget)

        return subwidget

    def createstatuspie(self):
        # ideally want to add this into a seperate widget then -> statspage
        """counts: [new, learning, relearning, young, mature]"""
        statuses = ['New', 'Learning', 'Relearning', 'Young', 'Mature']
        con = sqlite3.connect(database)
        cur = con.cursor()
        counts = [0] * 5
        if self.deck:
            params = [(0, self.user.id, self.deck.did), (1, self.user.id, self.deck.did), (3, self.user.id, self.deck.did)]
            for i in range(3):
                cur.execute("""SELECT COUNT(DISTINCT uc.id) FROM user_cards uc
                INNER JOIN cards c ON uc.cid = c.id
                WHERE uc.status = ? 
                AND uc.uid = ? 
                AND c.deck_id = ?""",
                            (params[i]))
                counts[i] = cur.fetchone()[0]

            cur.execute(
                """SELECT COUNT(DISTINCT uc.id) FROM user_cards uc
                 INNER JOIN cards c ON uc.cid = c.id
                 WHERE uc.status = ?
                  AND uc.uid = ? 
                  AND c.deck_id = ? 
                  AND uc.ivl < ?""",
                (2, self.user.id, self.deck.did, 30 * 86400))
            counts[3] = cur.fetchone()[0]
            cur.execute(
                """SELECT COUNT(DISTINCT uc.id) FROM user_cards uc
                 INNER JOIN cards c ON uc.cid = c.id
                 WHERE uc.status = ?
                 AND uc.uid = ? 
                 AND c.deck_id = ? 
                 AND uc.ivl >= ?""",
                (2, self.user.id, self.deck.did, 30 * 86400))
            counts[4] = cur.fetchone()[0]
        else:
            params = [(0, self.user.id), (1, self.user.id), (3, self.user.id)]
            for i in range(3):
                cur.execute("""SELECT COUNT(DISTINCT id) FROM user_cards WHERE status = ? AND uid = ?""",
                            (params[i]))
                counts[i] = cur.fetchone()[0]

            cur.execute(
                """SELECT COUNT(DISTINCT id) FROM user_cards WHERE status = ? AND uid = ? AND ivl < ?""",
                (2, self.user.id, 30 * 86400))
            counts[3] = cur.fetchone()[0]
            cur.execute(
                """SELECT COUNT(DISTINCT id) FROM user_cards WHERE status = ? AND uid = ? AND ivl >= ?""",
                (2, self.user.id, 30 * 86400))
            counts[4] = cur.fetchone()[0]

        cleaned_counts = []
        cleaned_colours = []
        cleaned_statuses = []
        explode = []
        explodefloat = 0
        for i in range(5):
            if counts[i] != 0:
                cleaned_counts.append(counts[i])
                cleaned_colours.append(self.statuscolours[i])
                cleaned_statuses.append(statuses[i])
                explode.append(explodefloat)

        canvas = MplCanvas(self, width=4, height=4, dpi=100)
        # labels=cleaned_statuses, autopct=lambda p: '{:.0f}'.format(p * sum(counts) / 100), pctdistance=0.85,
        canvas.axes.pie(cleaned_counts, colors=cleaned_colours, explode=explode, startangle=90)
        canvas.axes.set_facecolor('#363636')
        canvas.fig.set_facecolor('#363636')

        canvas.fig.subplots_adjust(left=-0.05, right=1.05, bottom=-0.05, top=1.05)

        # center_circle = mpatches.Circle((0, 0), 0.7, color='#363636')
        # canvas.axes.add_artist(center_circle)
        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        subwidget = QWidget()
        layout = QHBoxLayout()
        subwidget.setLayout(layout)
        layout.addWidget(canvas)

        textwidget = QWidget()
        textlayout = QGridLayout()
        textwidget.setLayout(textlayout)

        font = QFont()
        font.setPointSize(15)

        # statuses = ['New', 'Learning', 'Relearning', 'Young', 'Mature']

        newlabel = QLabel("New")
        newlabel.setStyleSheet(f"color:{self.statuscolours[0]}")
        newlabel.setAlignment(Qt.AlignLeft)
        newlabel.setFont(font)

        newcount = QLabel(f"{counts[0]}")
        newcount.setAlignment(Qt.AlignRight)
        newcount.setFont(font)

        learninglabel = QLabel("Learning")
        learninglabel.setStyleSheet(f"color:{self.statuscolours[1]}")
        learninglabel.setAlignment(Qt.AlignLeft)
        learninglabel.setFont(font)

        learningcount = QLabel(f"{counts[1]}")
        learningcount.setAlignment(Qt.AlignRight)
        learningcount.setFont(font)

        relearninglabel = QLabel("Relearning")
        relearninglabel.setStyleSheet(f"color:{self.statuscolours[2]}")
        relearninglabel.setMinimumSize(140, 0)
        relearninglabel.setAlignment(Qt.AlignLeft)
        relearninglabel.setFont(font)

        relearningcount = QLabel(f"{counts[2]}")
        relearningcount.setAlignment(Qt.AlignRight)
        relearningcount.setFont(font)

        younglabel = QLabel("Young")
        younglabel.setStyleSheet(f"color:{self.statuscolours[3]}")
        younglabel.setAlignment(Qt.AlignLeft)
        younglabel.setFont(font)

        youngcount = QLabel(f"{counts[3]}")
        youngcount.setAlignment(Qt.AlignRight)
        youngcount.setFont(font)

        maturelabel = QLabel("Mature")
        maturelabel.setStyleSheet(f"color:{self.statuscolours[4]}")
        maturelabel.setAlignment(Qt.AlignLeft)
        maturelabel.setFont(font)

        maturecount = QLabel(f"{counts[4]}")
        maturecount.setAlignment(Qt.AlignRight)
        maturecount.setFont(font)

        totallabel = QLabel("Total")
        totallabel.setAlignment(Qt.AlignLeft)
        totallabel.setFont(font)

        totalcount = QLabel(f"{sum(counts)}")
        totalcount.setAlignment(Qt.AlignRight)
        totalcount.setFont(font)

        # calculate percentage of cards for each status
        if sum(counts) != 0:
            new_percentage = round(counts[0] / sum(counts) * 100, 1)
            learning_percentage = round(counts[1] / sum(counts) * 100, 1)
            relearning_percentage = round(counts[2] / sum(counts) * 100, 1)
            young_percentage = round(counts[3] / sum(counts) * 100, 1)
            mature_percentage = round(counts[4] / sum(counts) * 100, 1)
        else:
            new_percentage = learning_percentage = relearning_percentage = young_percentage = mature_percentage = 0

        # create labels for each status with percentage counts
        newpct = QLabel(f"({new_percentage}%)")
        newpct.setAlignment(Qt.AlignRight)
        newpct.setFont(font)

        learningpct = QLabel(f"({learning_percentage}%)")
        learningpct.setAlignment(Qt.AlignRight)
        learningpct.setFont(font)

        relearningpct = QLabel(f"({relearning_percentage}%)")
        relearningpct.setAlignment(Qt.AlignRight)
        relearningpct.setFont(font)

        youngpct = QLabel(f"({young_percentage}%)")
        youngpct.setAlignment(Qt.AlignRight)
        youngpct.setFont(font)

        maturepct = QLabel(f"({mature_percentage}%)")
        maturepct.setAlignment(Qt.AlignRight)
        maturepct.setFont(font)
        maturepct.setMinimumSize(80, 0)

        # textlayout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding), 0, 0)
        textlayout.addWidget(newlabel, 1, 0)
        textlayout.addWidget(newcount, 1, 1)
        textlayout.addWidget(newpct, 1, 2)
        textlayout.addWidget(learninglabel, 2, 0)
        textlayout.addWidget(learningcount, 2, 1)
        textlayout.addWidget(learningpct, 2, 2)
        textlayout.addWidget(relearninglabel, 3, 0)
        textlayout.addWidget(relearningcount, 3, 1)
        textlayout.addWidget(relearningpct, 3, 2)
        textlayout.addWidget(younglabel, 4, 0)
        textlayout.addWidget(youngcount, 4, 1)
        textlayout.addWidget(youngpct, 4, 2)
        textlayout.addWidget(maturelabel, 5, 0)
        textlayout.addWidget(maturecount, 5, 1)
        textlayout.addWidget(maturepct, 5, 2)
        textlayout.addWidget(totallabel, 6, 0)
        textlayout.addWidget(totalcount, 6, 1)

        # textlayout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding), 6, 0)

        textlayout.setRowStretch(0, 1)
        textlayout.setRowStretch(6, 1)
        textlayout.setColumnStretch(3, 1)

        layout.addWidget(textwidget)
        # come back to here to add text stuff

        return subwidget

    def statuscount(self, status, cur):
        if self.deck:
            cur.execute(f"""SELECT COUNT (r.id) FROM revlog r
                        INNER JOIN user_cards uc ON r.ucid = uc.id
                        INNER JOIN cards c on uc.cid = c.id
                        WHERE uc.uid = ? 
                        AND c.deck_id = ?
                        AND r.status = ?
                        AND (r.time >= {math.floor(time() / 86400) * 86400}
                        AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id, self.deck.did, status))
        else:
            cur.execute(f"""SELECT COUNT (r.id) FROM revlog r
                            INNER JOIN user_cards uc ON r.ucid = uc.id
                            WHERE uc.uid = ? 
                            AND r.status = ?
                            AND (r.time >= {math.floor(time() / 86400) * 86400}
                            AND r.time <= {math.ceil(time() / 86400) * 86400})""",
                        (self.user.id, status))

        return cur.fetchone()[0]

    def createintervalsbar(self, maxivl, percentage):
        # handle ranges so if range falls into a given bracket, ivls are grouped into divisions.
        # when plotting over ranges, keep the sql fetch the same, just filter the dataframe to cut out values before plotting
        con = sqlite3.connect(database)
        cur = con.cursor()
        if maxivl:
            if self.deck:
                cur.execute("""SELECT uc.ivl FROM user_cards uc
                INNER JOIN cards c ON uc.cid = c.id
                INNER JOIN decks d ON c.deck_id = d.id
                WHERE uc.uid = ?
                AND d.id = ?
                AND uc.ivl >= 86400
                AND uc.ivl <= ?""", (self.user.id, self.deck.did, maxivl * 86400))
            else:
                cur.execute("""SELECT uc.ivl FROM user_cards uc
                WHERE uc.uid = ?
                AND uc.ivl >= 86400
                AND uc.ivl <= ?""", (self.user.id, maxivl * 86400))
        elif percentage:
            if self.deck:
                cur.execute("""SELECT COUNT(uc.id) FROM user_cards uc
                INNER JOIN cards c ON uc.cid = c.id
                INNER JOIN decks d ON c.deck_id = d.id
                WHERE uc.uid = ?
                AND d.id = ?
                AND uc.ivl >= 86400""", (self.user.id, self.deck.did))
                count = cur.fetchone()[0]
                tofetch = math.ceil(count * percentage)

                cur.execute("""SELECT uc.ivl FROM user_cards uc
                INNER JOIN cards c ON uc.cid = c.id
                INNER JOIN decks d ON c.deck_id = d.id
                WHERE uc.uid = ?
                AND d.id = ?
                AND uc.ivl >= 86400
                ORDER BY uc.ivl ASC
                LIMIT ?""", (self.user.id, self.deck.did, tofetch))
            else:
                cur.execute("""SELECT COUNT(uc.id) FROM user_cards uc
                                WHERE uc.uid = ?
                                AND uc.ivl >= 86400""", (self.user.id,))

                count = cur.fetchone()[0]
                tofetch = math.ceil(count * percentage)

                cur.execute("""SELECT uc.ivl FROM user_cards uc
                WHERE uc.uid = ?
                AND uc.ivl >= 86400
                AND uc.ivl >= 86400
                ORDER BY uc.ivl ASC
                LIMIT ?""", (self.user.id, tofetch))
        else:
            if self.deck:
                cur.execute("""SELECT uc.ivl FROM user_cards uc
                INNER JOIN cards c ON uc.cid = c.id
                INNER JOIN decks d ON c.deck_id = d.id
                WHERE uc.uid = ?
                AND d.id = ?
                AND uc.ivl >= 86400""", (self.user.id, self.deck.did))
            else:
                cur.execute("""SELECT uc.ivl FROM user_cards uc
                WHERE uc.uid = ?
                AND uc.ivl >= 86400""", (self.user.id,))

        # min ivl = 1 day to avoid having to deal with sub 1-day cards

        ivlsdf = pd.DataFrame(cur.fetchall(), columns=['ivl'])

        if ivlsdf['ivl'].empty:
            nodata = QLabel("No Data")
            font = QFont()
            font.setPointSize(24)
            nodata.setFont(font)
            nodata.setStyleSheet("color:#8c8c8c;")
            nodata.setAlignment(Qt.AlignCenter)
            nodata.setMinimumSize(0, 300)
            return nodata

        ivlsdf = (ivlsdf / 86400).astype(int)

        canvas = MplCanvas(self, width=5, height=4, dpi=100)
        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        ivlcounts = ivlsdf.groupby(['ivl']).size().reset_index(name='count')

        if maxivl:
            for i in range(1, maxivl + 1):
                count = ivlcounts.loc[ivlcounts['ivl'] == i]
                if count.empty:
                    ivlcounts.loc[len(ivlcounts)] = [i, 0]
        else:
            for i in range(1, max(ivlcounts['ivl']) + 1):
                count = ivlcounts.loc[ivlcounts['ivl'] == i]
                if count.empty:
                    ivlcounts.loc[len(ivlcounts)] = [i, 0]
            ivlcounts = ivlcounts.sort_values(by=['ivl']).reset_index(drop=True)

        ivlcounts = ivlcounts.sort_values(by=['ivl']).reset_index(drop=True)

        group_size = math.ceil(max(ivlcounts['ivl']) / 80)
        num_groups = math.ceil(len(ivlcounts['ivl']) / group_size)
        groups = [(i * group_size + 1) for i in range(num_groups)]
        group_ranges = [x - 1 for x in groups]
        ivlcounts['group'] = pd.cut(ivlcounts['ivl'], bins=group_ranges + [max(group_ranges) + group_size],
                                    labels=groups)
        grouped_counts = ivlcounts.groupby('group')['count'].sum().reset_index()
        grouped_counts['group'] = grouped_counts['group'].astype(int)

        canvas.axes.bar(grouped_counts['group'], grouped_counts['count'], color=self.statuscolours[0], alpha=1,
                        width=group_size*0.9, align='edge')
        canvas.axes.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        canvas.axes.set_xlim(right=max(grouped_counts['group'] + group_size), left=1)

        ax2 = canvas.axes.twinx()

        ax2.plot(grouped_counts['group'] + group_size/2, grouped_counts['count'].cumsum(), c='#a6a6a6', lw=0.2)
        ax2.fill_between(grouped_counts['group'] + group_size/2, grouped_counts['count'].cumsum(), 0, alpha=0.1, color='#8C8C8C')
        ax2.set_ylim(0, max(grouped_counts['count'].cumsum()))
        ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax2.set_ylim(bottom=0)

        ax3 = canvas.axes.twinx()
        ax3.bar(grouped_counts['group'], max(grouped_counts['count']), color='white', alpha=0, width=group_size*0.9,
                align='edge')
        ax3.get_yaxis().set_ticks([])

        canvas.axes.spines[['top']].set_visible(False)
        ax2.spines[['top', 'bottom', 'left', 'right']].set_visible(False)
        ax3.spines[['top', 'left', 'bottom', 'right']].set_visible(False)

        canvas.axes.spines[['left', 'bottom', 'right']].set_color('#8C8C8C')

        canvas.axes.tick_params(colors='#8C8C8C')
        ax2.tick_params(colors='#8C8C8C')
        ax3.tick_params(colors='#8C8C8C')

        canvas.axes.set_facecolor('#363636')
        canvas.fig.set_facecolor('#363636')

        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        cursor = mplcursors.cursor(ax3, hover=mplcursors.HoverMode.Transient)

        @cursor.connect("add")
        def on_add(sel):
            sel.annotation.get_bbox_patch().set(fc="white")
            sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=0)
            sel.annotation.set_fontsize(9)
            index = sel.index
            # range checking here later on
            if group_size == 1:
                ivl = grouped_counts.iloc[index]["group"]
                ivltext = f"with a {ivl} day inteval"
            else:
                ivlstart = grouped_counts.iloc[index]['group']
                ivlend = ivlstart + group_size - 1
                ivltext = f"with a {ivlstart}-{ivlend} day inteval"
            count = grouped_counts.iloc[index]["count"]
            if count == 1:
                cardsno = f"{count} card with a "
            else:
                cardsno = f"{count} cards with a "
            cumulative = grouped_counts['count'].cumsum()[index]
            x = decimal.Decimal(cumulative / sum(grouped_counts['count']))
            cumpct = x * 100

            rounded_percentage = cumpct.quantize(decimal.Decimal('0.1'), rounding=decimal.ROUND_HALF_UP)

            sel.annotation.set_text(f"{cardsno}{ivltext}\nRunning Total: {rounded_percentage}%")
            x, y, width, height = sel.artist[sel.index].get_bbox().bounds
            sel.annotation.xy = (x + width / 2, y + height)
            sel.artist[sel.index].set_alpha(0.1)

        @cursor.connect("remove")
        def on_remove(sel):
            sel.artist[sel.index].set_alpha(0)
            for sel in cursor.selections:
                sel.artist[sel.index].set_alpha(0.1)

        textwidget = QWidget()
        textlayout = QVBoxLayout()
        textwidget.setLayout(textlayout)

        font = QFont()
        font.setPointSize(15)

        con = sqlite3.connect(database)
        cur = con.cursor()
        if self.deck:
            cur.execute("""SELECT AVG(uc.ivl) FROM user_cards uc
                        INNER JOIN cards c ON uc.cid = c.id
                        INNER JOIN decks d ON c.deck_id = d.id
                        WHERE uc.uid = ?
                        AND d.id = ?""", (self.user.id, self.deck.did))
        else:
            cur.execute("""SELECT AVG(ivl) FROM user_cards
                        WHERE uid = ?""", (self.user.id,))

        avgivl = cur.fetchone()[0]

        avgivllabel = QLabel(f"Average Interval: {converttime(avgivl, full=True)}")
        avgivllabel.setAlignment(Qt.AlignHCenter)
        avgivllabel.setFont(font)

        textlayout.addWidget(avgivllabel)

        subwidget = QWidget()
        sublayout = QVBoxLayout()
        subwidget.setLayout(sublayout)
        sublayout.addWidget(canvas)
        sublayout.addWidget(textwidget)

        return subwidget

    def createeasefactorbar(self):
        con = sqlite3.connect(database)
        cur = con.cursor()

        if self.deck:
            cur.execute("""SELECT uc.ef FROM user_cards uc
            INNER JOIN cards c on uc.cid = c.id
            WHERE c.deck_id = ?
            AND uc.uid = ?""", (self.deck.did, self.user.id))
        else:
            cur.execute("""SELECT uc.ef FROM user_cards uc
                        WHERE uc.uid = ?""", (self.user.id,))

        efdf = pd.DataFrame(cur.fetchall(), columns=['ef'])

        if efdf['ef'].empty:
            nodata = QLabel("No Data")
            font = QFont()
            font.setPointSize(24)
            nodata.setFont(font)
            nodata.setStyleSheet("color:#8c8c8c;")
            nodata.setAlignment(Qt.AlignCenter)
            nodata.setMinimumSize(0, 300)
            return nodata

        canvas = MplCanvas(self, width=5, height=4, dpi=100)
        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        efcounts = efdf.groupby(['ef']).size().reset_index(name='count')

        # need to do some kind of range handling, so if max card ease - 130 is greater than a certain value,

        for i in range(130, int(max(efcounts['ef'])) + 1):
            count = efcounts.loc[efcounts['ef'] == i]
            if count.empty:
                efcounts.loc[len(efcounts)] = [i, 0]
        efcounts = efcounts.sort_values(by=['ef']).reset_index(drop=True)

        ef_max = efcounts['ef'].max()
        if ef_max >= 200:
            group_size = 5
        else:  # could add a group size 2
            group_size = 1
        num_groups = math.ceil((ef_max - 130) / group_size) + 1
        groups = [(130 + i * group_size) for i in range(num_groups)]
        group_ranges = [x - 1 for x in groups]
        efcounts['group'] = pd.cut(efcounts['ef'], bins=group_ranges + [max(group_ranges) + group_size], labels=groups)
        grouped_counts = efcounts.groupby('group')['count'].sum().reset_index()
        grouped_counts['group'] = grouped_counts['group'].astype(int)

        color_map = ['#F52A2A', '#F43326', '#F43C22', '#F3451E', '#F34F1A', '#F25A16', '#F16412', '#F0700E',
                     '#EB7B0F', '#E6860F', '#E1910F', '#DD9B0F', '#D8A40F', '#D3AC0F', '#CEB40F', '#CABC0F',
                     '#C5C30F', '#B8C00F', '#A9BC0F', '#9AB70F', '#8CB20F', '#7FAE0F', '#72A90F', '#66A50F',
                     '#5AA00F', '#4F9B0F', '#44970F', '#3A920E', '#318E0E', '#28890E', '#20850E', '#18800E',
                     '#107C0D', '#0D7711', '#0D7317']

        if len(grouped_counts['group']) <= len(color_map):
            colors = color_map[:len(grouped_counts['group'])]
        else:
            colors = color_map + (['#001AFF'] * (len(grouped_counts['group']) - len(color_map)))

        # try to get a gradient from red @ 130 to green/dark green past 250
        canvas.axes.bar(grouped_counts['group'], grouped_counts['count'], color=colors, alpha=1, width=group_size - 0.5,
                        align='edge')
        canvas.axes.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        # canvas.axes.set_xlabel('Due')

        canvas.axes.set_xlim(right=max(grouped_counts['group'] + 1.5 * group_size), left=130 - 0.5 * group_size)

        ax3 = canvas.axes.twinx()
        ax3.bar(grouped_counts['group'], max(grouped_counts['count']), color='white', alpha=0, width=group_size - 0.5,
                align='edge')
        ax3.get_yaxis().set_ticks([])

        canvas.axes.spines[['top']].set_visible(False)
        ax3.spines[['top', 'left', 'bottom', 'right']].set_visible(False)

        canvas.axes.spines[['left', 'bottom', 'right']].set_color('#8C8C8C')

        canvas.axes.tick_params(colors='#8C8C8C')
        ax3.tick_params(colors='#8C8C8C')

        canvas.axes.set_facecolor('#363636')
        canvas.fig.set_facecolor('#363636')

        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        cursor = mplcursors.cursor(ax3, hover=mplcursors.HoverMode.Transient)

        @cursor.connect("add")
        def on_add(sel):
            sel.annotation.get_bbox_patch().set(fc="white")
            sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=0)
            sel.annotation.set_fontsize(9)
            index = sel.index
            ease = grouped_counts.iloc[index]['group']
            count = grouped_counts.iloc[index]['count']
            if count == 1:
                counttext = f"{count} card with "
            else:
                counttext = f"{count} cards with "
            sel.annotation.set_text(f"{counttext}{ease}% ease")
            x, y, width, height = sel.artist[sel.index].get_bbox().bounds
            sel.annotation.xy = (x + width / 2, y + height)
            sel.artist[sel.index].set_alpha(0.1)

        @cursor.connect("remove")
        def on_remove(sel):
            sel.artist[sel.index].set_alpha(0)
            for sel in cursor.selections:
                sel.artist[sel.index].set_alpha(0.1)

        font = QFont()
        font.setPointSize(15)

        avgeaselabel = QLabel()
        avgeaselabel.setAlignment(Qt.AlignHCenter)
        avgeaselabel.setFont(font)

        con = sqlite3.connect(database)
        cur = con.cursor()

        if self.deck:
            cur.execute("""SELECT AVG(uc.ef) FROM user_cards uc
                        INNER JOIN cards c ON uc.cid = c.id
                        INNER JOIN decks d ON c.deck_id = d.id
                        WHERE uc.uid = ?
                        AND d.id = ?""", (self.user.id, self.deck.did))
        else:
            cur.execute("""SELECT AVG(ef) FROM user_cards
                        WHERE uid = ?""", (self.user.id,))

        avgease = cur.fetchone()[0]
        cur.close()
        con.close()

        avgeaselabel.setText(f"Average ease: {int(round(avgease, 0))}%")

        subwidget = QWidget()
        sublayout = QVBoxLayout()
        subwidget.setLayout(sublayout)
        sublayout.addWidget(canvas)
        sublayout.addWidget(avgeaselabel)

        return subwidget

    def createanswerbuttonsbar(self, daysrange):
        con = sqlite3.connect(database)
        cur = con.cursor()

        learningcounts = []
        youngcounts = []
        maturecounts = []
        if daysrange:
            today = datetime.date.today()
            todaytimestamp = int(mktime(today.timetuple()))
            cutoff = todaytimestamp - 86400 * daysrange
        else:
            cutoff = 0

        if self.deck:
            for i in range(4):
                cur.execute("""SELECT COUNT(r.id) FROM revlog r
                INNER JOIN user_cards uc ON r.ucid = uc.id
                INNER JOIN cards c ON uc.cid = c.id
                WHERE r.ease = ?
                AND uc.uid = ?
                AND c.deck_id = ?
                AND (r.status = 1 OR r.status = 3)
                AND r.time >= ?""", (i, self.user.id, self.deck.did, cutoff))
                count = cur.fetchone()[0]
                learningcounts.append(count)

        else:
            for i in range(4):
                cur.execute("""SELECT COUNT(r.id) FROM revlog r
                INNER JOIN user_cards uc ON r.ucid = uc.id
                WHERE r.ease = ?
                AND uc.uid = ?
                AND (r.status = 1 OR r.status = 3)
                AND r.time >= ?""", (i, self.user.id, cutoff))
                count = cur.fetchone()[0]
                learningcounts.append(count)

        if self.deck:
            for i in range(4):
                cur.execute("""SELECT COUNT(r.id) FROM revlog r
                INNER JOIN user_cards uc ON r.ucid = uc.id
                INNER JOIN cards c ON uc.cid = c.id
                WHERE r.ease = ?
                AND uc.uid = ?
                AND c.deck_id = ?
                AND r.status = 2
                AND r.lastivl < ?
                AND r.time >= ?""", (i, self.user.id, self.deck.did, 30 * 86400, cutoff))
                count = cur.fetchone()[0]
                youngcounts.append(count)

        else:
            for i in range(4):
                cur.execute("""SELECT COUNT(r.id) FROM revlog r
                INNER JOIN user_cards uc ON r.ucid = uc.id
                WHERE r.ease = ?
                AND uc.uid = ?
                AND r.status = 2
                AND r.lastivl < ?
                AND r.time >= ?""", (i, self.user.id, 30 * 86400, cutoff))
                count = cur.fetchone()[0]
                youngcounts.append(count)

        if self.deck:
            for i in range(4):
                cur.execute("""SELECT COUNT(r.id) FROM revlog r
                INNER JOIN user_cards uc ON r.ucid = uc.id
                INNER JOIN cards c ON uc.cid = c.id
                WHERE r.ease = ?
                AND uc.uid = ?
                AND c.deck_id = ?
                AND r.status = 2
                AND r.lastivl >= ?
                AND r.time >= ?""", (i, self.user.id, self.deck.did, 30 * 86400, cutoff))
                count = cur.fetchone()[0]
                maturecounts.append(count)
        else:
            for i in range(4):
                cur.execute("""SELECT COUNT(r.id) FROM revlog r
                INNER JOIN user_cards uc ON r.ucid = uc.id
                WHERE r.ease = ?
                AND uc.uid = ?
                AND r.status = 2
                AND r.lastivl >= ?
                AND r.time >= ?""", (i, self.user.id, 30 * 86400, cutoff))
                count = cur.fetchone()[0]
                maturecounts.append(count)

        cur.close()
        con.close()

        allcounts = [x for x in zip(learningcounts, youngcounts, maturecounts)]

        if all(sum(tup) == 0 for tup in allcounts):
            nodata = QLabel("No Data")
            font = QFont()
            font.setPointSize(24)
            nodata.setFont(font)
            nodata.setStyleSheet("color:#8c8c8c;")
            nodata.setAlignment(Qt.AlignCenter)
            nodata.setMinimumSize(0, 300)
            return nodata

        x = np.arange(3)

        canvas = MplCanvas(self, width=5, height=4, dpi=100)

        # Set the width of each bar
        bar_width = 0.15

        # Calculate the x-axis positions for each group of bars
        # x_pos = [i for i in range(12)]

        # Plot the bars for the first set of values
        canvas.axes.bar(x, allcounts[0], width=bar_width - 0.01, color=self.answercolours[0])
        canvas.axes.bar(x + bar_width, allcounts[1], width=bar_width - 0.01, color=self.answercolours[1])
        canvas.axes.bar(x + 2 * bar_width, allcounts[2], width=bar_width - 0.01, color=self.answercolours[2])
        canvas.axes.bar(x + 3 * bar_width, allcounts[3], width=bar_width - 0.01, color=self.answercolours[3])

        # Set the x-axis tick positions and labels
        canvas.axes.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        canvas.axes.set_xticks(x + bar_width * 1.5)
        # todo change labels

        try:
            learninglabel = f"Learning ({round((sum(learningcounts) - learningcounts[0]) / sum(learningcounts) * 100, 2)}%)"
        except:
            learninglabel = f"Learning"
        try:
            younglabel = f"Young ({round((sum(youngcounts) - youngcounts[0]) / sum(youngcounts) * 100, 2)}%)"
        except:
            younglabel = f"Young"
        try:
            maturelabel = f"Mature ({round((sum(maturecounts) - maturecounts[0]) / sum(maturecounts) * 100, 2)}%)"
        except:
            maturelabel = f"Mature"
        canvas.axes.set_xticklabels([learninglabel, younglabel, maturelabel])

        x_positions = np.concatenate([x, x + bar_width, x + 2 * bar_width, x + 3 * bar_width])
        # array of all plotted x positions which will be used for plotting the highlight bars and allow for
        # case handling of the tooltip

        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        ax3 = canvas.axes.twinx()
        ax3.bar(x_positions, np.max(allcounts, axis=None) * len(x_positions), color='white', alpha=0,
                width=bar_width - 0.01)
        ax3.get_yaxis().set_ticks([])

        canvas.axes.spines[['top']].set_visible(False)
        ax3.spines[['top', 'left', 'bottom', 'right']].set_visible(False)

        canvas.axes.spines[['left', 'bottom', 'right']].set_color('#8C8C8C')
        canvas.axes.tick_params(colors='#8C8C8C')
        ax3.tick_params(colors='#8C8C8C')

        canvas.axes.set_facecolor('#363636')
        canvas.fig.set_facecolor('#363636')

        cursor = mplcursors.cursor(ax3, hover=mplcursors.HoverMode.Transient)

        @cursor.connect("add")
        def on_add(sel):
            sel.annotation.get_bbox_patch().set(fc="white")
            sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=0)
            sel.annotation.set_fontsize(9)
            index = sel.index
            countvalues = np.array(allcounts).flatten()
            if index % 3 == 0:
                offset = 0
            elif index % 3 == 1:
                offset = 1
            else:
                offset = 2

            if index // 3 == 0:
                ease = 0
            elif index // 3 == 1:
                ease = 1
            elif index // 3 == 2:
                ease = 2
            else:
                ease = 3

            total = 0
            for i in range(0, len(countvalues), 3):
                total += countvalues[i + offset]

            pressedcount = countvalues[index]
            button = f"Button: {ease}"  # could change this to easy, hard, etc. using a dict
            timespressed = f"Times pressed: {pressedcount} ({round((pressedcount / total) * 100, 2)}%)"
            correct = f"{total - countvalues[index % 3]}/{total} correct ({round(((total - countvalues[index % 3]) / total) * 100, 2)}%)"

            sel.annotation.set_text(f"{button}\n{timespressed}\n{correct}")
            x, y, width, height = sel.artist[sel.index].get_bbox().bounds
            sel.annotation.xy = (x + width / 2, y + height)
            sel.artist[sel.index].set_alpha(0.1)

        @cursor.connect("remove")
        def on_remove(sel):
            sel.artist[sel.index].set_alpha(0)
            for sel in cursor.selections:
                sel.artist[sel.index].set_alpha(0.1)

        return canvas



class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)


class TodayStatsWidget(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("todaywidget.ui", self)
        self.setStyleSheet('background-color:#363636')


class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("graphwidget.ui", self)
        self.setStyleSheet('background-color:#363636')


class Browse(QWidget):
    # todo card data will automatically update with changes made by the creator, could add an option that allow
    #  creator to allow/disallow copies being made
    # also maybe open another window if the creator is accessing a deck, for now will just no connect the button
    # also need to refactor to avoid using 2 duplicate containers for decks
    def __init__(self, user, stack):
        self.user = user
        super().__init__()
        loadUi("browse.ui", self)
        connectmainbuttons(self, stack)

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

    def fetchpublicdecks(self, searchfilter):
        con = sqlite3.connect(database)
        cur = con.cursor()
        con.create_function("REGEXP", 2, regexp)
        if searchfilter:
            try:
                cur.execute("""SELECT ud.id, d.name, d.desc, u.username FROM decks d INNER JOIN user_decks ud ON d.id 
                = ud.deck_id INNER JOIN users u ON d.created_uid = u.id WHERE d.isPublic = 1 AND isDeleted = 0 AND 
                ud.uid = d.created_uid AND (d.name REGEXP ? OR d.desc REGEXP ? OR u.username REGEXP ?)""",
                            (searchfilter,
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
        cur.execute(
            """SELECT t.fields, c.data FROM cards c INNER JOIN templates t ON c.template_id = t.id WHERE deck_id = ? ORDER BY RANDOM () LIMIT 3""",
            (self.deck.did,))
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
            cur.execute("""INSERT INTO user_decks (deck_id, uid, config_id) VALUES (?, ?, ?)""",
                        (self.deck.did, self.user.id, cfgid))
            cur.execute("""SELECT c.id FROM cards c WHERE c.deck_id = ?""", (self.deck.did,))
            cids = cur.fetchall()
            for cid in cids:
                cid = cid[0]
                cur.execute("""SELECT id FROM user_cards WHERE cid = ? AND uid = ?""", (cid, self.user.id))
                if not cur.fetchone():
                    cur.execute("""INSERT INTO user_cards (uid, cid, ivl, type, status, reps, lapses, odue, left)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (self.user.id, cid, None, 0, 0, 0, 0, time(), 0))
            self.addbutton.setText("Remove")

        else:
            self.addbutton.setText("Add")
            cur.execute("""DELETE FROM user_decks WHERE deck_id = ? AND uid = ?""", (self.deck.did, self.user.id))

        con.commit()
        cur.close()
        con.close()

    def checkifinlibrary(self):
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT id FROM user_decks ud WHERE ud.uid = ? AND ud.deck_id = ?""",
                    (self.user.id, self.deck.did))
        exists = cur.fetchone() is not None
        return exists


#############################


def resetstack(stack):
    """
    used after navigating away from any of the main 5 pages
    """
    for i in range(stack.count() - 8):
        widget = stack.widget(8)
        stack.removeWidget(widget)
        widget.deleteLater()


def gotodecks(stack):
    stack.widget(3).refresh()
    resetstack(stack)
    stack.setCurrentIndex(3)


def gotoadd(stack):
    stack.widget(4).refresh()
    resetstack(stack)
    stack.setCurrentIndex(4)


def gotocards(stack):
    stack.widget(5).refresh()
    resetstack(stack)
    stack.setCurrentIndex(5)


def gotostats(stack):
    stack.widget(6).refresh()
    resetstack(stack)
    stack.setCurrentIndex(6)


def gotobrowse(stack):
    stack.widget(7).refresh()
    resetstack(stack)
    stack.setCurrentIndex(7)


def connectmainbuttons(window, stack):
    window.decks.clicked.connect(lambda: gotodecks(stack))
    window.add.clicked.connect(lambda: gotoadd(stack))
    window.cards.clicked.connect(lambda: gotocards(stack))
    window.stats.clicked.connect(lambda: gotostats(stack))
    window.browse.clicked.connect(lambda: gotobrowse(stack))


# def refreshmainwindows():
#     """
#     stack widgets [3,4,5,6,7] = [DecksMain, AddCard, CardsMain, StatsPage, Browse]
#     """
#     stack.widget(4).refresh()
#     stack.widget(5).refresh()
#     stack.widget(6).refresh()
#     stack.widget(7).refresh()


def converttime(seconds, full=False):
    # todo, issue in time conversion, think it is flooring
    duration = datetime.timedelta(seconds=seconds)

    years = duration.days // 365
    months = duration.days // 30.44 % 12
    days = duration.days % 30.44
    hours = duration.seconds // 3600
    minutes = (duration.seconds // 60) % 60

    if not full:
        if years > 0:
            return f"{years:.1f}y"
        elif months > 0:
            return f"{months:.1f}mo"
        elif days > 0:
            return f"{days:.0f}d"
        elif hours > 0:
            return f"{hours:.0f}h"
        else:
            return f"{minutes:.0f}m"
    else:
        if years > 0:
            return f"{years:.1f} years"
        elif months > 0:
            return f"{months:.1f} months"
        elif days > 0:
            return f"{days:.0f} days"
        elif hours > 0:
            return f"{hours:.0f} hours"
        else:
            return f"{minutes:.0f} minutes"


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


def regexp(expr, item):
    """
    A function to be used in filtering and retrieving published decks, matching the user's input to fields in the database
    :param expr: the input to be used when filtering
    :param item: the field which is being checked for a match with the expression
    :return: returns True if a match is found and re.search() returns a match item
    """
    return re.search(expr, item, re.IGNORECASE) is not None

"""
PROGRAM EXECUTION:
"""

database = 'data/newdb.db'

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.resize(1600, 900)
    main_window.show()
    sys.exit(app.exec_())
