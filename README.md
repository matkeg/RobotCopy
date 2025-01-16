# RobotCopy
A college project written in Python which handles folder backups using the Windows **robocopy** command. 

## Uses
<p align="left">
  <img src="https://skillicons.dev/icons?i=qt,py,visualstudio">
</p>


## Requirements - For Development

### User Interface
Microsoft C++ Build Tools > Desktop development with C++[^1], Qt Designer, PyQt5
[^1]: *Microsoft C++ Build Tools with the Desktop development with C++ module is required to use Qt Designer.*
>  *Qt Designer was used for UI editing, however the UI can be edited with any Text Editor by changing the `.ui` file.*

### Backend
Python Installation, PyQt5, psutil, pywin32
> *Python 3.13.0 was used to create this program, older or newer versions might be incompatible with this source code.*

### Required Modules
PyQt5, psutil, pywin32, wmi, pyudev

## Requirements - Software Use
- Windows 10 and 11, potentially down to Windows Vista.

---

## Setup - Software Use
<strike>Either download the `.exe` from the Releases section</strike> or download the whole source as a ZIP file, extract it and run the <kbd>main.py</kbd> file.

## Setup - Development Use
In order to make changes to this program, make sure to download any missing software from the *Requirements - For Development* list and preferably using Visual Studio Code, open the folder.

### User Interface Changes
You can change the User Interface by changing the `.ui` file/s. Use Qt Designer for best results and easier workflow.</br>
In order for Python to accept any new assets, you need to update the <kbd>assets.qrc</kbd> file (which Qt Designer automatically generates) and compile a new <kbd>assets.py</kbd> file.

To compile a new <kbd>assets.py</kbd> file, go to the directory where the <kbd>assets.qrc</kbd> file is located using the command prompt and execute this command.
```
pyrcc5 assets.qrc -o assets.py
```

### Backend Changes
You can change the logic of the program by modifying any `.py` file located directly under the `src` folder or <kbd>src/libraries</kbd>.</br>
Test/debug new changes by running <kbd>src/main.py.</kbd>
