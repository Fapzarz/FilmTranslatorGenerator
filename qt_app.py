#!/usr/bin/env python
"""
Film Translator Generator - Qt Edition
Main application file for the Qt-based GUI version.
"""
import os
import sys
import json
from datetime import datetime
import torch
import gc
import tempfile
import subprocess

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                               QPushButton, QVBoxLayout, QHBoxLayout, QSplitter,
                               QListWidget, QFrame, QComboBox, QProgressBar,
                               QFileDialog, QMessageBox, QTabWidget, QTextEdit,
                               QSpinBox, QCheckBox, QRadioButton, QScrollArea,
                               QSlider, QStatusBar, QMenu, QMenuBar, QTreeView)
from PySide6.QtCore import Qt, QUrl, QSize, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QPixmap, QFont, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

# Import project modules (will need to be updated for Qt compatibility)
from config import (
    APP_TITLE, CONFIG_FILE, get_default_config, LANGUAGES, 
    WHISPER_MODELS, DEVICES, COMPUTE_TYPES, OUTPUT_FORMATS, 
    GITHUB_URL, APP_VERSION, TRANSLATION_PROVIDERS, 
    OPENAI_MODELS, ANTHROPIC_MODELS, DEEPSEEK_MODEL, GEMINI_MODELS,
    SUBTITLE_FONTS, SUBTITLE_COLORS, SUBTITLE_SIZES, SUBTITLE_POSITIONS,
    SUBTITLE_OUTLINE_COLORS, SUBTITLE_OUTLINE_WIDTHS, SUBTITLE_BG_COLORS, SUBTITLE_BG_OPACITY,
    DEFAULT_SHORTCUTS
)
from backend.transcribe import transcribe_video, load_whisper_model
from backend.translate import translate_text
from backend.translate import validate_gemini_key, validate_openai_key, validate_anthropic_key
from utils.format import format_output
from utils.media import extract_video_thumbnail, play_video_preview, get_video_info

# New Qt-friendly managers will replace the Tkinter-based versions
# from gui import project_manager, queue_manager, video_processor, subtitle_styler, editor_manager, shortcut_manager


class QtAppGUI(QMainWindow):
    """Main application window for Film Translator Generator - Qt Edition."""
    
    def __init__(self):
        super().__init__()
        
        # Basic window setup
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # Initialize app variables - similar to Tkinter version
        self.video_queue = []
        self.processed_file_data = {}
        self.current_processing_video = None
        self.current_project_path = None
        
        self.transcribed_segments = None
        self.translated_segments = None
        self.current_output = None
        
        # Initialize GUI variables - will use Qt mechanisms instead of StringVar
        self.target_language = LANGUAGES[0] if LANGUAGES else "English"
        self.whisper_model_name = WHISPER_MODELS[0] if WHISPER_MODELS else "base"
        self.device = DEVICES[0] if DEVICES else "cpu"
        self.compute_type = COMPUTE_TYPES.get(self.device, ["float32"])[0] if COMPUTE_TYPES else "float32"
        self.theme = "dark"  # Qt themes work differently
        self.accent_color = "blue"
        self.batch_size = 16
        self.output_format = "srt"
        self.preview_enabled = True
        self.auto_save_enabled = False
        
        # API Settings
        self.translation_provider = TRANSLATION_PROVIDERS[0] if TRANSLATION_PROVIDERS else "Gemini"
        self.gemini_api_key = ""
        self.openai_api_key = ""
        self.anthropic_api_key = ""
        self.deepseek_api_key = ""
        self.gemini_model = GEMINI_MODELS[0] if GEMINI_MODELS else ""
        self.openai_model = OPENAI_MODELS[0] if OPENAI_MODELS else ""
        self.anthropic_model = ANTHROPIC_MODELS[0] if ANTHROPIC_MODELS else ""
        
        # Gemini parameters
        self.gemini_temperature = 0.0
        self.gemini_top_p = 1.0
        self.gemini_top_k = 40
        
        # Subtitle style settings
        self.subtitle_font = SUBTITLE_FONTS[0] if SUBTITLE_FONTS else "Arial"
        self.subtitle_color = SUBTITLE_COLORS[0] if SUBTITLE_COLORS else "white"
        self.subtitle_size = SUBTITLE_SIZES[2] if SUBTITLE_SIZES else "medium"
        self.subtitle_position = SUBTITLE_POSITIONS[0] if SUBTITLE_POSITIONS else "bottom"
        self.subtitle_outline_color = SUBTITLE_OUTLINE_COLORS[0] if SUBTITLE_OUTLINE_COLORS else "black"
        self.subtitle_outline_width = SUBTITLE_OUTLINE_WIDTHS[1] if SUBTITLE_OUTLINE_WIDTHS else "1"
        self.subtitle_bg_color = SUBTITLE_BG_COLORS[0] if SUBTITLE_BG_COLORS else "black"
        self.subtitle_bg_opacity = SUBTITLE_BG_OPACITY[0] if SUBTITLE_BG_OPACITY else "0"
        
        # Media player components 
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # Setup UI components
        self.setup_ui()
        
        # Initialize managers - will be implemented later
        # self.project_manager = ProjectManager(self)
        # self.queue_manager = QueueManager(self)
        # self.video_processor = VideoProcessor(self)
        # self.subtitle_styler = SubtitleStyler(self)
        # self.editor_manager = EditorManager(self)
        # self.shortcut_manager = ShortcutManager(self)
        
        # Load configuration
        self._load_config()
        
        # Status bar for messages
        self.statusBar().showMessage('Ready')
    
    def setup_ui(self):
        """Create the main UI components."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout with splitter
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create left panel (similar to Tkinter version)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # Queue section
        queue_frame = QFrame()
        queue_frame.setFrameShape(QFrame.StyledPanel)
        queue_frame.setFrameShadow(QFrame.Raised)
        queue_layout = QVBoxLayout(queue_frame)
        
        queue_header = QLabel("Video Queue")
        queue_header.setStyleSheet("font-weight: bold;")
        queue_layout.addWidget(queue_header)
        
        self.video_listbox = QListWidget()
        self.video_listbox.currentItemChanged.connect(self.on_video_select_in_queue)
        queue_layout.addWidget(self.video_listbox)
        
        queue_buttons_layout = QHBoxLayout()
        add_button = QPushButton("Add Video(s)")
        add_button.clicked.connect(self.add_videos_to_queue)
        queue_buttons_layout.addWidget(add_button)
        
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove_from_queue)
        queue_buttons_layout.addWidget(remove_button)
        
        queue_layout.addLayout(queue_buttons_layout)
        
        # Statistics
        stats_layout = QVBoxLayout()
        self.stat_total_files = QLabel("Total Files: 0")
        self.stat_processed_files = QLabel("Processed: 0")
        self.stat_pending_files = QLabel("Pending: 0")
        self.stat_failed_files = QLabel("Failed: 0")
        
        stats_layout.addWidget(self.stat_total_files)
        stats_layout.addWidget(self.stat_processed_files)
        stats_layout.addWidget(self.stat_pending_files)
        stats_layout.addWidget(self.stat_failed_files)
        
        queue_layout.addLayout(stats_layout)
        left_layout.addWidget(queue_frame)
        
        # Settings section
        settings_frame = QFrame()
        settings_frame.setFrameShape(QFrame.StyledPanel)
        settings_frame.setFrameShadow(QFrame.Raised)
        settings_layout = QVBoxLayout(settings_frame)
        
        settings_header = QLabel("Settings")
        settings_header.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(settings_header)
        
        # Basic settings fields
        settings_layout.addWidget(QLabel("Target Language:"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(LANGUAGES)
        self.language_combo.setCurrentText(self.target_language)
        settings_layout.addWidget(self.language_combo)
        
        settings_layout.addWidget(QLabel("Whisper Model:"))
        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems(WHISPER_MODELS)
        self.whisper_model_combo.setCurrentText(self.whisper_model_name)
        settings_layout.addWidget(self.whisper_model_combo)
        
        settings_layout.addWidget(QLabel("Output Format:"))
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(OUTPUT_FORMATS)
        self.output_format_combo.setCurrentText(self.output_format)
        settings_layout.addWidget(self.output_format_combo)
        
        left_layout.addWidget(settings_frame)
        
        # Process button
        self.process_button = QPushButton("Process Selected Video")
        self.process_button.clicked.connect(self.process_selected_video)
        self.process_button.setStyleSheet("font-weight: bold; padding: 10px;")
        left_layout.addWidget(self.process_button)
        
        # Progress section
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_status = QLabel("Ready")
        progress_layout.addWidget(self.progress_status)
        
        left_layout.addWidget(progress_frame)
        
        # Add left panel to splitter
        splitter.addWidget(left_panel)
        
        # Create right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # Video preview section
        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.StyledPanel)
        preview_frame.setFrameShadow(QFrame.Raised)
        preview_layout = QVBoxLayout(preview_frame)
        
        preview_header = QLabel("Video Preview")
        preview_header.setStyleSheet("font-weight: bold;")
        preview_layout.addWidget(preview_header)
        
        # Use QVideoWidget instead of thumbnail
        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)
        preview_layout.addWidget(self.video_widget)
        
        # Video controls
        controls_layout = QHBoxLayout()
        
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_video_playback)
        controls_layout.addWidget(self.play_button)
        
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_video_position)
        controls_layout.addWidget(self.position_slider)
        
        preview_layout.addLayout(controls_layout)
        
        # Video info
        info_layout = QHBoxLayout()
        self.video_duration_label = QLabel("Duration: N/A")
        self.video_size_label = QLabel("Size: N/A")
        info_layout.addWidget(self.video_duration_label)
        info_layout.addWidget(self.video_size_label)
        preview_layout.addLayout(info_layout)
        
        right_layout.addWidget(preview_frame)
        
        # Output tabs
        self.tab_widget = QTabWidget()
        
        # Output tab
        output_tab = QWidget()
        output_layout = QVBoxLayout(output_tab)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        output_buttons_layout = QHBoxLayout()
        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_to_clipboard)
        output_buttons_layout.addWidget(copy_button)
        
        save_button = QPushButton("Save to File")
        save_button.clicked.connect(self.save_output_file)
        output_buttons_layout.addWidget(save_button)
        
        output_layout.addLayout(output_buttons_layout)
        
        self.tab_widget.addTab(output_tab, "Output")
        
        # Comparison tab
        comparison_tab = QWidget()
        comparison_layout = QVBoxLayout(comparison_tab)
        
        comparison_splitter = QSplitter(Qt.Vertical)
        
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        comparison_splitter.addWidget(self.original_text)
        
        self.translated_text = QTextEdit()
        self.translated_text.setReadOnly(True)
        comparison_splitter.addWidget(self.translated_text)
        
        comparison_layout.addWidget(comparison_splitter)
        
        self.tab_widget.addTab(comparison_tab, "Comparison")
        
        # Editor tab
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)
        
        self.editor_text = QTextEdit()
        editor_layout.addWidget(self.editor_text)
        
        editor_buttons_layout = QHBoxLayout()
        save_editor_button = QPushButton("Save Changes")
        save_editor_button.clicked.connect(self.save_editor_changes)
        editor_buttons_layout.addWidget(save_editor_button)
        
        editor_layout.addLayout(editor_buttons_layout)
        
        self.tab_widget.addTab(editor_tab, "Subtitle Editor")
        
        # Log tab
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        self.tab_widget.addTab(log_tab, "Log")
        
        right_layout.addWidget(self.tab_widget)
        
        # Add right panel to splitter
        splitter.addWidget(right_panel)
        
        # Set initial sizes for splitter
        splitter.setSizes([300, 700])
        
        # Create menu bar
        self.create_menus()
        
        # Connect media player signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.playback_state_changed)
    
    def create_menus(self):
        """Create application menus."""
        # File menu
        file_menu = self.menuBar().addMenu("File")
        
        add_videos_action = QAction("Add Video(s) to Queue", self)
        add_videos_action.triggered.connect(self.add_videos_to_queue)
        file_menu.addAction(add_videos_action)
        
        load_project_action = QAction("Load Project", self)
        load_project_action.triggered.connect(self.load_project)
        file_menu.addAction(load_project_action)
        
        save_project_action = QAction("Save Project", self)
        save_project_action.triggered.connect(self.save_project)
        file_menu.addAction(save_project_action)
        
        save_project_as_action = QAction("Save Project As...", self)
        save_project_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_project_as_action)
        
        file_menu.addSeparator()
        
        save_subtitles_action = QAction("Save Subtitles", self)
        save_subtitles_action.triggered.connect(self.save_output_file)
        file_menu.addAction(save_subtitles_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = self.menuBar().addMenu("Settings")
        
        theme_menu = settings_menu.addMenu("Theme")
        # TODO: Implement Qt theming
        
        advanced_settings_action = QAction("Advanced Settings", self)
        advanced_settings_action.triggered.connect(self.open_advanced_settings)
        settings_menu.addAction(advanced_settings_action)
        
        shortcuts_action = QAction("Keyboard Shortcuts...", self)
        shortcuts_action.triggered.connect(self.open_shortcut_settings)
        settings_menu.addAction(shortcuts_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("Help")
        
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self.open_documentation)
        help_menu.addAction(docs_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    # Core functionality methods - stubs to be implemented
    def _load_config(self):
        """Load configuration from JSON file or use defaults."""
        self.log_status("Loading configuration...")
        # Will be implemented fully
    
    def _save_config(self):
        """Save current configuration to JSON file."""
        self.log_status("Saving configuration...")
        # Will be implemented fully
    
    def log_status(self, message, level="INFO"):
        """Log a message to the status bar and log area."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # Update status bar
        self.statusBar().showMessage(message)
        
        # Update log text area
        if hasattr(self, 'log_text'):
            self.log_text.append(log_message)
    
    # Placeholder methods - to be implemented
    def add_videos_to_queue(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Video Files", "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv);;All Files (*)"
        )
        if file_paths:
            self.log_status(f"Added {len(file_paths)} videos to queue")
            # Actual implementation will come later
    
    def remove_from_queue(self):
        pass
    
    def on_video_select_in_queue(self):
        pass
    
    def process_selected_video(self):
        pass
    
    def toggle_video_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def position_changed(self, position):
        self.position_slider.setValue(position)
    
    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
    
    def set_video_position(self, position):
        self.media_player.setPosition(position)
    
    def playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText('Pause')
        else:
            self.play_button.setText('Play')
    
    def copy_to_clipboard(self):
        pass
    
    def save_output_file(self):
        pass
    
    def save_editor_changes(self):
        pass
    
    def load_project(self):
        pass
    
    def save_project(self):
        pass
    
    def save_project_as(self):
        pass
    
    def open_advanced_settings(self):
        pass
    
    def open_shortcut_settings(self):
        pass
    
    def open_documentation(self):
        pass
    
    def show_about(self):
        QMessageBox.about(
            self, 
            "About Film Translator Generator",
            f"Film Translator Generator v{APP_VERSION}\n\n"
            "A tool for automatic transcription and translation of video files.\n\n"
            "Uses Faster-Whisper for transcription and various AI models for translation."
        )
    
    def closeEvent(self, event):
        """Handle application closing."""
        self.log_status("Application closing. Saving configuration...")
        self._save_config()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = QtAppGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 