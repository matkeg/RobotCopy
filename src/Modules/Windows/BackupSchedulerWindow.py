# Provides access and logic to the backup scheduler window.
# Author: https://github.com/matkeg
# Date: January 7th 2025

# PyQt5 Libraries
from PyQt5.QtCore import pyqtSignal

# Asset Resources and Utilities
from src.Modules.QtUtils import *
from src.Features.fetcher import *

# Logic
from ..BackupLogic import *

# ------------------------------------------------------------------------------------ #

class BackupSchedulerWindow(QMainWindow):
    # --- CROSS WINDOW BRIDGE ----------------- #
    scheduleTransmission = pyqtSignal(dict)
    
    def __init__(self, existingData: Optional[ScheduleData] = None):
        super().__init__()
        # Load the .ui file
        loadUi(
            FFlag("BackupSchedulerPath") or 
            "src/Interface/BackupScheduler.ui",
            True, self    
        )

        # --- DIALOG ACTIONS ---------------------- #
        def handleDialogButtons(button):
            clickedRole = self.dialogButtons.buttonRole(button)
            if clickedRole == QDialogButtonBox.ResetRole:
                self.setExistingData(existingData)

            elif clickedRole == QDialogButtonBox.AcceptRole:
                self.scheduleTransmission.emit(self.collectScheduleData())
                self.close()

            elif clickedRole == QDialogButtonBox.RejectRole:
                #self.scheduleTransmission.emit()
                self.close()

        # --- SETUP CONNECTIONS AND FETCH DYNAMIC OBJECTS --- #
        self.dialogButtons: QDialogButtonBox = findObject(self, "dialogButtons")
        self.dialogButtons.clicked.connect(handleDialogButtons)

        self.initiationTypeCombo: QComboBox = findObject(self, "initiationType")
        self.initiationTypeCombo.currentIndexChanged.connect(self.onInitiationChange)

        # RECURRENCE OPTIONS
        self.recurrenceTypeCombo: QComboBox = findObject(self, "recurrenceType")
        self.recurrenceTypeCombo.currentIndexChanged.connect(self.onRecurrenceTypeChange)

        self.recurrenceStepUnitCombo: QComboBox = findObject(self, "recurrenceStepUnit")
        self.recurrenceStepUnitCombo.currentIndexChanged.connect(self.onRecurrenceUnitChange)

        self.recurrenceStepInput: QSpinBox = findObject(self, "recurrenceStep")

        # TIME SPECIFIC OPTIONS
        self.timeSettingsGroup: QGroupBox = findObject(self, "timeSettingsGroup")
        self.weekdaysGrid: QGroupBox = findObject(self, "weekdaysGrid")

        self.timeNowCheck: QCheckBox = findObject(self, "timeNowCheck")

        self.dateTimeEdit: QDateTimeEdit = findObject(self, "dateTimeEdit")
        self.dateTimeEdit.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.dateTimeEdit.setMinimumDateTime(QDateTime.currentDateTime().addSecs(300))

        # WEEKDAYS CHOICES
        self.mondayChoice: QCheckBox = findObject(self, "mondayChoice")
        self.tuesdayChoice: QCheckBox = findObject(self, "tuesdayChoice")
        self.wednesdayChoice: QCheckBox = findObject(self, "wednesdayChoice")
        self.thursdayChoice: QCheckBox = findObject(self, "thursdayChoice")
        self.fridayChoice: QCheckBox = findObject(self, "fridayChoice")
        self.saturdayChoice: QCheckBox = findObject(self, "saturdayChoice")
        self.sundayChoice: QCheckBox = findObject(self, "sundayChoice")

        # INITIATE THE VIEW
        self.onInitiationChange(self.initiationTypeCombo.currentIndex())

        self.onRecurrenceTypeChange(self.recurrenceTypeCombo.currentIndex())
        self.onRecurrenceUnitChange(self.recurrenceStepUnitCombo.currentIndex())

        # Set the existing data if it exists.
        self.setExistingData(existingData)

    # --------------------------------------------- #

    def setExistingData(self, existingData: Optional[ScheduleData] = None):
        if existingData is None:
            return

        # Initiation Type Combobox
        initiation_type = getattr(existingData, 'initiation_type', None)
        if initiation_type is not None:
            self.initiationTypeCombo.setCurrentIndex(initiation_type)

        # Starting Time
        start_time = getattr(existingData, 'start_time', None)
        if start_time is not None:
            startingTime = start_time.get_unix_time()
            if startingTime != 0:
                self.timeNowCheck.setChecked(False)
                self.dateTimeEdit.setDateTime(QDateTime.fromSecsSinceEpoch(startingTime))
            else:
                self.timeNowCheck.setChecked(True)

        # Recurrence Type Combobox
        recurrence_type = getattr(existingData, 'recurrence_type', None)
        if recurrence_type is not None:
            self.recurrenceTypeCombo.setCurrentIndex(recurrence_type)

        # Recurrence Step (Ex. HOW MANY Days, HOW MANY Weeks) Input
        recurrence_step = getattr(existingData, 'recurrence_step', None)
        if recurrence_step is not None:
            self.recurrenceStepInput.setValue(recurrence_step)

        # Recurrence Step UNIT (Ex. DAYS, WEEKS) Combobox
        recurrence_step_unit = getattr(existingData, 'recurrence_step_unit', None)
        if recurrence_step_unit is not None:
            self.recurrenceStepUnitCombo.setCurrentIndex(recurrence_step_unit)

        # Weekdays Selection Checkboxes
        week_init_days = getattr(existingData, 'week_init_days', None)
        if week_init_days is not None:
            self.mondayChoice.setChecked("Monday" in week_init_days)
            self.tuesdayChoice.setChecked("Tuesday" in week_init_days)
            self.wednesdayChoice.setChecked("Wednesday" in week_init_days)
            self.thursdayChoice.setChecked("Thursday" in week_init_days)
            self.fridayChoice.setChecked("Friday" in week_init_days)
            self.saturdayChoice.setChecked("Saturday" in week_init_days)
            self.sundayChoice.setChecked("Sunday" in week_init_days)
        

    def onInitiationChange(self, index: int):
        if index == 0: # NEVER
            self.timeSettingsGroup.setEnabled(False)

        elif index == 1: # AT STARTUP
            self.timeSettingsGroup.setEnabled(False)

        elif index == 2: # ON A SCHEDULE
            self.timeSettingsGroup.setEnabled(True)

        elif index == 3: # AT CURRENT USER'S LOGON
            self.timeSettingsGroup.setEnabled(False)


    def onRecurrenceUnitChange(self, index: int):
        if index == 0: # DAYS...
            self.weekdaysGrid.setEnabled(False)

        elif index == 1: # WEEKS
            self.weekdaysGrid.setEnabled(True)


    def onRecurrenceTypeChange(self, index: int):
        if index == 0: # EVERY...
            self.recurrenceStepUnitCombo.setEnabled(True)
            self.recurrenceStepInput.setEnabled(True)

        elif index == 1: # ONCE
            self.recurrenceStepUnitCombo.setEnabled(False)
            self.recurrenceStepInput.setEnabled(False)

    # --------------------------------------------- #

    def collectScheduleData(self) -> dict:
        # Calculate special variables
        if self.timeNowCheck.isChecked():
            selected_start_time = BackupStartTime()
        else:
            selected_start_time = BackupStartTime(self.dateTimeEdit.dateTime())


        # Calculate the selected days
        selected_weekdays = DaysOfWeek()

        if self.mondayChoice.isChecked():
            selected_weekdays.add("Monday")

        if self.tuesdayChoice.isChecked():
            selected_weekdays.add("Tuesday")

        if self.wednesdayChoice.isChecked():
            selected_weekdays.add("Wednesday")

        if self.thursdayChoice.isChecked():
            selected_weekdays.add("Thursday")

        if self.fridayChoice.isChecked():
            selected_weekdays.add("Friday")

        if self.saturdayChoice.isChecked():
            selected_weekdays.add("Saturday")

        if self.sundayChoice.isChecked():
            selected_weekdays.add("Sunday")

        # If no choices are selected, set monday as the default day.
        if len(selected_weekdays) == 0:
            selected_weekdays.add("Monday")

        # Gather the data from the form, and return the said data.
        return {
            "initiation_type": self.initiationTypeCombo.currentIndex(),
            
            "start_time": selected_start_time,

            "recurrence_type": self.recurrenceTypeCombo.currentIndex(),
            "recurrence_step": self.recurrenceStepInput.value(),
            "recurrence_step_unit": self.recurrenceStepUnitCombo.currentIndex(),

            "week_init_days": selected_weekdays
        }

