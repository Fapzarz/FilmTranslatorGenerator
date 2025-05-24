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
import webbrowser

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                               QPushButton, QVBoxLayout, QHBoxLayout, QSplitter,
                               QListWidget, QFrame, QComboBox, QProgressBar,
                               QFileDialog, QMessageBox, QTabWidget, QTextEdit,
                               QSpinBox, QCheckBox, QRadioButton, QScrollArea,
                               QSlider, QStatusBar, QMenu, QMenuBar, QTreeView,
                               QStackedWidget)
from PySide6.QtCore import Qt, QUrl, QSize, QTimer, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QPixmap, QFont, QColor, QPalette
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
from utils.media import extract_video_thumbnail, play_video_preview, get_video_info, diagnose_video_playback

# Import the Qt-compatible manager classes
from managers.project_manager import ProjectManager
from managers.queue_manager import QueueManager
from managers.preview_manager import PreviewManager
from managers.editor_manager import EditorManager
from managers.video_processor import VideoProcessor
from managers.subtitle_styler import SubtitleStyler
from managers.shortcut_manager import ShortcutManager
# Additional managers will be implemented as needed


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
        
        # Initialize default values for configuration
        self.target_language = "Indonesian"
        self.whisper_model_name = "small"
        self.device = "cpu"
        self.compute_type = "float32" 
        self.theme = "light"
        self.accent_color = "#4b6eaf"
        self.batch_size = 500
        self.output_format = "srt"
        self.preview_enabled = True
        self.auto_save_enabled = True
        
        # Initialize default values for translation providers
        self.translation_provider = "gemini"
        self.gemini_api_key = ""
        self.openai_api_key = ""
        self.anthropic_api_key = ""
        self.deepseek_api_key = ""
        self.gemini_model = "gemini-pro"
        self.openai_model = "gpt-4"
        self.anthropic_model = "claude-3-opus"
        self.gemini_temperature = 0.7
        self.gemini_top_p = 0.9
        self.gemini_top_k = 40
        
        # Initialize default values for subtitle styling
        self.subtitle_font = "Arial"
        self.subtitle_color = "White"
        self.subtitle_size = "Medium"
        self.subtitle_position = "Bottom"
        self.subtitle_outline_color = "Black"
        self.subtitle_outline_width = "1"
        self.subtitle_bg_color = "Black"
        self.subtitle_bg_opacity = "50"
        
        # Media player components (keep for advanced editor but don't display in main UI)
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.7)
        self.media_player.setAudioOutput(self.audio_output)
        
        # Connect media signals (keeping minimal error handling)
        self.media_player.errorOccurred.connect(self.handle_media_error)
        
        # Setup UI components
        self.setup_ui()
        
        # Initialize managers
        self.project_manager = ProjectManager(self)
        self.queue_manager = QueueManager(self)
        self.preview_manager = PreviewManager(self)
        self.editor_manager = EditorManager(self)
        self.video_processor = VideoProcessor(self)
        self.subtitle_styler = SubtitleStyler(self)
        self.shortcut_manager = ShortcutManager(self)
        
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
        
        # Setup context menu for video list
        self.video_listbox.setContextMenuPolicy(Qt.CustomContextMenu)
        self.video_listbox.customContextMenuRequested.connect(self.show_video_context_menu)
        
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
        
        # Add Subtitle Styler to left panel
        subtitle_styler_frame = QFrame()
        subtitle_styler_frame.setFrameShape(QFrame.StyledPanel)
        subtitle_styler_frame.setFrameShadow(QFrame.Raised)
        subtitle_styler_layout = QVBoxLayout(subtitle_styler_frame)
        
        subtitle_styler_header = QLabel("Subtitle Styling")
        subtitle_styler_header.setStyleSheet("font-weight: bold;")
        subtitle_styler_layout.addWidget(subtitle_styler_header)
        
        # Font selection
        subtitle_styler_layout.addWidget(QLabel("Font:"))
        self.subtitle_font_combo = QComboBox()
        self.subtitle_font_combo.addItems(SUBTITLE_FONTS)
        self.subtitle_font_combo.setCurrentText(self.subtitle_font)
        subtitle_styler_layout.addWidget(self.subtitle_font_combo)
        
        # Color selection
        subtitle_styler_layout.addWidget(QLabel("Color:"))
        self.subtitle_color_combo = QComboBox()
        self.subtitle_color_combo.addItems(SUBTITLE_COLORS)
        self.subtitle_color_combo.setCurrentText(self.subtitle_color)
        subtitle_styler_layout.addWidget(self.subtitle_color_combo)
        
        # Size selection
        subtitle_styler_layout.addWidget(QLabel("Size:"))
        self.subtitle_size_combo = QComboBox()
        self.subtitle_size_combo.addItems(SUBTITLE_SIZES)
        self.subtitle_size_combo.setCurrentText(self.subtitle_size)
        subtitle_styler_layout.addWidget(self.subtitle_size_combo)
        
        # Position selection
        subtitle_styler_layout.addWidget(QLabel("Position:"))
        self.subtitle_position_combo = QComboBox()
        self.subtitle_position_combo.addItems(SUBTITLE_POSITIONS)
        self.subtitle_position_combo.setCurrentText(self.subtitle_position)
        subtitle_styler_layout.addWidget(self.subtitle_position_combo)
        
        # Apply style button
        apply_style_button = QPushButton("Apply Style")
        apply_style_button.clicked.connect(lambda: self.subtitle_styler.apply_subtitle_style())
        subtitle_styler_layout.addWidget(apply_style_button)
        
        left_layout.addWidget(subtitle_styler_frame)
        
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
        
        # Settings frame (moved to right panel)
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
        
        right_layout.addWidget(settings_frame)
        
        # Video preview section
        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.StyledPanel)
        preview_frame.setFrameShadow(QFrame.Raised)
        preview_layout = QVBoxLayout(preview_frame)
        
        preview_header = QLabel("Video Information")
        preview_header.setStyleSheet("font-weight: bold;")
        preview_layout.addWidget(preview_header)
        
        # Info container
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        
        # File info dan action buttons
        file_info_layout = QHBoxLayout()
        self.file_name_label = QLabel("No video selected")
        file_info_layout.addWidget(self.file_name_label)
        file_info_layout.addStretch()
        
        open_editor_button = QPushButton("Open Advanced Editor")
        open_editor_button.clicked.connect(self.open_advanced_subtitle_editor)
        open_editor_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 16px;")
        file_info_layout.addWidget(open_editor_button)
        
        info_layout.addLayout(file_info_layout)
        
        # Video info dalam layout horizontal
        video_info_layout = QHBoxLayout()
        self.video_duration_label = QLabel("Duration: N/A")
        self.video_size_label = QLabel("Size: N/A")
        video_info_layout.addWidget(self.video_duration_label)
        video_info_layout.addWidget(self.video_size_label)
        info_layout.addLayout(video_info_layout)

        # Detailed video technical info
        video_tech_info_layout_1 = QHBoxLayout()
        self.video_codec_label = QLabel("Video Codec: N/A")
        self.audio_codec_label = QLabel("Audio Codec: N/A")
        video_tech_info_layout_1.addWidget(self.video_codec_label)
        video_tech_info_layout_1.addWidget(self.audio_codec_label)
        info_layout.addLayout(video_tech_info_layout_1)

        video_tech_info_layout_2 = QHBoxLayout()
        self.bitrate_label = QLabel("Bitrate: N/A")
        self.dimensions_label = QLabel("Dimensions: N/A") # Added for completeness
        video_tech_info_layout_2.addWidget(self.bitrate_label)
        video_tech_info_layout_2.addWidget(self.dimensions_label)
        info_layout.addLayout(video_tech_info_layout_2)
        
        # Processing status
        self.processing_status_label = QLabel("Status: Not processed")
        info_layout.addWidget(self.processing_status_label)
        
        preview_layout.addWidget(info_container)
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
        
        # Theme menu implementation
        theme_menu = settings_menu.addMenu("Theme")
        
        light_theme_action = QAction("Light", self)
        light_theme_action.triggered.connect(lambda: self.apply_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("Dark", self)
        dark_theme_action.triggered.connect(lambda: self.apply_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
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
        
        # Tools menu
        tools_menu = self.menuBar().addMenu("Tools")
        
        advanced_subtitle_editor_action = QAction("Advanced Subtitle Editor", self)
        advanced_subtitle_editor_action.triggered.connect(self.open_advanced_subtitle_editor)
        tools_menu.addAction(advanced_subtitle_editor_action)
    
    # Core functionality methods - update to use manager implementations
    def _load_config(self):
        """Load configuration from JSON file or use defaults."""
        self.log_status("Loading configuration...")
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Apply saved configuration
                self.target_language = config.get('target_language', self.target_language)
                self.whisper_model_name = config.get('whisper_model', self.whisper_model_name)
                self.device = config.get('device', self.device)
                self.compute_type = config.get('compute_type', self.compute_type)
                self.theme = config.get('theme', self.theme)
                self.accent_color = config.get('accent_color', self.accent_color)
                self.batch_size = config.get('batch_size', self.batch_size)
                self.output_format = config.get('output_format', self.output_format)
                self.preview_enabled = config.get('preview', self.preview_enabled)
                self.auto_save_enabled = config.get('auto_save', self.auto_save_enabled)
                
                # Load translation provider settings
                self.translation_provider = config.get('translation_provider', self.translation_provider)
                self.gemini_api_key = config.get('gemini_api_key', self.gemini_api_key)
                self.openai_api_key = config.get('openai_api_key', self.openai_api_key)
                self.anthropic_api_key = config.get('anthropic_api_key', self.anthropic_api_key)
                self.deepseek_api_key = config.get('deepseek_api_key', self.deepseek_api_key)
                self.gemini_model = config.get('gemini_model', self.gemini_model)
                self.openai_model = config.get('openai_model', self.openai_model)
                self.anthropic_model = config.get('anthropic_model', self.anthropic_model)
                
                # Load Gemini model parameters
                self.gemini_temperature = config.get('gemini_temperature', self.gemini_temperature)
                self.gemini_top_p = config.get('gemini_top_p', self.gemini_top_p)
                self.gemini_top_k = config.get('gemini_top_k', self.gemini_top_k)
                
                # Load subtitle style settings
                self.subtitle_font = config.get('subtitle_font', self.subtitle_font)
                self.subtitle_color = config.get('subtitle_color', self.subtitle_color)
                self.subtitle_size = config.get('subtitle_size', self.subtitle_size)
                self.subtitle_position = config.get('subtitle_position', self.subtitle_position)
                self.subtitle_outline_color = config.get('subtitle_outline_color', self.subtitle_outline_color)
                self.subtitle_outline_width = config.get('subtitle_outline_width', self.subtitle_outline_width)
                self.subtitle_bg_color = config.get('subtitle_bg_color', self.subtitle_bg_color)
                self.subtitle_bg_opacity = config.get('subtitle_bg_opacity', self.subtitle_bg_opacity)
                
                # Load processed file data
                self.processed_file_data = config.get('processed_file_data', {})
                
                # Populate video_queue from processed_file_data keys
                self.video_queue = list(self.processed_file_data.keys())

                # Update UI with loaded settings
                self.language_combo.setCurrentText(self.target_language)
                self.whisper_model_combo.setCurrentText(self.whisper_model_name)
                self.output_format_combo.setCurrentText(self.output_format)
                
                # Apply the saved theme
                self.apply_theme(self.theme)
                
                # Load queue from config after other settings are applied
                if hasattr(self, 'queue_manager'): # Ensure queue_manager is initialized
                    self.queue_manager.load_queue_from_config()

                self.log_status("Configuration loaded successfully.")
            else:
                self.log_status("No configuration file found. Using defaults.")
        except Exception as e:
            self.log_status(f"Error loading configuration: {e}", "ERROR")
    
    def _save_config(self):
        """Save current configuration to JSON file using the secure save_config function."""
        self.log_status("Saving configuration...")
        try:
            # Import the secure save_config function
            from config import save_config
            
            # Update variables from UI
            self.target_language = self.language_combo.currentText()
            self.whisper_model_name = self.whisper_model_combo.currentText()
            self.output_format = self.output_format_combo.currentText()
            
            config = {
                'target_language': self.target_language,
                'whisper_model': self.whisper_model_name,
                'device': self.device,
                'compute_type': self.compute_type,
                'theme': self.theme,
                'accent_color': self.accent_color,
                'batch_size': self.batch_size,
                'output_format': self.output_format,
                'preview': self.preview_enabled,
                'auto_save': self.auto_save_enabled,
                'translation_provider': self.translation_provider,
                'gemini_api_key': self.gemini_api_key,
                'openai_api_key': self.openai_api_key,
                'anthropic_api_key': self.anthropic_api_key,
                'deepseek_api_key': self.deepseek_api_key,
                'gemini_model': self.gemini_model,
                'openai_model': self.openai_model,
                'anthropic_model': self.anthropic_model,
                'gemini_temperature': self.gemini_temperature,
                'gemini_top_p': self.gemini_top_p,
                'gemini_top_k': self.gemini_top_k,
                'subtitle_font': self.subtitle_font,
                'subtitle_color': self.subtitle_color,
                'subtitle_size': self.subtitle_size,
                'subtitle_position': self.subtitle_position,
                'subtitle_outline_color': self.subtitle_outline_color,
                'subtitle_outline_width': self.subtitle_outline_width,
                'subtitle_bg_color': self.subtitle_bg_color,
                'subtitle_bg_opacity': self.subtitle_bg_opacity,
                'processed_file_data': self.processed_file_data
            }
            
            # Use the secure save_config function that handles encryption
            save_config(config)
            
            self.log_status("Configuration saved successfully.")
        except Exception as e:
            self.log_status(f"Error saving configuration: {e}", "ERROR")
    
    def log_status(self, message, level="INFO"):
        """Log a message to the status bar and log area."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        
        # Update status bar
        self.statusBar().showMessage(message)
        
        # Update log text area
        if hasattr(self, 'log_text'):
            self.log_text.append(log_message)
    
    # Implement core functionality methods using manager classes
    def add_videos_to_queue(self):
        """Add videos to the processing queue."""
        self.queue_manager.add_videos_to_queue()
    
    def remove_from_queue(self):
        """Remove the selected video from the queue."""
        self.queue_manager.remove_selected_video_from_queue()
        
        # Reset informasi video
        self.file_name_label.setText("No video selected")
        self.video_duration_label.setText("Duration: N/A")
        self.video_size_label.setText("Size: N/A")
        self.video_codec_label.setText("Video Codec: N/A")
        self.audio_codec_label.setText("Audio Codec: N/A")
        self.bitrate_label.setText("Bitrate: N/A")
        self.dimensions_label.setText("Dimensions: N/A")
        self.processing_status_label.setText("Status: Not processed")
    
    def on_video_select_in_queue(self):
        """Handle selection change in the video queue."""
        current_item = self.video_listbox.currentItem() # Use currentItem to get the QListWidgetItem
        
        if current_item is not None:
            current_row = self.video_listbox.row(current_item) # Get row index from item
            if 0 <= current_row < len(self.video_queue):
                video_path = self.video_queue[current_row]
                
                # Dapatkan informasi video
                video_info = get_video_info(video_path)
                
                # Update labels
                self.file_name_label.setText(f"Selected: {os.path.basename(video_path)}")
                self.video_duration_label.setText(f"Duration: {video_info.get('duration', 'N/A')}")
                self.video_size_label.setText(f"Size: {video_info.get('size', 'N/A')}")
                self.video_codec_label.setText(f"Video Codec: {video_info.get('video_codec', 'N/A')}")
                self.audio_codec_label.setText(f"Audio Codec: {video_info.get('audio_codec', 'N/A')}")
                self.bitrate_label.setText(f"Bitrate: {video_info.get('bitrate', 'N/A')}")
                self.dimensions_label.setText(f"Dimensions: {video_info.get('dimensions', 'N/A')}")

                # Update processing status
                file_data = self.processed_file_data.get(video_path, {})
                status = file_data.get('status', 'Not processed')
                self.processing_status_label.setText(f"Status: {status}")

                # Call queue_manager's selection update AFTER updating local labels
                self.queue_manager.on_video_select_in_queue()
                return # Explicitly return after successful update

        # If no valid item is selected or row is out of bounds, reset labels
        self.file_name_label.setText("No video selected")
        self.video_duration_label.setText("Duration: N/A")
        self.video_size_label.setText("Size: N/A")
        self.video_codec_label.setText("Video Codec: N/A")
        self.audio_codec_label.setText("Audio Codec: N/A")
        self.bitrate_label.setText("Bitrate: N/A")
        self.dimensions_label.setText("Dimensions: N/A")
        self.processing_status_label.setText("Status: Not processed")
        # Also call queue_manager's update for deselection if necessary
        self.queue_manager.on_video_select_in_queue() # Assuming this handles deselection appropriately
    
    def process_selected_video(self):
        """Process the selected video."""
        self.video_processor.start_processing()
    
    def copy_to_clipboard(self):
        """Copy the current output to the clipboard."""
        text = self.output_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.log_status("Copied output to clipboard.")
        else:
            self.log_status("No output to copy.", "WARNING")
    
    def save_output_file(self):
        """Save the current output to a file."""
        content = self.output_text.toPlainText()
        if not content:
            QMessageBox.warning(self, "Warning", "No output content to save.")
            return
        
        format_extension = self.output_format
        
        default_filename = "subtitle"
        if self.video_listbox.currentRow() >= 0 and self.video_listbox.currentRow() < len(self.video_queue):
            video_path = self.video_queue[self.video_listbox.currentRow()]
            default_filename = os.path.splitext(os.path.basename(video_path))[0]
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Subtitle File",
            default_filename + "." + format_extension,
            f"Subtitle Files (*.{format_extension});;All Files (*)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log_status(f"Output saved to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {e}")
                self.log_status(f"Error saving file: {e}", "ERROR")
    
    def save_editor_changes(self):
        """Save changes from the subtitle editor."""
        self.editor_manager.save_editor_changes()
    
    def load_project(self):
        """Load a project file."""
        self.project_manager.load_project()
    
    def save_project(self):
        """Save the current project."""
        self.project_manager.save_project()
    
    def save_project_as(self):
        """Save the current project with a new filename."""
        self.project_manager.save_project_as()
    
    def open_advanced_settings(self):
        """Open the advanced settings dialog."""
        from dialogs.advanced_settings import AdvancedSettingsDialog
        dialog = AdvancedSettingsDialog(self)
        dialog.settings_updated.connect(lambda: self.log_status("Advanced settings applied."))
        dialog.exec()
    
    def open_shortcut_settings(self):
        """Open the keyboard shortcuts dialog."""
        self.shortcut_manager.open_shortcut_dialog()
    
    def open_documentation(self):
        """Open the documentation."""
        # Path to documentation index
        docs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "index.html")
        
        # Check if documentation exists
        if os.path.exists(docs_path):
            # Open in default browser
            self.log_status("Opening documentation in browser...")
            webbrowser.open(f"file://{os.path.abspath(docs_path)}")
        else:
            self.log_status("Documentation files not found.", "WARNING")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Documentation Not Found",
                "Documentation files could not be found. Please check your installation."
            )
    
    def show_about(self):
        """Show the about dialog."""
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

    def handle_media_error(self, error, error_string):
        """Handle media player errors."""
        self.log_status(f"Media Player Error: {error_string}", "ERROR")
        QMessageBox.critical(
            self,
            "Media Player Error",
            f"An error occurred while playing the video:\n{error_string}\n\nMake sure you have the necessary codecs installed."
        )

    # media_status_changed method removed since we no longer need it

    def diagnose_playback_issue(self):
        """Run diagnostics on the currently selected video to identify playback issues."""
        current_row = self.video_listbox.currentRow()
        if current_row < 0 or current_row >= len(self.video_queue):
            self.log_status("No video selected for diagnosis", "WARNING")
            return
        
        video_path = self.video_queue[current_row]
        self.log_status(f"Running diagnostics on: {video_path}")
        
        # Get detailed diagnostic information
        diag_result = diagnose_video_playback(video_path)
        
        # Log diagnostics information
        self.log_status("Diagnostic Results:")
        for key, value in diag_result.items():
            if key != 'issues':
                self.log_status(f"  {key}: {value}")
        
        if diag_result['issues']:
            self.log_status("Issues found:")
            for issue in diag_result['issues']:
                self.log_status(f"  - {issue}", "WARNING")

    def show_video_context_menu(self, position):
        """Show context menu for video list."""
        current_row = self.video_listbox.currentRow()
        
        # Only show context menu if an item is selected
        if current_row >= 0:
            context_menu = QMenu()
            
            # Diagnose action
            diagnose_action = QAction("Diagnose Video Playback", self)
            diagnose_action.triggered.connect(self.diagnose_playback_issue)
            context_menu.addAction(diagnose_action)
            
            # Advanced subtitle editor action
            edit_action = QAction("Open Advanced Subtitle Editor", self)
            edit_action.triggered.connect(self.open_advanced_subtitle_editor)
            context_menu.addAction(edit_action)
            
            # Remove action
            remove_action = QAction("Remove from Queue", self)
            remove_action.triggered.connect(self.remove_from_queue)
            context_menu.addAction(remove_action)
            
            # Show context menu at cursor position
            context_menu.exec(self.video_listbox.mapToGlobal(position))

    def apply_theme(self, theme_name):
        """Apply the selected theme to the application."""
        self.theme = theme_name
        self.log_status(f"Applying {theme_name} theme")
        
        app = QApplication.instance()
        
        if theme_name == "dark":
            # Sun Valley inspired dark theme
            app.setStyle("Fusion")  # Use Fusion style as base
            dark_palette = QPalette()
            
            # Warm dark colors
            bg_color = QColor(32, 32, 32)
            text_color = QColor(240, 240, 240)
            accent_color = QColor(75, 110, 175)  # Soft blue accent
            secondary_bg = QColor(45, 45, 45)
            
            # Set colors for dark theme
            dark_palette.setColor(QPalette.Window, bg_color)
            dark_palette.setColor(QPalette.WindowText, text_color)
            dark_palette.setColor(QPalette.Base, secondary_bg)
            dark_palette.setColor(QPalette.AlternateBase, bg_color)
            dark_palette.setColor(QPalette.ToolTipBase, bg_color)
            dark_palette.setColor(QPalette.ToolTipText, text_color)
            dark_palette.setColor(QPalette.Text, text_color)
            dark_palette.setColor(QPalette.Button, bg_color)
            dark_palette.setColor(QPalette.ButtonText, text_color)
            dark_palette.setColor(QPalette.Link, accent_color)
            dark_palette.setColor(QPalette.Highlight, accent_color)
            dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
            
            # Apply the palette
            app.setPalette(dark_palette)
            
            # Custom style sheet for additional elements
            stylesheet = """
            QMainWindow, QDialog {
                background-color: #202020;
                border-radius: 8px;
            }
            QFrame {
                border-radius: 8px;
            }
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                background-color: #2d2d2d;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #313131;
                color: #e0e0e0;
                padding: 8px 12px;
                border: none;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #4b6eaf;
                color: white;
            }
            QPushButton {
                background-color: #404040;
                color: #f0f0f0;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4b6eaf;
            }
            QPushButton:pressed {
                background-color: #3c5a91;
            }
            QComboBox {
                background-color: #404040;
                color: #f0f0f0;
                border: 1px solid #505050;
                border-radius: 6px;
                padding: 6px 12px;
                min-height: 24px;
            }
            QComboBox::drop-down {
                border: none;
                border-left: 1px solid #505050;
                width: 20px;
            }
            QLineEdit, QTextEdit {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #505050;
                border-radius: 6px;
                padding: 6px;
            }
            QListWidget {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #505050;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #4b6eaf;
            }
            QListWidget::item:hover {
                background-color: #3c5a91;
            }
            QMenuBar {
                background-color: #202020;
                color: #f0f0f0;
                border-bottom: 1px solid #3a3a3a;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #4b6eaf;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #505050;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 28px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4b6eaf;
            }
            QMessageBox {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border-radius: 8px;
            }
            QLabel {
                color: #f0f0f0;
            }
            QProgressBar {
                border: 1px solid #505050;
                border-radius: 6px;
                background-color: #2d2d2d;
                text-align: center;
                color: white;
                min-height: 16px;
            }
            QProgressBar::chunk {
                background-color: #4b6eaf;
                border-radius: 5px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #505050;
                height: 8px;
                background: #2d2d2d;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4b6eaf;
                border: none;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QScrollBar:vertical {
                border: none;
                background: #2d2d2d;
                width: 12px;
                border-radius: 6px;
                margin: 12px 0px;
            }
            QScrollBar::handle:vertical {
                background: #505050;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 10px;
            }
            QSpinBox {
                background-color: #2d2d2d;
                color: #f0f0f0;
                border: 1px solid #505050;
                border-radius: 6px;
                padding: 4px;
            }
            """
            app.setStyleSheet(stylesheet)
        else:
            # Sun Valley inspired light theme
            app.setStyle("Fusion")  # Use Fusion style as base
            light_palette = QPalette()
            
            # Clean light colors
            bg_color = QColor(245, 245, 250)
            text_color = QColor(30, 30, 30)
            accent_color = QColor(75, 110, 175)  # Same blue accent as dark theme
            secondary_bg = QColor(255, 255, 255)
            
            # Set colors for light theme
            light_palette.setColor(QPalette.Window, bg_color)
            light_palette.setColor(QPalette.WindowText, text_color)
            light_palette.setColor(QPalette.Base, secondary_bg)
            light_palette.setColor(QPalette.AlternateBase, bg_color)
            light_palette.setColor(QPalette.ToolTipBase, secondary_bg)
            light_palette.setColor(QPalette.ToolTipText, text_color)
            light_palette.setColor(QPalette.Text, text_color)
            light_palette.setColor(QPalette.Button, bg_color)
            light_palette.setColor(QPalette.ButtonText, text_color)
            light_palette.setColor(QPalette.Link, accent_color)
            light_palette.setColor(QPalette.Highlight, accent_color)
            light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
            
            # Apply the palette
            app.setPalette(light_palette)
            
            # Custom style sheet for additional elements
            stylesheet = """
            QMainWindow, QDialog {
                background-color: #f5f5fa;
                border-radius: 8px;
            }
            QFrame {
                border-radius: 8px;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background-color: #ffffff;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #efefef;
                color: #202020;
                padding: 8px 12px;
                border: none;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #4b6eaf;
                color: white;
            }
            QPushButton {
                background-color: #e8e8e8;
                color: #202020;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4b6eaf;
                color: white;
            }
            QPushButton:pressed {
                background-color: #3c5a91;
                color: white;
            }
            QComboBox {
                background-color: #ffffff;
                color: #202020;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 6px 12px;
                min-height: 24px;
            }
            QComboBox::drop-down {
                border: none;
                border-left: 1px solid #d0d0d0;
                width: 20px;
            }
            QLineEdit, QTextEdit {
                background-color: #ffffff;
                color: #202020;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 6px;
            }
            QListWidget {
                background-color: #ffffff;
                color: #202020;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #4b6eaf;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e8e8e8;
            }
            QMenuBar {
                background-color: #f5f5fa;
                color: #202020;
                border-bottom: 1px solid #e0e0e0;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #4b6eaf;
                color: white;
            }
            QMenu {
                background-color: #ffffff;
                color: #202020;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 28px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4b6eaf;
                color: white;
            }
            QMessageBox {
                background-color: #ffffff;
                color: #202020;
                border-radius: 8px;
            }
            QLabel {
                color: #202020;
            }
            QProgressBar {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background-color: #ffffff;
                text-align: center;
                color: #202020;
                min-height: 16px;
            }
            QProgressBar::chunk {
                background-color: #4b6eaf;
                border-radius: 5px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #d0d0d0;
                height: 8px;
                background: #ffffff;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4b6eaf;
                border: none;
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                border-radius: 6px;
                margin: 12px 0px;
            }
            QScrollBar::handle:vertical {
                background: #d0d0d0;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 10px;
            }
            QSpinBox {
                background-color: #ffffff;
                color: #202020;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 4px;
            }
            """
            app.setStyleSheet(stylesheet)
        
        # Save the theme setting
        self._save_config()

    def open_advanced_subtitle_editor(self):
        """Open the advanced subtitle editor dialog."""
        current_row = self.video_listbox.currentRow()
        if current_row < 0 or current_row >= len(self.video_queue):
            QMessageBox.warning(self, "Warning", "Please select a video first.")
            return
        
        video_path = self.video_queue[current_row]
        segments = None
        
        # Get current segments if available
        file_data = self.processed_file_data.get(video_path)
        if file_data:
            if file_data.get('translated_segments'):
                segments = file_data.get('translated_segments')
            elif file_data.get('transcribed_segments'):
                segments = file_data.get('transcribed_segments')
        
        try:
            # Import here to avoid circular imports
            from dialogs.advanced_subtitle_editor import AdvancedSubtitleEditor
            dialog = AdvancedSubtitleEditor(self, segments=segments, video_path=video_path)
            
            # Connect the signal for updated segments
            dialog.subtitle_updated.connect(lambda updated_segments: self.update_segments_from_editor(video_path, updated_segments))
            
            # Show dialog
            dialog.exec()
        except ImportError as e:
            QMessageBox.critical(self, "Error", f"Failed to load Advanced Subtitle Editor: {e}")
            self.log_status(f"Error loading Advanced Subtitle Editor: {e}", "ERROR")
    
    def update_segments_from_editor(self, video_path, updated_segments):
        """Update segments data from Advanced Subtitle Editor."""
        if video_path not in self.processed_file_data:
            self.processed_file_data[video_path] = {'status': 'Pending'}
        
        file_data = self.processed_file_data[video_path]
        
        # Update translated segments with edited segments
        file_data['translated_segments'] = updated_segments
        
        # If the file hasn't been previously processed, mark it as done
        if file_data.get('status') == 'Pending':
            file_data['status'] = 'Done'
        
        # Update UI
        self.queue_manager.on_video_select_in_queue()
        self.log_status(f"Updated subtitle segments for {os.path.basename(video_path)}")
        
        # Save configuration with updated data
        self._save_config()

def main():
    app = QApplication(sys.argv)
    window = QtAppGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 