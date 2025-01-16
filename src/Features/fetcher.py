# Provides functions related to securely fetching a local FFlag (feature flag).

# Use the fetcher.py in order to fetch a feature flag. Removing the "feature_flags.py"
# file will result in the fetcher returning None, unless a FFlag is set in the runtime
# which the program should handle correctly inside the temporary_flags dictionary.
# Deleting the "feature_flags.py" might cause program instability.

# Author: https://github.com/matkeg
# Date: January 1st 2025

try:
    from . import feature_flags
except ImportError:
    feature_flags = None

# Temporary storage for feature flags if feature_flags.py is missing
temporary_flags = {}

# ------------------------------------------------------------------------------------ #

def getFFlag(flag_name: str) -> any:
    """
    Attempts to fetch and return the value of the requested feature flag.

    If there is no feature flag with such a name or the feature_flags.py is removed, `None` will be returned.
    """
    if feature_flags is None:
        print(f"feature_flags.py is missing. Returning value from temporary storage for '{flag_name}'.")
        return temporary_flags.get(flag_name, None)

    try:
        # Fetch the feature flag dynamically from the feature_flags module
        return getattr(feature_flags, flag_name, None)
    except AttributeError:
        # In case the feature flag is not found in feature_flags.py
        print(f"Feature flag '{flag_name}' not found.")
        return None

getFeatureFlag = getFFlag
fetchFlag = getFFlag
FFlag = getFFlag

# ------------------------------------------------------------------------------------ #

def setFFlag(flag_name: str, value: any) -> None:
    """
    Sets the value of the requested feature flag in the current runtime session.

    If the flag doesn't exist, it will be added to the runtime session.
    """
    if feature_flags is None:
        # Use the temporary storage to set the feature flag
        print(f"feature_flags.py is missing. Storing '{flag_name}' in temporary storage.")
        temporary_flags[flag_name] = value
        return

    # Dynamically set or add the feature flag in the module
    setattr(feature_flags, flag_name, value)

setFeatureFlag = setFFlag
setFlag = setFFlag
