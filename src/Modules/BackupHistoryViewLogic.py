# Logic related to the Backup History View, such as fetching backup history, binding data to the view, etc...
# Author: https://github.com/matkeg
# Date: January 19th 2025

import os
import json

from typing import Optional, List
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from concurrent.futures import ThreadPoolExecutor


from .BackupLogic import *
from .AppDataLogic import load_data, save_data, StorageFolder, FileType, get_storage_folder_path
from .Utils import error, warn
from .QtUtils import *

# ------------------------------------------------------------------------------------ #

def saveBackupHistory(history: List[BackupHistoryData]) -> bool:
    """Saves the backup history to a JSON file."""
    try:
        history_data = [entry.to_dict() for entry in history]
        return save_data("backup_history", history_data, StorageFolder.LOGS, FileType.JSON)
    except Exception as e:
        error(f"Error saving backup history: {e}", "saveBackupHistory Error")
        return False

def loadBackupHistory() -> List[BackupHistoryData]:
    """Loads the backup history from a JSON file."""
    try:
        history_data = load_data("backup_history", StorageFolder.LOGS, silent=True) or []
        return [BackupHistoryData.from_dict(entry) for entry in history_data]
    except Exception as e:
        error(f"Error loading backup history: {e}", "loadBackupHistory Error")
        return []

def addBackupHistoryEntry(entry: BackupHistoryData) -> bool:
    """Adds a new entry to the backup history."""
    history = loadBackupHistory()
    history.append(entry)
    return saveBackupHistory(history)

def clearBackupHistory() -> bool:
    """Clears the backup history."""
    return saveBackupHistory([])

# ------------------------------------------------------------------------------------ #

def populateBackupHistoryView(tree_widget: QTreeWidget):
    """Populates the QTreeWidget with backup history data."""
    tree_widget.clear()
    history = loadBackupHistory()
    for entry in history:
        item = QTreeWidgetItem([
            entry.backup_name,
            entry.backup_time.toString('M/d/yyyy h:mm AP'),
            get_last_two_subfolders(entry.origin_folder),
            get_last_two_subfolders(entry.destination_folder),
            BackupOperationGroup.represent(entry.operation_group),
            BackupOperationResult.represent(entry.operation_result, True)
        ])

        item.setData(0, 32, entry)

        icon = QIcon("src/Interface/Icons/FolderUp.ico")
        if entry.operation_result == BackupOperationResult.SUCCESS:
            item.setIcon(0, icon)
        else:
            disabled_icon = QIcon(icon.pixmap(16, 16, QIcon.Disabled))
            item.setIcon(0, disabled_icon)
            # Set the background color to a slight red for unsuccessful backups
            for i in range(item.columnCount()):
                item.setBackground(i, QColor(255, 220, 220))  # Light red color

        tree_widget.addTopLevelItem(item)
            

def displayBackupProperties(tree_widget: QTreeWidget, properties_widget: QTreeWidget):
    """Displays the properties of the selected backup history entry."""
    selected_items = tree_widget.selectedItems()
    if not selected_items:
        return

    selected_item = selected_items[0]
    entry: BackupHistoryData = selected_item.data(0, 32)

    properties_widget.clear()
    properties = [
        ("Friendly Name", entry.backup_name),
        ("Origin Path", entry.origin_folder),
        ("Destination Path", entry.destination_folder),
        ("Date and Time", entry.backup_time.toString('M/d/yyyy h:mm AP')),
        ("Operation Group", BackupOperationGroup.represent(entry.operation_group)),
        ("Operation Result", BackupOperationResult.represent(entry.operation_result))
    ]

    for prop, value in properties:
        prop_item = QTreeWidgetItem([prop, value])
        properties_widget.addTopLevelItem(prop_item)
