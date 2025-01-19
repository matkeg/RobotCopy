# Provides access and logic to the backup setup window.
# Author: https://github.com/matkeg
# Date: January 5th 2025

# PyQt5 Libraries
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QPushButton, QLineEdit, QWidget, QTreeWidgetItem
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
from ..FileSystemUtils import arePathsTheSame, isUsingBackupFolder


# ------------------------------------------------------------------------------------ #

class BackupSetupWindow(QMainWindow):
    currentDataUpdated = pyqtSignal()

    CurrentBackupData = {
        "friendly_name": None,

        "origin_folder": None,
        "destination_folder": None,
        "uses_backups_subfolder": False,

        "initiation_type": 0,
                
        "start_time": None,

        "recurrence_type": None,
        "recurrence_step": None,
        "recurrence_step_unit": None,

        "week_init_days": None,

        "backup_id": None
    }

    def __init__(self, windowAction: Optional[BackupSetupAction] = BackupSetupAction.SETUP_ONE_TIME, existingData: Optional[BackupScheduleData] = None, callback: Optional[callable] = None, callbackArgs: Optional[list] = None):
        super().__init__()
        self.callback = callback
        self.callbackArgs = callbackArgs or []
        
        # Load the .ui file
        loadUi(
            FFlag("BackupSetupPath") or 
            "src/Interface/BackupSetup.ui",
            True, self    
        )

        # --- DIALOG ACTIONS ---------------------- #
        def handleDialogButtons(button):
            clickedRole = self.dialogButtons.buttonRole(button)
            if clickedRole == QDialogButtonBox.ResetRole:
                self.setExistingData(existingData)

            elif clickedRole == QDialogButtonBox.AcceptRole:
                self.attemptDataCollectionAndSubmit(windowAction)

            elif clickedRole == QDialogButtonBox.RejectRole:
                self.close()

        # --- SETUP CONNECTIONS AND FETCH DYNAMIC OBJECTS --- #
        self.friendlyNameInput: QLineEdit = findObject(self, "friendlyNameInput")

        fromFolderBrowse: QPushButton = findObject(self, "fromFolderLocationFileBrowser")
        fromFolderBrowse.clicked.connect(self.getOriginFolder)
        self.fromFolderLocationInput: QLineEdit = findObject(self, "fromFolderLocationInput")
        self.fromFolderLocationInput.returnPressed.connect(self.updateCurrentData)

        toFolderBrowse: QPushButton = findObject(self, "toFolderLocationFileBrowser")
        toFolderBrowse.clicked.connect(self.getDestinationFolder)
        self.toFolderLocationInput: QLineEdit = findObject(self, "toFolderLocationInput")
        self.toFolderLocationInput.returnPressed.connect(self.updateCurrentData)

        editTriggerButton: QPushButton = findObject(self, "EditTriggerBtn")
        editTriggerButton.clicked.connect(self.showScheduler)

        self.backupFolderCheck: QCheckBox = findObject(self, "backupSubfolder")
        self.backupFolderCheck.stateChanged.connect(self.updateCurrentData)

        self.toFolderLocationInput: QLineEdit = findObject(self, "toFolderLocationInput")
        self.toFolderLocationInput.returnPressed.connect(self.updateCurrentData)

        self.dialogButtons: QDialogButtonBox = findObject(self, "dialogButtons")
        self.dialogButtons.clicked.connect(handleDialogButtons)

        self.triggerInfoTree: QTreeWidget = findObject(self, "triggerInfoTree")

        # --- SETUP DATA UPDATE SIGNAL ------------ #
        self.currentDataUpdated.connect(self.updateUiData)

        # --- SETUP BACKUP ID --------------------- #
        if existingData is not None and existingData.backup_id is not None:
            self.CurrentBackupData["backup_id"] = existingData.backup_id
            self.currentDataUpdated.emit()

        # --- HANDLE WINDOW ACTION ---------------- #
        triggerGroup: QGroupBox = findObject(self, "TriggerGroup")

        if windowAction is BackupSetupAction.REGISTER:
            self.setWindowTitle("Register Backup")
            triggerGroup.setEnabled(True)

            setUnsecureText(self, "header_tip_text", 
                """
                <html><head/><body><p>
                <span style=" font-size:10pt; font-weight:600;">New Backup</span><br/>
                <span style=" font-size:9pt;">Select two folders: one as the source of the files to be backed up and another as the backup destination.<br/>For better reliability, the source and destination folders should be located on different storage devices.
                </span></p></body></html>
                """
            )

        if windowAction is BackupSetupAction.SETUP_ONE_TIME:
            self.setWindowTitle("Setup One-Time Backup")
            triggerGroup.setEnabled(False)

            setUnsecureText(self, "header_tip_text", 
                """
                <html><head/><body><p>
                <span style=" font-size:10pt; font-weight:600;">New One-Time Backup</span><br/>
                <span style=" font-size:9pt;">Select two folders: one as the source of the files to be backed up and another as the backup destination.<br/>This backup will only run once and won't be registered in the Backup Registry.
                </span></p></body></html>
                """
            )

        elif windowAction is BackupSetupAction.EDIT:
            self.setWindowTitle("Edit Backup")
            triggerGroup.setEnabled(True)
            self.setExistingData(existingData)

            setUnsecureText(self, "header_tip_text", 
                """
                <html><head/><body><p>
                <span style=" font-size:10pt; font-weight:600;">Edit Backup</span><br/>
                <span style=" font-size:9pt;">Select two folders: one as the source of the files to be backed up and another as the backup destination.<br/>For better reliability, the source and destination folders should be located on different storage devices.
                </span></p></body></html>
                """
            )

        # Create additional storages
        self.windows = {}

    # --------------------------------------------- #

    def updateCurrentData(self):
        """Updates the current backup data."""
        # Collect the data from the window.
        self.CurrentBackupData["friendly_name"] = self.friendlyNameInput.text()
        self.CurrentBackupData["origin_folder"] = self.fromFolderLocationInput.text()
        self.CurrentBackupData["destination_folder"] = self.toFolderLocationInput.text()

        # If backupFolderCheck is checked, add /Backups to the destination folder path.
        self.CurrentBackupData["uses_backups_subfolder"] = self.backupFolderCheck.isChecked()

        # Emit the dataUpdated signal to update the UI
        self.currentDataUpdated.emit()

    # --------------------------------------------- #

    @staticmethod
    def inputIsInvalid(input: str | None, required_type: type | None = None) -> bool:
        """Check if input is None or if it's a string with only whitespace or empty."""
        if input is None or (isinstance(input, str) and input.strip() == ""):
            return True
        
        if required_type is not None and not isinstance(input, required_type):
            return True
        
        return False

    def attemptDataCollectionAndSubmit(self, windowAction: Optional[BackupSetupAction] = BackupSetupAction.REGISTER):
        debuggingEnabled = FFlag("BackupSetupOperationDebuggingEnabled") or False
        if debuggingEnabled: print("--- START OF DATA COLLECTION -------------------------------")

        # Some data must be provided, while some is optional. For required data we will prompt the
        # user and inform them that before submitting, they must provide us with said data.
        # For optional data which was not provided, a default will be assigned.

        # Update the folder info, in case a invalid path is set in the inputs.
        # This will santeize the most important inputs.
        self.updateFolderInfo()

        # Update the current data with the latest inputs.
        self.updateCurrentData()

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
        
        if arePathsTheSame(self.CurrentBackupData["origin_folder"], self.CurrentBackupData["destination_folder"]):
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
        
         # Find the appropriate backup id for the backup.
        backupId = get_environment_value("TotalBackups", 0) + 1
        if self.CurrentBackupData["backup_id"] is not None: 
            backupId = self.CurrentBackupData["backup_id"]


        # Final construction, construct the desired destination folder.
        destination_folder_path = self.CurrentBackupData["destination_folder"]
        if self.CurrentBackupData["uses_backups_subfolder"]:
            destination_folder_path = os.path.join(
            self.CurrentBackupData["destination_folder"], "Backups"
            )

        scheduleData = BackupScheduleData(
            friendly_name = self.CurrentBackupData["friendly_name"],
            origin_folder = os.path.normpath(self.CurrentBackupData["origin_folder"]),
            destination_folder = destination_folder_path,

            initiation_type = self.CurrentBackupData["initiation_type"],
            start_time = self.CurrentBackupData["start_time"],
            recurrence_type = self.CurrentBackupData["recurrence_type"],
            recurrence_step = self.CurrentBackupData["recurrence_step"],
            recurrence_step_unit = self.CurrentBackupData["recurrence_step_unit"],

            week_init_days = self.CurrentBackupData["week_init_days"],

            backup_id = backupId
        )

        # Based on which backup setup action is provided, we will send the data accordingly.
        print(windowAction)
        success = False
        if windowAction is BackupSetupAction.REGISTER or windowAction is BackupSetupAction.EDIT:
            success = edit_data(
                "backup"+str(backupId),
                scheduleData.to_dict(),
                StorageFolder.BACKUPS,
                FileType.BackupEntry
            )

        elif windowAction is BackupSetupAction.SETUP_ONE_TIME:
            # TODO: Implement one-time backup logic
            success = False
            
        if success:
            increment_environment_value("TotalBackups", 1, 0)

            if debuggingEnabled: 
                print("Data saving successful")
                print("--- DATA PROCESSED SUCCESSFULLY ----------------------------")
            
            # Execute the callback function if provided
            if self.callback:
                self.callback(*self.callbackArgs)
        
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
            self.CurrentBackupData["initiation_type"] = data.get("initiation_type", 0)
            self.CurrentBackupData["start_time"] = data.get("start_time", None)

            self.CurrentBackupData["recurrence_type"] = data.get("recurrence_type", None)
            self.CurrentBackupData["recurrence_step"] = data.get("recurrence_step", None)
            self.CurrentBackupData["recurrence_step_unit"] = data.get("recurrence_step_unit", None)

            self.CurrentBackupData["week_init_days"] = data.get("week_init_days", None)

            self.currentDataUpdated.emit()

    def showScheduler(self):
        # Update the current data before showing the scheduler this will
        # prevent data resets if the user hasn't updated the data
        # (pressed enter on inputs) before showing the scheduler.
        self.updateCurrentData()

        # Show the scheduler window
        self.windows["backupScheduler"] = BackupSchedulerWindow(
            ScheduleData(
                self.CurrentBackupData["initiation_type"],
                self.CurrentBackupData["start_time"],
                self.CurrentBackupData["recurrence_type"],
                self.CurrentBackupData["recurrence_step_unit"],
                self.CurrentBackupData["recurrence_step"],
                self.CurrentBackupData["week_init_days"]
            )
        )
        self.windows["backupScheduler"].scheduleTransmission.connect(self.handleSchedulerData)

    # --------------------------------------------- #

    def translateToBackupScheduleDataClass(self) -> BackupScheduleData:
        """Translate the current data to a BackupScheduleData class."""
        return BackupScheduleData(
            self.CurrentBackupData.get("friendly_name", ""),
            self.CurrentBackupData.get("origin_folder", ""),
            self.CurrentBackupData.get("destination_folder", ""),
            self.CurrentBackupData.get("initiation_type", 0),
            self.CurrentBackupData.get("start_time", BackupStartTime()),
            self.CurrentBackupData.get("recurrence_type", RecurrenceType.SINGLE),
            self.CurrentBackupData.get("recurrence_step", 1),
            self.CurrentBackupData.get("recurrence_step_unit", RecurrenceStepUnit.DAYS),
            self.CurrentBackupData.get("week_init_days", DaysOfWeek("Monday")),
            self.CurrentBackupData.get("backup_id", None)
        )

    # --------------------------------------------- #

    def setExistingData(self, existingData: Optional[BackupScheduleData] = None):
        # Update CurrentBackupData dictionary
        self.CurrentBackupData["friendly_name"] = getattr(existingData, "friendly_name", None)
        self.CurrentBackupData["origin_folder"] = getattr(existingData, "origin_folder", None)

        self.CurrentBackupData["destination_folder"] = getattr(existingData, "destination_folder", None)
        uses_backups_subfolder, parent_folder = isUsingBackupFolder(self.CurrentBackupData["destination_folder"])
        self.CurrentBackupData["uses_backups_subfolder"] = uses_backups_subfolder
        if uses_backups_subfolder:
            self.CurrentBackupData["destination_folder"] = parent_folder

        self.CurrentBackupData["initiation_type"] = getattr(existingData, "initiation_type", 0)
        self.CurrentBackupData["start_time"] = getattr(existingData, "start_time", None)
        self.CurrentBackupData["recurrence_type"] = getattr(existingData, "recurrence_type", None)
        self.CurrentBackupData["recurrence_step"] = getattr(existingData, "recurrence_step", None)
        self.CurrentBackupData["recurrence_step_unit"] = getattr(existingData, "recurrence_step_unit", None)
        self.CurrentBackupData["week_init_days"] = getattr(existingData, "week_init_days", None)

        self.CurrentBackupData["backup_id"] = getattr(existingData, "backup_id", None)

        # Emit the dataUpdated signal to update the UI
        self.currentDataUpdated.emit()

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

    def updateUiData(self):
        """Updates the UI with the current backup data."""
        self.updateTriggerInfoTree()
        self.updateInputsToData()
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

    def updateInputsToData(self):
        """Updates the inputs to the current backup data."""
        self.friendlyNameInput.setText(self.CurrentBackupData.get("friendly_name", ""))
        self.fromFolderLocationInput.setText(self.CurrentBackupData.get("origin_folder", ""))
        self.toFolderLocationInput.setText(self.CurrentBackupData.get("destination_folder", ""))

        self.backupFolderCheck.setChecked(self.CurrentBackupData.get("uses_backups_subfolder", False))

    def updateTriggerInfoTree(self):
        """Updates the triggerInfoTree with the current backup data."""
        self.triggerInfoTree.clear()

        # Translate initiation type to friendly name
        initiation_type = BackupTriggerType.represent(
            self.CurrentBackupData["initiation_type"]
        ).upper()

        # Determine recurrence type and step
        if self.CurrentBackupData["recurrence_type"] == RecurrenceType.SINGLE:
            recurrence_type = "ONCE"
        else:
            step_unit = RecurrenceStepUnit.represent(
                self.CurrentBackupData["recurrence_step_unit"]
            ).upper()
            recurrence_type = f"EVERY {self.CurrentBackupData['recurrence_step']} {step_unit}"

        # Handle start time
        start_time = BackupStartTime.represent(self.CurrentBackupData["start_time"]).upper()

        # Handle week days
        if self.CurrentBackupData["recurrence_step_unit"] == RecurrenceStepUnit.WEEKS:
            week_days = DaysOfWeek.represent(self.CurrentBackupData["week_init_days"]).upper()
        else:
            week_days = "-"

        # Adjust fields based on initiation type
        if initiation_type in ["NEVER", "STARTUP", "USER LOGON"]:
            recurrence_type = "-"
            week_days = "-"

        initiation_item = QTreeWidgetItem(["Initiation", initiation_type])
        start_time_item = QTreeWidgetItem(["Starting On", start_time])
        recurrence_item = QTreeWidgetItem(["Recurring", recurrence_type])
        week_days_item = QTreeWidgetItem(["On Days", week_days])

        self.triggerInfoTree.addTopLevelItem(initiation_item)
        self.triggerInfoTree.addTopLevelItem(start_time_item)
        self.triggerInfoTree.addTopLevelItem(recurrence_item)
        self.triggerInfoTree.addTopLevelItem(week_days_item)





