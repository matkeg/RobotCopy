# Qt Utility Python module for use in Qt applications.
# Author: https://github.com/matkeg
# Date: December 8th 2024

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QObject
from PyQt5 import uic

from typing import Optional, Callable
from .Utils import *

import json

# ------------------------------------------------------------------------------------ #

class textMode():
    RAW = "RAW",
    JSON = "JSON"


def setLabelTextAdvanced(parent: QWidget, targetTextObject: str, mode: textMode, value: str):
    """
    Attempts to find the object specified and attempts to set its text property to either 
    the text passed with RAW textMode or looks for an text entry in a `prompts.JSON` file under the provided entry.
    """

    # While functional, and being used, this function is not fully implemented.

    text = None
    if mode == textMode.JSON:
        with open("src/JSON/prompts.json", "r", encoding="utf-8") as jsonFile:
            data = json.load(jsonFile)
            text = data[value]
    else:
        text = value

    if text is not None:
        textObject: QLabel = findObject(parent, targetTextObject)
        if (textObject is not None) and hasProperty(textObject, "text"):
            textObject.setText(text) 
        else:
            error(
                "Can't set text for the found object "+str(textObject)+" ("+str(attemptToGetObjectName(textObject))+") because it does not have the text property. Are we referencing the right object?",
                "setUnsecureText Error"
                )
    else:
        error(
                "Can't set text for the found object "+str(textObject)+" ("+str(attemptToGetObjectName(textObject))+") because an proper text value cannot be found. Are we referencing the right JSON entry?",
                "setTextAdvanced Error"
                )
    
# ------------------------------------------------------------------------------------ #

def setLabelText(object: QWidget, text: str, showOnChange: Optional[bool] = False):
    """Sets the text of the object's child whose name ends in "Text". """

    for child in object.findChildren(QWidget): 
        if child.objectName().endswith("Text"):
            if isinstance(child, QLabel):  # Make sure it's a QLabel
                child.setText(text) 
                # Check wether showOnChange is passed.
                if showOnChange is True:
                    object.show()

            break


# ------------------------------------------------------------------------------------ #

def addQTreeItem(tree: QTreeWidget, data_dict: dict):
    column_count = tree.columnCount()
    data_values = list(data_dict.values())
    
    # Check if there are fewer or more values than columns in the tree
    if len(data_values) < column_count:
        data_values.extend([''] * (column_count - len(data_values)))
        print(f"addQTreeItem() warning: Less data than columns, added blank data for the missing columns.")
        
    elif len(data_values) > column_count:
        data_values = data_values[:column_count]
        print(f"addQTreeItem() warning: More data than columns, extra data ignored.")
    
    # Create the QTreeWidgetItem with the values
    item = QTreeWidgetItem(data_values)
    
    # Add the item to the tree widget
    tree.addTopLevelItem(item)

# ------------------------------------------------------------------------------------ #

def registerActionCallback(context: QWidget, action_name: str, function: Callable) -> QObject | None:
    """Attempts to find the action in the current context, using its name, and if successful, registers the passed function as the action's callback."""
    
    # Find the action.
    action = findAction(context, action_name)
    
    if action:
        # Register the action.
        action.triggered.connect(function)

        return action.triggered
    else:
        error(
            "Can't find action '"+str(action_name)+"' in the passed context '"+str(context)+"'.",
            "registerActionCallback Error"
        )
    

# ------------------------------------------------------------------------------------ #

def findObject(parent: QWidget, objectName: str) -> (QWidget | None):
    """
    Attempts to find a object that is a descendant of the passed parent.
    Acts as an wrapper function for `QWidget.findChild()` method.
    """

    if hasattr(parent, "findChild"):
        return parent.findChild(QWidget, objectName)
    else:
        error(
            "Can't find '"+str(objectName)+"' because the passed parent '"+str(parent)+"' does not have the `findChild` method.",
            "findObject Error"
            )
        
# ------------------------------------------------------------------------------------ #

def findAction(parent: QWidget, actionName: str) -> (QAction | None):
    """
    Attempts to find a object that is a descendant of the passed parent.
    Acts as an wrapper function for `QWidget.findChild()` method.
    """

    if hasattr(parent, "findChild"):
        return parent.findChild(QAction, actionName)
    else:
        error(
            "Can't find '"+str(actionName)+"' because the passed parent '"+str(parent)+"' does not have the `findChild` method.",
            "findObject Error"
            )       

# ------------------------------------------------------------------------------------ #

def setUnsecureText(parent: QWidget, targetTextObject: str, text: Optional[str] = "Text"):
    """Attempts to find the object specified and attempts to set its text property to the passed text."""

    textObject: QLabel = findObject(parent, targetTextObject)
    if (textObject is not None) and hasProperty(textObject, "text"):
        textObject.setText(text) 
    else:
         error(
            "Can't set text for the found object "+str(textObject)+" ("+str(attemptToGetObjectName(textObject))+") because it does not have the text property. Are we referencing the right object?",
            "setUnsecureText Error"
            )
    

# ------------------------------------------------------------------------------------ #

def setUnsecurePixmap(parent: QWidget, targetPixmapObject: str, image: QPixmap | QIcon):
    """Attempts to find the object specified and attempts to set its pixmap (image) property to the passed pixmap (image)."""

    # Attempt to find the target object.
    pixmapObject: QLabel = findObject(parent, targetPixmapObject)

    # We will convert an QIcon to a QPixmap.
    if isinstance(image, QIcon):
        image = image.pixmap(pixmapObject.width(), pixmapObject.height(), QIcon.Normal, QIcon.On)

    # Main operation
    if isinstance(image, QPixmap):
        if (pixmapObject is not None) and hasProperty(pixmapObject, "pixmap"):
            pixmapObject.setPixmap(image)    
        else:
            error(
                "Can't set pixmap for the found object "+str(pixmapObject)+" ("+str(attemptToGetObjectName(pixmapObject))+") because it does not have the pixmap property. Are we referencing the right object?",
                "setUnsecurePixmap Error"
                )
    else:
        error(
                "Can't set pixmap for the found object "+str(pixmapObject)+" ("+str(attemptToGetObjectName(pixmapObject))+") because the passed image property is not a QPixmap.",
                "setUnsecurePixmap Error"
                )
         
# ------------------------------------------------------------------------------------ #

def loadUi(uiPath: str, showOnLoad: Optional[bool] = False, parent: Optional[QWidget] = None):
    """Attempts to load a window from a `.ui` file, given the `.ui` file path is passed."""
    try:
        # Load the UI into the provided parent (e.g., self for MainWindow)
        uic.loadUi(uiPath, parent)

        if showOnLoad:
            parent.show()  # Show the UI window if showOnLoad is True

    except FileNotFoundError:
        error(f"Error: The file '{uiPath}' was not found.", "Critical Error")
    except Exception as e:
        error(f"An error occurred while loading the UI: {e}", "Critical Error")

# ------------------------------------------------------------------------------------ #