# A custom subclass of the QTreeWidget which prevents items from being selected while 
# the mouse is pressed and hovering over items. Additionally, it adds keyboard arrow navigation.

# CHANGINIG THE LOCATION OF THIS FILE CAN CAUSE CRITICAL ERRORS, BE SURE TO ALSO MODIFY THE
# PROMOTED CLASS INSIDE QT DESIGNER (MainWindow.ui) FILE AND CHANGE THE IMPORTS INSIDE THE CODE.

# Author: https://github.com/matkeg
# Date: December 9th 2024

from PyQt5.QtWidgets import QTreeWidget, QAbstractItemView
from PyQt5.QtGui import QMouseEvent, QKeyEvent
from PyQt5.QtCore import Qt

from src.Features.fetcher import *

# ------------------------------------------------------------------------------------ #

def changeStyle(widget: QTreeWidget):
    widget.setSelectionMode(QAbstractItemView.NoSelection)

    widget.setStyleSheet("""
        QTreeWidget::item:!selected:focus {
            background: transparent;             
            border: none;
            outline: none;
        }                   
    """)

# ------------------------------------------------------------------------------------ #

class QClickTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set initial selection mode and focus policy
        changeStyle(self)

    def showEvent(self, event):
        if self.selectionMode() != 0:
            # If selection mode is not 0, change the style.
            changeStyle(self)

            if FFlag("QClickTreeWidgetDebuggingEnabled") is True:
                print(f"Changed style for object: {self.objectName()}")
                print(f"Set selection mode during showEvent: {self.selectionMode()}")
                print(f"Set focus policy during showEvent: {self.focusPolicy()}")

        super().showEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        # Get the item under the mouse
        item = self.itemAt(event.pos())
        
        if item:
            # Deselect other items
            for i in range(self.topLevelItemCount()):
                self.topLevelItem(i).setSelected(False)

            # Select the item
            item.setSelected(True)
            # Update the current item based on selection
            self.setCurrentItem(item)

        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        # Get the currently selected item
        selected_item = None
        for i in range(self.topLevelItemCount()):
            if self.topLevelItem(i).isSelected():
                selected_item = self.topLevelItem(i)
                break

        if selected_item:
            current_index = self.indexOfTopLevelItem(selected_item)

            # Navigate up or down
            if event.key() == Qt.Key_Up:
                if current_index > 0:
                    # Deselect the current item
                    selected_item.setSelected(False)

                    # Select the previous item
                    new_item = self.topLevelItem(current_index - 1)
                    new_item.setSelected(True)
                    self.setCurrentItem(new_item)

            elif event.key() == Qt.Key_Down:
                if current_index < self.topLevelItemCount() - 1:
                    # Deselect the current item
                    selected_item.setSelected(False)

                    # Select the next item
                    new_item = self.topLevelItem(current_index + 1)
                    new_item.setSelected(True)
                    self.setCurrentItem(new_item)

        else:
            # If no item is selected, select the first item
            if self.topLevelItemCount() > 0:
                first_item = self.topLevelItem(0)
                first_item.setSelected(True)
                self.setCurrentItem(first_item)

        event.accept()
