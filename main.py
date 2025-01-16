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
        
        # Set-up the backup registry view, button logic.
        self.actionsBackups: QListWidget = findObject(self, "actionsBackups")
        self.actionsSelection: QListWidget = findObject(self, "actionsSelection")

        self.actionsBackups.itemDoubleClicked.connect(self.on_backup_action_clicked)
        self.actionsBackups.itemActivated.connect(self.on_backup_action_clicked)
        self.actionsSelection.itemDoubleClicked.connect(self.on_selection_action_clicked)
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
        self.windows["backup_setup"] = BackupSetupWindow(BackupSetupAction.REGISTER)

    def showOneTimeBackup(self):
        self.windows["backup_setup_once"] = BackupSetupWindow(BackupSetupAction.SETUP_ONE_TIME)

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
        # Handle the selection action click event
        print(f"Selection action clicked: {item.text()}")

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
    print(BackupTriggerType.STARTUP == 1)
    app = QApplication([])
    app.setStyle("Fusion")
    mainWindow = MainWindow()
    mainWindow.backup_tree.itemSelectionChanged.connect(mainWindow.handle_backup_selection)
    
    app.exec_()