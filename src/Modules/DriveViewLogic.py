# Logic related to the Drive View, such as drive scanning, metadata scanning, size formatting, etc...
# Author: https://github.com/matkeg
# Date: December 9th 2024

import psutil, win32api, win32file, wmi, pythoncom, os

# For custom thread names
import threading

from typing import Optional
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor

from warnings import deprecated

from ..Features.fetcher import *
from .Utils import error, info, warn
from .QtUtils import *

# ------------------------------------------------------------------------------------ #

class FormattedDiskInfo:
    """A class which holds formated data of a given drive."""
    def __init__(
            self, 
            drive_letter: Optional[str] = "?:", drive_name: Optional[str] = "Unknown", formatted_free_space: Optional[str] = "Unknown", file_system: Optional[str] = "Unknown", 
            drive_type: Optional[str] = "Unknown", is_windows: Optional[bool | str] = "Unknown", disk_model: Optional[str] = "Unknown", disk_manufacturer: Optional[str] = "Unknown"
        ):
        """Constructor to initialize the formatted disk information, which will be displayed to the user."""

        def frm(value: any) -> str:
            """Formats a value based on certain hardcoded formatting rules."""
            # Translate booleans.
            if isinstance(value, bool):  
                if value is True:
                    return "Yes"
                elif value is False:
                    return "No"

            elif isinstance(value, str) and len(value) <= 0:   
                return "Unknown"
            
            elif value is not None:
                return str(value)
            
            else:
                return "Unknown"

        self.driveLetter = frm(drive_letter)
        self.driveName = frm(drive_name)
        self.driveType = frm(drive_type)
        self.diskModel = frm(disk_model)
        self.diskManufacturer = frm(disk_manufacturer)

        self.fileSystem = frm(file_system)
        self.freeSpace = frm(formatted_free_space)

        self.isWindows = frm(is_windows)

    def __repr__(self):
        """Return a string representation of the FormattedDiskInfo instance."""
        return (f"Drive Letter: {self.driveLetter}\nDrive Name: {self.driveName}\n"
                f"Free Space: {self.freeSpace}\nFile System: {self.fileSystem}\n"
                f"Drive Type: {self.driveType}\nIs Windows Installation: {self.isWindows}\n"
                f"Disk Model Name: {self.diskModel}\nDisk Manufacturer: {self.diskManufacturer}")

# ------------------------------------------------------------------------------------ #

class DriveViewPopulationWorker(QThread):
    """Worker thread for fetching drive data and populating the drive view."""
    finished = pyqtSignal()
    status_update = pyqtSignal(str)
    drive_data = pyqtSignal(list)

    def run(self):
        """Main method that runs in the thread."""
        setFFlag("DYNViewsAreRefreshing", True)

        # Set a custom name (in order for it not to be "Dummy-X")
        # Might not work on specific operating systems.
        current_thread = threading.current_thread()
        current_thread.name = "DrivePopulationThread"
        try:
            self.status_update.emit("Fetching available drives...")
            
            # Get drive data in the thread
            drives_data = getAvailableDrivesData()
            
            # Emit the collected data
            self.drive_data.emit(drives_data)
            self.finished.emit()
            
        except Exception as e:
            error(str(e), "Drive Population Error")
            self.finished.emit()

def populateDriveView(mainWindow: QMainWindow, treeWidget: QTreeWidget):
    """
    Populates the Drive View by fetching and displaying drive data in a separate thread.
    """
    # Check if there is an ongoing view refreshing operation.
    if getFFlag("DYNViewsAreRefreshing") is True:
        return;

    # Start updating the drive view by firstly clearing the treeWidget.
    treeWidget.clear()

    def handleItemSelection():
        selectedItems = treeWidget.selectedItems()
        selectedItem: QTreeWidgetItem = selectedItems[0] if selectedItems else None
        if selectedItem is None:
            return
        
        associatedEntry: FormattedDiskInfo = selectedItem.data(0, 32)
        
        # Hide a possible previous infoLabel.
        infoLabel = findObject(mainWindow, "infoLabel")
        if infoLabel.isVisible and associatedEntry.driveType != "Removable":
            infoLabel.hide()
            
        if associatedEntry is None:
            warn("No entry data is associated with this QTreeWidgetItem.")
        else:
            # Warning the user of consequences of removable drives.
            if associatedEntry.driveType == "Removable":
                setLabelTextAdvanced(mainWindow, "infoText", textMode.JSON, "info_removable_drive")
                findObject(mainWindow, "infoLabel").show()

            # Setting the icon.
            setUnsecurePixmap(mainWindow, "driveIcon", selectedItem.icon(0))

            # Setting the name.
            setUnsecureText(mainWindow, "InsightsDriveName", 
                f"""<html><head/><body><p><span style=" font-weight:600;">
                {associatedEntry.driveName} ({associatedEntry.driveLetter})</span></p></body></html>""")

            # Setting the insights.
            setUnsecureText(mainWindow, "InsightsDriveInfo", 
                f"""<html><head/><body><p><span style=" color:#a5a5a5;">Drive Type:</span> 
                {associatedEntry.driveType}<br/><span style=" color:#a3a3a3;">Free Space:</span> 
                {associatedEntry.freeSpace}</p></body></html>""")

            setUnsecureText(mainWindow, "InsightsDiskInfo", 
                f"""<html><head/><body><p><span style=" color:#a3a3a3;">Disk Model:</span> 
                {associatedEntry.diskModel}<br/><span style=" color:#a3a3a3;">Disk Manufacturer:</span> 
                {associatedEntry.diskManufacturer}</p></body></html>""")

            setUnsecureText(mainWindow, "InsightsDriveWindows", 
                f"""<html><head/><body><p><span style=" color:#a3a3a3;">Windows Installation:</span> 
                {associatedEntry.isWindows}</p></body></html>""")

    def updateTreeView(drives_data):
        """Updates the tree view with the processed drive data."""
        treeWidget.clear()
        
        for entry in drives_data:
            driveFullName = f"{entry.driveName} ({entry.driveLetter})"
            newTreeEntry = QTreeWidgetItem(treeWidget, [driveFullName, "0", "0", "--/--/---- --:-- --"])
            newTreeEntry.setData(0, 32, entry)

            if entry.isWindows == "Yes":
                newTreeEntry.setIcon(0, QIcon("src/Interface/Icons/Drives/DriveInstallation.ico"))
            elif entry.isWindows == "No":
                newTreeEntry.setIcon(0, QIcon("src/Interface/Icons/Drives/Drive.ico"))
            else:
                newTreeEntry.setIcon(0, QIcon("src/Interface/Icons/Drives/DriveUnknown.ico"))

    def updateStatus(message: str):
        """Updates the status label with the current operation."""
        setUnsecureText(mainWindow, "statusText", message)
        findObject(mainWindow, "statusLabel").show()

    def onPopulationFinished():
        """Cleanup after population is complete."""
        findObject(mainWindow, "statusLabel").hide()
        # Re-enable the Content widget
        content_widget = findObject(mainWindow, "Content")
        content_widget.setEnabled(True)
        worker.deleteLater()

        setFFlag("DYNViewsAreRefreshing", False)

    # Disable the Content widget during population
    content_widget = findObject(mainWindow, "Content")

    # Hide labels, and disable the content widget while the population operation is ongoing.
    warningLabel = findObject(mainWindow, "warningLabel")
    errorLabel = findObject(mainWindow, "errorLabel")
    infoLabel = findObject(mainWindow, "infoLabel")
    executeFunction("hide", errorLabel, warningLabel, infoLabel)

    content_widget.setEnabled(False)

    # Create and set up the worker thread
    worker = DriveViewPopulationWorker()
    worker.status_update.connect(updateStatus)
    worker.drive_data.connect(updateTreeView)
    worker.finished.connect(onPopulationFinished)
    
    # Set up item selection handling
    treeWidget.itemSelectionChanged.connect(handleItemSelection)
    
    # Start the worker thread
    worker.start()

# ------------------------------------------------------------------------------------ #

def formatStorageSize(valueInBytes: int) -> str:
    """Converts a storage size in bytes to the most appropriate unit."""
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    power = 1024
    for unit in units:
        if valueInBytes < power:
            return f"{valueInBytes:.2f} {unit}" if unit != "bytes" else f"{valueInBytes} {unit}"
        valueInBytes /= power
    return f"{valueInBytes:.2f} YB"

# ------------------------------------------------------------------------------------ #

def getAvailableDrives() -> list[str]:
    """Returns a list of drive letters (symbolizing drives) currently connected to the user's machine."""
    drives = []
    # Loop through drive letters from 'A' to 'Z'
    for letter in range(65, 91):
        drive = f"{chr(letter)}:/"

        # Check if the drive exists
        if os.path.exists(drive):
            drives.append(chr(letter))
    return drives

# ------------------------------------------------------------------------------------ #

@deprecated("Use getAvailableDrivesData() for way faster and more reliable data fetching.") 
def getDriveData(drive_letter) -> FormattedDiskInfo:
    """
        #### Deprecated - Use getAvailableDrivesData() for way faster and more reliable data fetching.

        Retrieves data regarding the drive and its disk, which will be shown to the user.
       
        Returns a FormattedDiskInfo object which holds string formatted disk data.
    """
    try:
        # Normalize drive letter
        raw_drive_letter = drive_letter.upper()
        drive_letter = raw_drive_letter + ":\\"

        # Get disk usage information
        usage = psutil.disk_usage(drive_letter)
        
        # Get partition info
        partitions = psutil.disk_partitions()
        partition_info = next((p for p in partitions if p.device == drive_letter), None)

        if not partition_info:
            return [{"error": f"Drive {raw_drive_letter} not found"}]

        # Detect Windows installation
        is_windows = os.path.exists(os.path.join(drive_letter, "Windows"))

        # Get volume information
        volume_info = win32api.GetVolumeInformation(drive_letter)
        drive_name = volume_info[0]
        file_system = volume_info[4]

        # Determine drive type
        drive_type_code = win32file.GetDriveType(drive_letter)
        drive_type_map = {
            win32file.DRIVE_UNKNOWN: "Unknown",
            win32file.DRIVE_NO_ROOT_DIR: "Invalid",
            win32file.DRIVE_REMOVABLE: "Removable",
            win32file.DRIVE_FIXED: "Fixed",
            win32file.DRIVE_REMOTE: "Network",
            win32file.DRIVE_CDROM: "CD-ROM",
            win32file.DRIVE_RAMDISK: "RAM Disk",
        }
        drive_type = drive_type_map.get(drive_type_code, "Unknown")

        # Retrieve disk model and manufacturer using WMI
        physical_disk = None
        for disk in wmi.WMI().Win32_DiskDrive():
            for partition in disk.associators("Win32_DiskDriveToDiskPartition"):
                for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                    if logical_disk.DeviceID == raw_drive_letter + ":":
                        physical_disk = disk
                        break
                if physical_disk:
                    break
            if physical_disk:
                break

        if physical_disk:
            disk_model = physical_disk.Model
            disk_manufacturer = physical_disk.Manufacturer or "Unknown"
        else:
            disk_model = "Unknown"
            disk_manufacturer = "Unknown"

        # Assembling and returning the data.
        return FormattedDiskInfo(
            raw_drive_letter+":", drive_name, formatStorageSize(usage.free), 
            file_system, drive_type, is_windows, disk_model, disk_manufacturer
        )

    except Exception as e:
        error(str(e), "getDriveData Error")
        return FormattedDiskInfo()

# ------------------------------------------------------------------------------------ #

def getAvailableDrivesData() -> list[FormattedDiskInfo]:
    """
        Retrieves data from all available drives and their disks, which will be shown to the user.
        
        Returns FormattedDiskInfo objects which hold string formatted disk data. 
        
        Uses threading for faster data retrival.
    """
    drives_data = []
    drives = [f"{chr(letter)}:\\" for letter in range(65, 91) if os.path.exists(f"{chr(letter)}:/")]

    def process_drive(drive_letter):
        try:
            pythoncom.CoInitialize()  # Initialize COM in the thread

            # Get disk usage info
            usage = psutil.disk_usage(drive_letter)

            # Get partition info
            partitions = psutil.disk_partitions()
            partition_info = next((p for p in partitions if p.device == drive_letter), None)
            if not partition_info:
                return None

            # Check for Windows installation
            is_windows = os.path.exists(os.path.join(drive_letter, "Windows"))

            # Get volume information
            volume_info = win32api.GetVolumeInformation(drive_letter)
            drive_name = volume_info[0]
            file_system = volume_info[4]

            # Determine drive type
            drive_type_code = win32file.GetDriveType(drive_letter)
            drive_type_map = {
                win32file.DRIVE_UNKNOWN: "Unknown",
                win32file.DRIVE_NO_ROOT_DIR: "Invalid",
                win32file.DRIVE_REMOVABLE: "Removable",
                win32file.DRIVE_FIXED: "Fixed",
                win32file.DRIVE_REMOTE: "Network",
                win32file.DRIVE_CDROM: "CD-ROM",
                win32file.DRIVE_RAMDISK: "RAM Disk",
            }
            drive_type = drive_type_map.get(drive_type_code, "Unknown")

            # Retrieve disk model and manufacturer using WMI
            physical_disk = None
            for disk in wmi.WMI().Win32_DiskDrive():
                for partition in disk.associators("Win32_DiskDriveToDiskPartition"):
                    for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                        if logical_disk.DeviceID == drive_letter[0] + ":":
                            physical_disk = disk
                            break
                    if physical_disk:
                        break
                if physical_disk:
                    break

            if physical_disk:
                disk_model = physical_disk.Model
                disk_manufacturer = physical_disk.Manufacturer or "Unknown"
            else:
                disk_model = "Unknown"
                disk_manufacturer = "Unknown"

            # Assembling and returning the data.
            return FormattedDiskInfo(
                drive_letter[0] + ":",
                drive_name,
                formatStorageSize(usage.free),
                file_system,
                drive_type,
                is_windows,
                disk_model,
                disk_manufacturer,
            )
        except Exception as e:
            error(str(e), f"Error processing drive {drive_letter}")
            return None
        finally:
            pythoncom.CoUninitialize()  # Clean up COM in the thread

    # Use threads for faster data retrival.
    with ThreadPoolExecutor(thread_name_prefix="DriveDataWorker") as executor:
        results = executor.map(process_drive, drives)

    # Collect non-None results
    drives_data = [result for result in results if result is not None]
    return drives_data