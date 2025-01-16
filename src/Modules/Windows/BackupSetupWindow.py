# Provides access and logic to the backup setup window.
# Author: https://github.com/matkeg
# Date: January 5th 2025

# PyQt5 Libraries
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QPushButton, QLineEdit, QWidget
from PyQt5.QtCore import pyqtSignal
from typing import Optional

# Asset Resources and Utilities
from src.Modules.QtUtils import *
from src.Features.fetcher import *
from src.Modules.FileSystemUtils import *

# Windows
from src.Modules.Windows.BackupSchedulerWindow import BackupSchedulerWindow

# Backup Logic
from ..BackupLogic import *
from ..AppDataLogic import *
from ..FileSystemUtils import arePathsTheSame


# ------------------------------------------------------------------------------------ #

class BackupSetupWindow(QMainWindow):
    currentDataUpdated = pyqtSignal()

    CurrentBackupData = {
        "friendly_name": None,

        "origin_folder": None,
        "destination_folder": None,

        "initiation_type": None,
                
        "start_time": None,

        "recurrence_type": None,
        "recurrence_step": None,
        "recurrence_step_unit": None,

        "week_init_days": None,
    }

    def __init__(self, windowAction: Optional[BackupSetupAction] = BackupSetupAction.SETUP_ONE_TIME, existingData: Optional[BackupScheduleData] = None):
        super().__init__()
        # Load the .ui file
        loadUi(
            FFlag("BackupSetupPath") or 
            "src/Interface/BackupSetup.ui",
            True, self    
        )

        self.currentDataUpdated.connect(lambda: print(self.CurrentBackupData))

        # --- HANDLE WINDOW ACTION ---------------- #
        triggerGroup: QGroupBox = findObject(self, "TriggerGroup")

        if windowAction is BackupSetupAction.REGISTER:
            self.setWindowTitle("Register Backup")
            triggerGroup.setEnabled(True)

        if windowAction is BackupSetupAction.SETUP_ONE_TIME:
            self.setWindowTitle("Setup One-Time Backup")
            triggerGroup.setEnabled(False)

        elif windowAction is BackupSetupAction.EDIT:
            self.setWindowTitle("Edit Backup")
            triggerGroup.setEnabled(False)
            self.setExistingData(existingData)

        # --- DIALOG ACTIONS ---------------------- #
        def handleDialogButtons(button):
            clickedRole = self.dialogButtons.buttonRole(button)
            if clickedRole == QDialogButtonBox.ResetRole:
                self.setExistingData(existingData)

            elif clickedRole == QDialogButtonBox.AcceptRole:
                self.attemptDataCollectionAndSubmit()

            elif clickedRole == QDialogButtonBox.RejectRole:
                self.close()

        # --- SETUP CONNECTIONS AND FETCH DYNAMIC OBJECTS --- #
        self.friendlyNameInput: QLineEdit = findObject(self, "friendlyNameInput")

        fromFolderBrowse: QPushButton = findObject(self, "fromFolderLocationFileBrowser")
        fromFolderBrowse.clicked.connect(self.getOriginFolder)
        self.fromFolderLocationInput: QLineEdit = findObject(self, "fromFolderLocationInput")
        self.fromFolderLocationInput.returnPressed.connect(self.updateFolderInfo)

        toFolderBrowse: QPushButton = findObject(self, "toFolderLocationFileBrowser")
        toFolderBrowse.clicked.connect(self.getDestinationFolder)
        self.toFolderLocationInput: QLineEdit = findObject(self, "toFolderLocationInput")
        self.toFolderLocationInput.returnPressed.connect(self.updateFolderInfo)

        editTriggerButton: QPushButton = findObject(self, "EditTriggerBtn")
        editTriggerButton.clicked.connect(self.showScheduler)

        self.backupFolderCheck: QCheckBox = findObject(self, "backupSubfolder")
        self.backupFolderCheck.stateChanged.connect(self.updateFolderInfo)

        self.toFolderLocationInput: QLineEdit = findObject(self, "toFolderLocationInput")
        self.toFolderLocationInput.returnPressed.connect(self.updateFolderInfo)

        self.dialogButtons: QDialogButtonBox = findObject(self, "dialogButtons")
        self.dialogButtons.clicked.connect(handleDialogButtons)

        self.updateFolderInfo()

        # Create additional storages
        self.windows = {}

    # --------------------------------------------- #

    @staticmethod
    def inputIsInvalid(input: str | None, required_type: type | None = None) -> bool:
        """Check if input is None or if it's a string with only whitespace or empty."""
        if input is None or (isinstance(input, str) and input.strip() == ""):
            return True
        
        if required_type is not None and not isinstance(input, required_type):
            return True
        
        return False

    def attemptDataCollectionAndSubmit(self):
        debuggingEnabled = FFlag("BackupSetupOperationDebuggingEnabled") or False
        if debuggingEnabled: print("--- START OF DATA COLLECTION -------------------------------")

        # Some data must be provided, while some is optional. For required data we will prompt the
        # user and inform them that before submitting, they must provide us with said data.
        # For optional data which was not provided, a default will be assigned.

        # Update the folder info, in case a invalid path is set in the inputs.
        # This will santeize the most important inputs.
        self.updateFolderInfo()

        # First, collect the data from the window.
        self.CurrentBackupData["friendly_name"] = self.friendlyNameInput.text()
        self.CurrentBackupData["origin_folder"] = self.fromFolderLocationInput.text()
        self.CurrentBackupData["destination_folder"] = self.toFolderLocationInput.text()

        # An important check for required data.
        if self.inputIsInvalid(self.CurrentBackupData["origin_folder"], str):
            error(
                "The origin folder is not valid, please check that you've entered a "
                "correct path to the folder you'd like to backup files from and try again.",
                "Input Error"
                )
            return
        
        if self.inputIsInvalid(self.CurrentBackupData["destination_folder"], str):
            error(
                "The destination folder is not valid, please check that you've entered a "
                "correct path to the folder you'd like to store the backed-up files to and try again.",
                "Input Error"
                )
            return
        
        # Before defaulting optional data, make sure to check for irregularities.
        if len(self.CurrentBackupData["friendly_name"]) > (FFlag("BackupFriendlyNameMaxCharacters") or 80):
            error(
                "The name is too long, please make the name shorter.",
                "Data Problem"
                )
            return
        
        pathsAreSame = arePathsTheSame(self.CurrentBackupData["origin_folder"], self.CurrentBackupData["destination_folder"])
        if pathsAreSame is True :
            error(
                "The origin and destination folders refer to the same location. "
                "Please ensure that the folders are different.",
                "Data Problem"
            )
            return
        
        if arePathsUnderSameFolder(self.CurrentBackupData["origin_folder"], self.CurrentBackupData["destination_folder"]):
            error(
                "The origin and destination folders cannot be subdirectories of each other. "
                "Please ensure that the folders are not nested within one another.",
                "Data Problem"
            )
            return
        
        # Default optional values.
        if self.inputIsInvalid(self.CurrentBackupData["friendly_name"], str):
            print("The backup's name is not valid, defaulting to 'Backup'")
            self.CurrentBackupData["friendly_name"] = "Backup"

        if self.inputIsInvalid(self.CurrentBackupData["initiation_type"], int):
            print("Initiation is not valid, defaulting to 'NEVER' (0)")
            self.CurrentBackupData["initiation_type"] = BackupTriggerType.NEVER

        if self.inputIsInvalid(self.CurrentBackupData["start_time"], BackupStartTime):
            print("Start time is not valid, defaulting to 'ASAP' (0epoch)")
            self.CurrentBackupData["start_time"] = BackupStartTime()

        if self.inputIsInvalid(self.CurrentBackupData["recurrence_type"], int):
            print("Recurrence type is not valid, defaulting to 'SINGLE' (1)")
            self.CurrentBackupData["recurrence_type"] = RecurrenceType.SINGLE

        if self.inputIsInvalid(self.CurrentBackupData["recurrence_step"], int):
            print("Recurrence step is not valid, defaulting to 1")
            self.CurrentBackupData["recurrence_step"] = 1

        if self.inputIsInvalid(self.CurrentBackupData["recurrence_step_unit"], int):
            print("Recurrence step unit is not valid, defaulting to 'Days' (0)")
            self.CurrentBackupData["recurrence_step_unit"] = RecurrenceStepUnit.DAYS
        
        if self.inputIsInvalid(self.CurrentBackupData["week_init_days"], DaysOfWeek):
            print("Week initiation days is not valid, defaulting to Monday")
            self.CurrentBackupData["week_init_days"] = DaysOfWeek("Monday")
        
        if debuggingEnabled: 
            print("Data collection successful")
            print("--- DATA SAVING START --------------------------------------")
        
        backupId = get_environment_value("TotalBackups", 0) + 1
        
        scheduleData = BackupScheduleData(
            friendly_name = self.CurrentBackupData["friendly_name"],
            origin_folder = self.CurrentBackupData["origin_folder"],
            destination_folder = self.CurrentBackupData["destination_folder"],

            initiation_type = self.CurrentBackupData["initiation_type"],
            start_time = self.CurrentBackupData["start_time"],
            recurrence_type = self.CurrentBackupData["recurrence_type"],
            recurrence_step = self.CurrentBackupData["recurrence_step"],
            recurrence_step_unit = self.CurrentBackupData["recurrence_step_unit"],

            week_init_days = self.CurrentBackupData["week_init_days"]
        )

        success = save_data(
            "Backup"+str(backupId),
            scheduleData.to_dict(),
            StorageFolder.BACKUPS,
            FileType.BackupEntry
        )

        if success:
            increment_environment_value("TotalBackups", 1, 0)

            if debuggingEnabled: 
                print("Data saving successful")
                print("--- DATA PROCESSED SUCCESSFULLY ----------------------------")
        
        else:
            error("Data processing failed. Please try again.")
        
        self.close()
        

    # --------------------------------------------- #

    def handleSchedulerData(self, data: dict):
        """Handle the schedule data received from BackupSchedulerWindow."""
        # If data is None, the dialog was cancelled
        if data is None:
            return
        
        else:
            self.CurrentBackupData["initiation_type"] = data.get("initiation_type", None)
            self.CurrentBackupData["start_time"] = data.get("start_time", None)

            self.CurrentBackupData["recurrence_type"] = data.get("recurrence_type", None)
            self.CurrentBackupData["recurrence_step"] = data.get("recurrence_step", None)
            self.CurrentBackupData["recurrence_step_unit"] = data.get("recurrence_step_unit", None)

            self.CurrentBackupData["week_init_days"] = data.get("week_init_days", None)

            self.currentDataUpdated.emit()

    def showScheduler(self):
        self.windows["backupScheduler"] = BackupSchedulerWindow()
        self.windows["backupScheduler"].scheduleTransmission.connect(self.handleSchedulerData)

    # --------------------------------------------- #

    def setExistingData(self, existingData: Optional[BackupScheduleData] = None):
        # Friendly Name
        self.friendlyNameInput.setText(
            getattr(existingData, "friendly_name", "")
        )

        # Folder Inputs
        self.fromFolderLocationInput.setText(
            getattr(existingData, "origin_folder", "")
        )

        # isUsingBackupFolder will return with 2 valuable arguments.
        usingBackupsFolder, parentFolder = isUsingBackupFolder(getattr(existingData, "destination_folder", ""))
        self.toFolderLocationInput.setText(parentFolder)
        self.backupFolderCheck.setChecked(usingBackupsFolder)

    def selectDirectory(self, title: str):
        return QFileDialog.getExistingDirectory(
            parent=self,
            caption=title,
            directory="",
            options=QFileDialog.ShowDirsOnly
        )

    def getOriginFolder(self):
        self.fromFolderLocationInput.setText(
            self.selectDirectory("Select Origin Folder")
        )
        self.updateFolderInfo()

    def getDestinationFolder(self):
        self.toFolderLocationInput.setText(
            self.selectDirectory("Select Destination Folder")
        ) 
        self.updateFolderInfo()

    # --------------------------------------------- #

    def updateFolderInfo(self):
        """Sets the folder info inside the UI"""
        fromFolderData = getFolderData(self.fromFolderLocationInput, AccessType.Read)
        toFolderData = getFolderData(self.toFolderLocationInput, AccessType.Write)
        
        backupFolderSuffix = ""
        if self.backupFolderCheck.isChecked():
            backupFolderSuffix = " / Backups"

        # ---- Setting the name --------------------------------------#
        setUnsecureText(self, "fromFolderInsightsName", 
            f"""<html><head/><body><p><span style=" font-weight:600;">
            {truncateWithDots(fromFolderData.folder_name, 25)}</span></p></body></html>""")
        
        setUnsecureText(self, "toFolderInsightsName", 
            f"""<html><head/><body><p><span style=" font-weight:600;">
            {truncateWithDots(toFolderData.folder_name, 25)}{backupFolderSuffix}</span></p></body></html>""")

        # ---- Setting the general info ------------------------------#
        setUnsecureText(self, "fromFolderInsightsInfo", 
            f"""<html><head/><body><p><span style=" color:#a5a5a5;">Drive:</span> 
            {fromFolderData.drive_letter}<br/><span style=" color:#a3a3a3;">Size:</span> 
            {fromFolderData.folder_size}</p></body></html>""")
        
        setUnsecureText(self, "toFolderInsightsInfo", 
            f"""<html><head/><body><p><span style=" color:#a5a5a5;">Drive:</span> 
            {toFolderData.drive_letter}<br/><span style=" color:#a3a3a3;">Size:</span> 
            {toFolderData.folder_size}</p></body></html>""")
        
        # ---- Setting the counter info ------------------------------#
        setUnsecureText(self, "fromFolderInsightsCounter", 
            f"""<html><head/><body><p><span style=" color:#a5a5a5;">Files:</span> 
            {fromFolderData.number_of_files}<br/><span style=" color:#a3a3a3;">Folders:</span> 
            {fromFolderData.number_of_folders}</p></body></html>""")
        
        setUnsecureText(self, "toFolderInsightsCounter", 
            f"""<html><head/><body><p><span style=" color:#a5a5a5;">Files:</span> 
            {toFolderData.number_of_files}<br/><span style=" color:#a3a3a3;">Folders:</span> 
            {toFolderData.number_of_folders}</p></body></html>""")


        
    
        
