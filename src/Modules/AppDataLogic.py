# Handles data saving, incompatible data logic versions, etc...
# Author: https://github.com/matkeg
# Date: January 7th 2025

# Standard Libraries
import os, shutil, json
from enum import Enum
from typing import Optional

# Local Modules
from ..Features.fetcher import getFFlag
from .QtUtils import *

# Program Name
PROGRAM_NAME = getFFlag("ProgramName") or "RobotCopy"
FILE_STRUCTURE_COMPATIBILITY_VERSION = getFFlag("CRITICALFileStructureCompatibilityVersion") or 1

# ------------------------------------------------------------------------------------ #

class StorageFolder(Enum):
    BACKUPS = "Backups"
    GENERAL = "Storage"
    LOGS = "Logs"
    TEMP = "Temp"
    UNDEFINED = ""

class FileType(Enum):
    BackupEntry = getFFlag("BackupEntryFileExtension") or "rcbe"
    JSON = "json"
    XML = "xml"
    Text = "txt"

# ------------------------------------------------------------------------------------ #

def get_app_data_path() -> str:
    """Returns the AppData directory path for the application."""
    app_data_path = os.path.join(os.getenv("APPDATA", ""), PROGRAM_NAME)
    os.makedirs(app_data_path, exist_ok=True)
    return app_data_path


def get_storage_folder_path(folder: Optional[StorageFolder] = StorageFolder.UNDEFINED) -> str:
    """Returns the full path for a storage folder within the AppData directory."""
    base_path = get_app_data_path()

    if folder is None or folder == StorageFolder.UNDEFINED:
        return base_path
    
    folder_path = os.path.join(base_path, folder.value)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def get_data_file_path(filename: str, folder: Optional[StorageFolder] = StorageFolder.UNDEFINED, file_type: Optional[FileType] = None) -> str:
    """Returns the full path for a data file within the specified storage folder."""
    base_path = os.path.join(get_storage_folder_path(folder), filename)

    if file_type:
        return f"{base_path}.{file_type.value}"
    
    return base_path


def find_file_path(filename: str, folder: Optional[StorageFolder] = StorageFolder.UNDEFINED) -> Optional[str]:
    """Finds the full path of a file by checking all possible extensions."""
    for file_type in FileType:
        potential_path = get_data_file_path(filename, folder, file_type)

        if os.path.exists(potential_path):
            return potential_path
        
    return get_data_file_path(filename, folder)


# ------------------------------------------------------------------------------------ #

def get_environment_value(key: str, default_value: any = None) -> any:
    """Retrieves a specific value from the environment data file."""
    try:
        env_data = load_data("enviroment", StorageFolder.UNDEFINED, silent=True) or {}
        return env_data.get(key, default_value)
    except Exception as e:
        error(f"Error getting environment value {key}: {e}", "get_environment_value Error")
        return default_value

def set_environment_value(key: str, value: any) -> bool:
    """Sets or updates a specific value in the environment data file."""
    try:
        env_data = load_data("enviroment", StorageFolder.UNDEFINED, silent=True) or {}
        env_data[key] = value
        return save_data("enviroment", env_data, StorageFolder.UNDEFINED)
    except Exception as e:
        error(f"Error setting environment value {key}: {e}", "set_environment_value Error")
        return False

def increment_environment_value(key: str, increment: int = 1, default_value: int = 0) -> Optional[int]:
    """Increments a numeric value in the environment data file, useful for handling Ids."""
    try:
        current_value = get_environment_value(key, default_value)
        if not isinstance(current_value, (int, float)):
            current_value = default_value
        new_value = current_value + increment
        if set_environment_value(key, new_value):
            return new_value
        return None
    except Exception as e:
        error(f"Error incrementing environment value {key}: {e}", "increment_environment_value Error")
        return None

# ------------------------------------------------------------------------------------ #

def save_data(filename: str, data: dict, folder: Optional[StorageFolder] = StorageFolder.UNDEFINED, file_type: Optional[FileType] = None) -> bool:
    """Saves the provided data as a file in the specified storage folder with the given extension."""
    try:
        file_path = get_data_file_path(filename, folder, file_type)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        error(f"Error saving data to {filename}: {e}", "save_data Error")
        return False


def edit_data(filename: str, newData: dict, folder: Optional[StorageFolder] = StorageFolder.UNDEFINED, file_type: Optional[FileType] = None) -> bool:
    """Edits existing data or adds new data to a file. If the file does not exist, it creates a new one with the provided data."""
    try:
        # Load existing data or create an empty structure
        data = load_data(filename, folder, silent=True) or {}
        
        # Apply updates
        data.update(newData)
        
        # Save the updated data
        return save_data(filename, data, folder, file_type)
    
    except Exception as e:
        error(f"Error editing data in {filename}: {e}", "edit_data Error")
        return False


def load_data(filename: str, folder: Optional[StorageFolder] = StorageFolder.UNDEFINED, silent: Optional[bool] = False) -> Optional[dict]:
    """Loads and returns data from a file in the specified storage folder."""
    try:
        file_path = find_file_path(filename, folder)

        if not os.path.exists(file_path):
            if not silent:
                error(f"File {filename} does not exist in {folder.value if folder else 'root'} folder.", "load_data Error")  
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    except Exception as e:
        error(f"Error loading data from {filename}: {e}", "load_data Error")
        return None
    

def remove_data(filename: str, folder: Optional[StorageFolder] = StorageFolder.UNDEFINED) -> bool:
    """Removes a data file from the specified storage folder."""
    try:
        file_path = find_file_path(filename, folder)

        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    except Exception as e:
        error(f"Error removing {filename}: {e}", "remove_data Error")
        return False


def load_or_create_data(filename: str, default_data: dict, folder: Optional[StorageFolder] = StorageFolder.UNDEFINED, file_type: Optional[FileType] = None) -> dict:
    """Loads data from a file or creates it with default data if it doesn't exist."""
    data = load_data(filename, folder, silent=True)

    if data is None:
        save_data(filename, default_data, folder, file_type)
        return default_data
    
    return data


# ------------------------------------------------------------------------------------ #

# Compatibility check
enviroment_data = load_or_create_data(
    "enviroment", {
        "DO_NOT_CHANGE_THIS_FILE_MANUALLY": 0,
        "FileStructureCompatibilityVersion": FILE_STRUCTURE_COMPATIBILITY_VERSION
    }, StorageFolder.UNDEFINED
)

if enviroment_data.get("FileStructureCompatibilityVersion", 0) != FILE_STRUCTURE_COMPATIBILITY_VERSION:
    user_proceed = ask(
        f"This version of {PROGRAM_NAME} is incompatible with your current saved data, which was likely "
        f"created in a different version of this program.\n\n"
        f"To avoid issues like program instability or data corruption, all saved data - including "
        f"scheduled backups, backup history, settings, and preferences - must be deleted.\n\nYou can choose not "
        f"to delete this data by closing or canceling this prompt. However, you won't be able to use this version of "
        f"{PROGRAM_NAME} until the incompatible data is removed.\n\nYou can save a copy of your current data, which "
        f"is stored at: {get_app_data_path()}",
        "Incompatible Data",
        AskAnswer.OK_CANCEL
    )
    
    if user_proceed is not True:
        exit()

    else:
        shutil.rmtree(get_app_data_path())
        
        enviroment_data = {
            "DO_NOT_CHANGE_THIS_FILE_MANUALLY": 0,
            "FileStructureCompatibilityVersion": FILE_STRUCTURE_COMPATIBILITY_VERSION
            }
        save_data("enviroment", enviroment_data, StorageFolder.UNDEFINED)