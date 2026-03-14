#!/usr/bin/env python3
"""
Civic Transparency Toolkit
===========================
A desktop application for running an AI-powered civic transparency pipeline.

Analyzes public government records and produces accessible civic reports
using a 9-prompt editorial pipeline powered by Claude.

Usage:
    python main.py

Requirements:
    pip install customtkinter anthropic
"""

import sys
import os

# Ensure the app directory is on the path (for PyInstaller compatibility)
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

from gui import CivicTransparencyApp


def main():
    app = CivicTransparencyApp()
    app.mainloop()


if __name__ == "__main__":
    main()
