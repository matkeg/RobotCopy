# Handles backups, providing classes related to backup's info, etc...
# Author: https://github.com/matkeg
# Date: January 5th 2025

# PyQt5 Libraries
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QPushButton, QLineEdit, QWidget
from PyQt5.QtCore import QDateTime
from typing import Optional

import datetime

# Asset Resources and Utilities
from src.Modules.QtUtils import *
from src.Features.fetcher import *
from src.Modules.FileSystemUtils import *
from src.Modules.AppDataLogic import *

# ------------------------------------------------------------------------------------ #

class BackupSetupAction:
    REMOVE = 0
    REGISTER = 1
    SETUP_ONE_TIME = 2
    EDIT = 3

# ------------------------------------------------------------------------------------ #

# NUMBERS CORESPOND TO THEIR COMBOBOX'S INDEX, CHANGING THE ORDER OF THE COMBOBOX ITEMS
# OR CHANGING THE VALUES IN THESE CLASSES COULD LEAD TO UNEXPECTED PROGRAM BEHAVIOR. 

class BackupTriggerType():
    """Specifies the scenario when the backup is initiated."""
    NEVER = 0
    STARTUP = 1
    SCHEDULED = 2
    USER_LOGON = 3

    @staticmethod
    def represent(value) -> str:
        values = {
            0: "Never",
            1: "Startup",
            2: "Scheduled",
            3: "User Logon"
        }
        return values.get(value, "-")

class RecurrenceType():
    """Specifies whether the backup occurs once or repeats."""
    RECURRING = 0
    SINGLE = 1

    @staticmethod
    def represent(value) -> str:
        values = {
            0: "Recurring",
            1: "Once"
        }
        return values.get(value, "-")

class RecurrenceStepUnit():
    """Specifies the unit for recurring steps."""
    DAYS = 0
    WEEKS = 1

    @staticmethod
    def represent(value) -> str:
        values = {
            0: "Days",
            1: "Weeks"
        }
        return values.get(value, "-")

class BackupStartTime:
    """Represents the starting time for a backup."""
    def __init__(self, time: Optional[QDateTime] = None):
        # If no QDateTime is passed, default to epoch time
        if isinstance(time, int):
            self.timestamp = time
        elif time is None:
            self.timestamp = 0
        else:
            # Convert QDateTime to a Unix timestamp (seconds since 1970-01-01)
            self.timestamp = time.toSecsSinceEpoch()

    def get_qdatetime(self) -> QDateTime:
        """Returns the stored time as a QDateTime object."""
        return QDateTime.fromSecsSinceEpoch(self.timestamp)

    def get_unix_time(self) -> int:
        """Returns the stored time as a Unix timestamp."""
        return self.timestamp
    
    def __repr__(self):
        return (
            f"BackupStartTime("
            f"timestamp -> {repr(self.timestamp)}, "
            f"friendly_date_time -> {QDateTime.fromSecsSinceEpoch(self.timestamp).toString('MM-dd-yyyy HH:mm:ss')}"
            f")"
        )
    
    @staticmethod
    def represent(value: Optional['BackupStartTime']) -> str:
        """Returns a user-facing representation of this class."""
        if value is None or value.get_unix_time() == 0:
            return "ASAP"
        else:
            return value.get_qdatetime().toString('M/d/yyyy h:mm AP')

class DaysOfWeek:
    """Represents a collection of days of the week."""
    VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}

    def __init__(self, *days):
        self.days = set()
        for day in days:
            self.add(day)

    def add(self, day: str):
        """Adds a valid day to the collection."""
        if day not in self.VALID_DAYS:
            raise ValueError(f"{day} is not a valid day of the week.")
        self.days.add(day)

    def remove(self, day: str):
        """Removes a day from the collection."""
        self.days.remove(day)

    def add_from_iterable(self, iterable):
        """
        Adds valid days from an iterable (e.g., list, set, or dictionary).
        If a dictionary is passed, only values are considered.
        """
        if isinstance(iterable, dict):
            iterable = iterable.values()
        for day in iterable:
            if day in self.VALID_DAYS:
                self.days.add(day)
            else:
                raise ValueError(f"{day} is not a valid day of the week.")

    def __contains__(self, day: str):
        """Checks if a day is in the collection."""
        return day in self.days

    def __iter__(self):
        return iter(self.days)

    def __len__(self):
        return len(self.days)

    def __repr__(self):
        days = ", ".join(sorted(self.days))
        return f"Days Of Week -> [{days}]"

    def get_days_list(self):
        """Returns the days as a sorted list."""
        return sorted(self.days)

    @staticmethod
    def represent(value: Optional['DaysOfWeek'], full: Optional[bool] = False) -> str:
        """Returns a user-facing representation of this class."""
        if value is None or value.get_days_list() == []:
            return "-"
        else:
            sorted_days = sorted(value.days, key=lambda day: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].index(day))
            if full:
                return ", ".join(sorted_days)
            else:
                return ", ".join(day[:3] for day in sorted_days)


# ------------------------------------------------------------------------------------ #

class BackupScheduleData:
    """Stores configuration data for a backup schedule."""

    def __init__(
        self,
        friendly_name: str,
        origin_folder: str, destination_folder: str,
        initiation_type: BackupTriggerType, start_time: BackupStartTime,
        recurrence_type: RecurrenceType, recurrence_step_unit: RecurrenceStepUnit, recurrence_step: int,
        week_init_days: Optional[DaysOfWeek] = None,
        backup_id: Optional[int] = None,
    ):
        # User assigned, friendly name
        self.friendly_name = friendly_name

        # Describes the origin and destination folders
        self.origin_folder = origin_folder
        self.destination_folder = destination_folder

        # Describes how and when the backup is initiated
        self.initiation_type = initiation_type
        self.start_time = start_time

        # Describes if the backup is recurring or occurs only once
        self.recurrence_type = recurrence_type
        self.recurrence_step_unit = recurrence_step_unit
        self.recurrence_step = recurrence_step

        # Specifies the days of the week for weekly recurrence
        self.weekly_init_days = week_init_days or DaysOfWeek()

        # Unique identifier for the backup schedule
        self.backup_id = backup_id

    def to_dict(self) -> dict:
        """Convert the backup schedule to a JSON-serializable dictionary."""
        return {
            "friendly_name": self.friendly_name,
            "origin_folder": self.origin_folder,
            "destination_folder": self.destination_folder,
            "initiation_type": self.initiation_type,
            "start_time": self.start_time.get_unix_time(),
            "recurrence_type": self.recurrence_type,
            "recurrence_step_unit": self.recurrence_step_unit,
            "recurrence_step": self.recurrence_step,
            "weekly_init_days": list(self.weekly_init_days.days),
            "backup_id": self.backup_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BackupScheduleData':
        """Create a BackupScheduleData instance from a dictionary."""
        days = DaysOfWeek()
        days.add_from_iterable(data.get("weekly_init_days", []))
        
        return cls(
            friendly_name = data["friendly_name"],
            origin_folder = data["origin_folder"],
            destination_folder = data["destination_folder"],
            initiation_type = data["initiation_type"],
            start_time = BackupStartTime(data["start_time"]),
            recurrence_type = data["recurrence_type"],
            recurrence_step_unit = data["recurrence_step_unit"],
            recurrence_step = data["recurrence_step"],
            week_init_days = days,
            backup_id = data["backup_id"]
        )

    def __repr__(self):
        return (
            f"BackupScheduleData(\n"
            f"    origin_folder={repr(self.origin_folder)},\n"
            f"    destination_folder={repr(self.destination_folder)},\n"
            f"    initiation_type={repr(self.initiation_type)},\n"
            f"    start_time={repr(self.start_time)},\n"
            f"    recurrence_type={repr(self.recurrence_type)},\n"
            f"    recurrence_step_unit={repr(self.recurrence_step_unit)},\n"
            f"    recurrence_step={self.recurrence_step},\n"
            f"    weekly_init_days={repr(self.weekly_init_days)}\n"
            f"    backup_id={self.backup_id}\n"
            f")"
        )

# ------------------------------------------------------------------------------------ #

class ScheduleData:
    """Stores configuration data for a schedule, not to be confused with BackupScheduleData."""

    def __init__(
        self,
        initiation_type: Optional[BackupTriggerType] = None,
        start_time: Optional[BackupStartTime] = None,
        recurrence_type: Optional[RecurrenceType] = None,
        recurrence_step_unit: Optional[RecurrenceStepUnit] = None,
        recurrence_step: Optional[int] = None,
        week_init_days: Optional[DaysOfWeek] = None,
    ):
        self.initiation_type = initiation_type
        self.start_time = start_time or BackupStartTime()
        self.recurrence_type = recurrence_type
        self.recurrence_step_unit = recurrence_step_unit
        self.recurrence_step = recurrence_step
        self.week_init_days = week_init_days or DaysOfWeek()

    def to_dict(self) -> dict:
        """Convert the schedule data to a JSON-serializable dictionary."""
        return {
            "initiation_type": self.initiation_type,
            "start_time": self.start_time.get_unix_time(),
            "recurrence_type": self.recurrence_type,
            "recurrence_step_unit": self.recurrence_step_unit,
            "recurrence_step": self.recurrence_step,
            "week_init_days": list(self.week_init_days.days),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ScheduleData':
        """Create a ScheduleData instance from a dictionary."""
        days = DaysOfWeek()
        days.add_from_iterable(data.get("week_init_days", []))
        
        return cls(
            initiation_type = data.get("initiation_type"),
            start_time = BackupStartTime(data.get("start_time")),
            recurrence_type = data.get("recurrence_type"),
            recurrence_step_unit = data.get("recurrence_step_unit"),
            recurrence_step = data.get("recurrence_step"),
            week_init_days = days,
        )

    def __repr__(self):
        return (
            f"ScheduleData(\n"
            f"    initiation_type={repr(self.initiation_type)},\n"
            f"    start_time={repr(self.start_time)},\n"
            f"    recurrence_type={repr(self.recurrence_type)},\n"
            f"    recurrence_step_unit={repr(self.recurrence_step_unit)},\n"
            f"    recurrence_step={self.recurrence_step},\n"
            f"    week_init_days={repr(self.week_init_days)}\n"
            f")"
        )

# ------------------------------------------------------------------------------------ #

def remove_backup_data(backup_id: int):
    """Removes a backup schedule data file."""
    try:
        file_path = find_file_path(f"backup{backup_id}", StorageFolder.BACKUPS)

        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    except Exception as e:
        error(
            f"Error removing backup data for ID: {backup_id}, maybe you've already removed it?\n\n{e}",
              "remove_backup_data Error"
        )

def find_backup_data(backup_id: int) -> BackupScheduleData:
    """Finds and returns a backup schedule data file."""
    try:
        file_path = find_file_path(f"backup_{backup_id}", StorageFolder.BACKUPS)

        if not os.path.exists(file_path):
            error(f"Backup data for ID: {backup_id} does not exist.", "find_backup_data Error")
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
            return BackupScheduleData.from_dict(backup_data)
    
    except Exception as e:
        error(f"Error fetching backup data for ID: {backup_id}.\n\n{e}", "find_backup_data Error")
        return None