# Logic related to fetching basic info/metadata of files/folders.
# Author: https://github.com/matkeg
# Date: January 5th 2025

import os
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional
from PyQt5.QtWidgets import QLineEdit

from .Utils import warn, error

class FolderData():
    def __init__(
            self, 
            folder_path: Optional[str] = "Unknown", folder_name: Optional[str] = "Unknown", 
            drive_letter: Optional[str] = "?:", folder_size: Optional[str] = "Unknown", 
            number_of_files: Optional[str] = "Unknown", number_of_folders: Optional[str] = "Unknown", 
        ):
        """Constructor to initialize the formatted folder data, which will be displayed to the user."""
        self.folder_path = folder_path
        self.folder_name = folder_name
        self.drive_letter = drive_letter
        self.folder_size = folder_size
        self.number_of_files = number_of_files
        self.number_of_folders = number_of_folders

    def __repr__(self):
        return (
            f"FolderData(Path: {self.folder_path}, Name: {self.folder_name}, Drive: {self.drive_letter}, "
            f"Size: {self.folder_size}, Files: {self.number_of_files}, Folders: {self.number_of_folders})"
        )

class AccessType(Enum):
    """Enum for specifying the type of access to check."""
    Read = "Read"
    Write = "Write"
    ReadAndWrite = "Read And Write"

@dataclass
class FolderStats:
    total_size: int = 0
    file_count: int = 0
    folder_count: int = 0

# ------------------------------------------------------------------------------------ #

def analyzeFolderChunk(chunk_path: str, max_depth: int = 15, current_depth: int = 0) -> FolderStats:
    """
    Analyzes a portion of the folder structure.
    - Includes a depth limit to prevent infinite recursion.
    - Handles inaccessible paths gracefully.
    """
    stats = FolderStats()

    # Prevent infinite recursion by limiting depth
    if current_depth >= max_depth:
        print(f"Skipping {chunk_path}: Max recursion depth reached.")
        return stats

    try:
        with os.scandir(chunk_path) as entries:
            for entry in entries:
                if entry.is_file(follow_symlinks=False):
                    stats.file_count += 1
                    stats.total_size += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    sub_stats = analyzeFolderChunk(entry.path, max_depth, current_depth + 1)
                    stats.file_count += sub_stats.file_count
                    stats.folder_count += sub_stats.folder_count
                    stats.total_size += sub_stats.total_size
    except (PermissionError, FileNotFoundError) as e:
        print(f"Error accessing {chunk_path}: {e}")
    
    return stats

# ------------------------------------------------------------------------------------ #

def arePathsUnderSameFolder(path1: str, path2: str) -> bool:
    """Check if one path is a subdirectory of the other."""
    real_path1 = os.path.realpath(path1)
    real_path2 = os.path.realpath(path2)

    # Check if path1 is a subdirectory of path2 or vice versa
    return real_path1.startswith(real_path2) or real_path2.startswith(real_path1)

# ------------------------------------------------------------------------------------ #

def arePathsTheSame(path1: str, path2: str) -> bool:
    """Check if two paths point to the same file or directory."""
    try:
        real_path1 = os.path.realpath(path1)
        real_path2 = os.path.realpath(path2)
        return real_path1 == real_path2
    except Exception as e:
        print(f"Error comparing paths: {e}")
        return None

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

def canAccessFolder(folder_path: str, accessType: Optional[AccessType] = AccessType.ReadAndWrite, noisy: Optional[bool] = False) -> bool:
    """
    Checks whether the passed folder is accessible for the specified type of access.
    - Ensures the folder exists and is a valid directory.
    - Verifies the current user has read, write, or read-and-write permissions.
    """

    if not isValidPath(folder_path, False):
        if noisy is True:
            warn(f"The path '{folder_path}' does not lead to a valid directory.", "Target Not Found")
        return False

    try:
        if accessType == AccessType.Read:
            # Test read access by attempting to list directory contents
            with os.scandir(folder_path) as entries:
                _ = [entry for entry in entries]
            return True

        elif accessType == AccessType.Write:
            # Test write access by attempting to create and delete a temporary file
            test_file_path = os.path.join(folder_path, "TEMP_write_file")
            with open(test_file_path, "w") as temp_file:
                temp_file.write("Testing write access.")
            os.remove(test_file_path)
            return True

        elif accessType == AccessType.ReadAndWrite:
            # Test both read and write access
            return (
                canAccessFolder(folder_path, AccessType.Read, noisy) and
                canAccessFolder(folder_path, AccessType.Write, noisy)
            )

    except (PermissionError, FileNotFoundError, OSError) as e:
        if noisy is True:
            error(
                f"The folder you've selected, {folder_path}, does not allow for {accessType.name.lower()} operations. "
                f"Please ensure to select a folder which is not {accessType.name.lower()} locked.\n\n"
                f"{str(e)}",
                "Access Denied"
            )

        return False

    return False

# ------------------------------------------------------------------------------------ #

def isValidPath(folder_path: str, noisy: Optional[bool] = False) -> bool:
    """
    Validates a folder's path.
    """
    if not folder_path:  # Check for an empty path
        return False

    # Check if the path exists and is a directory
    if not os.path.isdir(folder_path):
        if noisy is True:
            warn(f"The path '{folder_path}' does not lead to a valid directory.", "Target Not Found")

        return False

    # Normalize and split the path into components
    normalized_path = os.path.normpath(folder_path)
    path_components = normalized_path.split(os.sep)

    # Check for root-level paths (e.g., 'C:\\', '/', 'D:\\')
    if len(path_components) <= 1 or (len(path_components) == 2 and path_components[1] == ''):
        if noisy is True:
            warn(f"The path '{folder_path}' must lead to a subfolder of a drive, but not to a drive itself.", "Invalid Path")
        return False

    # If all checks pass, the path is valid
    return True

# ------------------------------------------------------------------------------------ #

def isUsingBackupFolder(folder_path: str):
    """
    Checks if the given folder path points to a folder named "Backups".
        
    Returns a tuple: (boolean, str) 
    - boolean: True if the folder is named "Backups", False otherwise.
    - str: The parent path if it's a "Backups" folder, else the input folder path.
    """
    # In case nothing is passed.
    if folder_path is None:
        return False, ""
    
    # Normalize the folder path for consistent behavior across OSes
    folder_path = os.path.normpath(folder_path)
    
    # Get the folder name and parent path
    folder_name = os.path.basename(folder_path)
    parent_path = os.path.dirname(folder_path)
    
    if folder_name == "Backups":
        return True, parent_path
    else:
        # In case the folder path leads to nothing, sometimes this
        # function might return ".", we need to prevent this, thus:
        if folder_path == ".":
            return False, ""
        else:
            return False, folder_path

# ------------------------------------------------------------------------------------ #

def getFolderData(input: QLineEdit | str, accessType: Optional[AccessType] = AccessType.ReadAndWrite, max_workers: Optional[int] = None) -> FolderData:
    """
    Analyzes folder content using parallel processing.
    Returns FolderData object with formatted information.
    """
    if type(input) is QLineEdit:
        folder_path = input.text()
    else:
        folder_path = input

    # Check if the folder path is actually passed.
    # We do this to prevent prompts from 'canAccessFolder'.
    if len(folder_path) == 0:
        return FolderData()

    if not canAccessFolder(folder_path, accessType, True):
        if type(input) is QLineEdit:
            input.setText("")

        # Return empty folder data for invalid paths.
        return FolderData()

    if not os.path.exists(folder_path):
        return FolderData()

    # Get top-level entries for parallel processing
    top_level_dirs = []
    initial_stats = FolderStats()
    
    try:
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_file(follow_symlinks=False):
                    initial_stats.file_count += 1
                    initial_stats.total_size += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    initial_stats.folder_count += 1
                    top_level_dirs.append(entry.path)
    except PermissionError:
        return FolderData()

    # Process subdirectories in parallel
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="FolderAnalyzer") as executor:
        results = executor.map(analyzeFolderChunk, top_level_dirs)

    # Combine all results
    for result in results:
        initial_stats.file_count += result.file_count
        initial_stats.folder_count += result.folder_count
        initial_stats.total_size += result.total_size

    # Format the results using existing utility
    formatted_size = formatStorageSize(initial_stats.total_size)
    
    return FolderData(
        folder_path=folder_path,
        folder_name=os.path.basename(folder_path),
        drive_letter=os.path.splitdrive(folder_path)[0],
        folder_size=formatted_size,
        number_of_files=str(initial_stats.file_count),
        number_of_folders=str(initial_stats.folder_count)
    )