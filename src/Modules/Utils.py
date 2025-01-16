# Utility Python module for use in general python applications.
# Author: https://github.com/matkeg
# Date: December 9th 2024

from typing import Optional
from tkinter import messagebox

# ------------------------------------------------------------------------------------ #

class AskAnswer:
    YES_NO = 1
    OK_CANCEL = 2
    RETRY_CANCEL = 3
    YES_NO_CANCEL = 4

# ------------------------------------------------------------------------------------ #

def executeFunction(functionName: str, *objects):
    """
    Executes the given method (by name) on each provided object. 
    Reports back to the user of any failed attempts to execute the function.
    """
    missing_function_objects = []  # To track objects missing the function
    failed_executions = []  # To track objects whose functions failed to execute

    for obj in objects:
        function = getattr(obj, functionName, None)
        if callable(function):
            try:
                function()
            except Exception as e:
                # Log or store the failure for reporting
                failed_executions.append((obj, str(e)))
        else:
            missing_function_objects.append(obj)

    # Prompt a warning for any objects which don't have the provided function
    if missing_function_objects:
        warn((
            f"There is no function under the name '{functionName}' "
            f"for the following objects:\n\n" +
            "\n".join(str(obj) for obj in missing_function_objects)
        ))

    # Report any functions that failed during execution
    if failed_executions:
        error((
            f"The following objects encountered errors during execution "
            f"of '{functionName}':\n\n" +
            "\n".join(f"{str(obj)}: {error}" for obj, error in failed_executions)
        ), "executeFunction Error")

# ------------------------------------------------------------------------------------ #

def error(text: Optional[str] = "An unknown error occured.", title: Optional[str] = "Error", raiseError: Optional[bool] = False):
    """Prompts a tkinter error messagebox with the passed message."""
    messagebox.showerror(title, text)

    # Deprecated, do not use raiseError, doing so will only redirect your code editor to this point.
    if raiseError is True:
        raise Exception(text)

def warn(text: Optional[str] = "An warning was initiated.", title: Optional[str] = "Warning"):
    """Prompts a tkinter warning messagebox with the passed message."""
    messagebox.showwarning(title, text)

def info(text: Optional[str] = "An info box was initiated.", title: Optional[str] = "Info"):
    """Prompts a tkinter info messagebox with the passed message."""
    messagebox.showinfo(title, text) 

def ask(text: Optional[str] = "No message provided.", title: Optional[str] = "Warning", answers: Optional[AskAnswer] = AskAnswer.OK_CANCEL) -> bool | None:
    """Prompts a tkinter ask messagebox with the passed message and provided answers."""
    if answers is AskAnswer.OK_CANCEL:
        return messagebox.askokcancel(title, text)
    elif answers is AskAnswer.RETRY_CANCEL:
        return messagebox.askretrycancel(title, text)
    elif answers is AskAnswer.YES_NO_CANCEL:
        return messagebox.askyesnocancel(title, text)
    else:
        return messagebox.askyesno(title, text)

# ------------------------------------------------------------------------------------ #

def hasProperty(object: any, propertyName: str) -> bool:
    """Returns true if the passed object has the passed property and vice versa."""
    return object.property(propertyName) is not None

# ------------------------------------------------------------------------------------ #

def attemptToGetObjectName(object: any) -> str | None:
    """Attempts to get the object's name."""
    try:
        # Check if the object has a 'name' attribute or method
        if hasattr(object, "objectName"):
            return object.objectName()
        elif hasattr(object, "__name__"):
            return object.__name__
        elif hasattr(object, "name"):
            return object.name
        else:
            return None
    except Exception as e:
        # Return None if there is no data.
        return None

# ------------------------------------------------------------------------------------ #

def truncateWithDots(text: str, limit: Optional[int] = 20):
    """Truncates a string to the specified character limit and appends '...' if needed."""
    if len(text) > limit:
        return text[:limit] + '...'
    return text

# ------------------------------------------------------------------------------------ #