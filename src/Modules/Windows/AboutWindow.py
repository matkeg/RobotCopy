# Provides access and logic to the about window.
# Author: https://github.com/matkeg
# Date: January 4th 2025

# PyQt5 Libraries
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

# Asset Resources and Utilities
from src.Modules.QtUtils import *
from src.Features.fetcher import *

# ------------------------------------------------------------------------------------ #

class AboutWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load the .ui file
        loadUi(
            FFlag("AboutWindowPath") or 
            "src/Interface/AboutWindow.ui",
            True, self    
        )

        closeBtn: QPushButton = findObject(self, "closeButton")
        closeBtn.clicked.connect(self.close)

        issueBtn: QPushButton = findObject(self, "issueButton")
        issueBtn.clicked.connect(self.reportIssue)

        githubBtn: QPushButton = findObject(self, "githubButton")
        githubBtn.clicked.connect(self.viewGitHub)

        # Get the project web path in order to be able to redirect the user to the webpage.
        self.projectWebPath = FFlag("BaseProjectWebPath") or "https://github.com/matkeg/RobotCopy"

    def sendToPage(self, suffix: str):
        if self.projectWebPath is None:
            error("Cannot redirect you to the desired webpage because the project's base web path is not specified.", "No project web path")
        else:
            QDesktopServices.openUrl(QUrl(f"{self.projectWebPath}{suffix}"))

    def reportIssue(self):
        self.sendToPage("/issues")

    def viewGitHub(self):
        self.sendToPage("")