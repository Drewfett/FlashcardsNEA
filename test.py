from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QGridLayout, QPushButton, QWidget

class DeckWidget(QWidget):
    clicked = pyqtSignal()

    def __init__(self, name, description, parent=None):
        super().__init__(parent)
        self.name = name
        self.description = description

        # create the widget UI elements
        self.name_label = QPushButton(name)
        self.description_label = QPushButton(description)

        # set up the layout
        layout = QGridLayout()
        layout.addWidget(self.name_label, 0, 0)
        layout.addWidget(self.description_label, 1, 0)
        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == 1:  # left mouse button
            self.clicked.emit()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # create the grid layout
        grid_layout = QGridLayout()

        # example decks
        decks = [("Deck 1", "Description 1"), ("Deck 2", "Description 2")]

        # add each deck widget to the grid layout
        for row, (name, description) in enumerate(decks):
            deck_widget = DeckWidget(name, description)
            deck_widget.clicked.connect(self.on_deck_clicked)
            grid_layout.addWidget(deck_widget, row, 0)

        self.setLayout(grid_layout)

    def on_deck_clicked(self):
        # handle deck click event
        deck_widget = self.sender()
        print(f"Clicked {deck_widget.name}")

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()








