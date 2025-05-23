"""
Film Translator Generator - Entry point for the modular implementation

This script runs the Film Translator Generator application, which:
1. Transcribes audio from video files using Faster-Whisper
2. Translates the transcriptions using Google Gemini API
3. Generates subtitle files in various formats (SRT, VTT, TXT)

Usage:
    python main.py

Requirements:
    See requirements.txt for Python dependencies
    FFMPEG must be installed and in the system PATH
    For GPU acceleration, CUDA and cuDNN must be properly installed
"""
import sys
from PySide6.QtWidgets import QApplication
from qt_app import QtAppGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QtAppGUI()
    window.show()
    sys.exit(app.exec()) 