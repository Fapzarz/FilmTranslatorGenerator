#!/usr/bin/env python
"""
Proof of Concept for Film Translator Generator using PySide6
This file demonstrates a simple Qt application with video playback capabilities.
"""
import os
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                               QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QSlider)
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

class VideoPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Film Translator Generator - Qt PoC')
        self.setGeometry(100, 100, 800, 600)
        
        # Create a menu bar
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu('File')
        
        # Add menu actions
        open_action = QAction('Open Video', self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Create video player components
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        main_layout.addWidget(self.video_widget)
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        self.play_button = QPushButton('Play')
        self.play_button.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_button)
        
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.position_slider)
        
        main_layout.addLayout(controls_layout)
        
        # Add a subtitle display area
        self.subtitle_label = QLabel("Subtitle text will appear here")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("background-color: rgba(0, 0, 0, 128); color: white; padding: 8px;")
        main_layout.addWidget(self.subtitle_label)
        
        # Connect media player signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.playback_state_changed)
        
        # Status bar for messages
        self.statusBar().showMessage('Ready')
    
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video", "", 
                                                 "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv);;All Files (*)")
        if file_path:
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.play_button.setText('Play')
            self.statusBar().showMessage(f'Loaded: {os.path.basename(file_path)}')
    
    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def position_changed(self, position):
        self.position_slider.setValue(position)
        
        # Simulate subtitle display - in a real app this would look up subtitles
        # based on the current position
        current_seconds = position // 1000
        if current_seconds % 5 == 0:  # Show example subtitle every 5 seconds
            self.subtitle_label.setText(f"Example subtitle at {current_seconds} seconds")
        elif current_seconds % 5 == 2:  # Clear it after 2 seconds
            self.subtitle_label.setText("")
    
    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
    
    def set_position(self, position):
        self.media_player.setPosition(position)
    
    def playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText('Pause')
        else:
            self.play_button.setText('Play')

    def error_occurred(self, error, error_string):
        self.statusBar().showMessage(f"Error: {error_string}")


def main():
    app = QApplication(sys.argv)
    window = VideoPlayerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 