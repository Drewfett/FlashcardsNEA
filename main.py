import datetime
import decimal
import math
import random
import re
import sqlite3
import sys
from queue import Queue
from time import time, mktime

import mplcursors
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, Qt
from PyQt5.Qt import QStandardItem, QStandardItemModel, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QDialog, QApplication, QAction, QStackedWidget, QMainWindow, QMenu, QToolButton, QLabel, \
    QSizePolicy, QVBoxLayout, QHeaderView, QLineEdit, QSpinBox, QTableView, QSpacerItem, QAbstractItemView, \
    QRadioButton, QGridLayout, QHBoxLayout, QMenuBar, QButtonGroup
from PyQt5.uic import loadUi
from matplotlib import ticker
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# todo maybe add descriptions to graphs
# MAIN THINGS TODO:

#  Review system and displaying flashcards - covered
#  todo - storing html and escaped fields, what do i need to have. how to enable a dark mode for the html page,
#   + how to go about storing sound and image files in a database or somewhere else and referencing them
#  need to write some kind of interpreter for html where fields are converted into their data.
# mainly done ^ still could try to work out how to use dark mode.


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


# TODO - whenever a card is added/deleted to a public deck, could update for all users by checking the user_cards table
#  to see if the connection exists for all users with a user_decks connection to that card's parent deck

# todo - browse window components, WHEN DECK CLICKED - NEW WINDOW: DISPLAYS deck name, description, (creator),
#  (+ratings), sample of cards, options to either add deck to library (no modification of cards
#  and updates in line with changes made by the creator) or copy the deck (allows for modification of cards) - stats
#  for each, comments/ratings section.
#  also for need a bunch of selection statement to ensure consistent logic when adding decks to your library

# todo could add optional fuzzing in review - incorporate into user settings

# todo do i need add password?

# todo, just realised comma seperated fields are a really bad idea due to the possible inclusion of commas in card data
# see if hubbard can offer a suggestion -  if coded well can replace with "|" and reset the database

# todo - would be pretty cool towards the end if I could change the decks main window to display dekcs as dynamically
#  generated widgets that can be clicked - ideas in chatgpt + with sorting on counts/name

"""
Current Progress with sections of the program - outdated

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
basictemplate_fields = 'Front' + "," + 'Back'
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


# Class for mapping user data to a user object for use in the program
class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.collapsetime = None
        self.neworder = None  # (0 = new first, 1 = new last, [2 = spread out])
        self.fetchpreferences()

    def fetchpreferences(self):
        # retrieves the user's preferences from the database
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT collapsetime, neworder FROM users WHERE id = ?""", (self.id,))
        self.collapsetime, self.neworder = cur.fetchone()
        cur.close()
        con.close()


# Class for mapping data of decks from the database to deck objects for use throughout the program
class Deck(QStandardItem):
    def __init__(self, id, user, font_size=13, set_bold=False):
        super().__init__()

        # configuring how deck items are displayed in a qtreeview
        fnt = QFont()
        fnt.setPointSize(font_size)
        fnt.setBold(set_bold)

        self.setEditable(False)
        self.setFont(fnt)

        # setup of other variables
        self.udid = id
        self.user = user

        # fetching data related to the deck (part of which is also fetching an associated config)
        self.fetchdata()

        # set text for when displayed in a PyQt5 view
        self.setText(self.name)

    def fetchdata(self):
        # retrieval of data from the database
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT d.name, d.id, d.desc, ud.config_id, d.isPublic, d.created_uid, d.isDeleted 
        FROM user_decks ud 
        INNER JOIN decks d ON ud.deck_id = d.id 
        WHERE ud.id = ?""", (self.udid,))
        fetch = cur.fetchone()
        self.name, self.did, self.desc, self.config_id, self.public, self.creator_id, self.isDeleted = fetch

        # creates a config objects for the deck (slightly inneficient but handling small data)
        self.config = Config(self.config_id)

        # fetching the total number of cards in the deck (used for public decks)
        cur.execute("""SELECT COUNT (c.id) FROM cards c INNER JOIN decks d ON c.deck_id = d.id WHERE d.id = ?""",
                    (self.did,))
        try:
            self.cardcount = cur.fetchone()[0]
        except:
            self.cardcount = 0

        cur.close()
        con.close()

    def save(self):
        # updates deck attributes in the database if the creator is accessing this function
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
            return


# Class for housing data of flashcards retrieved from the database
class Flashcard(QStandardItem):
    def __init__(self, id, font_size=13, set_bold=False):
        super().__init__()

        # configuring how flashcard items are displayed in a qtreeview
        fnt = QFont()
        fnt.setPointSize(font_size)
        fnt.setBold(set_bold)

        self.setEditable(False)
        self.setFont(fnt)

        # setup of other variables
        self.id = id
        self.cid = None
        self.fetch_attributes()

        # setting text for display in a qtreeview
        sortfielddata = self.data[self.fields.index(self.sortfield)]
        self.setText(sortfielddata)

    def fetch_attributes(self):
        # fetching of card data
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

        # fetching fields and sortfield of the associated template
        cur.execute("""SELECT fields, sortfield
                                FROM templates
                                WHERE id = ?
                                """, (self.template_id,))
        self.fields, self.sortfield = cur.fetchone()

        # splitting fields and data into an array
        self.fields = self.fields.split(",")
        self.data = self.data.split(",")

        # zipping these 2 arrays togther into a dictionary for convenience when accessing data of a given field
        self.zip = dict(zip(self.fields, self.data))

        cur.close()
        con.close()

    def update(self, uid):
        # function to update data relevant to the actual card (as opposed to user-card review/scheduling values)
        con = sqlite3.connect(database)
        cur = con.cursor()

        # fetches and checks if the creator is accessing the card
        cur.execute("""SELECT created_uid FROM CARDS WHERE id = ?""", (self.cid,))
        created_user = cur.fetchone()[0]

        # rejoins card data into a comma seperated string
        data = ",".join(self.data)

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
            return
        con.commit()
        cur.close()
        con.close()

    def review_update(self, new_ivl, new_ef, new_due):
        # function which updates user-card data that is modified by and used for reviewing/scheduling
        con = sqlite3.connect(database)
        cur = con.cursor()

        # replacing/updating of values
        self.interval = new_ivl
        self.ease_factor = new_ef
        self.due = new_due

        # change executed in the database
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


# Class for storing and updating config parameters
class Config(QStandardItem):
    def __init__(self, configid, font_size=13, set_bold=False):
        super().__init__()

        # fetching of settings values using the config id
        self.id = configid
        self.deleted = False
        self.loadvalues()

        # styling for display in any item models in the ui
        fnt = QFont()
        fnt.setPointSize(font_size)
        fnt.setBold(set_bold)

        self.setEditable(False)
        self.setFont(fnt)
        self.setText(self.name)

    def loadvalues(self):
        # fetching and assigning values form the database
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
        # updating values for the record identified by the config object's id
        con = sqlite3.connect(database)
        cur = con.cursor()

        # if the config is to be deleted, the config of all decks which it is assigned to is set to the user's default
        if self.deleted:
            cur.execute("""SELECT MIN(id) FROM configs
                        WHERE uid = ?""", (self.user.id,))
            defaultcfgid = cur.fetchone()[0]

            cur.execute(f"""UPDATE user_decks
                        SET config_id = ? WHERE config_id = ? AND uid = ?""",
                        (defaultcfgid, self.current_config.id, self.user.id))
            cur.execute(f"""DELETE FROM configs where id = {self.current_config.id}""")
            return

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
        """, (self.new_delays, self.new_grad_ivls, self.new_init_ef, self.new_per_day, self.rev_per_day,
              self.rev_easy_factor, self.rev_hard_factor, self.max_ivl, self.lapse_delays, self.lapse_percent,
              self.min_ivl, self.leech_fails, self.name, self.id))
        con.commit()
        cur.close()
        con.close()


# Class for managing/changing templates and retrieving associated data
class Template(QStandardItem):
    def __init__(self, id):
        super().__init__()
        # initialisation of variables
        self.id = id
        self.fields = None
        self.sortfield = None
        self.styling = None
        self.back = None
        self.front = None
        self.name = None
        self.fields = None

        # loading of values
        self.load()

        # setting text for display in item models
        self.setText(self.name)

    def load(self):
        # loading template data from the database
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute(
            """SELECT name, fields, sortfield, front_format, back_format, styling FROM templates WHERE id = ?""",
            (self.id,))
        self.name, self.fields, self.sortfield, self.front, self.back, self.styling = cur.fetchone()
        cur.close()
        con.close()

    def addfield(self, field_name):
        # adds a field to the template's comma seperated fields string
        # splits the string into an array, appends the new field and then rejoins
        fields = self.fields.split(",")
        fields.append(field_name)
        self.fields = ",".join(fields)

    def renamefield(self, old_name, new_name):
        # renames a field in the template's comma seperated fields string
        # splits the string into an array, finds and the index of and renames the field passed as 'old_name'
        fields = self.fields.split(",")
        fields[fields.index(old_name)] = new_name
        self.fields = ",".join(fields)

    def repositionfield(self, old_index, new_index):
        # repositions a field in the template's comma seperated fields string
        # splits the string into an array
        fields = self.fields.split(",")

        # then passes the array to a function which repositions an item in a list given an old and new index
        fields = repositionitem(fields, old_index, new_index)

        # rejoins the returned array
        self.fields = ",".join(fields)

    def removefield(self, delfield):
        # renames a field in the template's comma seperated fields string
        # splits the string into an array, finds and the index of and deletes the field passed as 'delfield'
        fields = self.fields.split(",")
        fields = [field for field in fields if field != delfield]
        self.fields = ",".join(fields)


# A function used in repositining fields within an array, initially used for templates but is also needed to
# reorder data in associated cards
def repositionitem(list, old_index, new_index):
    # checks if the indexes are the same
    if old_index == new_index:
        return list

    # gets the item to be moved
    item = list[old_index]
    if new_index < old_index:
        # shift items down which are in the range (old index, new index], starting from the old index end
        # (i.e. filling the emptied space)
        for i in range(old_index, new_index, -1):
            list[i] = list[i - 1]
        list[new_index] = item
    elif new_index > old_index:
        # shift items up which are in the range (old index, new index], starting from the old index end
        # (i.e. filling the emptied space)
        for i in range(old_index, new_index, 1):
            list[i] = list[i + 1]
        list[new_index] = item
    return list


"""WINDOW CLASSES"""


# commented
class MainWindow(QMainWindow):
    """
    Class used to manage and display all the different windows in the program, aswell as create a menu bar which is
     used to access user preferences and to sign out
    """

    def __init__(self):
        super().__init__()
        self.user = None

        self.menubar = QMenuBar(self)
        # create menu items and add them to the menu bar
        omos_menu = self.menubar.addMenu("Omos")

        # Preceding spaces used when naming actions because they are reserved keywords on macOS
        # (and for indentation purposes)
        omos_menu.addAction(" Preferences")
        omos_menu.addAction(" Sign Out")
        omos_menu.addSeparator()

        # create and connect the quit action
        quit_action = QAction(" Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        omos_menu.addAction(quit_action)

        # connect preferences action and disable initially
        preferences_action = omos_menu.actions()[0]
        preferences_action.setObjectName("Preferences")
        preferences_action.triggered.connect(self.openpreferences)
        preferences_action.setEnabled(False)

        # connect signout action and disable initially
        signout_action = omos_menu.actions()[1]
        signout_action.setObjectName("Signout")
        signout_action.triggered.connect(self.signout)
        signout_action.setEnabled(False)

        # set the QMenuBar for the main window
        self.setMenuBar(self.menubar)

        # create a QStackedWidget to manage the child views
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
        while self.stack.count() > 3:
            self.stack.removeWidget(self.stack.widget(3))

        # disable the "Preferences" and "Sign Out" actions
        preferences_action = self.menubar.findChild(QAction, "Preferences")
        signout_action = self.menubar.findChild(QAction, "Signout")
        preferences_action.setEnabled(False)
        signout_action.setEnabled(False)

        # clear text inputted on login and create account windows
        self.stack.widget(1).reset()
        self.stack.widget(2).reset()

        # show the welcome screen
        self.stack.setCurrentIndex(0)

    def openpreferences(self):
        # checks that a user is logged in
        if not self.user:
            return

        # shows the preferences window as a dialog, connects the accepted state ('OK' button) to a function which
        # saves the user's preferences
        self.preferenceswindow = PreferencesWindow(self.user)
        self.preferenceswindow.buttonBox.accepted.connect(self.savepreferences)
        self.preferenceswindow.exec()

    def savepreferences(self):
        # retrieving values from the preferences window and converting the collapse time into seconds
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

        # deletes/hides the preferences window
        self.preferenceswindow.deleteLater()  # #


# Window for user preferences
class PreferencesWindow(QDialog):
    """
    A class which loads the preferences window UI file and allows the user to change their preferences for reviewing
    """

    def __init__(self, user):
        super().__init__()
        loadUi("preferenceswindow.ui", self)
        self.user = user
        self.collapsetimebox.setValue(self.user.collapsetime / 60)
        self.neworderbox.addItem("Show new cards after reviews", 0)
        self.neworderbox.addItem("Show new cards before reviews", 1)
        # self.neworderbox.addItem(QStandardItem("Show new cards mixed in with reviews"), 2)
        self.neworderbox.setCurrentIndex(self.user.neworder)


# Welcome screen window
class WelcomeScreen(QDialog):
    def __init__(self, stack, mainwindow):
        super().__init__()
        loadUi("welcome.ui", self)

        # reference to the mainwindow and stack passed
        self.stack = stack
        self.mainwindow = mainwindow

        # connects buttons in the ui
        self.login.clicked.connect(self.gotologin)
        self.createaccount.clicked.connect(self.gotocreation)

    def gotologin(self):
        self.stack.setCurrentIndex(1)

    def gotocreation(self):
        self.stack.setCurrentIndex(2)


# Window for logging in to an account which already exists
class Login(QDialog):
    def __init__(self, stack, mainwindow):
        super().__init__()
        loadUi("login.ui", self)

        # initialising user attribute, passing references from the parent widget and connecting/configuring
        # buttons and widgets
        self.user = None
        self.stack = stack
        self.mainwindow = mainwindow
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.login.clicked.connect(self.loginfunction)
        self.createaccount.clicked.connect(lambda: self.stack.setCurrentIndex(2))

    def reset(self):
        # used for sign out
        self.user = None
        self.emailfield.setText("")
        self.passwordfield.setText("")
        self.error.setText("")

    def loginfunction(self):
        # getting inputted values from the ui
        email = self.emailfield.text()
        password = self.passwordfield.text()

        # checking for values in all inputs
        if len(email) == 0 or len(password) == 0:
            self.error.setText("Please input all fields")
        else:
            # fetching the hashed password associated with the user's email
            con = sqlite3.connect(database)
            cur = con.cursor()
            cur.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
            result = cur.fetchone()

            # if a hash is found, the inputted password is hashed and compared to the stored hash
            if result:
                pw_hash = sha_256(password)
                result_hash = result[0]

                # if not the same, the incorrect password has been entered and an error message is displayed
                if result_hash != pw_hash:
                    self.error.setText("Incorrect Password")
                    cur.close()
                    con.close()
                    return

                # if they do match, a user object is created with values fetched from the database passed as parameters
                cur.execute("SELECT username, id FROM users WHERE email = ?",
                            (email,))
                name, uid = cur.fetchone()
                self.user = User(uid, name)

                # all main windows are instantiated and added then to the stack, allowing them to be managed and
                # displayed, the user is also passed as a parameter due to the use of the uid in retrieving data
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

                # the user of the mainwindow is set in order to complete the functionality of the signout option
                self.mainwindow.user = self.user

                # menu bar options requiring a user are enabled
                preferences = self.mainwindow.menubar.findChild(QAction, "Preferences")
                preferences.setEnabled(True)
                signout = self.mainwindow.menubar.findChild(QAction, "Signout")
                signout.setEnabled(True)

                # the stack focus is switched to the decks window
                gotodecks(self.stack)

            else:
                # no value fetched means the email doesn't exist in the users table
                self.error.setText("Email is not registered")

            cur.close()
            con.close()


# Window for account creation
class CreateAccount(QDialog):
    def __init__(self, stack, mainwindow):
        super().__init__(parent=mainwindow)
        loadUi("create_account.ui", self)

        # initialising user attribute, passing references from the parent widget and connecting/configuring
        # buttons and widgets
        self.user = None
        self.stack = stack
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.register_.clicked.connect(self.registeracc)
        self.login.clicked.connect(lambda: self.stack.setCurrentIndex(1))

    def reset(self):
        # used for sign out
        self.user = None
        self.usernamefield.setText("")
        self.emailfield.setText("")
        self.passwordfield.setText("")
        self.error.setText("")

    def registeracc(self):
        # getting inputted values from line edits in the ui
        username = self.usernamefield.text()
        email = self.emailfield.text()
        password = self.passwordfield.text()

        # checking for values in all inputs
        if len(email) == 0 or len(password) == 0 or len(username) == 0:
            self.error.setText("Please input all fields")
        else:

            # checking if an account with the same email/username already exists and displaying relevant messages if so
            con = sqlite3.connect(database)
            cur = con.cursor()
            cur.execute("SELECT email, username FROM users WHERE email = ? OR username = ?", (email, username))
            fetch = cur.fetchone()
            if fetch:
                if email == fetch[0]:
                    self.error.setText("Email already in use, please login")
                elif username == fetch[1]:
                    self.error.setText("Username already in use, please login")

            # if the email and username are unique, the inputted password is hashed and stored alongside the other as a
            # record in the users table
            else:
                # hashing the password
                pw_hash = sha_256(password)

                # creating the user
                cur.execute("""INSERT INTO users (username, password_hash, email, doc, dom) 
                    VALUES (?, ?, ?, ?, ?) RETURNING id""", (username, pw_hash, email, time(), time())
                            )

                # the automatically generated uid for the record is returned
                uid = cur.fetchone()[0]

                # adding the basic config to the user's account
                cur.execute(default_config_insert, (uid,))

                # adding basic template to the user's account
                addbasictemplate(uid, cur)
                con.commit()

                # setting the user, instantiating main windows and adding them to the stacked widget
                self.user = User(uid, username)

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

                # setting the user of the main window
                self.mainwindow.user = self.user

                # menu bar options requiring a user are enabled
                preferences = self.mainwindow.menubar.findChild(QAction, "Preferences")
                preferences.setEnabled(True)
                signout = self.mainwindow.menubar.findChild(QAction, "Signout")
                signout.setEnabled(True)

                # focus of the stack is set to the main decks window
                gotodecks(self.stack)

            cur.close()
            con.close()


# Main window to display and manage all of a users decks and allow for them to be selected to review
class DecksMain(QWidget):
    def __init__(self, user, stack):
        super().__init__()
        loadUi("decksmain.ui", self)
        self.renamewindow = None
        self.adddeckwindow = None
        self.user = user
        self.stack = stack

        # connecting buttons to switch to other windows
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

        # connecting a right click menu allowing for renaming and deletion of decks
        self.decktree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.decktree.customContextMenuRequested.connect(self.deckmenu)

        # connecting other buttons
        self.adddeckbutton.clicked.connect(self.adddeck)

        # refreshing the decks in the tree view
        self.refreshtree()

    def refresh(self):
        # used when this window is navigated to from another window, updates in case changes have been made
        self.refreshtree()
        self.alertlabel.setText("")

    def adddeck(self):
        # shows a window for adding a deck, connects the create button to a function which will carry out the change
        self.adddeckwindow = AddDeckWindow(self.user)
        self.adddeckwindow.exec()
        self.adddeckwindow.createbutton.clicked.connect(self.adddeckfunc)

    def adddeckfunc(self):
        # retrieving inputs from the window
        deckname = self.adddeckwindow.namelineedit.text()
        desc = self.adddeckwindow.desclineedit.text()
        config = self.adddeckwindow.configscombobox.itemData(self.adddeckwindow.configscombobox.currentIndex())

        # checks for an input into the dekcname window
        if not deckname:
            self.adddeckwindow.emptylable.setText("You have not entered a name for the deck")
            return

        # if there is a name, the deck is created in the database
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute(f"""INSERT INTO decks (name, desc, created, modified, created_uid, isPublic, isDeleted)
                    VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                    (deckname, desc, time(), config.id, self.user.id, 0, 0))
        deckid = cur.fetchone()[0]

        # a user-deck conncetion is also created in the link table
        cur.execute(f"""INSERT INTO user_decks (uid, deck_id, config_id) VALUES (?, ?, ?)""",
                    (self.user.id, deckid, config.id))
        con.commit()
        cur.close()
        con.close()

        # deleting the window for adding the deck from memory
        self.adddeckwindow.deleteLater()
        self.adddeckwindow = None

        # refreshing the main deck window to show any changes
        self.refresh()

    def refreshtree(self):
        # clear the tree model
        self.treeModel.removeRows(0, self.treeModel.rowCount())
        rootnode = self.treeModel.invisibleRootItem()

        # iterating through and adding deck items to the tree
        for udid, desc in self.fetch_decks():
            rootnode.appendRow([Deck(udid, self.user), QStandardItem(desc)])

        # retrieving counts for each deck item
        self.fetch_counts()

    def opendeck(self, val):
        # called when a deck in the tree is clicked, retrieves the deck and then transistions to a window for the
        # selected deck
        deck = self.decktree.model().item(val.row())

        # creating and adding the window
        deckselect = DeckSelected(self.user, deck, self.stack)
        self.stack.addWidget(deckselect)

        # clears any other windows, changed this to be a dialog so that it can't be navigated away from
        self.adddeckwindow = None
        self.stack.setCurrentIndex(8)

    def fetch_decks(self):
        # fetching decks that the user has a connection in the database to
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute(
            """SELECT user_decks.id, decks.desc FROM decks 
            INNER JOIN user_decks ON user_decks.deck_id = decks.id 
            WHERE user_decks.uid = ?""",
            (self.user.id,))
        udids = []
        descriptions = []

        # creating arrays of user-deck ids, deck names and descriptions to be used in display for the tree
        for fetch in cur.fetchall():
            udids.append(fetch[0])
            descriptions.append(fetch[1])

        cur.close()
        con.close()

        return zip(udids, descriptions)

    def fetch_counts(self):
        # fetching new and due card counts for each deck to be displayed in the tree
        con = sqlite3.connect(database)
        cur = con.cursor()

        # iterating through each deck in the tree
        for i in range(self.decktree.model().rowCount()):
            deck = self.decktree.model().item(i, 0)

            # todo (condisder) might be better to split counts into 3 types then add together + pass values to selected
            #  window or use the queue formation algorithm and derive counts from there

            # fetching count of due cards
            cur.execute(f"""SELECT COUNT (uc.id) FROM user_cards uc 
                        INNER JOIN cards c ON uc.cid = c.id 
                        INNER JOIN user_decks ud ON c.deck_id = ud.deck_id
                        WHERE ud.id = {deck.udid} 
                        AND uc.uid = {self.user.id}
                        AND (uc.status = 1 OR uc.status = 2 OR uc.status = 3)
                        AND uc.due <= {math.ceil(time() / 86400) * 86400}
                        """)
            duecount = cur.fetchone()[0]

            # fetching count of the number of unqiue cards which have been reviewed today by the user
            # (in the given deck)
            cur.execute(f"""SELECT COUNT (DISTINCT revlog.ucid) FROM revlog 
            INNER JOIN user_cards uc ON revlog.ucid = uc.id 
            INNER JOIN cards c on uc.cid = c.id 
            INNER JOIN user_decks ud ON c.deck_id = ud.deck_id 
            WHERE ud.id = {deck.udid}
            AND ud.uid = {self.user.id}
            AND (revlog.time >= {math.floor(time() / 86400) * 86400} 
            AND revlog.time <= {math.ceil(time() / 86400) * 86400})""")
            reviewedtodaycount = cur.fetchone()[0]

            # fetching count of the number of cards which have been reviewed today by the user but are still due to be
            # reviewed today (in the given deck)
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

            # corrects the due count if the (actual) number of due cards exceeds the config's limit for reviews in a day
            if duecount + reviewedtodaycount - stillinqueuecount >= deck.config.rev_per_day:
                duecount = deck.config.rev_per_day - reviewedtodaycount + stillinqueuecount

            # fetching the count of new cards still in the deck
            cur.execute(f"""SELECT COUNT (DISTINCT uc.id) FROM user_cards uc 
            INNER JOIN cards c ON uc.cid = c.id 
            INNER JOIN user_decks ud ON c.deck_id = ud.deck_id
            WHERE ud.id = {deck.udid} AND uc.status = 0 AND uc.uid = {self.user.id}
            """)
            newcount = cur.fetchone()[0]

            # fetching the count of cards in the deck which were learned/first reviewed today
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

            # corrects the newcount if it (those reviewed today + new cards left in the deck) exceeds the config limit
            # of new cards to be reviewed in a day
            if newcount + newreviewedtodaycount >= deck.config.new_per_day:
                newcount = deck.config.new_per_day - newreviewedtodaycount

            # corrects the new count if the new count + due count exceeds the
            if newcount + newreviewedtodaycount + duecount + reviewedtodaycount - stillinqueuecount > \
                    deck.config.rev_per_day:
                newcount = deck.config.rev_per_day - (duecount + reviewedtodaycount - stillinqueuecount)

            # sets the new and due counts of the appropriate column for the deck's row
            index = self.decktree.model().index(i, 2)
            self.decktree.model().setData(index, newcount)
            index = self.decktree.model().index(i, 3)
            self.decktree.model().setData(index, duecount)

    def deckmenu(self, position):
        # rightclick menu for the deck tree, connects the actions to respective functions
        # instantiating the menu
        menu = QMenu()

        # creating and connecting actions
        rename = QAction(self.tr("Rename"), menu)
        rename.triggered.connect(self.rename)
        delete = QAction(self.tr("Delete"), menu)
        delete.triggered.connect(self.delete)

        # adding actions to the menu
        menu.addActions([rename, delete])

        # display the menu at the point which the tree was clicked
        menu.exec_(self.decktree.viewport().mapToGlobal(position))

    def rename(self):
        # get the deck item from the row which was right-clicked
        deck = self.decktree.model().item(self.decktree.currentIndex().row())

        # check if the user is the creator of the deck
        if deck.creator_id != self.user.id:
            self.alertlabel.setText("You are not the creator of this deck")
            return

        # if they are the creator, a window to rename the deck is displayed
        self.renamewindow = NameWindow()
        self.renamewindow.okbutton.clicked.connect(lambda: self.confirmrename(deck))

        # the window's line edit's text is set as the selected deck's name
        self.renamewindow.namelineedit.setText(deck.name)
        self.renamewindow.exec()

    def confirmrename(self, deck):
        # renames a deck when the confirm button is pressed in the rename window
        newname = self.renamewindow.namelineedit.text()

        # updates and savesthe deck's name
        deck.name = newname
        deck.save()

        # deletes the window from memory and refreshes the main deck page
        self.renamewindow.deleteLater()
        self.refresh()

    def delete(self):
        # retrieves the deck item from the selected row
        deck = self.decktree.model().item(self.decktree.currentIndex().row())

        # creating a window for deletion
        deletedialog = DeleteDeckDialog(deck, self.user)

        # checking if the deck can be deleted (this returns false if a deck is currently public), and connects the
        # ok button if it is allowed. If not, a message will be displayed in the dialog box and no change will be made
        # when ok is pressed
        if deletedialog.allowdeletion:
            deletedialog.buttonBox.accepted.connect(lambda: self.confirmdelete(deck))

        deletedialog.exec()

    def confirmdelete(self, deck):
        # difference between deleting and removing of a public deck is that deleting also deletes all cards,
        # removing keeps card progress

        con = sqlite3.connect(database)
        cur = con.cursor()

        # retrieves user-card connection ids of all of the user's card connection for cards in the deck
        cur.execute("""SELECT uc.id FROM user_cards uc 
        INNER JOIN cards c ON uc.cid = c.id
        INNER JOIN decks d on c.deck_id = d.id
        WHERE uc.uid = ?
        AND d.id = ?""", (self.user.id, deck.did))

        # deletes these connections
        for fetch in cur.fetchall():
            ucid = fetch[0]
            cur.execute("""DELETE FROM user_cards WHERE id = ?""", (ucid,))

        # deletes the user-deck connection
        cur.execute("""DELETE FROM user_decks
        WHERE deck_id = ?
        AND uid = ?""", (deck.did, self.user.id))

        # checks if other users have access to the deck
        cur.execute("""SELECT id FROM user_decks
        WHERE deck_id = ?""", (deck.did,))

        # deletes the deck and associated cards if no other users have access (to avoid storage of redundant data)
        if not cur.fetchone():
            cur.execute("""DELETE FROM cards WHERE deck_id = ?""", (deck.did,))
            cur.execute("""DELETE FROM decks WHERE id = ?""", (deck.did,))

        # todo might also need to clear user-cards stuff

        con.commit()
        cur.close()
        con.close()
        self.refresh()


# Window for adding a new deck, allows for a deck name and a config to be chosen
class AddDeckWindow(QDialog):
    def __init__(self, user):
        # initialising the window/class and loading ui
        super().__init__()
        loadUi("adddeckwindow.ui", self)
        self.user = user
        self.configs = None
        self.fetchconfigs()
        self.fillconfigsbox()

    def fetchconfigs(self):
        # create a list of the user's configs
        self.configs = []
        self.configscombobox.clear()
        con = sqlite3.connect(database)
        cur = con.cursor()

        # fetching all of a users configs
        cur.execute("SELECT id FROM configs WHERE uid = ?", [self.user.id])
        cfgids = cur.fetchall()

        # adding config items to the configs array
        for cfgid in cfgids:
            self.configs.append(Config(cfgid))

        cur.close()
        con.close()

    def fillconfigsbox(self):
        # fill the configs box to allow for them to be selected
        for config in self.configs:
            if not config.deleted:
                self.configscombobox.addItem(config.name, config)


# Dialog window for when a user wants to delete a deck
class DeleteDeckDialog(QDialog):
    def __init__(self, deck, user):
        super().__init__()
        self.allowdeletion = None
        self.deck = deck
        self.user = user
        loadUi("deletedeck.ui", self)
        self.settext()

    def settext(self):
        # sets the window's text to either prompt the user for confirmation or alert the user to the fact that their
        # deck is currently public
        con = sqlite3.connect(database)
        cur = con.cursor()

        # check if the deck is public
        cur.execute("""SELECT isPublic FROM decks WHERE id = ?""", (self.deck.did,))
        deckpublic = cur.fetchone()[0]

        # if the deck was created by the user AND it is public
        if deckpublic == 1 and (self.deck.creator_id == self.user):
            self.allowdeletion = False
            self.label.setText("""The deck is currently public, please delist it before deleting this deck""")

        else:
            # allow deletion (see the confirm deletion method of the DecksMain class for nuance on this)
            self.allowdeletion = True
            cur.execute("""SELECT COUNT (id) FROM cards WHERE deck_id = ?""", (self.deck.did,))
            cardcount = cur.fetchone()[0]
            self.label.setText(f"""Delete {self.deck.name} and {cardcount} cards associated with it?""")

        cur.close()
        con.close()


# Window class for when a deck is selected from the main decks window
class DeckSelected(QWidget):
    def __init__(self, user, deck, stack):
        # setting up of the class
        self.studyobject = None
        self.optionswindow = None
        self.user = user
        self.deck = deck
        self.stack = stack
        super().__init__()
        loadUi("deckselected.ui", self)
        connectmainbuttons(self, self.stack)

        # get and display counts for the deck and the deck's name
        self.fetchcounts()
        self.deckname.setText(deck.name)

        # connect the button to configure deck options
        self.deckoptionsbutton.clicked.connect(self.deckoptions)

    def deckoptions(self):
        # displays a window for managing the deck's review options
        self.optionswindow = DeckOptions(self.user, self.deck)
        self.optionswindow.show()

    def study(self):
        # instantiates a class to manage the study flow/process
        self.studyobject = Study(self.user, self.deck, self.stack)

    def fetchcounts(self):
        # temporarily creates an isntance of the study class, passing the true to the counts parameter which bypasses
        # any normal setup of the class
        tempstudyclass = Study(self.user, self.deck, self.stack, counts=True)

        # this is then used to fill the queues and retrieve the number of cards in each queue
        newcount, learningcount, reviewcount = tempstudyclass.fetchcounts()

        # counts are displayed if there are cards to be reviewed
        if not newcount == learningcount == reviewcount == 0:
            self.newcount.setText(f"{newcount}")
            self.learningcount.setText(f"{learningcount}")
            self.reviewcount.setText(f"{reviewcount}")
            self.studybutton.clicked.connect(self.study)

        # if there are no cards to be reviewed, all the labels for dispalying counts are cleared and a message is
        # isplayed to inform the user of this. The study button is also not connected (could be deleted)
        else:
            self.clearlayout(self.countslayout)
            label = QLabel("Congratulations! You have finished studying this deck for now.")

            # styling of the label
            label.setAlignment(Qt.AlignHCenter)
            font = QFont()
            font.setPointSize(22)
            label.setFont(font)

            # adding the label to the window
            self.countslayout.addWidget(label)

    def clearlayout(self, layout):
        # RECURSIVE function to clear all the layouts and widgets within the layout passed as a parameter
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearlayout(item.layout())


# Class that handles the displaying and review of flashcards
class Study:
    """
    todo - do something with this
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
    def __init__(self, user, deck, stack, counts=False):
        self.user = user
        self.deck = deck
        self.stack = stack

        self.queues = [Queue(), Queue(), Queue()]

        if counts:
            return

        # creating variables
        self.card = None
        self.template = None
        self.starttime = None
        self.endtime = None
        self.reps = 0  # not used right now

        # instantiaion of the window for dispalaying the front of cards, connecting flip button and adding it to the
        # stack
        self.studyfront = StudyFront(self.stack)
        self.studyfront.flipbutton.clicked.connect(self.flip)
        self.stack.addWidget(self.studyfront)

        # instantiaion of the window for dispalaying the back, connecting of buttons and adding to stack
        self.studyback = StudyBack(self.stack)
        self.studyback.againbutton.clicked.connect(lambda: self.review(0))
        self.studyback.hardbutton.clicked.connect(lambda: self.review(1))
        self.studyback.goodbutton.clicked.connect(lambda: self.review(2))
        self.studyback.easybutton.clicked.connect(lambda: self.review(3))
        self.stack.addWidget(self.studyback)

        # initiate the review process
        self.startreview()

    def fetchcounts(self):
        # used soleley for the deck selected window, fills queues and returns the number of cards in each
        self.fill_new()
        self.fill_review()

        # collapse=True is passed here to get the total number of learning cards if the user were to finish reviewing
        # everything else
        self.fill_learn(collapse=True)

        # calculating the number of items in each queue by dequeueing into a list
        newcount = len(list(self.queues[0].queue))
        learncount = len(list(self.queues[1].queue))
        reviewcount = len(list(self.queues[2].queue))

        return newcount, learncount, reviewcount

    def startreview(self):
        # attempts to load a card
        self.loadcard()

        if not self.card:
            # function call is exited, returning to the previous window is handled in the loadcard method
            return

        # creates and loads the card's template
        self.template = Template(self.card.template_id)

        # stores the start time of the review
        self.starttime = time()

        # shows the front side of the card and waits for a review input
        self.showfront()

    def showfront(self):
        # creates HTML for the front side of the card
        front = self.fillfront()

        # displays the front side of the card on the front window
        self.studyfront.htmlview.setHtml(
            f"""<head><style>{self.template.styling}</style></head> <body class='card'>{front}</body>""")

        # displays the front window
        self.stack.setCurrentIndex(9)

    def fillfront(self):
        # this function is used to replace all the fields referenced in the template's front layout

        # first any new lines are removed
        front = re.sub(r"\n", "", self.template.front)

        # iteratively checks to see if the layout contains any text of the form '{{...}}' in which case the field needs
        # to be replaced with the card's data for that field
        match = True
        while match:
            match = re.search(r"\{\{(.+?)}}", front)
            if match:
                match = match.group(0)

                # exctracts the field from the match object (removing the escape characters)
                field = match[2:-2]

                # substitues the appropriate data into the front string
                front = re.sub(match, f"{self.card.zip[field]}", front)

        # once all fields have been replaced, the string is returned
        return front

    def fillback(self):
        # a different function is necessary for replacing the fields in the template's back layout, due to the
        # inclusion of the {{FrontSide}} field, which has to be checked for
        # (actually could just create another paremater, TODO)
        back = re.sub(r"\n", "", self.template.back)

        # operates in the same way as fillfront, iteratively checking for escaped fields
        match = True
        while match:
            match = re.search(r"\{\{(.+?)}}", back)
            if match:
                match = match.group(0)
                field = match[2:-2]

                # the front side is retrieved if referenced
                if field == "FrontSide":
                    front = self.fillfront()
                    back = re.sub(match, f"{front}", back)

                else:
                    back = re.sub(match, f"{self.card.zip[field]}", back)
        return back

    def loadcard(self):
        # attempts to get a card for review
        self.card = self.get_card()

        # if there are no more cards, the user is sent back to the selected deck page
        if not self.card:
            # removes the front and back widgets and changes the stack's index to the selected deck page
            for i in range(self.stack.count() - 9):
                widget = self.stack.widget(9)
                self.stack.removeWidget(widget)
                widget.deleteLater()
                self.stack.setCurrentIndex(8)

                # the fetchcounts method of the selected deck page is called to update the text and show that all cards
                # have been reviewed
                self.stack.widget(8).fetchcounts()

            return

    def flip(self):
        # goes to the StudyBack window which allows for review of the card
        self.stack.setCurrentIndex(10)

        # displays the back of the card, and intervals for each button
        self.showback()

    def showback(self):
        # fetches and formats HTML for the backside of the card
        back = self.fillback()

        # calculates a set of intervals dependent of the status of the card
        if self.card.status == 0 or self.card.status == 1:

            # new/learning handled identically, the only difference is in updating their status and ease
            self.new_ivls, self.due_ivls = self.calculateintervals1()

        elif self.card.status == 2:
            # intervals calculated for a review card
            self.new_ivls, self.due_ivls = self.calculateintervals2()

        elif self.card.status == 3:
            # intervals calculated for a relearning card
            self.new_ivls, self.due_ivls = self.calculateintervals3()

        # new intervals and due intervals are seperated due to the fact that intervals can be updated
        # (e.g. on failing a card, however the time which it is next due for review can be independent of this)

        # setting text of the labels to display the next intervals for each button
        self.studyback.againivllabel.setText(converttime(self.due_ivls[0]))
        self.studyback.hardivllabel.setText(converttime(self.due_ivls[1]))
        self.studyback.goodivllabel.setText(converttime(self.due_ivls[2]))
        self.studyback.easyivllabel.setText(converttime(self.due_ivls[3]))

        # display the back of the card
        self.studyback.htmlview.setHtml(
            f"""<head><style>{self.template.styling}</style></head> <body class='card'>{back}</body>""")

    def review(self, ease):
        # once a button is clicked after reviewing the back side of the card, the time is logged and ease passed to a
        # function which updates the card's interval
        self.endtime = time()
        self.reviewcard(ease)

        # review of a new card is started
        self.startreview()

    def reviewcard(self, ease):
        # todo) NOTE FOR WRITEUP, CAN FIND OLD VERSION OF THIS FUNCTION ON GOOGLE DRIVE TO DEMONSTRATE HOW IT HAS
        #  BEEN REFACTORED - WILL DEFINITELY ALLOW FOR EASIER EXPLANATION - use for pseudocode showing
        #  overall function of the algorithm

        new_ef = self.card.ease_factor  # for convenience if it is not changed at any point in the function

        # only changes in left and ease factore handled here
        self.card.reps += 1

        # status before review is captured to be stored in the review log
        status_log = self.card.status

        # NEW CARDS
        if self.card.status == 0:
            # retrieve new delays and update the number of reviews the card has left
            new_delays = [int(x) for x in self.deck.config.new_delays.split(",")]
            self.card.left = len(new_delays)

            # assign a new ease factor of the config's initial ease factor for new cards
            new_ef = self.deck.config.new_init_ef

            # change the status to learning -> it will then be processed as a learning card aswell
            self.card.status = 1

        # LEARNING CARDS
        if self.card.status == 1:
            # retrieve new delays
            new_delays = [int(x) * 60 for x in self.deck.config.new_delays.split(",")]

            # set left to the number of learning steps
            if ease == 0:
                self.card.left = len(new_delays)

            # reduce left by 1
            elif ease == 2:
                self.card.left -= 1

                # graduate if the card has no more learning steps
                if self.card.left == 0:
                    # set card status to review
                    self.card.status = 2

            # instantly graduate the card
            elif ease == 3:
                self.card.status = 2
                self.card.left = 0

        # REVIEW CARDS
        # todo add in leech fails/flagging?
        elif self.card.status == 2:

            # lapse occured
            if ease == 0:
                # retrieve lapse/relearning steps
                lapse_delays = [int(x) * 60 for x in self.deck.config.lapse_delays.split(",")]
                self.card.lapses += 1

                # calculate a new ease factor
                new_ef = self.card.ease_factor - 20

                # change status to relearning
                self.card.status = 3

                # left = number of relearning steps
                self.card.left = len(lapse_delays)

            elif ease == 1:
                # new ease factor reduced
                new_ef = self.card.ease_factor - 15

            elif ease == 3:
                # new ease factore increased
                new_ef = self.card.ease_factor + 20

            # ensures ease factor is at least 130%
            if new_ef < 130:
                new_ef = 130

        elif self.card.status == 3:
            lapse_delays = [int(x) for x in self.deck.config.lapse_delays.split(",")]

            if ease == 0:
                # relearning progress reset
                self.card.left = len(lapse_delays)

            elif ease == 2:
                # card progresses 1 step
                self.card.left -= 1

                if self.card.left == 0:
                    # card is graduated to 'review' if no more relearning steps
                    self.card.status = 2

            # card instantly graduated from relearning
            elif ease == 3:
                self.card.status = 2
                self.card.left = 0

        # new due and new ivls calculated for logging the review
        new_due = time() + self.due_ivls[ease]
        new_ivl = self.new_ivls[ease]

        # review logged
        self.log_review(ease, status_log, new_ivl, new_ef)

        # card values updated after logging the review
        self.card.review_update(new_ivl, new_ef, new_due)

        return

    def calculateintervals1(self):
        # calculation of intervals for status = 0 and 1 (handled the same as mentioned before)

        new_delays = [int(x) * 60 for x in self.deck.config.new_delays.split(",")]
        new_grad_ivls = [int(x) for x in self.deck.config.new_grad_ivls.split(",")]

        due_ivls = [0] * 4
        new_ivls = [0] * 4

        # values for 'again'
        new_ivls[0] = new_delays[0]
        due_ivls[0] = new_ivls[0]

        # check if the card is new in which case left will later become the number of learning steps
        # (however this change is only actuated once a review button has been pressed_
        if self.card.status == 0:
            left = len(new_delays)

        # if the card status is learning the left value can just be taken as is
        else:
            left = self.card.left

        # if not on the last step and hard is pressed, the next interval and due time is halfway between the current
        # step and the next
        if left != 1:
            new_ivls[1] = (new_delays[-left] + new_delays[-left + 1]) / 2
            due_ivls[1] = new_ivls[1]

        # if on the final step then the interval stays the same
        elif left == 1:
            new_ivls[1] = new_delays[-left]
            due_ivls[1] = new_ivls[1]

        # if the card would graduate on pressing good
        if left - 1 == 0:
            # new interval is the 'good' graduation interval for the config
            new_ivls[2] = new_grad_ivls[0] * 86400
            due_ivls[2] = new_ivls[2]

        else:
            # new interval is that of the next step for learning cards
            new_ivls[2] = new_delays[-(left - 1)]
            due_ivls[2] = new_ivls[2]

        # for a grading of 'easy' the card is immediately graduated so the next interval is the easy graduating interval
        new_ivls[3] = new_grad_ivls[1] * 86400
        due_ivls[3] = new_ivls[3]

        return new_ivls, due_ivls

    def calculateintervals2(self):
        # for status = 2 (review)
        due_ivls = [0] * 4
        new_ivls = [0] * 4

        # retrieval of lapse delays + min/max ivls
        lapse_delays = [int(x) * 60 for x in self.deck.config.lapse_delays.split(",")]
        min_ivl = self.deck.config.min_ivl * 86400
        max_ivl = self.deck.config.max_ivl * 86400

        # interval is changed here, but because the card has been failed (again pressed), however the new interval
        # is not used in calculating next due interval since the card enters the relearning state
        new_ivls[0] = self.card.interval * self.deck.config.lapse_percent / 100
        if new_ivls[0] < min_ivl:
            new_ivls[0] = min_ivl
        due_ivls[0] = lapse_delays[0]

        # 'hard' calculations - new interval is just the old interval multiplied by the hard factor
        new_ivls[1] = self.card.interval * self.deck.config.rev_hard_factor / 100
        due_ivls[1] = new_ivls[1]

        # 'good' calculations
        # if the card is being reviewed later than it should have been a bonus of half the extra time is added to the
        # card's interval in the calculation
        if math.ceil(self.card.due / 86400) * 86400 < math.ceil(time() / 86400) * 86400:
            bonus = (math.ceil(time() / 86400) * 86400 - math.ceil(self.card.due / 86400) * 86400) / 2
        else:
            bonus = 0

        # new interval and due_ivl calculated
        new_ivls[2] = (self.card.interval + bonus) * self.card.ease_factor / 100
        due_ivls[2] = new_ivls[2]

        # 'easy' calculations - delayed reviews are applied in the same way as above, but the bonus is all of the days
        if math.ceil(self.card.due / 86400) * 86400 < math.ceil(time() / 86400) * 86400:
            bonus = (math.ceil(time() / 86400) * 86400 - math.ceil(self.card.due / 86400) * 86400)
        else:
            bonus = 0

        # calculation involves the multiplication by the easy factor for the deck
        new_ivls[3] = (self.card.interval + bonus) * (self.card.ease_factor / 100) * (
                self.deck.config.rev_easy_factor / 100)
        due_ivls[3] = new_ivls[3]

        return new_ivls, due_ivls

    def calculateintervals3(self):
        # for status 3 (relearning)

        # retrieval of relevant config settings that require operations to be performed
        lapse_delays = [int(x) * 60 for x in self.deck.config.lapse_delays.split(",")]
        min_ivl = self.deck.config.min_ivl * 86400

        due_ivls = [0] * 4
        new_ivls = [0] * 4

        # 'again' interval calculations
        new_ivls[0] = self.card.interval * self.deck.config.lapse_percent / 100
        if new_ivls[0] < min_ivl:
            new_ivls[0] = min_ivl
        due_ivls[0] = lapse_delays[0]

        # DON'T CHANGE INTERVALS HERE - as the card is in the relearning state its interval should not be affected

        # 'hard' due interval calculations
        if self.card.left != 1:
            # if more steps after the curreny, next due interval is halfway between the current step and next
            due_ivls[1] = time() + (self.deck.config.lapse_percent[-self.card.left] + self.deck.config.lapse_percent[
                -self.card.left + 1]) / 2

        if self.card.left == 1:
            # if on the final step, due interval is repeated
            due_ivls[1] = lapse_delays[-self.card.left]

        # card ivl unchanged
        new_ivls[1] = self.card.interval

        # 'good' calculations
        if self.card.left - 1 == 0:
            # if on the final step, the next due time is the card's interval prior to being lapsed
            due_ivls[2] = self.card.interval
        else:
            # otherwise it moves on to the next relearning step
            due_ivls[2] = lapse_delays[-(self.card.left - 1)]
        new_ivls[2] = self.card.interval

        # 'easy' intervals - card is instantly graduated and the review interval is the card previous interval as above
        due_ivls[3] = self.card.interval
        new_ivls[3] = self.card.interval

        return new_ivls, due_ivls

    def log_review(self, ease, status_log, new_ivl, new_ef):
        # logging the review of a card
        con = sqlite3.connect(database)
        cur = con.cursor()

        # retrieves the most recent time of review for the card which is being reviewed
        cur.execute("""SELECT time from revlog WHERE ucid = ? ORDER BY time DESC""", (self.card.id,))
        try:
            last_time = cur.fetchone()[0]
        except:
            last_time = None

        # insert a record into revlog with all the relevant data - some is not used but could be used down the line just
        # to show all of a card's past reviews and associated values such as ease factor and intervals
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
        # todo not sure what this is talking about ^

        # first checks if the queue has cards in it, if so True is returned which prompts a card to be fetched from
        # the queue
        if not self.queues[1].empty():
            return True

        # if the queue is empty, the fetching process begins
        con = sqlite3.connect(database)
        cur = con.cursor()

        # collapse is flagged as True once all other new/due cards in the queue have been reviewed
        if not collapse:
            cutoff = time()
        else:
            # the collapse time in the user's preferences it added to the cutoff in order to review cards now which are
            # due in the (typically near) future
            cutoff = time() + self.user.collapsetime

        # initially thought there might be issues with the intergration of review per day count into here however it
        # is consistent/acts as intended through fetching the count of reviewed cards due to how queue formation
        # works sequentially (i.e. one queue has to be emptied before another queue is filled)

        # fetching count of the number of unqiue cards which have been reviewed today by the user (in the given deck)
        # in order to limit the number of cards which are fetched and placed into the queue
        cur.execute(f"""SELECT COUNT (DISTINCT revlog.ucid) FROM revlog 
        INNER JOIN user_cards uc ON revlog.ucid = uc.id 
        INNER JOIN cards c on uc.cid = c.id 
        INNER JOIN user_decks ud ON c.deck_id = ud.deck_id 
        WHERE ud.id = {self.deck.udid}
        AND ud.uid = {self.user.id}
        AND (revlog.time >= {math.floor(time() / 86400) * 86400} 
        AND revlog.time <= {math.ceil(time() / 86400) * 86400})""")
        reviewedtodaycount = cur.fetchone()[0]

        cardlimit = self.deck.config.rev_per_day - reviewedtodaycount

        # fetching user-cards ids of learning/relearning cards which are to be reviewed in the deck,
        # limited by the value calculated above
        cur.execute(
            """SELECT uc.id FROM user_cards uc 
            INNER JOIN cards c ON uc.cid = c.id 
            INNER JOIN decks d ON c.deck_id = d.id 
            WHERE d.id = ? 
            AND (uc.status = 1 OR uc.status = 3) 
            AND uc.due <= ? 
            AND uc.uid = ? 
            ORDER BY uc.id ASC LIMIT ?""",
            (self.deck.did, cutoff, self.user.id, cardlimit))

        # order by id ASC here is arbitrary for deterministic ordering - would you want to  prioritise certain cards?

        # all fetched cards are added to the queue
        for ucid in cur.fetchall():
            self.queues[1].put(Flashcard(ucid[0]))

        cur.close()
        con.close()

        # if the queue now has cards in it, True is now returned again prompting a card to be taken from this queue
        if not self.queues[1].empty():
            return True

    def fill_new(self):
        # first checks if the queue has cards in it, if so True is returned which prompts a card to be fetched from
        # the queue
        if not self.queues[0].empty():
            return True

        # no cards in the queue -> trying to fetch cards
        con = sqlite3.connect(database)
        cur = con.cursor()
        # this assumes that card id is the same as order for cards to be learnt, might want to assign a deck_idx to
        # user_cards with status 0 that can be changed and allows for custom learning orders

        # retrieves the number of new cards which have been reviewed today
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

        # fetching count of the number of unqiue cards which have been reviewed today (for same application as above)
        cur.execute(f"""SELECT COUNT (DISTINCT revlog.ucid) FROM revlog 
               INNER JOIN user_cards uc ON revlog.ucid = uc.id 
               INNER JOIN cards c on uc.cid = c.id 
               INNER JOIN user_decks ud ON c.deck_id = ud.deck_id 
               WHERE ud.id = {self.deck.udid}
               AND ud.uid = {self.user.id}
               AND (revlog.time >= {math.floor(time() / 86400) * 86400} 
               AND revlog.time <= {math.ceil(time() / 86400) * 86400})""")
        reviewedtodaycount = cur.fetchone()[0]

        # determines whether the constraining factor is:
        # a) the overall reviews per day limit
        # b) the limit on new cards reviewed per day
        cardlimit = min(self.deck.config.rev_per_day - reviewedtodaycount,
                        self.deck.config.new_per_day - newreviewedcount)

        # fetch new card user-cards ids of cards to be added the to queue
        cur.execute(
            """SELECT uc.id FROM user_cards uc 
            INNER JOIN cards c ON uc.cid = c.id 
            INNER JOIN decks d ON c.deck_id = d.id 
            WHERE d.id = ? 
            AND uc.uid = ?
            AND uc.status = 0 
            ORDER BY uc.id ASC LIMIT ?""",
            (self.deck.did, self.user.id, cardlimit))

        # place each card into the queue
        for ucid in cur.fetchall():
            self.queues[0].put(Flashcard(ucid[0]))

        # need to store and track cards added to queue and last update time for resetting over new days. IMPORTANT HERE
        # so that more and more new cards don't keep getting added ?
        # again what is this? ^^^ todo
        cur.close()
        con.close()

        # another check for cards in the queue
        if not self.queues[0].empty():
            return True

    def fill_review(self):
        # checks if the queue already has cards in it, if so returns True prompting for a card to be fetched
        if not self.queues[2].empty():
            return True

        con = sqlite3.connect(database)
        cur = con.cursor()

        # fetching count of the number of unqiue cards which have been reviewed today (for same application as above)
        cur.execute(f"""SELECT COUNT (DISTINCT revlog.ucid) FROM revlog 
                       INNER JOIN user_cards uc ON revlog.ucid = uc.id 
                       INNER JOIN cards c on uc.cid = c.id 
                       INNER JOIN user_decks ud ON c.deck_id = ud.deck_id 
                       WHERE ud.id = {self.deck.udid}
                       AND ud.uid = {self.user.id}
                       AND (revlog.time >= {math.floor(time() / 86400) * 86400} 
                       AND revlog.time <= {math.ceil(time() / 86400) * 86400})""")
        reviewedtodaycount = cur.fetchone()[0]

        cardlimit = self.deck.config.rev_per_day - reviewedtodaycount

        # fetch user-cards ids for review cards in the deck that are due
        cur.execute(
            """SELECT uc.id FROM user_cards uc
             INNER JOIN cards c ON uc.cid = c.id 
             INNER JOIN decks d ON c.deck_id = d.id
             INNER JOIN user_decks ud ON ud.deck_id = d.id 
             WHERE ud.id = ? 
             AND uc.status = 2 
             AND uc.due <= ? 
             AND uc.uid = ? ORDER BY uc.due ASC LIMIT ?""",
            (self.deck.udid, math.ceil(time() / 86400) * 86400, self.user.id, cardlimit))

        # put cards onto the review queue
        for ucid in cur.fetchall():
            self.queues[2].put(Flashcard(ucid[0]))

        cur.close()
        con.close()

        # check if cards have been added to the queue as before
        if not self.queues[2].empty():
            return True

    def get_card(self):
        # public method used here to seperate the logic of determining which card should be studied next from the
        # process of actually retrieving and incrementing the card counter
        card = self._get_card()
        if card:
            self.reps += 1  # currently not used
        return card

    def _get_card(self):
        """Return the next due card or None"""

        # checks for learning cards that are due now
        c = self.get_learn_card()
        if c:
            return c

        # new cards first, or time for one?
        # [either new first or last currently implemented - have not allowed for mixed]
        if self.time_for_new_card():
            c = self.get_new_card()
            if c:
                return c

        # checks for review cards (status 2) which are due
        c = self.get_review_card()
        if c:
            return c

        # checks if there are any new cards left which are due
        c = self.get_new_card()
        if c:
            return c

        # collapse or finish reviewing if there are no more learning cards to be reviewed within the collapse limit
        return self.get_learn_card(collapse=True)

    def get_learn_card(self, collapse=False):
        # attempts to get a learning/relearning card and fill the learning queue (passing the collapse parameter)
        if self.fill_learn(collapse):
            # if there are cards in the learning queue the card at the front of the queue is taken
            return self.queues[1].get()
        else:
            return None

    def get_new_card(self):
        # attempts to get a fill the new queue
        if self.fill_new():
            # if there are cards in the new queue the card at the front of the queue is taken
            return self.queues[0].get()

    def get_review_card(self):
        # attempts to get a fill the review queue
        if self.fill_review():
            return self.queues[2].get()

    def time_for_new_card(self):
        # determines if a new card should be shown (in relation to the review cards)
        if self.user.neworder == 0:
            # if new cards last
            return False
        elif self.user.neworder == 1:
            # if new cards first
            return True
        elif self.user.neworder == 2:
            # this will never be called as right now
            # need some other function to manage spread of new cards within other reviews
            pass


# Window for displaying the front of flashcards and flip button
class StudyFront(QWidget):
    def __init__(self, stack):
        super().__init__()
        loadUi("studyfront.ui", self)
        connectmainbuttons(self, stack)

        # create and add a widget to display HTML
        self.htmlview = QWebEngineView()
        self.mainvlayout.insertWidget(2, self.htmlview, 1)


# Window for displaying the back of flashcards, and review buttons
class StudyBack(QWidget):
    def __init__(self, stack):
        super().__init__()
        loadUi("studyback.ui", self)
        connectmainbuttons(self, stack)

        # create and display a widget to display HTML
        self.htmlview = QWebEngineView()
        self.mainvlayout.insertWidget(2, self.htmlview, 0)

        # configure the layout stretching
        self.mainvlayout.setStretch(0, 0)
        self.mainvlayout.setStretch(1, 0)
        self.mainvlayout.setStretch(2, 1)
        self.mainvlayout.setStretch(3, 0)


# Class for dipslaying and managing deck options
class DeckOptions(QWidget):
    def __init__(self, user, deck=None):
        super().__init__()
        loadUi("deckoptions.ui", self)

        # initial set up of variables
        self.cfgnamewindow = None
        self.user = user
        self.deck = deck
        self.configs = []

        # filling a combo box with the user's configs and connecting index changed signals to display the configs values
        self.configscombobox.activated.connect(self.configchange)
        self.fetchconfigs()
        if deck:
            for config in self.configs:
                if config.id == self.deck.config_id:
                    idx = self.configs.index(config)
                    self.configscombobox.setCurrentIndex(idx)

        # fetch values for and display the first config
        self.configchange(self.configscombobox.currentIndex())

        # constructing the menu for the manage button
        self.constructmanagetoolmenu()

        # makes it so that whenever a value is changed the config object's data is updated
        self.connectvaluecontainers()

        # connect the save button so that changes to configs are saved when pressed, allows for the discarding of
        # changes if the window is closed
        self.savebutton.clicked.connect(self.save)

    def configchange(self, index):
        # function to update values displayed for when a new config is selected
        self.current_config = self.configscombobox.itemData(index)
        self.__fillnewcardstab()
        self.__fillreviewstab()
        self.__filllapsestab()

    def save(self):
        # update the config attributes of the selected deck
        self.deck.config_id = self.current_config.id
        self.deck.config = self.current_config

        # sets the deck's config to the one currently selected in the database
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute(f"""UPDATE user_decks
                    SET config_id = ?
                    where id = ?
                    """, (self.deck.config_id, self.deck.udid))

        con.commit()
        cur.close()
        con.close()

        # saves changes made to all configs
        for config in self.configs:
            config.save()

        # close the window
        self.hide()
        self.deleteLater()

    def __fillnewcardstab(self):
        # retrieve and fill containers with the config's values for settings related to new cards
        new_delays = re.sub(",", " ", self.current_config.new_delays)
        grad_ivls = self.current_config.new_grad_ivls.split(",")
        grad_ivls = [int(x) for x in grad_ivls]
        self.newdelaysedit.setText(str(new_delays))
        self.newperdaybox.setValue(self.current_config.new_per_day)
        self.gradivlbox.setValue(grad_ivls[0])
        self.easyivlbox.setValue(grad_ivls[1])
        self.startingeasebox.setValue(self.current_config.new_init_ef)

    def __fillreviewstab(self):
        # retrieve and fill containers with the config's values for settings related to review cards
        self.maxdailyrevbox.setValue(self.current_config.rev_per_day)
        self.easybonusbox.setValue(self.current_config.rev_easy_factor)
        self.hardivlbox.setValue(self.current_config.rev_hard_factor)
        self.maxivlbox.setValue(self.current_config.max_ivl)

    def __filllapsestab(self):
        # retrieve and fill containers with the config's values for settings related to lapses of cards
        lapse_delays = re.sub(",", " ", self.current_config.lapse_delays)
        self.lapsedelaysedit.setText(lapse_delays)
        self.lapsepenaltybox.setValue(self.current_config.lapse_percent)
        self.minivlbox.setValue(self.current_config.min_ivl)
        self.leechthresholdbox.setValue(self.current_config.leech_fails)

    def fetchconfigs(self):
        # retrieve the users configs' ids from the database and creates condif objects from them storing them in an
        # array
        self.configs = []
        self.configscombobox.clear()
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("SELECT id FROM configs WHERE uid = ?", [self.user.id])
        cfgids = cur.fetchall()
        for cfgid in cfgids:
            self.configs.append(Config(cfgid[0]))
        self.fillconfigsbox()
        cur.close()
        con.close()

    def fillconfigsbox(self):
        # add configs to the combo box
        for config in self.configs:
            try:
                self.configscombobox.addItem(config.name, config)
            except Exception as e:
                print(e)

    def constructmanagetoolmenu(self):
        # creating actions for the manage button menu
        self.manageMenu = QMenu()
        self.addconfig = QAction("Add", self.managetool)
        self.cloneconfig = QAction("Clone", self.managetool)
        self.renameconfig = QAction("Rename", self.managetool)
        self.deleteconfig = QAction("Delete", self.managetool)

        # adding actions to the menu, and assigning the menu to the manage button
        self.manageMenu.addActions([self.addconfig, self.cloneconfig, self.renameconfig, self.deleteconfig])
        self.managetool.setMenu(self.manageMenu)
        self.managetool.setPopupMode(QToolButton.InstantPopup)

        # connecting actions to their respective functions
        self.addconfig.triggered.connect(self.add)
        self.cloneconfig.triggered.connect(self.clone)
        self.renameconfig.triggered.connect(self.rename)
        self.deleteconfig.triggered.connect(self.delete)

    def connectvaluecontainers(self):
        # iterating through widgets and connecting line edit and spin box value changes to update the config's values
        for widget in self.newcards.children() + self.reviews.children() + self.lapses.children():
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.updateconfig)
            if isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self.updateconfig)

    def updateconfig(self):
        # todo remove try/except
        # retrieves and formats the values in each container and assign them to the config's attributes
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
        print("here")
        # displays a window for the user to enter a name for a new config
        self.cfgnamewindow = CFGNameWindow()
        self.cfgnamewindow.show()

        # connects the confirm button to a function which will add the config
        self.cfgnamewindow.confirmbutton.clicked.connect(self.addfunc)

    def addfunc(self):
        # retrieve the config's name from the name window
        self.cfgnamewindow.name = self.cfgnamewindow.namelineedit.text()

        # ensures the name edit is not empty
        if self.cfgnamewindow.name:
            con = sqlite3.connect(database)
            cur = con.cursor()

            # inserts the config into the database
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
                        ?) RETURNING id""", (self.cfgnamewindow.name, self.user.id,))
            cfgid = cur.fetchone()[0]
            con.commit()
            cur.close()
            con.close()
            self.cfgnamewindow.hide()
            self.cfgnamewindow.deleteLater()

            # add the config the configs array and box
            config = Config(cfgid)
            self.configs.append(config)
            self.configscombobox.addItem(config.name, config)
            self.configscombobox.setCurrentIndex(self.configscombobox.count() - 1)

        else:
            # displays an alert message if no name is entered
            self.cfgnamewindow.emptylabel.setText("You have not entered a name for the config")

    def clone(self):
        # displays a window in which a name for the cloned config can be entered
        self.cfgnamewindow = CFGNameWindow()
        self.cfgnamewindow.show()
        self.cfgnamewindow.confirmbutton.clicked.connect(self.clonefunc)

        # it is initially set as '{configname} - clone'
        self.cfgnamewindow.namelineedit.setText(f"{self.current_config.name} - clone")

    def clonefunc(self):
        # confirms the cloning of a config, inserts a new config into the database with the same values as that
        # which is being cloned, only the name is changed
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
            self.cfgnamewindow.deleteLater()

            # adds the config to the configs array and combobox, sets the current index to the newly added config
            config = Config(cfgid)
            self.configs.append(config)
            self.configscombobox.addItem(config.name, config)
            self.configscombobox.setCurrentIndex(self.configscombobox.count() - 1)
        else:
            self.cfgnamewindow.emptylabel.setText("You have not entered a name for the config")

    def rename(self):
        # displays a window allowing the user to rename the config, rename=True changes the text of the confirmation
        # button in the initialisation of the window
        self.cfgnamewindow = CFGNameWindow(rename=True)

        # set the text of the line edit to be the current name of the config
        self.cfgnamewindow.namelineedit.setText(f"{self.current_config.name}")

        self.cfgnamewindow.show()
        self.cfgnamewindow.confirmbutton.clicked.connect(self.renamefunc)

    def renamefunc(self):
        # get the new config name
        self.cfgnamewindow.name = self.cfgnamewindow.namelineedit.text()

        if self.cfgnamewindow.name:
            # update the config object's name attribute
            self.current_config.name = self.cfgnamewindow.name

            # save the index of the current selected config which is being renamed
            idx = self.configscombobox.currentIndex()

            # clear and refill the box
            self.configscombobox.clear()
            self.fillconfigsbox()

            # set the index of the box back to the renamed config
            self.configscombobox.setCurrentIndex(idx)

            # close the name window
            self.cfgnamewindow.hide()
            self.cfgnamewindow.deleteLater()

        else:
            self.cfgnamewindow.emptylabel.setText("You have not entered a name for the config")

    def delete(self):
        # reminder when testing to reference an error where if a config was deleted that a deck was using and not
        # changed to another value, the program would crash upon trying to load said deck's config

        # retrieve the id of the user's defualt config
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT MIN(id) FROM configs
                    WHERE uid = ?""", (self.user.id,))
        defaultcfgid = cur.fetchone()[0]

        # compare it to the id of the config to be deleted
        if self.current_config.id == defaultcfgid:

            # prevent the default config from being deleted and alert the user
            self.errorlabel.setText("The default config cannot be deleted")
            return

        # get an index to change to (the previous config), could also set to 0 but it doesn't really matter
        delidx = self.configscombobox.currentIndex()
        tempidx = delidx - 1
        if tempidx == -1:
            tempidx = 0

        # config not deleted from the array as it needs to be deleted when saved, instead its deleted flag is set as
        # True, and it is stored until the save button is pressed, the combo box is only filled with configs where
        # deleted = False, so this works with any subsequent calls
        self.current_config.deleted = True
        self.configscombobox.setCurrentIndex(tempidx)
        self.configscombobox.removeItem(delidx)


# Window for editing a config's name
class CFGNameWindow(QWidget):
    def __init__(self, rename=False):
        super().__init__()
        loadUi("cfgnamewindow.ui", self)
        self.create = False
        self.name = None
        if rename:
            self.confirmbutton.setText("Confirm")


# Main window for browsing and managing all of a user's cards
class CardsMain(QWidget):
    # todo - consider adding filter for the user's and other user's cards
    # status, time when last reviewed, last ease in review, reps, lapses, interval, <- not done
    def __init__(self, user, stack):
        self.user = user
        super().__init__()
        loadUi("cardsmain.ui", self)
        connectmainbuttons(self, stack)
        self.searchbutton.clicked.connect(self.search)

        # setting up the filter button menu, adding and connection actions
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

        # setting up the cards tree
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

        # fetch all cards initially with no filter (optional call)
        self.search()

    def refresh(self):
        # refresh container objects
        self.filldeckslist()
        self.search()
        self.alertlabel.setText("")

    def filterlaststudiedfunc(self, days):
        # insert text to filter on how recently cards have been studied
        self.filterinput.setText(f"studied:{days}")
        self.search()

    def filterstatusfunc(self, status):
        # insert text to filter on card status
        self.filterinput.setText(f"status:{status.lower()}")
        self.search()

    def _filterwholecollection(self):
        # search with an empty filter text to retrieve all cards
        self.filterinput.setText("")
        self.search()

    def search(self):
        # fetch cards and fill the cards tree
        fetch = self.fetch_cards()
        self.fillcards(fetch)

    def fetch_cards(self):
        # todo - change this function so it only displays cards in active decks (ie with a user_deck field),
        #  or has an option to NOTE: this might cause issues when changing windows with the clause to
        #  retain edits so might be easier just to reset the selection
        filtertext = self.filterinput.text()

        con = sqlite3.connect(database)
        cur = con.cursor()

        # create a sql cursor function to check for regex matches on card data
        con.create_function("REGEXP", 2, regexp)

        """
        checks for filters of the form
        status:{new, learning, etc}
        studied:x
        deck:abc
        """

        expression = r"^(status|deck):[a-zA-Z]+|(studied):\d+$"
        match = re.search(expression, filtertext)

        # if a valid filter is present determine what it is and handle accordingly, if a filter format is present but
        # invalid, or there is no filter present the function will pass through selection statements and do a literal
        # search in the cards' data
        if match:
            if "status:" in match.group(0):
                statusints = {"new": 0, "learning": 1, "review": 2, "relearning": 3}

                # retrieve the status in the filter text
                status = match.group(0)[7:]

                # try to match the status
                if status in statusints:

                    # if a match is found retrieve cards of that status
                    cur.execute("""SELECT uc.id, d.name FROM user_cards uc INNER JOIN cards c ON uc.cid = c.id
                             INNER JOIN decks d ON c.deck_id = d.id 
                             WHERE uc.uid = ?
                             AND uc.status = ?""", (self.user.id, statusints[status]))
                    fetch = [(row[0], row[1]) for row in cur.fetchall()]
                    return fetch

            elif "deck:" in match.group(0):
                # retrieve the deck name by slicing the filter string and search for cards in decks matching
                # the deck name
                deckname = match.group(0)[5:]
                cur.execute("""SELECT uc.id, d.name FROM user_cards uc INNER JOIN cards c ON uc.cid = c.id
                         INNER JOIN decks d ON c.deck_id = d.id 
                         WHERE uc.uid = ? AND d.name = ?""", (self.user.id, deckname))
                fetch = [(row[0], row[1]) for row in cur.fetchall()]
                return fetch

            elif "studied:" in match.group(0):
                try:
                    # try to filter on cards last reviewed in a given number of days by the user, the algorithm will
                    # pass if an integer is not passed after studied:
                    days = int(match.group(0)[8:])

                    # gets the unix timestamp for the start of today
                    today = datetime.date.today()
                    timestamp = int(mktime(today.timetuple()))

                    # subtract the range of days in seconds and retrieve cards within that cutoff
                    cutoff = timestamp - (86400 * days)
                    cur.execute("""SELECT DISTINCT uc.id, d.name FROM user_cards uc INNER JOIN cards c ON uc.cid = c.id
                             INNER JOIN decks d ON c.deck_id = d.id 
                             INNER JOIN revlog r ON r.ucid = uc.id
                             WHERE r.time >= ?
                             AND uc.uid = ? """, (cutoff, self.user.id))
                    fetch = [(row[0], row[1]) for row in cur.fetchall()]
                    return fetch
                except:
                    pass

        # if no valid filter is present, check for a regex match in card data
        cur.execute("""SELECT uc.id, d.name FROM user_cards uc INNER JOIN cards c ON uc.cid = c.id
                 INNER JOIN decks d ON c.deck_id = d.id
                 WHERE uc.uid = ? AND c.data REGEXP ?""", (self.user.id, filtertext))

        # consider whether user_cards which aren't connected to a user_deck pair shouldn't be shown, but can still be
        # stored

        # retrieve cards
        fetch = [(row[0], row[1]) for row in cur.fetchall()]
        cur.close()
        con.close()

        return fetch

    def fillcards(self, fetch):
        # need to sort out card types

        # clear the cards item model
        self.rootNode.removeRows(0, self.rootNode.rowCount())

        # create card objects and add them to item model to be displayed in the tree view
        for cid, deckname in fetch:
            card = Flashcard(cid)

            # retrieve the due date if it exists, else due is an empty string
            try:
                due = str(datetime.datetime.fromtimestamp(card.due).isoformat(' ', 'seconds'))
            except Exception as e:
                due = ''

            self.rootNode.appendRow([card, QStandardItem(), QStandardItem(due), QStandardItem(deckname)])

    def editcard(self, idx):
        # displays all of a card's data in line edits for each field, the editing finished signal of which is
        # connected to a function which updates the card

        if idx.row() == -1:  # prevents crashing if search is used whilst a card is selected
            return

        # retrieve the selected card to be displayed
        self.editingcard = self.rootNode.child(idx.row())

        # only allow editing if the creator is accessing the card, data is still displayed for cards which aren't
        # editable
        if self.editingcard.creator_id != self.user.id:
            editable = False
        else:
            editable = True

        # clear the objects in the layout for displaying fields and data
        for i in reversed(range(self.scrollWidgetContents_layout.count())):
            self.scrollWidgetContents_layout.takeAt(i).widget().deleteLater()

        # create a font
        font = QFont()
        font.setPointSize(14)
        font.setWeight(50)

        if not editable:
            # add a label alerting the user to the fact that they cannot edit the card
            label = QtWidgets.QLabel(f"You cannot edit this card as you are not the creator")
            label.setStyleSheet("color:red;")
            self.scrollWidgetContents_layout.addWidget(label)

        # iteratively add field labels and a line edit containing the card's data for that field to a layout to be
        # displayed
        for i in range(len(self.editingcard.fields)):

            # creating and stylingthe field label
            label = QtWidgets.QLabel(f"{self.editingcard.fields[i]}")
            label.setFont(font)
            line_edit = QtWidgets.QLineEdit()
            line_edit.setMinimumHeight(41)
            line_edit.setMaximumHeight(41)
            line_edit.setFont(font)

            # setting the text of the line edit
            line_edit.setPlaceholderText("")
            if self.editingcard.data[i]:
                line_edit.setText(self.editingcard.data[i])
            else:
                line_edit.setText("")

            # disable editing of the line edits if applicable
            if not editable:
                line_edit.setReadOnly(True)

            # add the label and edit to the layout
            self.scrollWidgetContents_layout.addWidget(label)
            self.scrollWidgetContents_layout.addWidget(line_edit)

            # connect the line edit editing finished signal to the saveedit function, passing the line edit as a
            # parameter in order to obtain the text
            line_edit.editingFinished.connect(lambda le=line_edit, idx=i: self.saveedit(le, idx, self.editingcard))

    def saveedit(self, le, idx, card):
        # retrieve the text in a field's line edit and update the cards data for that field
        text = le.text()
        card.data[idx] = text
        card.setText(card.data[card.fields.index(card.sortfield)])
        try:
            card.update(self.user.id)
        except Exception as e:
            print(e)

    def filldeckslist(self):
        # fetch the user's decks and fill a list opbject to allow for filtering on decks
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
        # retrieve the selected deck set the filter text to filter for cards in that deck
        deck = self.deckslistmodel.item(idx.row(), 0)
        self.filterinput.setText(f'deck:{deck.name}')
        self.search()

    def cardsmenu(self, position):
        # creation and display of the right click menu for managing cards
        menu = QMenu()

        # creation, connecting and adding of actions
        changedeck = QAction(self.tr("Change Deck"), menu)
        changedeck.triggered.connect(self.changedeck) # won't allow moving cards from public decks
        changedue = QAction(self.tr("Change Due Date"), menu)
        changedue.triggered.connect(self.changedue)
        forget = QAction(self.tr("Forget"), menu)
        forget.triggered.connect(self.forget)
        delete = QAction(self.tr("Delete"), menu)
        delete.triggered.connect(self.delete)
        menu.addActions([changedeck, changedue, forget, delete])

        # displaying the menu at the appropriate position
        menu.exec_(self.cardstree.viewport().mapToGlobal(position))

    def changedeck(self):
        # todo: note this function might present issues for public decks and moving cards however this isn't significant
        #  enough to be fixed right now
        # could allow selection of multiple cards but currently only allows for a single card to be moved

        # retrieve the selected card
        card = self.cardstree.model().item(self.cardstree.currentIndex().row())
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT isPublic FROM decks WHERE id = ?""", (card.deck_id,))
        public = cur.fetchone()[0]

        # checks if the user made the card (and so has permission to move it)
        if card.creator_id != self.user.id and public:
            # todo - maybe change this to a dialog box
            self.alertlabel.setText("This card is part of a public deck and cannot be moved")
        else:
            # if the card can be moved a window is displayed allowing the user to select a deck to move the card to
            self.movewindow = MoveCard(self.user)
            self.movewindow.movebutton.clicked.connect(lambda: self.movecard(card))
            self.movewindow.exec()

    def movecard(self, card):
        # retrieves the selected deck and updates the card's deck reference
        deck = self.movewindow.decksmodel.item(self.movewindow.deckslist.currentIndex().row(), 0)
        if not deck:
            return
        card.deck_id = deck.did
        card.update(self.user.id)
        self.movewindow.deleteLater()
        self.refresh()

    def changedue(self):
        # displays a window allowing for the rescheduling of a card,
        card = self.cardstree.model().item(self.cardstree.currentIndex().row())
        self.reschedulewindow = RescheduleWindow()
        # connects the accept state (ok button) of the window to a function which will execute the rescheduling
        self.reschedulewindow.buttonBox.accepted.connect(lambda: self.reschedule(card))
        self.reschedulewindow.exec()

    def reschedule(self, card):
        # checks that the input is of a valid format and then reschedules acordingly
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

        # priority in selection is given to more complex cases first
        if "-" in match and '!' in match:
            # Handle the x-y! case
            x, y = match.split("-")
            y = y[:-1]
            x, y = map(int, [x, y])
            try:
                days_ivl = random.randint(x, y)
            except:
                # if y is less than x
                days_ivl = random.randint(y, x)
            ivl = days_ivl * 86400
            # max() ensures ivl isn't less than 1 day
            cur.execute("""UPDATE user_cards SET status = ?, due = ?, ivl = ? WHERE id = ?""",
                        (2, time() + ivl, max(ivl, 86400), card.id))

        elif "-" in match:
            # Handle the x-y case
            x, y = map(int, match.split("-"))
            try:
                days_ivl = random.randint(x, y)
            except:
                # if y is less than x
                days_ivl = random.randint(y, x)
            ivl = days_ivl * 86400
            cur.execute("""UPDATE user_cards SET status = ? due = ? WHERE id = ?""", (2, time() + ivl, card.id))

        elif "!" in match:
            # Handle the x! case
            x = int(match[:-1])
            ivl = x * 86400
            # max() ensures ivl isn't less than 1 day
            cur.execute("""UPDATE user_cards SET status = ?, due = ?, ivl = ? WHERE id = ?""",
                        (2, time() + ivl, max(ivl, 86400), card.id))

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
        # display a window prompting for confirmation for a card to be forgotten and with options for resetting
        card = self.cardstree.model().item(self.cardstree.currentIndex().row())
        self.forgetwindow = ForgetWindow()

        # connect the accept state to a function which will forget the card
        self.forgetwindow.buttonBox.accepted.connect(lambda: self.confirmforget(card))
        self.forgetwindow.exec()

    def confirmforget(self, card):
        con = sqlite3.connect(database)
        cur = con.cursor()

        # handling of two different options for forgetting a card, reps and lapses either can be optionally reset
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

        # displays a window prompting for the deletion of a card if the user created it
        if card.creator_id == self.user.id:
            self.deletewindow = DeleteCard()
            self.deletewindow.buttonBox.accepted.connect(lambda: self.confirmdelete(card))
            self.deletewindow.exec()
        else:
            self.alertlabel.setText("You cannot delete this card as you are not the creator")

    def confirmdelete(self, card):
        # executes deletion of a card when confirmed
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""DELETE FROM user_cards WHERE cid = ?""", (card.cid,))
        cur.execute("""DELETE FROM cards WHERE id = ?""", (card.cid,))
        con.commit()
        cur.close()
        con.close()
        self.deletewindow.deleteLater()
        self.refresh()


# Window for moving a card between decks
class MoveCard(QDialog):
    def __init__(self, user):
        super().__init__()
        loadUi("movecard.ui", self)
        self.user = user
        self.decksmodel = QStandardItemModel()
        self.loaddecks()

        # cancel just deletes the window without executing anything in the parent window
        self.cancelbutton.clicked.connect(self.deleteLater)

    def loaddecks(self):
        # fetches and load decks so that the user can select the deck which they wish to move the card to
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


# Window for the rescheduling of cards
class RescheduleWindow(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("reschedule.ui", self)
        self.buttonBox.rejected.connect(self.deleteLater)


# Window for forgetting cards
class ForgetWindow(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("forgetwindow.ui", self)
        self.buttonBox.rejected.connect(self.deleteLater)


# Confirmation window for deleting cards
class DeleteCard(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("deletecard.ui", self)
        self.buttonBox.rejected.connect(self.deleteLater)


# Main window for adding cards
class AddCard(QWidget):
    def __init__(self, user, stack):
        self.user = user

        # setup of the ui
        super().__init__()
        loadUi("addcard.ui", self)

        connectmainbuttons(self, stack)

        # setting the layout for a scroll widget which is used to display line edits for a templates fields
        # - allowing the user to input data to create cards
        self.scrollWidgetContents_layout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollWidgetContents_layout.setContentsMargins(0, 0, 0, 0)
        self.scrollWidgetContents_layout.setAlignment(Qt.AlignTop)

        self.scrollAreaWidgetContents.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.scroll.setWidget(self.scrollAreaWidgetContents)
        self.scroll.setWidgetResizable(True)

        # connecting the template button clicked signal to a function that will allow the user to view templates
        self.templatesbutton.clicked.connect(self.viewtemplates)
        self.templateswindow = None

        # fill the decks box with the user's decks
        self.fill_decks_box()

        # set the template initially to display line edits for its fields
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("SELECT MIN (id) FROM templates WHERE created_uid = ?", (self.user.id,))
        self.template = Template(cur.fetchone()[0])
        cur.close()
        con.close()

        # line edits generated through apply template
        self.applytemplate()

        # connecting the button to add cards
        self.addcard.clicked.connect(self.add_card)

    def applytemplate(self):
        # sets the templates button text to the name of the current template reference by self.template
        self.templatesbutton.setText(self.template.name)

        # clear the fields/line edits in the scroll widget layout
        for i in reversed(range(self.scrollWidgetContents_layout.count())):
            self.scrollWidgetContents_layout.itemAt(i).widget().deleteLater()

        # parse the template's fields
        split = self.template.fields.split(",")
        self.line_edits = []
        font = QFont()
        font.setPointSize(15)
        font.setWeight(50)

        # iterate through the fields, creating a line edit for entering data and label for the field's name
        for field in split:
            label = QtWidgets.QLabel(f"{field}")
            label.setFont(font)
            line_edit = QtWidgets.QLineEdit()
            line_edit.setMinimumHeight(41)
            line_edit.setMaximumHeight(41)
            line_edit.setFont(font)
            line_edit.setPlaceholderText("")

            # add the line edit and label to the layout
            self.scrollWidgetContents_layout.addWidget(label)
            self.scrollWidgetContents_layout.addWidget(line_edit)
            self.line_edits.append(line_edit)

    def viewtemplates(self):
        # create and show a templates window allowing the user to manage and select templates
        self.templateswindow = TemplatesWindow(self.user, self.template)
        self.templateswindow.show()

        # connect the select button of the tempalte window to setting this window's template
        self.templateswindow.selectbutton.clicked.connect(self.settemplate)

    def settemplate(self):
        # get the template from the templateswindow and assing it to self.template
        self.template = self.templateswindow.templatesmodel.item(
            self.templateswindow.templateslist.currentIndex().row(), 0)
        if self.template:
            self.applytemplate()
            self.templateswindow.hide()
        else:
            # nothing happens if a template has not been selected. Haven't found a better way to handle this as of now
            pass

    def fill_decks_box(self):
        # retrieves all the user's own decks (that they have created) and adds them to a combo box to allow for them to
        # be selected for cards to be added to them
        self.decksbox.clear()
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT ud.id, d.name FROM decks d INNER JOIN user_decks ud ON ud.deck_id = d.id INNER JOIN users         
        u on d.created_uid = u.id WHERE u.id = ?""", (self.user.id,))
        try:
            ud_ids, d_names = zip(*[(row[0], row[1]) for row in cur.fetchall()])
        except:
            ud_ids = []
            d_names = []

        for i in range(len(ud_ids)):
            self.decksbox.addItem(d_names[i], Deck(ud_ids[i], self.user))

    def refresh(self):
        self.fill_decks_box()
        # template refresh not necessary as template selection and display is handled in another window

    def add_card(self):
        # method which adds a card to the selected deck
        card_data = []
        empty = True

        # verifies that data has been inputted
        for line in self.line_edits:
            data = line.text()
            if data:
                empty = False
            card_data.append(data)

        if not empty:
            con = sqlite3.connect(database)
            cur = con.cursor()

            # parses the data to be stored as a comma seperated string
            card_data = ",".join(card_data)

            # displays an error message if no deck has been selected
            if not self.decksbox.currentText():
                self.error.setText("No deck selected")
                return

            # gets the current deck selected
            deck = self.decksbox.currentData()

            # insert the card in cards and create a user-card connection in the link table
            cur.execute("""INSERT INTO cards (data, deck_id, template_id, modified, created_uid)
                            VALUES (?, ?, ?, ?, ?) RETURNING id""",
                        (card_data, deck.did, self.template.id, time(), self.user.id))
            cid = cur.fetchone()[0]
            cur.execute("""INSERT INTO user_cards (uid, cid, ivl, type, status, reps, lapses, odue, left)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (self.user.id, cid, None, 0, 0, 0, 0, time(), 0))

            con.commit()
            cur.close()
            con.close()

            # clear the line edits
            for line in self.line_edits:
                line.setText("")

        else:
            self.error.setText("Card has no data")


# Window for managing templates
class TemplatesWindow(QWidget):
    def __init__(self, user, template):
        super().__init__()
        loadUi("templates.ui", self)
        self.user = user
        # used to set the selection of the templates list
        self.initialtemplate = template

        # filling templates list
        self.templatesmodel = QStandardItemModel()
        self.loadtemplates()

        # connecting buttons to their respective functions
        self.backbutton.clicked.connect(self.hide)
        self.addbutton.clicked.connect(self.addwindow)
        self.renamebutton.clicked.connect(self.renamewindow)
        self.deletebutton.clicked.connect(self.delete)
        self.fieldsbutton.clicked.connect(self.managefields)
        self.layoutbutton.clicked.connect(self.editlayout)

    def loadtemplates(self):
        # clear the templates model
        self.templatesmodel.clear()

        # fetch the user's templates' ids, add corresponding template objects to the templates model
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("SELECT id FROM templates WHERE created_uid = ?", (self.user.id,))
        for fetch in cur.fetchall():
            template = Template(fetch[0])

            # get the number of cards that use the template
            cur.execute(f"""SELECT COUNT (id) FROM cards WHERE template_id = {template.id}""")
            cardcount = cur.fetchone()[0]
            template.setText(f"{template.name} [{cardcount} cards]")
            self.templatesmodel.appendRow(template)

        cur.close()
        con.close()
        self.templateslist.setModel(self.templatesmodel)

        # setting the selection of the templates list by checking the index of each template against that
        # of self.initialtemplate
        for row in range(self.templatesmodel.rowCount()):
            template_index = self.templatesmodel.index(row, 0)
            template = self.templatesmodel.itemFromIndex(template_index)
            if template.id == self.initialtemplate.id:
                self.templateslist.setCurrentIndex(template_index)
                break

        self.initialtemplate = None

    def addwindow(self):
        # create and show a window for adding a new template - provides the user with a collection of options
        self.addtemplatewindow = AddTemplate(self.user)

        # connect the add button's clicked signal to a function to add the template
        self.addtemplatewindow.addbutton.clicked.connect(self.addtemplate)
        self.addtemplatewindow.exec()

    def addtemplate(self):
        # get the selected item from the add template window (can either be a template, or an item that will add a
        # standard/preset template)
        template = self.addtemplatewindow.optionsmodel.item(self.addtemplatewindow.optionslist.currentIndex().row(), 0)
        if not template:
            # button doesnt do anything
            return

        # window is not deleted so that the items can still be retrieved in the complete add function
        self.addtemplatewindow.hide()

        # create and display a window for entering the name of the template
        self.templatenamewindow = NameWindow()

        # can rewrite to use regex matching for more generalisation if more standard templates are created
        # sets the text of the line edit depending on the option selected
        if template.text() == "Add: Basic":
            self.templatenamewindow.namelineedit.setText("Basic")
        else: # == 'Clone: ...'
            self.templatenamewindow.namelineedit.setText(f"{template.name} copy")

        # connect the window's buttons - cancel will delete the window
        self.templatenamewindow.cancelbutton.clicked.connect(lambda: self.cancel(self.templatenamewindow))
        self.templatenamewindow.okbutton.clicked.connect(self.completeadd)
        self.templatenamewindow.exec()

    def completeadd(self):
        # gets the template or preset object
        template = self.addtemplatewindow.optionsmodel.item(self.addtemplatewindow.optionslist.currentIndex().row(), 0)

        # gets the text from the name window
        name = self.templatenamewindow.namelineedit.text()

        con = sqlite3.connect(database)
        cur = con.cursor()

        # adds a basic template if the preset object was selected
        if template.text() == "Add: Basic":
            addbasictemplate(self.user.id, cur)

        # clones the desired template, with the name being set as entered by the user
        else:
            cur.execute("""INSERT INTO templates (fields, sortfield, modified, created_uid, front_format, back_format,
             styling, name) VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
                        (template.fields, template.sortfield, time(), self.user.id,
                         template.front, template.back, template.styling, name))
        template_id = cur.fetchone()[0]
        con.commit()
        cur.close()
        con.close()

        # delete both windows
        self.templatenamewindow.deleteLater()
        self.addtemplatewindow.deleteLater()

        # reload the templates, set initial template to the one just added
        addedtemplate = Template(template_id)
        self.initialtemplate = addedtemplate
        self.loadtemplates()

    def renamewindow(self):
        # checks that a template has been selected to be renamed
        template = self.templatesmodel.item(self.templateslist.currentIndex().row(), 0)
        if not template:
            return

        # instantiates and displays a window for allowing the user to enter a new name
        self.renametemplatewindow = NameWindow()

        # sets the initial template for selecting after reloading templates on return
        self.initialtemplate = template

        # connect the buttons of the window and set the text of the line edit to the selected template's name
        self.renametemplatewindow.okbutton.clicked.connect(lambda: self.rename(template))
        self.renametemplatewindow.cancelbutton.clicked.connect(lambda: self.cancel(self.renametemplatewindow))
        self.renametemplatewindow.namelineedit.setText(template.name)
        self.renametemplatewindow.exec()

    def rename(self, template):
        # this function executes the renaming of a template, the template to be renamed is passed as a parameter
        # text is retrieved from the renaming window
        new_name = self.renametemplatewindow.namelineedit.text()
        con = sqlite3.connect(database)
        cur = con.cursor()

        # template name updated
        cur.execute("""UPDATE templates SET name = ? WHERE id = ?""", (new_name, template.id))
        con.commit()
        cur.close()
        con.close()

        # rename window deleted and templates reloaded
        self.renametemplatewindow.deleteLater()
        self.loadtemplates()

    def cancel(self, window):
        # deletes a window passed to the function and refreshes templates
        window.deleteLater()
        self.loadtemplates()

    def managefields(self):
        # gets the selected template
        template = self.templatesmodel.item(self.templateslist.currentIndex().row(), 0)
        if not template:
            return

        # instantiates and displays a window for managing the selected template's fields
        self.initialtemplate = template
        self.templatefieldswindow = TemplateFieldsWindow(template)

        # connect the window's buttons to appropriate functions
        self.templatefieldswindow.savebutton.clicked.connect(self.savetemplatefields)
        self.templatefieldswindow.cancelbutton.clicked.connect(lambda: self.cancel(self.templatefieldswindow))
        self.templatefieldswindow.show()

    def savetemplatefields(self):
        # This function is called on save button being clicked in the template fields window, instead of executing
        # changes within that class, they are made here - utilising a FIFO queue data structure here to handle
        # all the executions after saving, this could not be done in the other class as this would require changes
        # being commited before the save button was actually clicked, due to the potential for needing to change the
        # cards' data fields affected by changes in the template -  and not wanting to make/commit these changes should
        # the changes to the template's fields be discarded

        """
         (CAN USE THIS IN WRITEUP)
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

        con = sqlite3.connect(database)
        cur = con.cursor()

        # fetches all the instructions to be executed from the template fields window, classifying and handling each one
        for instruction, params in zip(self.templatefieldswindow.instructions, self.templatefieldswindow.params):

            # will add an empty field slot to the data  of the template's cards
            if instruction == "CARD_ADD_FIELD":
                # unpack the parameters (index not actually needed)
                cid, index = params

                # fetch the cards data
                cur.execute("SELECT data FROM cards WHERE id = ?", (cid,))
                data = cur.fetchone()[0]

                # add an empty container
                data = data.split(",")
                data.append(",")
                data = ",".join(data)

                # update the card's data
                cur.execute("""UPDATE cards SET data = ? WHERE id = ?""", (data, cid))

            # will delete a field from the template's cards at the appropriate position
            elif instruction == "CARD_DELETE_FIELD":
                # unpacking parameters
                cid, delindex = params

                # fetching the card's data
                cur.execute("SELECT data FROM cards WHERE id = ?", (cid,))
                data = cur.fetchone()[0]

                # deleting data at the index of the deleted field
                data = data.split(",")
                del data[delindex]

                # updating the cards' data
                data = ",".join(data)
                cur.execute("""UPDATE cards SET data = ? WHERE id = ?""", (data, cid))

            # reposition data corresponding to the template's repositioned field
            elif instruction == "CARD_REPOS_FIELD":
                # unpacking parameters
                cid, old_index, new_index = params

                # fetching the card's data
                cur.execute("SELECT data FROM cards WHERE id = ?", (cid,))
                data = cur.fetchone()[0]

                # repositioning the relevant field's data
                data = data.split(",")
                repositionitem(data, old_index, new_index)
                data = ",".join(data)

                # updating the card's data
                cur.execute("""UPDATE cards SET data = ? WHERE id = ?""", (data, cid))
            else:
                # any other changes to be made to the template can just be executed here, the appropriate statement
                # and values will be passed and no fetching is required
                print(instruction, params)
                cur.execute(instruction, params)

        con.commit()
        cur.close()
        con.close()

        # delete the fields window and reload templates
        self.templatefieldswindow.deleteLater()
        self.loadtemplates()

    def editlayout(self):
        # retrieve the selected template
        template = self.templatesmodel.item(self.templateslist.currentIndex().row(), 0)
        if not template:
            return

        # instanitate and display a window for managing the selected template's layout
        self.layoutwindow = LayoutWindow(template)

        # connec the window's buttons to appropriate functions
        self.layoutwindow.savebutton.clicked.connect(self.savetemplatelayout)
        self.layoutwindow.cancelbutton.clicked.connect(lambda: self.cancel(self.layoutwindow))
        self.layoutwindow.show()

    def savetemplatelayout(self):
        # todo need to check if the layouts are valid, if not have to create dialog prompt alerting them and preventing
        #  saving - return from this function, parent should be self.layoutwindow in init - will ignore for now

        # update the template's format and styling fields
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""UPDATE templates SET front_format = ?, back_format = ?, styling = ? WHERE id = ?""",
                    (self.layoutwindow.template.front, self.layoutwindow.template.back,
                     self.layoutwindow.template.styling, self.layoutwindow.template.id))
        con.commit()
        cur.close()
        con.close()

        # delete the window
        self.layoutwindow.deleteLater()

        # reload templates
        self.initialtemplate = self.layoutwindow.template
        self.loadtemplates()

    def delete(self):
        # gets the selected template
        template = self.templatesmodel.item(self.templateslist.currentIndex().row(), 0)
        if not template:
            return

        # trigger a message box to get confirmation of deletion
        msgbox = QtWidgets.QMessageBox()
        msgbox.setText("Delete this template and all of its associated cards?")
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msgbox.setDefaultButton(QtWidgets.QMessageBox.Ok)

        # wait for a response from the user
        response = msgbox.exec_()

        # call a method to execute deletion if the user confirms
        if response == QtWidgets.QMessageBox.Ok:
            self.confirmdelete(template.id)

    def confirmdelete(self, template_id):
        con = sqlite3.connect(database)
        cur = con.cursor()

        # fetch the ids of affected cards
        cur.execute("SELECT id FROM cards WHERE template_id = ?", (template_id,))
        card_ids = [row[0] for row in cur.fetchall()]

        # delete from user cards where cid references a card that is affected by the tempalate deletion
        for card_id in card_ids:
            cur.execute("DELETE FROM user_cards WHERE cid = ?", (card_id,))

        # delete all affected cards
        cur.execute("DELETE FROM cards WHERE template_id = ?", (template_id,))

        # delete the template
        cur.execute("DELETE FROM templates WHERE id = ?", (template_id,))

        con.commit()
        cur.close()
        con.close()

        # reload templates list
        self.loadtemplates()


# Window for displaying the layout of template
class LayoutWindow(QWidget):
    def __init__(self, template):
        # do I want to load the two widgets separately and add them to the layout if there is an issue with the
        # layout text (e.g. {{ missing }} or field doesn't exist, update preview to show this, use a flag variable to
        # check for errors and if save clicked with an error - open up a dialog to prompt the user to change the
        # template
        super().__init__()
        loadUi("templatelayout.ui", self)

        # create a widget for displaying a preview of the layout
        self.preview = QWebEngineView()
        self.previewwidget.layout().addWidget(self.preview, 2)

        # set the template
        self.template = template

        # initially select the front format button and display the contents of the front format
        self.formatfrontbutton.toggle()
        self.changeediting()

        # connect buttons' signals to appropriate functions that will update the necessary widgets
        self.formatfrontbutton.clicked.connect(self.changeediting)
        self.formatbackbutton.clicked.connect(self.changeediting)
        self.formatstylingbutton.clicked.connect(self.changeediting)
        self.frontpreviewbutton.clicked.connect(self.showpreview)
        self.backpreviewbutton.clicked.connect(self.showpreview)
        self.formattextedit.textChanged.connect(self.update)

    def changeediting(self):
        # called when a new layout component is selected to be edited (i.e. front, back, styling)
        # block output signals from the text edit, as we will be loading different text but do not want this to trigger
        # any updates of the template
        self.formattextedit.blockSignals(True)

        # load the corresponding data for whichever radio button has been selected
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

        # update the template and preview
        self.update()

    def update(self):
        # update the layout format which is currently being edited and load the appropriate preview
        if self.formatfrontbutton.isChecked():
            self.template.front = self.formattextedit.toPlainText()
        elif self.formatbackbutton.isChecked():
            self.template.back = self.formattextedit.toPlainText()
        else:
            self.template.styling = self.formattextedit.toPlainText()
        self.showpreview()

    def showpreview(self):
        # function to display the preview of the front/back layout of a template
        # check for {{
        # except no }}, set html to show an error
        # except field doesn't exist to show error
        # parse field as html
        # move selection to processpreview

        # check which side is to be displayed
        if self.frontpreviewbutton.isChecked():
            # get the parsed front preview
            preview = self.processpreview(1)
            # display the preivew
            self.preview.setHtml(preview)

        elif self.backpreviewbutton.isChecked():
            # get the parsed back preview
            preview = self.processpreview(0)
            # display the preview
            self.preview.setHtml(preview)

    def processpreview(self, side):
        # todo could probably refactor this aswell
        # side = 1 -> front, side = 0 -> back
        if side:

            # extract fields parses the layout to identify escaped fields and display them properly
            # checks for error's in parsing the front of the layout
            field_error, missing_brackets_error, front = self.extractfields(1)

            if field_error:
                # todo could pass the field as field error
                preview = "Field Doesn't exist"
            elif missing_brackets_error:
                preview = "'{{' is missing closing '}}'"
            else:
                # if no errors return the parsed front of the layout
                preview = f"<head><style>{self.template.styling}</style></head> <body class='card'>{front}</body>"

        else:
            field_error, missing_brackets_error, back = self.extractfields(0)

            # checks for error's in parsing the back of the layout
            if field_error:
                # could pass the field as field error
                preview = "Field Doesn't exist"
            elif missing_brackets_error:
                preview = "'{{' is missing closing '}}'"

            # if no errors return the parsed back side of the layout
            else:
                preview = f"<head><style>{self.template.styling}</style></head> <body class='card'>{back}</body>"

        # returns either an error message or the parsed preview
        return preview

    def extractfields(self, side):
        # todo - could refactor this fucntion to avoid the primary selection statement, just assign the appropriate
        #  layout at the start and check for frontside if side == 0
        # function iterates through the layout corresponding to the side parameter, replacing escaped fields with the
        # field and checking for errors in the syntax or fields being escaped which do not exist
        field_error = False
        missing_brackets_error = False

        if side == 1:
            layout = self.template.front
        else:
            layout = self.template.back

        # removes new lines from the string
        layout = re.sub(r"\n", "", layout)
        match = True

        while match:
            # searches for text of the form {{abc}}
            match = re.search(r"\{\{(.+?)}}", layout)

            if match:
                # if a match is found, extract the field and check it against the template's fields
                match = match.group(0)

                if match[2:-2] not in self.template.fields.split(","):
                    # if the field doesn't exist flag a field error
                    field_error = True
                    return field_error, missing_brackets_error, layout

                # if the back side is being parsed, check for FrontSide field
                elif match[2:-2] == "FrontSide" and side == 0:
                    # if the FrontSide is referenced, parse and fetch the front side of the template to be dipslayed
                    # in the back
                    field_error, missing_brackets_error, front = self.extractfields(1)

                    # sub the front into the back layout
                    layout = re.sub(match, f"{front}", layout)

                # if the field is valid, remove the escape characters
                else:
                    layout = re.sub(match, f"({match[2:-2]})", layout)

        # check for any unpaired opening curly brackets
        match = re.search(r"\{\{", layout)
        if match:
            missing_brackets_error = True

        # return error flags and the parsed
        return field_error, missing_brackets_error, layout


# Window to get a text input from user for setting the names of objects
class NameWindow(QDialog):
    def __init__(self):
        super().__init__()
        loadUi("namewindow.ui", self)
        self.cancelbutton.clicked.connect(self.deleteLater)


# A window for managing the fields of a selected template
class TemplateFieldsWindow(QWidget):
    def __init__(self, template):
        super().__init__()
        loadUi("templatefields.ui", self)
        self.template = template

        # setup of the standard item model for containing the template's fields
        self.fieldsmodel = QStandardItemModel()
        self.fieldslist.setModel(self.fieldsmodel)
        self.fieldslist.selectionModel().selectionChanged.connect(self.fieldselected)

        # connecting buttons to respective functions
        self.sortfieldradio.clicked.connect(self.changesortfield)
        self.addbutton.clicked.connect(self.addwindow)
        self.renamebutton.clicked.connect(self.renamewindow)
        self.reposbutton.clicked.connect(self.repositionwindow)
        self.deletebutton.clicked.connect(self.deletefield)

        # fetch the template's fields and add them to the list view model
        self.selectedfield = None
        self.fillfields()

        # initially select the first field, retrieve and store its name
        self.fieldslist.setCurrentIndex(self.fieldsmodel.index(0, 0))
        self.selectedfield = re.sub(r"^\d+: ", "",
                                    self.fieldsmodel.item(self.fieldslist.currentIndex().row(), 0).text())

        # initialisation of arrays for storing the series of sql instructions (or instruction 'codes') to be executed
        # and parameters for each instruction
        self.instructions = []
        self.params = []

    def fillfields(self):
        # clear the model
        self.fieldsmodel.clear()

        # add fields to the model, set the text of the items to be the index of the position of the field, and the
        # field name
        i = 1
        for field in self.template.fields.split(","):
            self.fieldsmodel.appendRow(QStandardItem(f"{i}: {field}"))
            if field == self.selectedfield:
                # set the selection of the fields list to the previously selected field
                self.fieldslist.setCurrentIndex(self.fieldsmodel.index(i-1, 0))

            i += 1

    def fieldselected(self):
        # get the field name by removing the index at the start of the item's text, and set it as the currently
        # selected field
        self.selectedfield = re.sub(r"^\d+: ", "",
                                    self.fieldsmodel.item(self.fieldslist.currentIndex().row(), 0).text())

        # set the radio button to indicate if the field is being used as the template's sortfield
        if self.selectedfield == self.template.sortfield:
            self.sortfieldradio.setChecked(True)
        else:
            self.sortfieldradio.setChecked(False)

    def changesortfield(self):
        # if the current sortfield is trying to be toggled off, set it to toggled on and return, as this would cause
        # the template's sortfield to be none - we want it to be replaced by another field
        if self.template.sortfield == self.selectedfield:
            self.sortfieldradio.setChecked(True)
            return

        # change the sortfield of the template when the radiobutton is toggled on another field
        self.template.sortfield = self.selectedfield
        self.instructions.append("""UPDATE templates SET sortfield = ? WHERE id = ?""")
        self.params.append((self.template.sortfield, self.template.id))

    def addwindow(self):
        # display a window for enetering a name of the new field
        self.namewindow = NameWindow()
        self.namewindow.okbutton.clicked.connect(self.addfield)
        self.namewindow.exec()

    def addfield(self):
        # get the entered name from the window, check it isn't a duplicate of another field and not empty,
        # then add it to the template if valid
        field_name = self.namewindow.namelineedit.text()
        if not field_name:
            self.namewindow.errorlabel.setText("Field must have a name")
            return
        elif field_name in self.template.fields.split(","):
            self.namewindow.errorlabel.setText("Field name already in use")
            return

        # add the field to the template object
        self.template.addfield(field_name)

        # append an instruction to update the template in the database on saving
        self.instructions.append("""UPDATE templates SET fields = ? WHERE id = ?""")
        self.params.append((self.template.fields, self.template.id))

        # select all the template's cards
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT id FROM cards WHERE template_id = ?""", (self.template.id,))

        # get the position of the added field
        field_pos = self.template.fields.split(",").index(field_name)
        for fetch in cur.fetchall():
            cid = fetch[0]
            # append an instruction to add a field slot to the card's data, with parameters of the card's id and
            # field position
            self.instructions.append("CARD_ADD_FIELD")
            self.params.append((cid, field_pos))

        cur.close()
        con.close()

        # refresh the fields list
        self.fillfields()

        # delete the name window
        self.namewindow.deleteLater()

    def renamewindow(self):
        # check that a field is selected
        if not self.selectedfield:
            return

        # display a window for renaming the field and set the line edit text to the field's current name
        old_name = self.selectedfield
        self.namewindow = NameWindow()
        self.namewindow.namelineedit.setText(self.selectedfield)

        # connect the window's buttons
        self.namewindow.okbutton.clicked.connect(lambda: self.renamefield(old_name))
        self.namewindow.exec()

    def renamefield(self, old_name):
        # get the new field name and check for validity
        new_name = self.namewindow.namelineedit.text()
        if new_name == old_name:
            self.namewindow.deleteLater()
            return
        if not new_name:
            self.namewindow.errorlabel.setText("Field must have a name")
            return
        elif new_name in self.template.fields.split(","):
            self.namewindow.errorlabel.setText("Field name already in use")
            return

        # rename the field in the template object
        self.template.renamefield(old_name, new_name)

        # append instructions for changing the template's fields data
        self.instructions.append("""UPDATE templates SET fields = ? WHERE id = ?""")
        self.params.append((self.template.fields, self.template.id))

        # delete the window and refresh the fields list
        self.namewindow.deleteLater()
        self.fillfields()

    def repositionwindow(self):
        # display a window for repositioning the selected field
        if not self.selectedfield:
            return
        old_index = self.template.fields.split(",").index(self.selectedfield)
        self.reposwindow = RepositionFieldWindow(self.template)
        self.reposwindow.okbutton.clicked.connect(lambda: self.repositionfield(old_index))
        self.reposwindow.show()

    def repositionfield(self, old_index):
        # ensures the new index entered is valid
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

        # reposition the field
        self.template.repositionfield(old_index, new_index)

        # append an instruction for updating the template
        self.instructions.append("""UPDATE templates SET fields = ? WHERE id = ?""")
        self.params.append((self.template.fields, self.template.id))

        # fetch all the affected cards
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT id FROM cards WHERE template_id = ?""", (self.template.id,))

        # append instrutions for repositioning the card's data to align with the new field position
        for fetch in cur.fetchall():
            cid = fetch[0]
            self.instructions.append("CARD_REPOS_FIELD")
            self.params.append((cid, old_index, new_index))

        cur.close()
        con.close()

        # delete the window
        self.reposwindow.deleteLater()

        # refresh the fields
        self.fillfields()

    def deletefield(self):
        # display a dialog prompting for confirmation for deleting the field
        if not self.selectedfield:
            return
        deletewindow = DeleteFieldWindow(self, self.template, self.selectedfield)
        deletewindow.buttonBox.accepted.connect(self.delete)
        deletewindow.exec()

    # todo - if time fix issues with layouts when a field in the layout is deleted
    def delete(self):
        # get the field to be deleted
        delfield = self.selectedfield

        # delete the field from the template
        field_pos = self.template.fields.split(",").index(delfield)
        self.template.removefield(delfield)

        # append an instruction to delete the field from the template in the database
        self.instructions.append("""UPDATE templates SET fields = ? WHERE id = ?""")
        self.params.append((self.template.fields, self.template.id))

        # fetch the template's cards
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT id FROM cards WHERE template_id = ?""", (self.template.id,))

        # append instructions to delete the corresponding data entry from the cards
        for fetch in cur.fetchall():
            cid = fetch[0]
            self.instructions.append("CARD_DELETE_FIELD")
            self.params.append((cid, field_pos))
        cur.close()
        con.close()

        # refresh the fields
        self.fillfields()


# A window for repositioning a template
class RepositionFieldWindow(QWidget):
    def __init__(self, template):
        super().__init__()

        # repurposing the same ui file but changing the text
        loadUi("namewindow.ui", self)
        self.count = len(template.fields.split(","))
        self.label.setText(f"Enter New Position ({1} - {self.count}):")
        self.cancelbutton.clicked.connect(self.deleteLater)


# Confirmation window for deleting fields
class DeleteFieldWindow(QDialog):
    def __init__(self, parent_wnd, template, field):
        super().__init__(parent_wnd)
        loadUi("deletetemplate.ui", self)
        # self.setFixedSize(400, 200)

        # get the number of affected cards
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT COUNT (id) FROM cards WHERE template_id = ?""", (template.id,))
        totalcount = cur.fetchone()[0]

        # check whether there are any cards affected which are in public decks to alert the user
        cur.execute("""SELECT c.data, d.isPublic FROM cards c INNER JOIN decks d ON c.deck_id = d.id WHERE 
        template_id = ?""", (template.id,))

        # todo was getting the number of cards with data in that specific field but decided not to, clean this
        affected_idx = template.fields.split(",").index(field)
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

        # set the text of the dialog box
        self.totalnoteslabel.setText(f"Delete field '{field}' from {totalcount} notes")
        # self.noteswithdatalabel.setText(f"Of which {affectedcount} contain data in this field")
        if affectspublic:
            self.warninglabel.setText("Deleting this field will affect decks which you have published!")
        self.buttonBox.rejected.connect(self.deleteLater)


# Window for adding templates - displays a collection of options for adding/cloning
class AddTemplate(QDialog):
    def __init__(self, user):
        super().__init__()
        loadUi("addtemplate.ui", self)
        self.user = user
        self.optionsmodel = QStandardItemModel()
        self.backbutton.clicked.connect(self.hide)
        self.filloptions()

    def filloptions(self):
        # add options for adding standard templates
        self.optionsmodel.clear()
        self.optionsmodel.appendRow(QStandardItem("Add: Basic"))

        # get the user's templates and add options (items) for cloning them
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
# [work out way to show historic reviews (number on each day)] - matplotlib imshow(z)? - low priority/scrapped, would be
#  some kind of heatmap
# Success rate breakdown by hours over a given time frame - on hold, could be cool though


# Main window for allowing the user to see a collection of various statistics
# todo - could add an option for seeing overdue reviews in the future reviews graph
class StatsPage(QWidget):
    def __init__(self, user, stack):
        # arrays containing colours to be used in graphs
        self.statuscolours = ['#6BAED6', '#DF8C50', '#CF6A52', '#84C685', '#48A461']
        self.answercolours = ['#8F0B29', '#D5A365', '#9DBE69', '#0B5E37']

        # standard window setup
        self.user = user
        super().__init__()
        loadUi("statspage.ui", self)
        connectmainbuttons(self, stack)

        # creation of the layout for housing widgets which will display the various graphs/statistics
        layout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)

        self.scrollarea.setWidget(self.scrollAreaWidgetContents)
        self.scrollarea.setWidgetResizable(True)
        self.scrollAreaWidgetContents.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scrollAreaWidgetContents.setLayout(layout)
        self.scrollAreaWidgetContents.layout().setAlignment(Qt.AlignTop)

        # connecting of the top level buttons and deck box for viewing statistics of a certain deck, or for all the
        # user's cards
        self.allcardsbutton.clicked.connect(self.allcardstoggled)
        self.deckbutton.clicked.connect(self.deckbuttontoggled)
        self.decksbox.currentIndexChanged.connect(self.changedeck)
        self.decksbox.currentIndexChanged.connect(self.refreshgraphs)

        # initially set the statistics to be for all cards, disable the decksbox
        self.allcardsbutton.setChecked(True)
        self.decksbox.setEnabled(False)
        self.deck = None

        # create the widgets to house various statistics and add them to the layout
        self.createstatswidgets()

        # refresh/create all the graphs within those widgets and fill the decks box
        self.refresh()

    def refresh(self):
        # refresh graphs and the decks box
        # only the graphs are refreshed in order to minimise load and speed up the program
        self.filldecksbox()
        self.refreshgraphs()

    def createstatswidgets(self):
        # could refactor this into multiple seperate functions, only being called once though
        buttonfont = QFont()
        buttonfont.setPointSize(16)

        todaywidget = TodayStatsWidget()
        self.scrollAreaWidgetContents.layout().addWidget(todaywidget)

        # Creating future due housing widget and elements - button groups used to ensure a button is always selected
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

        self.scrollAreaWidgetContents.layout().addSpacerItem(
            QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding))

        self.scrollAreaWidgetContents.layout().setContentsMargins(0, 0, 0, 0)

    def refreshgraphs(self):
        # refresh all of the data/graphs within the stats widgets
        self.updatetodaywidget(self.scrollAreaWidgetContents.layout().itemAt(0).widget())
        self.refreshfuturereviews()
        self.refreshpastreviews()
        self.refreshstatuswidget()
        self.refreshivlswidget()
        self.refresheasewidget()
        self.refreshanswerwidget()

    def updatetodaywidget(self, widget):
        todaywidget = widget
        con = sqlite3.connect(database)
        cur = con.cursor()
        # fetches for the total number of cards reviewed, total time taken, the number of times which the 'again' button
        # was pressed, counts for each card type reviewed, the number of mature cards reviewed and number of sucessful
        # reviews on these cards FOR TODAY, either from a selected deck, or for all of the user's cards
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

            newcount = self.statustodaycount(0, cur)
            learncount = self.statustodaycount(1, cur)
            reviewcount = self.statustodaycount(2, cur)
            relearncount = self.statustodaycount(3, cur)

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

            newcount = self.statustodaycount(0, cur)
            learncount = self.statustodaycount(1, cur)
            reviewcount = self.statustodaycount(2, cur)
            relearncount = self.statustodaycount(3, cur)

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

        # displays an appropriate message if nothing has been studied
        if totalcount == 0:
            todaywidget.overallcardsstudied.setText("No cards have been studied today")
            todaywidget.againcountlabel.setText("")
            todaywidget.breakdownlabel.setText("")
            todaywidget.maturecardslabel.setText("")

        else:
            # todo, format times here better, i.e. minutes for total time if > 60 etc.
            # sets text to display, the fetched statistics, also performs calculations for averages (e.g. time reviewed)
            # and success percentages
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

        return

    def statustodaycount(self, status, cur):
        # function which will return the number of cards of a certain status reviewed today, within either a deck or
        # in all the user's decks
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

    def refreshfuturereviews(self):
        # gets and refreshes the widget for future reviews
        futurewidget = self.scrollAreaWidgetContents.layout().itemAt(1).widget()
        buttonswidget = futurewidget.frame.findChild(QWidget, "buttonswidget")

        # gets the selected time frame for fetching the statistics over
        daysrange = None  # Default value for if the 'all' radio button is checked
        if buttonswidget.findChild(QRadioButton, "onemonth").isChecked():
            daysrange = 30
        elif buttonswidget.findChild(QRadioButton, "threemonths").isChecked():
            daysrange = 90
        elif buttonswidget.findChild(QRadioButton, "oneyear").isChecked():
            daysrange = 365

        # creates a bar graph of future reviews
        futuresubwidget = self.createfuturereviewsbar(daysrange)

        # checks for a previous graph and deletes it if present
        if futurewidget.frame.layout().count() > 3:
            futurewidget.frame.layout().itemAt(3).widget().deleteLater()

        # adds the newly generated graph to the widget
        futurewidget.frame.layout().addWidget(futuresubwidget)

    def refreshpastreviews(self):
        # gets and refreshes the widget for past reviews
        pastwidget = self.scrollAreaWidgetContents.layout().itemAt(2).widget()
        buttonswidget = pastwidget.frame.findChild(QWidget, "buttonswidget")

        # gets the time fram for fetching reviews over
        daysrange = None  # Default value for if the 'all' radio button is checked
        if buttonswidget.findChild(QRadioButton, "onemonth").isChecked():
            daysrange = 30
        elif buttonswidget.findChild(QRadioButton, "threemonths").isChecked():
            daysrange = 90
        elif buttonswidget.findChild(QRadioButton, "oneyear").isChecked():
            daysrange = 365

        # creates a bar graph displaying past reviews
        pastsubwidget = self.createpastreviewsbar(daysrange)

        # checks for a previous graph and deletes it if added
        if pastwidget.frame.layout().count() > 3:
            pastwidget.frame.layout().itemAt(3).widget().deleteLater()

        # add the new graph to the widget's layout
        pastwidget.frame.layout().addWidget(pastsubwidget)

    def refreshstatuswidget(self):
        # refreshes the widget displaying card statuses
        statuswidget = self.scrollAreaWidgetContents.layout().itemAt(3).widget()

        # creates a new pie chart for card statuses
        statussubwidget = self.createstatuspie()

        # deletes the old graph if present
        if statuswidget.frame.layout().count() > 2:
            statuswidget.frame.layout().itemAt(2).widget().deleteLater()

        # add the new graph to the widget
        statuswidget.frame.layout().addWidget(statussubwidget)

    def refreshivlswidget(self):
        # refeshing the widget displaying card intervals
        ivlswidget = self.scrollAreaWidgetContents.layout().itemAt(4).widget()
        buttonswidget = ivlswidget.frame.findChild(QWidget, "buttonswidget")

        # Default values for if the 'all' radio button is checked
        maxivl = None
        percentage = None

        # get the selected range
        if buttonswidget.findChild(QRadioButton, "onemonth").isChecked():
            maxivl = 31
        elif buttonswidget.findChild(QRadioButton, "half").isChecked():
            # will fetch 50% of the cards (with the lowest intervals) when the graph is created
            percentage = 0.5
        elif buttonswidget.findChild(QRadioButton, "ninety").isChecked():
            # will fetch 90% of the cards (with the lowest intervals) when the graph is created
            percentage = 0.9

        # create the bar graph for card intervals
        ivlsubwidget = self.createintervalsbar(maxivl, percentage)

        # delete a previous graph if one exists in the layout
        if ivlswidget.frame.layout().count() > 3:
            ivlswidget.frame.layout().itemAt(3).widget().deleteLater()

        # display then new graph in the widget
        ivlswidget.frame.layout().addWidget(ivlsubwidget)

    def refresheasewidget(self):
        # refresh the widget for statistics on card ease factors
        easewidget = self.scrollAreaWidgetContents.layout().itemAt(5).widget()

        # create the graph
        easesubwidget = self.createeasefactorbar()

        # delete any old graph
        if easewidget.frame.layout().count() > 2:
            easewidget.frame.layout().itemAt(2).widget().deleteLater()

        # add the new graph to the widget
        easewidget.frame.layout().addWidget(easesubwidget)

    def refreshanswerwidget(self):
        # refresh the answer buttons widget
        answerwidget = self.scrollAreaWidgetContents.layout().itemAt(6).widget()
        buttonswidget = answerwidget.frame.findChild(QWidget, "buttonswidget")

        daysrange = None  # Default value if none of the following radio buttons are checked

        # gets the range for fetching reviews
        if buttonswidget.findChild(QRadioButton, "onemonth").isChecked():
            daysrange = 30
        elif buttonswidget.findChild(QRadioButton, "threemonths").isChecked():
            daysrange = 90
        elif buttonswidget.findChild(QRadioButton, "oneyear").isChecked():
            daysrange = 365

        # create the bar graph of historic answers
        answerbar = self.createanswerbuttonsbar(daysrange)

        # delete any previous graph
        if answerwidget.frame.layout().count() > 3:
            answerwidget.frame.layout().itemAt(3).widget().deleteLater()

        # add the new graph to the housing widget
        answerwidget.frame.layout().addWidget(answerbar)

    def allcardstoggled(self):
        # called when 'all cards' is selected, self.deck to none which will lead to generation of statistics for all
        # cards on self.refreshgraphs being called
        if not self.allcardsbutton.isChecked():
            # prevents the button from being toggled off if selected
            self.allcardsbutton.setChecked(True)
            return
        self.decksbox.setEnabled(False)
        self.deck = None
        self.refreshgraphs()

    def deckbuttontoggled(self):
        # sets a deck, and refreshes graphs to generate statistics for the current deck selected in the deckbox
        if not self.deckbutton.isChecked():
            # same as above
            self.deckbutton.setChecked(True)
            return
        self.decksbox.setEnabled(True)
        self.deck = self.decksbox.currentData()
        self.refreshgraphs()

    def filldecksbox(self):
        # fills the decksbox, retains the deck selection if there was one prior to refreshing
        prevdeck = self.decksbox.currentData()

        # blocks signals to prevent changing/reloading the statistics windows
        self.decksbox.blockSignals(True)
        self.decksbox.clear()

        # fetch the user's linked decks
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT ud.id FROM user_decks ud WHERE ud.uid = ?""", (self.user.id,))
        try:
            udids = cur.fetchall()
        except:
            udids = []
            print("no decks exist")

        # add deck items to the combo box
        for udid in udids:
            deck = Deck(udid[0], self.user)
            self.decksbox.addItem(deck.name, deck)
            try:
                if deck.udid == prevdeck.udid:
                    self.decksbox.setCurrentIndex(self.decksbox.count() - 1)
            except AttributeError:
                pass

        # allow signals to be emitted again
        self.decksbox.blockSignals(False)

    def changedeck(self):
        # change the deck, the signal emitted by the combobox will also cause a refresh of the graphs
        if not self.deckbutton.isChecked():
            # if the index of changed while the deck button is not checked, do nothing. This shouldn't occur but is
            # just acting as a failsafe
            return
        self.deck = self.decksbox.currentData()

    def createfuturereviewsbar(self, daysrange):
        # this function returns a bar graph displaying the number of upcoming reviews for each day in the future and
        # text statistics relating to future reviews
        # todo configuration of this - perhaps allow for showing overdue if they exist, also add grouping a days
        today = datetime.date.today()
        todayend = int(mktime(today.timetuple())) + 86400

        con = sqlite3.connect(database)
        cur = con.cursor()

        # retrieve all the ids and due times of cards within the specified time range
        # (either for a deck or for the user's whole collection)
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

        # dump the retrieved data into a pandas data frame
        duesdf = pd.DataFrame(cur.fetchall(), columns=['id', 'due'])

        # if there is no data to display, create a "No Data" label and return it to be displayed
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

        # get today's date and time
        today = datetime.date.today()
        today_datetime = datetime.datetime.combine(today, datetime.datetime.min.time())

        # convert due times to datetime objects and subtract today's date from them to get days until due
        duesdf['due'] = pd.to_datetime(duesdf['due'], unit='s', origin='unix')
        duesdf['due'] = duesdf['due'].dt.date
        duesdf['due'] = pd.to_datetime(duesdf['due'])
        duesdf['due'] = (duesdf['due'] - today_datetime).dt.days

        # 'due' now contains the number of days in which a card is due

        # create a matplotlib canvas to display the data
        canvas = MplCanvas(self, width=5, height=4, dpi=100)
        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        # create a new df that groups the rows by due value, and adds a count for each due value present
        due_counts = duesdf.groupby(['due']).size().reset_index(name='count')
        due_counts['due'] = due_counts['due'].astype(int)

        # add counts for days which don't have any card due
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

        # filter where the due is at least 0 (so cards which are due today or later)
        due_counts = due_counts[due_counts['due'] >= 0]

        # sort the values on days in which the card is due
        due_counts = due_counts.sort_values(by=['due']).reset_index(drop=True)

        # plot a bar graph of due against count
        canvas.axes.bar(due_counts['due'], due_counts['count'], color=self.statuscolours[3], alpha=1)
        canvas.axes.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        # plot a cumulative frequency graph on the same axes, and fill below the plotted line
        ax2 = canvas.axes.twinx()
        ax2.plot(due_counts['due'], due_counts['count'].cumsum(), c='#a6a6a6', lw=0.2)
        ax2.fill_between(due_counts['due'], due_counts['count'].cumsum(), 0, alpha=0.1, color='#8C8C8C')
        ax2.set_ylim(0, max(due_counts['count'].cumsum()))
        ax2.set_ylim(bottom=0)
        ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        # set the limits of the x-axis
        if daysrange:
            canvas.axes.set_xlim(right=daysrange + 0.5, left=-0.5)
        else:
            canvas.axes.set_xlim(right=max(due_counts['due'] + 0.5), left=-0.5)

        # add a 3rd plot on the same graph, this is used for highlighting bars, and the plot is just bars of a constant
        # height and width equal to that of the first bars, alpha=0 means they are transparent and this will be changed
        # by the cursor to create a highlighting effect
        ax3 = canvas.axes.twinx()
        ax3.bar(range(max(due_counts['due']) + 1), max(due_counts['count']), color='white', alpha=0)
        ax3.get_yaxis().set_ticks([])

        # styling of the graph
        canvas.axes.spines[['top']].set_visible(False)
        ax2.spines[['top', 'bottom', 'left', 'right']].set_visible(False)
        ax3.spines[['top', 'left', 'bottom', 'right']].set_visible(False)

        canvas.axes.spines[['left', 'bottom', 'right']].set_color('#8C8C8C')

        canvas.axes.tick_params(colors='#8C8C8C')
        ax2.tick_params(colors='#8C8C8C')
        ax3.tick_params(colors='#8C8C8C')

        canvas.axes.set_facecolor('#363636')
        canvas.fig.set_facecolor('#363636')

        # set the canvas widget's size policy for when it is displayed
        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        # create a cursor that interacts with the highlight bar plot of the graph
        cursor = mplcursors.cursor(ax3, hover=mplcursors.HoverMode.Transient)

        # listener for the "add" event, triggered when cursor is added to the plot
        @cursor.connect("add")
        def on_add(sel):
            # modify appearance of the annotation that appears when hovering over a bar in the plot
            sel.annotation.get_bbox_patch().set(fc="white")
            sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=0)
            sel.annotation.set_fontsize(9)

            # set the text of the annotation based on the data associated with the (original) bar being hovered over
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

            # position the annotation on the plot and adjust the opacity of the selected bar
            x, y, width, height = sel.artist[sel.index].get_bbox().bounds
            sel.annotation.xy = (x + width / 2, y + height)
            sel.artist[sel.index].set_alpha(0.1)

        # listener for the "remove" event, triggered when cursor is removed from the plot
        @cursor.connect("remove")
        def on_remove(sel):
            # make the selected bar transparent when the cursor is removed
            # (actually sets all bars to transparent and makes one translucent if one is selected)
            sel.artist[sel.index].set_alpha(0)
            for sel in cursor.selections:
                sel.artist[sel.index].set_alpha(0.1)

        # set the font size for text statistic labels
        font = QFont()
        font.setPointSize(15)

        # create lables for total due, avg reviews due per day, number of cards due tomorrow
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

        # add these text widgets to a grid layout in the text widget
        textlayout.addWidget(totalreviewslabel, 0, 0)
        textlayout.addWidget(totalreviewsstat, 0, 1)
        textlayout.addWidget(avglabel, 1, 0)
        textlayout.addWidget(avgstat, 1, 1)
        textlayout.addWidget(tmrwlabel, 2, 0)
        textlayout.addWidget(tmrwstat, 2, 1)

        # add the canvas and text widget to a subwidget which can be displayed in the housing widget in the stats window
        subwidget = QWidget()
        sublayout = QVBoxLayout()
        subwidget.setLayout(sublayout)
        sublayout.addWidget(canvas)
        sublayout.addWidget(textwidget)

        # return the finalised subwidget
        return subwidget

    def createpastreviewsbar(self, daysrange):
        # create a bar graph showing number and type of past reviews over a range of days

        # set group size and number of groups - grouping used for larger date ranges in order to maintain the graphs
        # readability
        group_size = math.ceil(daysrange / 90)
        num_groups = math.ceil(daysrange / group_size)

        # get today's date
        today = datetime.date.today()
        todaytimestamp = int(mktime(today.timetuple()))

        # create lists of timestamps for the start of days stored in 'daystarts' and x values for the number of days ago
        # that reviews occured in 'days_x'
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

        # reverse daystarts and days_x lists
        daystarts.reverse()
        days_x.reverse()

        con = sqlite3.connect(database)
        cur = con.cursor()

        # initialize arrays
        mature = []
        young = []
        learning = []
        relearning = []
        new = []

        # loop over daystarts list
        for daystart in daystarts:
            # query the database for the logs of reviews for the current day
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

            # fetch the results of the query
            reviews = cur.fetchall()

            # initialize counts for the different types of reviews
            maturecount = youngcount = learningcount = relearningcount = newcount = 0

            # loop over the reviews and increment the counts
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

            # append the counts to their respective lists
            mature.append(maturecount)
            young.append(youngcount)
            learning.append(learningcount)
            relearning.append(relearningcount)
            new.append(newcount)

        if all(x == 0 for x in mature + young + learning + relearning + new):
            # If all lists have zero values, create a QLabel with the text "No Data" and return the label to
            # be displayed
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

        # Create groups of days based on group_size
        groups = [days_x[i] - group_size for i in range(0, daysrange + 1, group_size)]

        # sum the counts of reviews of each status on days in the group's range for each group
        mature = [sum(mature[i:i + group_size]) for i in range(0, daysrange + 1, group_size)]
        young = [sum(young[i:i + group_size]) for i in range(0, daysrange + 1, group_size)]
        learning = [sum(learning[i:i + group_size]) for i in range(0, daysrange + 1, group_size)]
        relearning = [sum(relearning[i:i + group_size]) for i in range(0, daysrange + 1, group_size)]
        new = [sum(new[i:i + group_size]) for i in range(0, daysrange + 1, group_size)]

        # create a matplotlib canvas widget to display the data
        canvas = MplCanvas(self, width=5, height=4, dpi=100)

        # plot bar graphs for each status on the same axis, for each subsequent bar graph the y-values are started at
        # the sum of all the previous y-values for that day - implemented via the bottom parameter
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

        # create an array of the sum of the number of reviews for each day range group
        revsum = np.array([sum(i) for i in zip(mature, young, relearning, learning, new)])
        revsum = np.flip(revsum)

        # calculate the cumulative sum value at each element of the array
        cumulative = np.cumsum(revsum)

        # plot the cumulative sum of reviews on the same x-axis, fill below this line to the x-axis for styling
        reversed_groups = [groups[i] for i in reversed(range(len(groups)))]
        ax2 = canvas.axes.twinx()
        ax2.plot([x + group_size / 2 for x in reversed_groups], cumulative, c='#a6a6a6', lw=0.2)
        ax2.fill_between([x + group_size / 2 for x in reversed_groups], cumulative, 0, alpha=0.1, color='#8C8C8C')
        ax2.set_ylim(bottom=0)
        ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        canvas.axes.set_xlim(right=0, left=min(groups))

        # plotting another bar graph on the same x-axis for highlighting as with the previous graph
        ax3 = canvas.axes.twinx()

        ax3.bar(groups, max(revsum), color='white', alpha=0, width=group_size * 0.9, align='edge')
        ax3.get_yaxis().set_ticks([])

        # modifying the appearance of the graph/canvas
        canvas.axes.spines[['top']].set_visible(False)
        ax2.spines[['top', 'bottom', 'left', 'right']].set_visible(False)
        ax3.spines[['top', 'left', 'bottom', 'right']].set_visible(False)

        canvas.axes.spines[['left', 'bottom', 'right']].set_color('#8C8C8C')

        canvas.axes.tick_params(colors='#8C8C8C')
        ax2.tick_params(colors='#8C8C8C')
        ax3.tick_params(colors='#8C8C8C')

        canvas.axes.set_facecolor('#363636')
        canvas.fig.set_facecolor('#363636')

        # create a cursor that interacts with the highlight bar plot of the graph
        cursor = mplcursors.cursor(ax3, hover=mplcursors.HoverMode.Transient)

        # listener for the "add" event, triggered when cursor is added to the plot
        @cursor.connect("add")
        def on_add(sel):
            # modifying the appearance of the annotation
            sel.annotation.get_bbox_patch().set(fc="white")
            sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=0)
            sel.annotation.set_fontsize(9)

            # fetching values for each count on the selected day/day range
            index = sel.index
            mature_val = mature[index]
            young_val = young[index]
            relearning_val = relearning[index]
            learning_val = learning[index]
            new_val = new[index]
            running_val = cumulative[len(cumulative) - 1 - index]

            # formatting of information to be displayed in the annotation box
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

            # position the annotation on the plot and adjust the opacity of the selected bar
            x, y, width, height = sel.artist[sel.index].get_bbox().bounds
            sel.annotation.xy = (x + width / 2, y + height)
            sel.artist[sel.index].set_alpha(0.1)

        # listener for the "remove" event, triggered when cursor is removed from the plot
        @cursor.connect("remove")
        def on_remove(sel):
            # make the selected bar transparent when the cursor is removed
            sel.artist[sel.index].set_alpha(0)
            for sel in cursor.selections:
                sel.artist[sel.index].set_alpha(0.1)

        # setting the size policy of the canvas widget
        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        # set font for text statistics labels
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

        # add labels to the layout to be displayed in the textwidget
        textlayout.addWidget(daysstudiedlabel, 0, 0)
        textlayout.addWidget(daysstudiedstat, 0, 1)
        textlayout.addWidget(totalreviewslabel, 1, 0)
        textlayout.addWidget(totalreviewsstat, 1, 1)
        textlayout.addWidget(avgdaysstudiedlabel, 2, 0)
        textlayout.addWidget(avgdaysstudiedstat, 2, 1)
        textlayout.addWidget(avgperiodlabel, 3, 0)
        textlayout.addWidget(avgperiodstat, 3, 1)

        # add the graph and text widget to a subwidget which can be returned and displayed in the stats window
        subwidget = QWidget()
        sublayout = QVBoxLayout()
        subwidget.setLayout(sublayout)
        sublayout.addWidget(canvas)
        sublayout.addWidget(textwidget)

        return subwidget

    def createstatuspie(self):
        # creates a pie chart visually representing the status of cards and text along with this breaking it down
        """counts: [new, learning, relearning, young, mature]"""
        statuses = ['New', 'Learning', 'Relearning', 'Young', 'Mature']
        con = sqlite3.connect(database)
        cur = con.cursor()

        # initialize an array for storing the counts of each card status
        counts = [0] * 5

        # fetch counts of each card status either within a deck or for all the user's cards
        if self.deck:
            # fetching counts for new,learning and relearning cards
            params = [(0, self.user.id, self.deck.did), (1, self.user.id, self.deck.did),
                      (3, self.user.id, self.deck.did)]
            for i in range(3):
                cur.execute("""SELECT COUNT(DISTINCT uc.id) FROM user_cards uc
                INNER JOIN cards c ON uc.cid = c.id
                WHERE uc.status = ? 
                AND uc.uid = ? 
                AND c.deck_id = ?""",
                            (params[i]))
                counts[i] = cur.fetchone()[0]

            # fetching the count of young cards
            cur.execute(
                """SELECT COUNT(DISTINCT uc.id) FROM user_cards uc
                 INNER JOIN cards c ON uc.cid = c.id
                 WHERE uc.status = ?
                  AND uc.uid = ? 
                  AND c.deck_id = ? 
                  AND uc.ivl < ?""",
                (2, self.user.id, self.deck.did, 30 * 86400))
            counts[3] = cur.fetchone()[0]

            # fetching the count of mature cards
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
            # same as above but for all cards instead of within a deck
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

        # initialises arrays for filtering counts so that only those greater than 0 are plotted
        cleaned_counts = []
        cleaned_colours = []
        cleaned_statuses = []

        # array for explode values (set to 0 = normal visualisation)
        explode = []
        explodefloat = 0

        # cleans the counts and status names
        for i in range(5):
            if counts[i] != 0:
                cleaned_counts.append(counts[i])
                cleaned_colours.append(self.statuscolours[i])
                cleaned_statuses.append(statuses[i])
                explode.append(explodefloat)

        # create a matplotlib canvas widget to display the data
        canvas = MplCanvas(self, width=4, height=4, dpi=100)

        # was using these parameters for labels on the graph but think it looks better without as of now
        # labels=cleaned_statuses, autopct=lambda p: '{:.0f}'.format(p * sum(counts) / 100), pctdistance=0.85,

        # plot a pie chart of the status counts
        canvas.axes.pie(cleaned_counts, colors=cleaned_colours, explode=explode, startangle=90)

        # modifying the appearance of the graph
        canvas.axes.set_facecolor('#363636')
        canvas.fig.set_facecolor('#363636')

        canvas.fig.subplots_adjust(left=-0.05, right=1.05, bottom=-0.05, top=1.05)

        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        # creation of a subwidget to which the pie graph and associated text widget will be added
        subwidget = QWidget()
        layout = QHBoxLayout()
        subwidget.setLayout(layout)
        layout.addWidget(canvas)

        textwidget = QWidget()
        textlayout = QGridLayout()
        textwidget.setLayout(textlayout)

        font = QFont()
        font.setPointSize(15)

        # create labels for each status and the number of cards of that status, minimum size set for display within the
        # layout in the ui

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

        # add all the labels to a grid layout
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

        # display labels within the layout correctly
        textlayout.setRowStretch(0, 1)
        textlayout.setRowStretch(6, 1)
        textlayout.setColumnStretch(3, 1)

        # add the text widget to the subwidget's layout
        layout.addWidget(textwidget)

        # return the subwidget
        return subwidget

    def createintervalsbar(self, maxivl, percentage):
        # creates a bar graph displaying the intervals of cards
        con = sqlite3.connect(database)
        cur = con.cursor()

        # if a value for a maximum interval has been selected (e.g. one month)
        if maxivl:
            # fetch cards with interval equal to or less than the specified interval
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

        # if a fraction of cards with the smallest interval is to be fetched
        elif percentage:
            # fetch the total number of cards (within the deck or in the user's collection)
            # then calculate a limit for the number of cards to be fetched as a fraction of this, order the cards by
            # interval ascending to get the cards with the lowest interval

            # todo - could have worked out a cuttof interval for the max interval, right now only some cards of the
            #  highest ivl could be selected (delete this if ignoring)
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

        # if no restrictions
        else:
            # fetch the intervals of all cards
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

        # (min ivl = 1 day to avoid having to deal with sub-day cards)

        # Creating a data frame from the data fetched from the database
        ivlsdf = pd.DataFrame(cur.fetchall(), columns=['ivl'])

        # if there is no data fetched, create and return a label with text "No Data" to be displayed
        if ivlsdf['ivl'].empty:
            nodata = QLabel("No Data")
            font = QFont()
            font.setPointSize(24)
            nodata.setFont(font)
            nodata.setStyleSheet("color:#8c8c8c;")
            nodata.setAlignment(Qt.AlignCenter)
            nodata.setMinimumSize(0, 300)
            return nodata

        # convert the interval values to days
        ivlsdf = (ivlsdf / 86400).astype(int)

        # create a matplotlib canvas
        canvas = MplCanvas(self, width=5, height=4, dpi=100)
        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        # create a new dataframe consisting of the counts for each interval value
        ivlcounts = ivlsdf.groupby(['ivl']).size().reset_index(name='count')

        # fill the counts dataframe with 0 counts for interval lengths where no cards have that interval
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

        # sort the datafram on interval ascending
        ivlcounts = ivlcounts.sort_values(by=['ivl']).reset_index(drop=True)

        # calculate a group size for the intervals (to better display the graph for large ranges) and number of groups
        group_size = math.ceil(max(ivlcounts['ivl']) / 80)
        num_groups = math.ceil(len(ivlcounts['ivl']) / group_size)

        # create an array of groups from these values
        groups = [(i * group_size + 1) for i in range(num_groups)]
        group_ranges = [x - 1 for x in groups]

        # group the counts in the ivlcounts dataframe into these group ranges, based on the value of 'ivl'
        ivlcounts['group'] = pd.cut(ivlcounts['ivl'], bins=group_ranges + [max(group_ranges) + group_size],
                                    labels=groups)
        grouped_counts = ivlcounts.groupby('group')['count'].sum().reset_index()
        grouped_counts['group'] = grouped_counts['group'].astype(int)

        # todo add gradient to this if time
        # plot these now grouped intervals as a bar chart
        canvas.axes.bar(grouped_counts['group'], grouped_counts['count'], color=self.statuscolours[0], alpha=1,
                        width=group_size * 0.9, align='edge')
        canvas.axes.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        canvas.axes.set_xlim(right=max(grouped_counts['group'] + group_size), left=1)

        # plot the cumulative number of cards at each interval group along the same x-axis
        ax2 = canvas.axes.twinx()

        ax2.plot(grouped_counts['group'] + group_size / 2, grouped_counts['count'].cumsum(), c='#a6a6a6', lw=0.2)
        ax2.fill_between(grouped_counts['group'] + group_size / 2, grouped_counts['count'].cumsum(), 0, alpha=0.1,
                         color='#8C8C8C')
        ax2.set_ylim(0, max(grouped_counts['count'].cumsum()))
        ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax2.set_ylim(bottom=0)

        # plot a transparent bar graph with the same widths as the first again for highlighting functionality
        ax3 = canvas.axes.twinx()
        ax3.bar(grouped_counts['group'], max(grouped_counts['count']), color='white', alpha=0, width=group_size * 0.9,
                align='edge')
        ax3.get_yaxis().set_ticks([])

        # modifying the appearance of the graph
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

        # create a cursor for interacting with the graph
        cursor = mplcursors.cursor(ax3, hover=mplcursors.HoverMode.Transient)

        # listener for the "add" event, triggered when cursor is added to the plot
        @cursor.connect("add")
        def on_add(sel):
            # styling of the annotation box
            sel.annotation.get_bbox_patch().set(fc="white")
            sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=0)
            sel.annotation.set_fontsize(9)

            # get the index of the bar being hovered over
            index = sel.index

            # checking group size to determine how to format the text displaying the interval of cards
            if group_size == 1:
                ivl = grouped_counts.iloc[index]["group"]
                ivltext = f"with a {ivl} day inteval"
            else:
                ivlstart = grouped_counts.iloc[index]['group']
                ivlend = ivlstart + group_size - 1
                ivltext = f"with a {ivlstart}-{ivlend} day inteval"

            # get the count of cards with an ivl in the plotted range
            count = grouped_counts.iloc[index]["count"]
            if count == 1:
                cardsno = f"{count} card with a "
            else:
                cardsno = f"{count} cards with a "

            # get the cumulative value at that point and convert it to a percentage of the plotted cards
            cumulative = grouped_counts['count'].cumsum()[index]
            x = decimal.Decimal(cumulative / sum(grouped_counts['count']))
            cumpct = x * 100
            rounded_percentage = cumpct.quantize(decimal.Decimal('0.1'), rounding=decimal.ROUND_HALF_UP)

            # set the text of the annotation
            sel.annotation.set_text(f"{cardsno}{ivltext}\nRunning Total: {rounded_percentage}%")

            # position the annotation on the plot and adjust the opacity of the selected bar
            x, y, width, height = sel.artist[sel.index].get_bbox().bounds
            sel.annotation.xy = (x + width / 2, y + height)
            sel.artist[sel.index].set_alpha(0.1)

        # listener for the "remove" event, triggered when cursor is removed from the plot
        @cursor.connect("remove")
        def on_remove(sel):
            # make the selected bar transparent when the cursor is removed
            sel.artist[sel.index].set_alpha(0)
            for sel in cursor.selections:
                sel.artist[sel.index].set_alpha(0.1)

        # create a widget to hold all the text statistics associated with the interval graph
        textwidget = QWidget()
        textlayout = QVBoxLayout()
        textwidget.setLayout(textlayout)

        font = QFont()
        font.setPointSize(15)

        # feth the average interval of cards in the deck/collection and display it in a label
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

        # add the graph and text widget to a subwidget which is returned to be displayed
        subwidget = QWidget()
        sublayout = QVBoxLayout()
        subwidget.setLayout(sublayout)
        sublayout.addWidget(canvas)
        sublayout.addWidget(textwidget)

        return subwidget

    def createeasefactorbar(self):
        # create a bar graph for ease factors of cards
        con = sqlite3.connect(database)
        cur = con.cursor()

        # fetch card ease factors either from a deck or all of the user's cards
        if self.deck:
            cur.execute("""SELECT uc.ef FROM user_cards uc
            INNER JOIN cards c on uc.cid = c.id
            WHERE c.deck_id = ?
            AND uc.uid = ?""", (self.deck.did, self.user.id))
        else:
            cur.execute("""SELECT uc.ef FROM user_cards uc
                        WHERE uc.uid = ?""", (self.user.id,))

        # dump the fetched data into a pandas dataframe
        efdf = pd.DataFrame(cur.fetchall(), columns=['ef'])

        # if no data fetched create and return a label to display this
        if efdf['ef'].empty:
            nodata = QLabel("No Data")
            font = QFont()
            font.setPointSize(24)
            nodata.setFont(font)
            nodata.setStyleSheet("color:#8c8c8c;")
            nodata.setAlignment(Qt.AlignCenter)
            nodata.setMinimumSize(0, 300)
            return nodata

        # create a matplotlib canvas widget for plotting the graph
        canvas = MplCanvas(self, width=5, height=4, dpi=100)
        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        # create a new datafram consisting of grouped counts of ease factor values
        efcounts = efdf.groupby(['ef']).size().reset_index(name='count')

        # fill the dataframe for ease factor's over the range with a count of 0 cards
        for i in range(130, int(max(efcounts['ef'])) + 1):
            count = efcounts.loc[efcounts['ef'] == i]
            if count.empty:
                efcounts.loc[len(efcounts)] = [i, 0]
        efcounts = efcounts.sort_values(by=['ef']).reset_index(drop=True)

        # range handling, so if max card ease is 200 or above, the cards are grouped for better display
        ef_max = efcounts['ef'].max()
        if ef_max >= 200:
            group_size = 5
        else:  # todo could add a group size 2
            group_size = 1

        # calculate the number of groups and create an array of these group values
        num_groups = math.ceil((ef_max - 130) / group_size) + 1
        groups = [(130 + i * group_size) for i in range(num_groups)]
        group_ranges = [x - 1 for x in groups]

        # create a new data frame holding the counts of cards in each ease factor group
        efcounts['group'] = pd.cut(efcounts['ef'], bins=group_ranges + [max(group_ranges) + group_size], labels=groups)
        grouped_counts = efcounts.groupby('group')['count'].sum().reset_index()
        grouped_counts['group'] = grouped_counts['group'].astype(int)

        # color map for ease factor values spanning from red (130) up to dark green (300)
        color_map = ['#F52A2A', '#F43326', '#F43C22', '#F3451E', '#F34F1A', '#F25A16', '#F16412', '#F0700E',
                     '#EB7B0F', '#E6860F', '#E1910F', '#DD9B0F', '#D8A40F', '#D3AC0F', '#CEB40F', '#CABC0F',
                     '#C5C30F', '#B8C00F', '#A9BC0F', '#9AB70F', '#8CB20F', '#7FAE0F', '#72A90F', '#66A50F',
                     '#5AA00F', '#4F9B0F', '#44970F', '#3A920E', '#318E0E', '#28890E', '#20850E', '#18800E',
                     '#107C0D', '#0D7711', '#0D7317']

        # map (better to interpolate but just takes the floor value) the color map to the actual values in the
        # grouped_counts array
        colors = []
        for i in range(len(grouped_counts['group'])):
            try:
                color = color_map[i * group_size // 5] # division by 5 as the color_map is for every 5th ef value
            except:
                # if the index is outside the range: append the final color
                color = '#0D7317'
            colors.append(color)

        # plot a bar graph of the ease factors
        canvas.axes.bar(grouped_counts['group'], grouped_counts['count'], color=colors, alpha=1, width=group_size - 0.5,
                        align='edge')
        canvas.axes.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        canvas.axes.set_xlim(right=max(grouped_counts['group'] + 1.5 * group_size), left=130 - 0.5 * group_size)

        # plot an invisible bar graph on the same axis used for highlighting
        ax3 = canvas.axes.twinx()
        ax3.bar(grouped_counts['group'], max(grouped_counts['count']), color='white', alpha=0, width=group_size - 0.5,
                align='edge')
        ax3.get_yaxis().set_ticks([])

        # modifying the graph's appearance
        canvas.axes.spines[['top']].set_visible(False)
        ax3.spines[['top', 'left', 'bottom', 'right']].set_visible(False)

        canvas.axes.spines[['left', 'bottom', 'right']].set_color('#8C8C8C')

        canvas.axes.tick_params(colors='#8C8C8C')
        ax3.tick_params(colors='#8C8C8C')

        canvas.axes.set_facecolor('#363636')
        canvas.fig.set_facecolor('#363636')

        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        # creating a cursor for interacting with the graph
        cursor = mplcursors.cursor(ax3, hover=mplcursors.HoverMode.Transient)

        # listener for the "add" event, triggered when cursor is added to the plot
        @cursor.connect("add")
        def on_add(sel):
            # styling of the annotation
            sel.annotation.get_bbox_patch().set(fc="white")
            sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=0)
            sel.annotation.set_fontsize(9)

            # get the index of the selection
            index = sel.index

            # retrieve ease factor value and card count for the selected bar
            ease = grouped_counts.iloc[index]['group']
            count = grouped_counts.iloc[index]['count']

            # format and display this
            if count == 1:
                counttext = f"{count} card with "
            else:
                counttext = f"{count} cards with "
            sel.annotation.set_text(f"{counttext}{ease}% ease")

            # positioning of the annotation and highlighting of the bar
            x, y, width, height = sel.artist[sel.index].get_bbox().bounds
            sel.annotation.xy = (x + width / 2, y + height)
            sel.artist[sel.index].set_alpha(0.1)

        # listener for the "remove" event, triggered when cursor is removed from the plot
        @cursor.connect("remove")
        def on_remove(sel):
            # remove highlighting on all bars, leave the selected bar highlighted
            sel.artist[sel.index].set_alpha(0)
            for sel in cursor.selections:
                sel.artist[sel.index].set_alpha(0.1)

        # displaying average ease factor of cards in the selection
        font = QFont()
        font.setPointSize(15)

        avgeaselabel = QLabel()
        avgeaselabel.setAlignment(Qt.AlignHCenter)
        avgeaselabel.setFont(font)

        con = sqlite3.connect(database)
        cur = con.cursor()

        # fetching the average value
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

        # adding text and the graph to a subwidget to be displayed
        subwidget = QWidget()
        sublayout = QVBoxLayout()
        subwidget.setLayout(sublayout)
        sublayout.addWidget(canvas)
        sublayout.addWidget(avgeaselabel)

        return subwidget

    def createanswerbuttonsbar(self, daysrange):
        # creates a bar chart showing the user's answers on cards of varying status (re/learning, young, mature) and
        # provides associated statistics
        con = sqlite3.connect(database)
        cur = con.cursor()

        # initialise arrays for storing values
        learningcounts = []
        youngcounts = []
        maturecounts = []

        # create a cutoff if the data is desired over a secified time period
        if daysrange:
            today = datetime.date.today()
            todaytimestamp = int(mktime(today.timetuple()))
            cutoff = todaytimestamp - 86400 * daysrange
        else:
            cutoff = 0

        # fetching the counts of each review ease/answer button for (re)learning cards
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

        # fetching the same data for young cards
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

        # and again for mature cards
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

        # create an array of tuples of the fetched values for each status, where each tuple (of 3) contains the values
        # for a different answer button
        allcounts = [x for x in zip(learningcounts, youngcounts, maturecounts)]

        # if there are no reviews at all, return a label to display this
        if all(sum(tup) == 0 for tup in allcounts):
            nodata = QLabel("No Data")
            font = QFont()
            font.setPointSize(24)
            nodata.setFont(font)
            nodata.setStyleSheet("color:#8c8c8c;")
            nodata.setAlignment(Qt.AlignCenter)
            nodata.setMinimumSize(0, 300)
            return nodata

        # creates an array of evenly spaced values from 0 to 3 with step 1 (0, 1, 2) for handling the positioning of
        # the bars when plotting
        x = np.arange(3)

        # create a matplotlib canvas for plotting the graph
        canvas = MplCanvas(self, width=5, height=4, dpi=100)
        canvas.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        # Set the width of each bar
        bar_width = 0.15

        # Plot the bars for the first set of values (counts for the 'again' button) - learning, young and mature at x
        # positions 0, 1 and 2 respectively
        canvas.axes.bar(x, allcounts[0], width=bar_width - 0.01, color=self.answercolours[0])

        # plot the same for the other answer buttons' set of values, with the bars to the right of the previously
        # plotted values
        canvas.axes.bar(x + bar_width, allcounts[1], width=bar_width - 0.01, color=self.answercolours[1])
        canvas.axes.bar(x + 2 * bar_width, allcounts[2], width=bar_width - 0.01, color=self.answercolours[2])
        canvas.axes.bar(x + 3 * bar_width, allcounts[3], width=bar_width - 0.01, color=self.answercolours[3])

        # Set the x-axis tick positions and labels
        canvas.axes.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        # set the x-axis ticks to be under the groups of bars for each card status type
        canvas.axes.set_xticks(x + bar_width * 1.5)

        # todo change labels
        # create labels for the x-axis to display successful review % and the type of review
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

        # array of all plotted x positions which will be used for plotting the highlight bars and allow for
        # case handling of the tooltip
        x_positions = np.concatenate([x, x + bar_width, x + 2 * bar_width, x + 3 * bar_width])

        # plot a invisible bar graph with uniform height at the positions in the above array for highlighting
        ax3 = canvas.axes.twinx()
        ax3.bar(x_positions, np.max(allcounts, axis=None) * len(x_positions), color='white', alpha=0,
                width=bar_width - 0.01)
        ax3.get_yaxis().set_ticks([])

        # modifying appearance
        canvas.axes.spines[['top']].set_visible(False)
        ax3.spines[['top', 'left', 'bottom', 'right']].set_visible(False)

        canvas.axes.spines[['left', 'bottom', 'right']].set_color('#8C8C8C')
        canvas.axes.tick_params(colors='#8C8C8C')
        ax3.tick_params(colors='#8C8C8C')

        canvas.axes.set_facecolor('#363636')
        canvas.fig.set_facecolor('#363636')

        # creating a cursor for interacting with the graph
        cursor = mplcursors.cursor(ax3, hover=mplcursors.HoverMode.Transient)

        buttons = {0: 'Again', 1: 'Hard', 2: 'Good', 3: 'Easy'}

        # listener for the "add" event, triggered when cursor is moved over the plot
        @cursor.connect("add")
        def on_add(sel):
            # styling of the annotation
            sel.annotation.get_bbox_patch().set(fc="white")
            sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=0)
            sel.annotation.set_fontsize(9)

            # retrieval of the index of the selected bar
            index = sel.index

            # flatten the array of tuples used earlier
            countvalues = np.array(allcounts).flatten()

            # get the relative position/offset of the value in the tuplet (e.g. if the value is the 2nd
            # (i.e. index MOD 3 = 1), it corresponds to young cards
            if index % 3 == 0:
                offset = 0
            elif index % 3 == 1:
                offset = 1
            else:
                offset = 2

            # get the tuplet which the value is in and therefore the corresponding ease/button, 0th -> again,
            # 1st -> hard, etc.
            if index // 3 == 0:
                ease = 0
            elif index // 3 == 1:
                ease = 1
            elif index // 3 == 2:
                ease = 2
            else:
                ease = 3

            # get the total number of reviews for that card type
            total = 0
            for i in range(0, len(countvalues), 3):
                total += countvalues[i + offset]

            # get the number of times the hovered bar's button has been pressed for that card type
            pressedcount = countvalues[index]
            button = f"Button: {ease} ({buttons[ease]})"  # could change this to easy, hard, etc. using a dict
            timespressed = f"Times pressed: {pressedcount} ({round((pressedcount / total) * 100, 2)}%)"
            correct = f"{total - countvalues[index % 3]}/{total} correct ({round(((total - countvalues[index % 3]) / total) * 100, 2)}%)"

            # display the annotation and highlight the bar
            sel.annotation.set_text(f"{button}\n{timespressed}\n{correct}")
            x, y, width, height = sel.artist[sel.index].get_bbox().bounds
            sel.annotation.xy = (x + width / 2, y + height)
            sel.artist[sel.index].set_alpha(0.1)

        # listener for the "remove" event, triggered when cursor is removed from the plot
        @cursor.connect("remove")
        def on_remove(sel):
            # remove highlighting from the bar that has been moved off of
            sel.artist[sel.index].set_alpha(0)
            for sel in cursor.selections:
                sel.artist[sel.index].set_alpha(0.1)

        # return the canvas
        return canvas


# Matplotlib canvas widget for plotting and displaying graphs within the PyQt5 interface
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)


# Widget used for displaying text statistics on the user's reviews
class TodayStatsWidget(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("todaywidget.ui", self)
        self.setStyleSheet('background-color:#363636')


# Generic widget used for housing a graph (and text) in the stats window
class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("graphwidget.ui", self)
        self.setStyleSheet('background-color:#363636')


# Main window for browsing public decks
class Browse(QWidget):
    # todo card data will automatically update with changes made by the creator, could add an option that allow
    #  creator to allow/disallow copies being made
    # also maybe open another window if the creator is accessing a deck (this could be cool if ideas for it),
    # for now will just no connect the button
    # todo also need to refactor to avoid using 2 duplicate containers for decks
    def __init__(self, user, stack):
        self.user = user
        super().__init__()
        loadUi("browse.ui", self)
        connectmainbuttons(self, stack)

        # Could later check for updates on a deck allowing the user to keep their current version or sync changes. For
        # now will just ignore this and have 1 time deck copying in the current state of the deck. If recopied new cards
        # will be added to the user's library

        # create a model for storing and displaying decks made public/shared by users
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

        # fetch public decks and fill the tree view model
        self.fillpublicdecks()

        # constructing the "My Decks" list - used to let the user toggle the publicity of their decks
        self.deckslistmodel = QStandardItemModel(0, 2, self.mydeckslist)
        self.deckslistmodel.setHeaderData(0, Qt.Horizontal, "Decks")
        self.deckslistmodel.setHeaderData(1, Qt.Horizontal, "Public")
        self.deckslistmodel.itemChanged.connect(self.togglepublic)
        self.mydeckslist.setModel(self.deckslistmodel)

        # fetch decks for this list
        self.fillmydeckslist()

        # connect the search button
        self.searchbutton.clicked.connect(self.fillpublicdecks)

    def fetchpublicdecks(self, searchfilter):
        # fetches all the public decks which match the text in the search filter bar and other data associated with
        # the decks

        # repeated fetches for no search filter maybe not necessary - could still keep seperate error message with
        # a smaller selection clause
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

        data = [[row[0], row[1], row[2], row[3]] for row in cur.fetchall()]
        card_counts = []

        # get counts of the number of cards in each fetched deck
        for i in range(len(data)):
            cur.execute("""SELECT COUNT(*) FROM cards WHERE deck_id = ?""", (data[i][0],))
            count = cur.fetchone()[0]
            card_counts.append(count)
            data[i].append(count)

        # return the array of data for each deck
        return data

    def fillpublicdecks(self):
        # clears the decks currently loaded in the model
        self.publicdecksrootnode.removeRows(0, self.publicdecksrootnode.rowCount())

        # fetches decks matching the search filter
        searchfilter = self.browsefilter.text()
        decks = self.fetchpublicdecks(searchfilter)

        # if there were decks which have been fetched, iterate through the decks' data and add items dispalying this
        # to the tree view model
        if decks:
            for id, name, desc, creator, cardcount in decks:
                self.publicdecksrootnode.appendRow(
                    [Deck(id, self.user), QStandardItem(desc), QStandardItem(creator), QStandardItem(cardcount)])

    def fillmydeckslist(self):
        # fetch all the user's created decks and add them to/display them in the "My Deck's list view"
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

        # add items displaying the deck's name and an adjacent checkbox for toggling whether the deck is public
        for i in range(len(dids)):
            deck = Deck(dids[i], self.user)
            self.decks.append(deck)
            check = QStandardItem()
            check.setCheckable(True)

            # set the state of the checkbox to match the publicity of the deck
            if deck.public == 1:
                check.setCheckState(2)
            else:
                check.setCheckState(0)
            self.checkboxes.append(check)
            self.deckslistmodel.appendRow([self.decks[i], check])

        cur.close()
        con.close()

    def togglepublic(self, check):
        # toggle the publicity of a deck and refresh the public deck's list to show this change
        deckpos = self.checkboxes.index(check)
        deck = self.decks[deckpos]
        if check.checkState() == 2:
            deck.public = 1
        else:
            deck.public = 0
        deck.save()
        self.fillpublicdecks()

    def selectdeck(self, idx):
        # called when a public deck is clicked to display a new window for interacting with the selected deck
        deck = self.deckstreeview.model().item(idx.row(), 0)
        if deck.creator_id == self.user.id:
            return
        self.publicdeckview = PublicDeckView(deck, self.user)
        self.publicdeckview.show()

    def refresh(self):
        # refresh the window without regenerating it
        self.fillpublicdecks()
        self.fillmydeckslist()


# Window for allowing a user to add a public deck to their library, and view other related information
class PublicDeckView(QWidget):
    def __init__(self, deck, user):
        # window setup, displaying attributes of the selected deck
        super().__init__()
        loadUi("publicdeckview.ui", self)
        self.deck = deck
        self.user = user
        self.descriptionlabel.setText(f"{deck.desc}")
        self.decknamelabel.setText(f"{deck.name}")

        # display the number of cards in the deck
        self.samplefromxcards.setText(self.samplefromxcards.text().replace("x", f"{self.deck.cardcount}"))

        # load samples from the deck's cards to be displayed to the user
        self.loadsamples()

        # connect the add button to a function which will add/remove the deck
        self.addbutton.clicked.connect(self.toggledeckadded)

        # set the text of the add button to remove if the deck is already in the user's library
        if self.checkifinlibrary():
            self.addbutton.setText("Remove")
        else:
            self.addbutton.setText("Add")

    def loadsamples(self):
        # fetches a random sample of cards from the deck and displays them to the user
        con = sqlite3.connect(database)
        cur = con.cursor()

        # fetching cards
        cur.execute(
            """SELECT t.fields, c.data FROM cards c 
            INNER JOIN templates t ON c.template_id = t.id 
            WHERE deck_id = ? ORDER BY RANDOM () LIMIT 3""",
            (self.deck.did,))
        samples = cur.fetchall()

        # creating/resetting the layout for adding widgets to for displaying the cards' data
        self.vlayout = QVBoxLayout(self.samplescrollareacontents)

        # iterate through the cards, displaying their fields and data in a table widget
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

            # setting of the appearance of the table
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

            # adding the table to the layout
            self.vlayout.addWidget(table)

        # add an expanding spacer widget to the layout if the tables do not fill the window/scroll area
        self.vlayout.addSpacerItem(QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def toggledeckadded(self):
        # either creates/removes a connection between the user and the selected deck in the database
        con = sqlite3.connect(database)
        cur = con.cursor()

        # if the deck is not in their library, create a connection to the deck in the link table and assign the user's
        # default config to the deck
        if not self.checkifinlibrary():
            cur.execute("""SELECT MIN(id) FROM configs
                    WHERE uid = ?""", (self.user.id,))
            cfgid = cur.fetchone()[0]
            cur.execute("""INSERT INTO user_decks (deck_id, uid, config_id) VALUES (?, ?, ?)""",
                        (self.deck.did, self.user.id, cfgid))

            # fetch the cards in the deck
            cur.execute("""SELECT c.id FROM cards c WHERE c.deck_id = ?""", (self.deck.did,))
            cids = cur.fetchall()

            # for each card check if the user already has an exisiting 'link' to it
            for cid in cids:
                cid = cid[0]
                cur.execute("""SELECT id FROM user_cards WHERE cid = ? AND uid = ?""", (cid, self.user.id))

                # if there is no user-card entry, create one
                if not cur.fetchone():
                    cur.execute("""INSERT INTO user_cards (uid, cid, ivl, type, status, reps, lapses, odue, left)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (self.user.id, cid, None, 0, 0, 0, 0, time(), 0))

            # change the text of the add/remove button to remove
            self.addbutton.setText("Remove")

        # if the deck is already in their library - delete the deck connection
        else:
            cur.execute("""DELETE FROM user_decks WHERE deck_id = ? AND uid = ?""", (self.deck.did, self.user.id))

            # set the button text to add
            self.addbutton.setText("Add")

        con.commit()
        cur.close()
        con.close()

    def checkifinlibrary(self):
        # checks if the window's deck has been added to the user's library
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""SELECT id FROM user_decks ud WHERE ud.uid = ? AND ud.deck_id = ?""",
                    (self.user.id, self.deck.did))
        exists = cur.fetchone() is not None
        return exists


#############################


def resetstack(stack):
    """
    used after navigating away from any of the main 5 pages - clears all widgets besides the main windows
    """
    for i in range(stack.count() - 8):
        widget = stack.widget(8)
        stack.removeWidget(widget)
        widget.deleteLater()


# functions which change the index of the stack to navigate to the desired window
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
    # connects the passed windows navigation buttons to the appropriate functions
    window.decks.clicked.connect(lambda: gotodecks(stack))
    window.add.clicked.connect(lambda: gotoadd(stack))
    window.cards.clicked.connect(lambda: gotocards(stack))
    window.stats.clicked.connect(lambda: gotostats(stack))
    window.browse.clicked.connect(lambda: gotobrowse(stack))


def converttime(seconds, full=False):
    # convert a time in seconds to the largest possible unit
    # todo, possible issue in time conversion, think it is flooring
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


# Hard coded to better understand the mechanisms behind the hash function - could add salting
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


# right rotate used in the hash function
def right_rotate(num, shift, size=32):
    return (num >> shift) | (num << size - shift)


def regexp(expr, item):
    """
    A function to be used in filtering and retrieving published decks (or other database items), matching the user's
     input to fields in the database
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
