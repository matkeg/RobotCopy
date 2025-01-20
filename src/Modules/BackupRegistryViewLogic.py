# Logic related to the Backup Registry View, such as fetching registered backups, button functionality, modification, etc...
# Author: https://github.com/matkeg
# Date: January 12th 2025

import os
import json

from typing import Optional, List
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor


from .BackupLogic import *
from .AppDataLogic import load_data, StorageFolder, FileType, get_storage_folder_path
from .Utils import error, warn
from .QtUtils import *

# ------------------------------------------------------------------------------------ #

def getRegisteredBackups() -> List[BackupScheduleData]:
    """Fetches the list of registered backups from the storage."""
    backups = []
    try:
        backups_folder = get_storage_folder_path(StorageFolder.BACKUPS)
        for filename in os.listdir(backups_folder):
            file_path = os.path.join(backups_folder, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
                backups.append(BackupScheduleData.from_dict(backup_data))
    except Exception as e:
        error(f"Error fetching registered backups: {e}", "getRegisteredBackups Error")
    return backups

# ------------------------------------------------------------------------------------ #

class BackupRegistryPopulationWorker(QThread):
    """Worker thread for fetching backup data and populating the backup registry view."""
    finished = pyqtSignal()
    status_update = pyqtSignal(str)
    backup_data = pyqtSignal(list)

    def run(self):
        """Main method that runs in the thread."""
        self.status_update.emit("Fetching registered backups...")
        try:
            backups_data = getRegisteredBackups()
            self.backup_data.emit(backups_data)
            self.finished.emit()
        except Exception as e:
            error(str(e), "Backup Registry Population Error")
            self.finished.emit()

def populateBackupRegistryView(mainWindow: QMainWindow, treeWidget: QTreeWidget):
    """
    Populates the Backup Registry View by fetching and displaying backup data in a separate thread.
    """
    
    # Start updating the backup registry view by firstly clearing the treeWidget.
    treeWidget.clear()

    def handleItemSelection():
        selectedItems = treeWidget.selectedItems()
        selectedItem = selectedItems[0] if selectedItems else None
        if selectedItem is None:
            return
        
        associatedEntry: BackupScheduleData = selectedItem.data(0, 32)
        
        if associatedEntry is None:
            warn("No entry data is associated with this QTreeWidgetItem.")
        else:
            # Display backup details in the main window
            setUnsecureText(mainWindow, "InsightsBackupName", 
                            f"""
                            <html><head/><body><p><span style=" font-weight:600;">{associatedEntry.friendly_name}</span></p></body></html>
                            """
            )
            
            setUnsecureText(mainWindow, "InsightsBackupLocations",
                            f"""
                            <html><head/><body><p><span style=" color:#a5a5a5;">From: </span>{associatedEntry.origin_folder}<br/>
                            <span style=" color:#a3a3a3;">To: </span>{associatedEntry.destination_folder}</p></body></html> 
                            """
            )

            initiation_at = "Never"
            if associatedEntry.initiation_type == BackupTriggerType.STARTUP:
                initiation_at = "At Startup"
            elif associatedEntry.initiation_type == BackupTriggerType.SCHEDULED:
                initiation_at = "On a Schedule"
            elif associatedEntry.initiation_type == BackupTriggerType.USER_LOGON:
                initiation_at = "At current user's Logon"
            setUnsecureText(mainWindow, "InsightsBackupBasicInfo",
                            f"""
                            <html><head/><body><p><span style=" color:#a5a5a5;">Triggered On: </span>{initiation_at}<br/>
                            <span style=" color:#a3a3a3;">Last Backup: </span>--/--/---- --:-- --</p></body></html> 
                            """
            )

    def updateTreeView(backups_data):
        """Updates the tree view with the processed backup data."""
        treeWidget.clear()
        
        for entry in backups_data:
            # Make the initiation type readable for the user.
            initiation_at = "NEVER"
            if entry.initiation_type == BackupTriggerType.STARTUP:
                initiation_at = "STARTUP"
            elif entry.initiation_type == BackupTriggerType.SCHEDULED:
                initiation_at = "SCHEDULE"
            elif entry.initiation_type == BackupTriggerType.USER_LOGON:
                initiation_at = "LOGON"

            # Create the new tree entry
            newTreeEntry = QTreeWidgetItem(
                treeWidget, 
                [
                    entry.friendly_name, 
                    get_last_two_subfolders(entry.origin_folder), 
                    get_last_two_subfolders(entry.destination_folder), 
                    initiation_at]
            )
            newTreeEntry.setData(0, 32, entry)
            newTreeEntry.setIcon(0, QIcon("src/Interface/Icons/Folders/linked.ico"))

    # Currently not used.
    #def updateStatus(message: str):
    #    """Updates the status label with the current operation."""
    #    setUnsecureText(mainWindow, "statusText", message)
    #    findObject(mainWindow, "statusLabel").show()

    def onPopulationFinished():
        """Cleanup after population is complete."""
        #findObject(mainWindow, "statusLabel").hide()
        worker.deleteLater()

    # Create and set up the worker thread
    worker = BackupRegistryPopulationWorker()
    #worker.status_update.connect(updateStatus)
    worker.backup_data.connect(updateTreeView)
    worker.finished.connect(onPopulationFinished)
    
    # Set up item selection handling
    treeWidget.itemSelectionChanged.connect(handleItemSelection)
    
    # Start the worker thread
    worker.start()

