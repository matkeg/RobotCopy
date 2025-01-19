<h1>
  <p align="center">
      <img src="src/Interface/Identity/banner.png" alt="RobotCopy Logo" width="512"/>
  </p>
</h1>
  
A college project written in Python which handles folder backups using the Windows **robocopy** command.

## Uses
<p align="left">
  <img src="https://skillicons.dev/icons?i=qt,py,visualstudio" alt="Qt, Python, Visual Studio">
</p>

## Requirements

To run this program, you need a Windows operating system that supports the **robocopy** command (Windows Vista or later).

For development purposes, additional requirements depend on the specific aspect of the program:

### User Interface
- **Microsoft C++ Build Tools**: Desktop development with C++[^1]
- **Qt Designer**
- **PyQt5**

[^1]: *Microsoft C++ Build Tools with the Desktop development with C++ module is required to use Qt Designer.*

> *While Qt Designer was used for UI editing, you can use any similar editor or a text editor to modify `.ui` files.*

### Backend
- **Python** (version 3.13.0 recommended)
- **Libraries:** PyQt5, psutil, pywin32, wmi, pyudev

> *Older or newer Python versions might be incompatible with this code.*

## Setup for Development

To modify the program, install the required tools and dependencies listed above. It’s recommended to use Visual Studio Code for editing.

### Modifying the User Interface
1. Edit the `.ui` files, preferably using Qt Designer for an efficient workflow.
2. Update the <kbd>assets.qrc</kbd> file if new assets are added (Qt Designer does this automatically).
3. In case you update the <kbd>assets.qrc</kbd> file, you need to compile a new <kbd>assets.py</kbd> file by running the following command in the directory containing <kbd>assets.qrc</kbd>:

```
pyrcc5 assets.qrc -o assets.py
```

### Modifying the Backend
1. Edit any `.py` files located in the project. Keep in mind that modifying certain files inside <kbd>src/modules</kbd> can easily cause errors in other files. Use Feature Flags inside <kbd>src/Features</kbd> to quickly change certain aspects of the program without much interuptions.
2. Test or debug changes by running <kbd>main.py</kbd>.

> *If you are using Visual Studio Code, you can start debugging from any file you've opened, thanks to the configuration in <kbd>.vscode/launch.json</kbd>. You can modify this file if you prefer different behavior.*
