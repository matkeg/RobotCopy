# PyQt5 Libraries
from PyQt5.QtWidgets import *

# Asset Resources and Utilities
import src.Interface.assets
from src.Modules.QtUtils import *
from src.Modules.Utils import *
from src.Modules.DriveViewLogic import *
from src.Modules.BackupRegistryViewLogic import *
from src.Features.fetcher import *

from src.Modules.AppDataLogic import *

from src.Modules.BackupLogic import BackupTriggerType

# Windows
from src.Modules.Windows.AboutWindow import AboutWindow
from src.Modules.Windows.BackupSetupWindow import BackupSetupWindow, BackupSetupAction

# Custom widget classes
from src.Interface.Classes.QClickTreeWidget import QClickTreeWidget

from src.Modules.BackupLogic import *

# ------------------------------------------------------------------------------------ #

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load the .ui file
        loadUi(
            FFlag("MainWindowPath") or 
            "src/Interface/MainWindow.ui",
            True, self    
        )

        # Create additional storages
        self.windows = {}

        # Hide the info labels
        warningLabel = findObject(self, "warningLabel")
        statusLabel = findObject(self, "statusLabel")
        errorLabel = findObject(self, "errorLabel")
        infoLabel = findObject(self, "infoLabel")
        executeFunction("hide", infoLabel, errorLabel, warningLabel, statusLabel)

        # Set-up the tab and tree resizing logic.
        tab_widget: QTabWidget = findObject(self, "tabWidget")
        self.drive_tree: QTreeWidget = findObject(self, "DriveTree")
        self.backup_tree: QTreeWidget = findObject(self, "BackupsTree")
        
        self.backup_tree.itemSelectionChanged.connect(self.handle_backup_selection)

        # Set-up the backup registry view, button logic.
        self.actionsBackups: QListWidget = findObject(self, "actionsBackups")
        self.actionsSelection: QListWidget = findObject(self, "actionsSelection")

        self.actionsBackups.itemActivated.connect(self.on_backup_action_clicked)
        self.actionsSelection.itemActivated.connect(self.on_selection_action_clicked)
        self.actionsBackups.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.actionsSelection.setDragDropMode(QAbstractItemView.NoDragDrop)

        # Set-up the tab double-click logic.
        tab_widget.tabBarDoubleClicked.connect(self.on_tab_double_clicked)
        
        # Resize columns to fit contents by deault.
        self.on_tab_double_clicked()

        # Bind functionality to the existing QActions.  
        registerActionCallback(self, "actionSwitchView", self.switchView)
        registerActionCallback(self, "actionRefreshView", self.refreshViews)
        registerActionCallback(self, "actionPromptAppInfo", self.showAbout)

        registerActionCallback(self, "actionAddScheduledBackup", self.showBackupScheduler)
        registerActionCallback(self, "actionInitiateSingleBackup", self.showOneTimeBackup)

        # Populate the drive and backups view.
        self.refreshViews()

    # -- MAIN WINDOW FUNCTIONS & ACTIONS ---------------------------- #

    # View refreshing logic.
    def refreshViews(self):
        populateDriveView(self, self.drive_tree)
        populateBackupRegistryView(self, self.backup_tree)

    # Prompt windows
    def showAbout(self):
        #print(AboutWindow())
        self.windows["about"] = AboutWindow()    

    def showBackupScheduler(self):
        self.windows["backup_setup"] = BackupSetupWindow(
            BackupSetupAction.REGISTER,
            callback=populateBackupRegistryView,
            callbackArgs=[self, self.backup_tree]
        )

    def showOneTimeBackup(self):
        self.windows["backup_setup_once"] = BackupSetupWindow(
            BackupSetupAction.SETUP_ONE_TIME,
            callback=populateBackupRegistryView,
            callbackArgs=[self, self.backup_tree]
        )

    def showBackupEditor(self, existingData: BackupScheduleData):
        self.windows["backup_edit"] = BackupSetupWindow(
            BackupSetupAction.EDIT,
            existingData,
            callback=populateBackupRegistryView,
            callbackArgs=[self, self.backup_tree]
        )

    # View refreshing logic.
    def switchView(self):
        tab_widget = findObject(self, "tabWidget")

        current_index = tab_widget.currentIndex()
        next_index = (current_index + 1) % tab_widget.count()  # Loop back to the first tab
        tab_widget.setCurrentIndex(next_index)

    def on_backup_action_clicked(self, item):
        # Handle the backup action double-click event
        if item.isSelected():
            index = self.actionsBackups.row(item)
            if index == 0:
                self.showBackupScheduler()
            elif index == 1:
                self.showOneTimeBackup()
                
            # Unselect the item
            item.setSelected(False)

    def on_selection_action_clicked(self, item):
        # Handle the selection action double-click event
        if item.isSelected():
            # Get the selected item from the backup tree
            selected_items = self.backup_tree.selectedItems()
            if not selected_items:
                return

            selected_item = selected_items[0]
            backup_data = selected_item.data(0, 32)


            # Check if we have a valid BackupScheduleData
            if not isinstance(backup_data, BackupScheduleData):
                return

            index = self.actionsSelection.row(item)
            if index == 0:
                info(
                    "Backup manual triggering not yet implemented.", 
                    "Not Implemented"
                )
            elif index == 1:
                self.showBackupEditor(backup_data)
            elif index == 2:
                info(
                    "Backup toggling not yet implemented.", 
                    "Not Implemented"
                )
        
            elif index == 3:
                remove_result = ask(
                    "Are you sure you want to remove the selected backup?",
                    "Remove Backup",
                    AskAnswer.YES_NO
                )

                if remove_result == True:
                    remove_backup_data(backup_data.backup_id)
                    populateBackupRegistryView(self, self.backup_tree)
                else:
                    return

            # Unselect the item
            item.setSelected(False)

    # Tab resizing logic.
    def on_tab_double_clicked(self):
        self.resize_tree_columns(self.drive_tree)
        self.resize_tree_columns(self.backup_tree)

    def resize_tree_columns(self, tree_widget):
        for column in range(tree_widget.columnCount()):
            tree_widget.resizeColumnToContents(column)

    def handle_backup_selection(self):
        selected_items = self.backup_tree.selectedItems()
        if selected_items:
            self.actionsSelection.setEnabled(True)
        else:
            self.actionsSelection.setEnabled(False)

# ------------------------------------------------------------------------------------ #

if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    mainWindow = MainWindow()
    
    app.exec_()