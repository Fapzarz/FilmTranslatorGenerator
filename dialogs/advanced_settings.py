"""
Advanced settings dialog for the Film Translator Generator Qt Edition.
"""
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                              QWidget, QLabel, QLineEdit, QComboBox, QCheckBox,
                              QPushButton, QGroupBox, QFormLayout, QSpinBox,
                              QDoubleSpinBox, QSlider, QMessageBox, QFrame)
from PySide6.QtCore import Qt, Signal, Slot

from config import (
    TRANSLATION_PROVIDERS, GEMINI_MODELS, OPENAI_MODELS,
    ANTHROPIC_MODELS, DEEPSEEK_MODEL
)

class AdvancedSettingsDialog(QDialog):
    """Advanced settings dialog with multiple tabs for configuration."""
    
    settings_updated = Signal()  # Signal emitted when settings are updated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.app = parent
        self.setWindowTitle("Advanced Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.tab_translation = QWidget()
        self.tab_transcription = QWidget()
        self.tab_appearance = QWidget()
        self.tab_advanced = QWidget()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.tab_translation, "Translation")
        self.tab_widget.addTab(self.tab_transcription, "Transcription")
        self.tab_widget.addTab(self.tab_appearance, "Appearance")
        self.tab_widget.addTab(self.tab_advanced, "Advanced")
        
        # Set up each tab
        self.setup_translation_tab()
        self.setup_transcription_tab()
        self.setup_appearance_tab()
        self.setup_advanced_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Buttons at the bottom
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def setup_translation_tab(self):
        """Set up the translation tab."""
        layout = QVBoxLayout(self.tab_translation)
        
        # Translation provider selection
        provider_group = QGroupBox("Translation Provider")
        provider_layout = QVBoxLayout()
        
        provider_label = QLabel("Select Provider:")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(TRANSLATION_PROVIDERS)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        
        # Deskripsi provider
        self.provider_description = QLabel()
        self.provider_description.setStyleSheet("font-style: italic; color: #666;")
        self.provider_description.setWordWrap(True)
        
        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addWidget(self.provider_description)
        
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)
        
        # Container for provider-specific settings
        self.provider_settings_container = QWidget()
        self.provider_settings_layout = QVBoxLayout(self.provider_settings_container)
        layout.addWidget(self.provider_settings_container)
        
        # Create provider-specific settings widgets
        self.setup_gemini_settings()
        self.setup_openai_settings()
        self.setup_anthropic_settings()
        self.setup_deepseek_settings()
        self.setup_local_model_settings()
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def setup_gemini_settings(self):
        """Set up Gemini-specific settings."""
        self.gemini_settings = QGroupBox("Google Gemini Settings")
        form_layout = QFormLayout()
        
        # API Key and validation layout
        key_layout = QHBoxLayout()
        
        self.gemini_api_key = QLineEdit()
        self.gemini_api_key.setEchoMode(QLineEdit.Password)
        self.gemini_api_key.setPlaceholderText("Enter Gemini API Key")
        key_layout.addWidget(self.gemini_api_key)
        
        self.gemini_validate_button = QPushButton("Validate")
        self.gemini_validate_button.clicked.connect(self.validate_gemini_key)
        key_layout.addWidget(self.gemini_validate_button)
        
        form_layout.addRow("API Key:", key_layout)
        
        self.gemini_model = QComboBox()
        self.gemini_model.addItems(GEMINI_MODELS)
        
        self.gemini_temperature = QDoubleSpinBox()
        self.gemini_temperature.setRange(0.0, 1.0)
        self.gemini_temperature.setSingleStep(0.1)
        self.gemini_temperature.setDecimals(1)
        
        self.gemini_top_p = QDoubleSpinBox()
        self.gemini_top_p.setRange(0.0, 1.0)
        self.gemini_top_p.setSingleStep(0.1)
        self.gemini_top_p.setDecimals(1)
        
        self.gemini_top_k = QSpinBox()
        self.gemini_top_k.setRange(1, 100)
        self.gemini_top_k.setSingleStep(1)
        
        form_layout.addRow("Model:", self.gemini_model)
        form_layout.addRow("Temperature:", self.gemini_temperature)
        form_layout.addRow("Top P:", self.gemini_top_p)
        form_layout.addRow("Top K:", self.gemini_top_k)
        
        self.gemini_settings.setLayout(form_layout)
        self.provider_settings_layout.addWidget(self.gemini_settings)
        self.gemini_settings.hide()
    
    def setup_openai_settings(self):
        """Set up OpenAI-specific settings."""
        self.openai_settings = QGroupBox("OpenAI Settings")
        form_layout = QFormLayout()
        
        # API Key and validation layout
        key_layout = QHBoxLayout()
        
        self.openai_api_key = QLineEdit()
        self.openai_api_key.setEchoMode(QLineEdit.Password)
        self.openai_api_key.setPlaceholderText("Enter OpenAI API Key")
        key_layout.addWidget(self.openai_api_key)
        
        self.openai_validate_button = QPushButton("Validate")
        self.openai_validate_button.clicked.connect(self.validate_openai_key)
        key_layout.addWidget(self.openai_validate_button)
        
        form_layout.addRow("API Key:", key_layout)
        
        self.openai_model = QComboBox()
        self.openai_model.addItems(OPENAI_MODELS)
        
        form_layout.addRow("Model:", self.openai_model)
        
        self.openai_settings.setLayout(form_layout)
        self.provider_settings_layout.addWidget(self.openai_settings)
        self.openai_settings.hide()
    
    def setup_anthropic_settings(self):
        """Set up Anthropic-specific settings."""
        self.anthropic_settings = QGroupBox("Anthropic Settings")
        form_layout = QFormLayout()
        
        # API Key and validation layout
        key_layout = QHBoxLayout()
        
        self.anthropic_api_key = QLineEdit()
        self.anthropic_api_key.setEchoMode(QLineEdit.Password)
        self.anthropic_api_key.setPlaceholderText("Enter Anthropic API Key")
        key_layout.addWidget(self.anthropic_api_key)
        
        self.anthropic_validate_button = QPushButton("Validate")
        self.anthropic_validate_button.clicked.connect(self.validate_anthropic_key)
        key_layout.addWidget(self.anthropic_validate_button)
        
        form_layout.addRow("API Key:", key_layout)
        
        self.anthropic_model = QComboBox()
        self.anthropic_model.addItems(ANTHROPIC_MODELS)
        
        form_layout.addRow("Model:", self.anthropic_model)
        
        self.anthropic_settings.setLayout(form_layout)
        self.provider_settings_layout.addWidget(self.anthropic_settings)
        self.anthropic_settings.hide()
    
    def setup_deepseek_settings(self):
        """Set up DeepSeek-specific settings."""
        self.deepseek_settings = QGroupBox("DeepSeek Settings")
        form_layout = QFormLayout()
        
        # API Key and validation layout
        key_layout = QHBoxLayout()
        
        self.deepseek_api_key = QLineEdit()
        self.deepseek_api_key.setEchoMode(QLineEdit.Password)
        self.deepseek_api_key.setPlaceholderText("Enter DeepSeek API Key")
        key_layout.addWidget(self.deepseek_api_key)
        
        self.deepseek_validate_button = QPushButton("Validate")
        self.deepseek_validate_button.clicked.connect(self.validate_deepseek_key)
        key_layout.addWidget(self.deepseek_validate_button)
        
        form_layout.addRow("API Key:", key_layout)
        
        model_label = QLabel(f"Model: {DEEPSEEK_MODEL}")
        model_label.setEnabled(False)  # Disabled since it's fixed
        
        form_layout.addRow(model_label)
        
        self.deepseek_settings.setLayout(form_layout)
        self.provider_settings_layout.addWidget(self.deepseek_settings)
        self.deepseek_settings.hide()
    
    def setup_local_model_settings(self):
        """Set up local model-specific settings."""
        self.local_model_settings = QGroupBox("Local Model Settings")
        form_layout = QFormLayout()
        
        label = QLabel("Local model support not yet implemented.")
        form_layout.addRow(label)
        
        self.local_model_settings.setLayout(form_layout)
        self.provider_settings_layout.addWidget(self.local_model_settings)
        self.local_model_settings.hide()
    
    def setup_transcription_tab(self):
        """Set up the transcription tab."""
        layout = QVBoxLayout(self.tab_transcription)
        
        # Whisper settings
        whisper_group = QGroupBox("Whisper Transcription Settings")
        whisper_layout = QFormLayout()
        
        # Batch size
        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 500)
        self.batch_size.setSingleStep(1)
        whisper_layout.addRow("Batch Size:", self.batch_size)
        
        # Device selection (CPU, CUDA, etc.)
        self.device_combo = QComboBox()
        self.device_combo.addItems(["cpu", "cuda"])
        whisper_layout.addRow("Device:", self.device_combo)
        
        # Compute type
        self.compute_type_combo = QComboBox()
        self.compute_type_combo.addItems(["float32", "float16", "int8"])
        whisper_layout.addRow("Compute Type:", self.compute_type_combo)
        
        # Auto-save option
        self.auto_save_check = QCheckBox("Auto-save subtitles after processing")
        whisper_layout.addRow(self.auto_save_check)
        
        whisper_group.setLayout(whisper_layout)
        layout.addWidget(whisper_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def setup_appearance_tab(self):
        """Set up the appearance tab."""
        layout = QVBoxLayout(self.tab_appearance)
        
        # Theme settings
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        theme_layout.addRow("Theme:", self.theme_combo)
        
        self.accent_color_combo = QComboBox()
        self.accent_color_combo.addItems(["Blue", "Green", "Red", "Purple", "Orange"])
        theme_layout.addRow("Accent Color:", self.accent_color_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def setup_advanced_tab(self):
        """Set up the advanced tab."""
        layout = QVBoxLayout(self.tab_advanced)
        
        # Misc settings
        misc_group = QGroupBox("Miscellaneous Settings")
        misc_layout = QFormLayout()
        
        self.preview_check = QCheckBox("Enable preview")
        misc_layout.addRow(self.preview_check)
        
        misc_group.setLayout(misc_layout)
        layout.addWidget(misc_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
    
    def load_current_settings(self):
        """Load current settings from the main app."""
        # Translation provider
        current_provider = self.app.translation_provider
        self.provider_combo.setCurrentText(current_provider)
        
        # Gemini settings
        self.gemini_api_key.setText(self.app.gemini_api_key)
        self.gemini_model.setCurrentText(self.app.gemini_model)
        self.gemini_temperature.setValue(self.app.gemini_temperature)
        self.gemini_top_p.setValue(self.app.gemini_top_p)
        self.gemini_top_k.setValue(self.app.gemini_top_k)
        
        # OpenAI settings
        self.openai_api_key.setText(self.app.openai_api_key)
        self.openai_model.setCurrentText(self.app.openai_model)
        
        # Anthropic settings
        self.anthropic_api_key.setText(self.app.anthropic_api_key)
        self.anthropic_model.setCurrentText(self.app.anthropic_model)
        
        # DeepSeek settings
        self.deepseek_api_key.setText(self.app.deepseek_api_key)
        
        # Transcription settings
        self.batch_size.setValue(self.app.batch_size)
        self.device_combo.setCurrentText(self.app.device)
        self.compute_type_combo.setCurrentText(self.app.compute_type)
        
        # Simple check for "On" string
        self.auto_save_check.setChecked(self.app.auto_save_enabled == "On")
        
        # Appearance settings
        theme_name = self.app.theme.capitalize()
        self.theme_combo.setCurrentText(theme_name)
        accent_name = self.app.accent_color.capitalize()
        self.accent_color_combo.setCurrentText(accent_name)
        
        # Misc settings
        if isinstance(self.app.preview_enabled, bool):
            self.preview_check.setChecked(self.app.preview_enabled)
        elif isinstance(self.app.preview_enabled, str):
            self.preview_check.setChecked(self.app.preview_enabled.lower() == "on")
        else:
            self.preview_check.setChecked(False)
        
        # Show appropriate provider settings
        self.on_provider_changed(current_provider)
        
        # Pastikan tab Translation aktif secara default (tab nomor 0)
        self.tab_widget.setCurrentIndex(0)
    
    def on_provider_changed(self, provider_name):
        """
        Handle provider selection change.
        
        Args:
            provider_name (str): The selected provider name
        """
        # Hide all provider settings
        self.gemini_settings.hide()
        self.openai_settings.hide()
        self.anthropic_settings.hide()
        self.deepseek_settings.hide()
        self.local_model_settings.hide()
        
        # Reset styling pada semua provider settings
        self.gemini_settings.setStyleSheet("")
        self.openai_settings.setStyleSheet("")
        self.anthropic_settings.setStyleSheet("")
        self.deepseek_settings.setStyleSheet("")
        self.local_model_settings.setStyleSheet("")
        
        # Show selected provider settings with highlight
        highlight_style = "QGroupBox { background-color: rgba(0, 120, 215, 0.1); border: 1px solid rgba(0, 120, 215, 0.5); }"
        
        # Update provider description
        if provider_name == "Gemini":
            self.provider_description.setText("Google's Gemini AI model for high-quality translations. Requires a Google AI API key.")
            self.gemini_settings.show()
            self.gemini_settings.setStyleSheet(highlight_style)
        elif provider_name == "OpenAI":
            self.provider_description.setText("OpenAI's GPT models known for accurate translations. Requires an OpenAI API key.")
            self.openai_settings.show()
            self.openai_settings.setStyleSheet(highlight_style)
        elif provider_name == "Anthropic":
            self.provider_description.setText("Anthropic Claude models, known for following instructions precisely. Requires an Anthropic API key.")
            self.anthropic_settings.show()
            self.anthropic_settings.setStyleSheet(highlight_style)
        elif provider_name == "DeepSeek":
            self.provider_description.setText("DeepSeek AI's translation models. Requires a DeepSeek API key.")
            self.deepseek_settings.show()
            self.deepseek_settings.setStyleSheet(highlight_style)
        elif provider_name == "Local Model":
            self.provider_description.setText("Use a locally installed model for translation (requires additional setup).")
            self.local_model_settings.show()
            self.local_model_settings.setStyleSheet(highlight_style)
    
    def save_settings(self):
        """Save settings to the main app."""
        # Translation provider
        self.app.translation_provider = self.provider_combo.currentText()
        
        # Gemini settings
        self.app.gemini_api_key = self.gemini_api_key.text()
        self.app.gemini_model = self.gemini_model.currentText()
        self.app.gemini_temperature = self.gemini_temperature.value()
        self.app.gemini_top_p = self.gemini_top_p.value()
        self.app.gemini_top_k = self.gemini_top_k.value()
        
        # OpenAI settings
        self.app.openai_api_key = self.openai_api_key.text()
        self.app.openai_model = self.openai_model.currentText()
        
        # Anthropic settings
        self.app.anthropic_api_key = self.anthropic_api_key.text()
        self.app.anthropic_model = self.anthropic_model.currentText()
        
        # DeepSeek settings
        self.app.deepseek_api_key = self.deepseek_api_key.text()
        
        # Transcription settings
        self.app.batch_size = self.batch_size.value()
        self.app.device = self.device_combo.currentText()
        self.app.compute_type = self.compute_type_combo.currentText()
        
        # Convert boolean to string format expected by the application
        self.app.auto_save_enabled = "On" if self.auto_save_check.isChecked() else "Off"
        
        # Appearance settings
        self.app.theme = self.theme_combo.currentText().lower()
        self.app.accent_color = self.accent_color_combo.currentText().lower()
        
        # Misc settings - pastikan selalu menyimpan nilai boolean
        self.app.preview_enabled = self.preview_check.isChecked()
        
        # Save to config
        self.app._save_config()
        
        # Emit signal
        self.settings_updated.emit()
        
        # Close dialog
        self.accept()
        
        # Log
        self.app.log_status("Advanced settings updated and saved.")
    
    # Tambahkan metode validasi API keys
    def validate_gemini_key(self):
        """Validate the Gemini API key."""
        api_key = self.gemini_api_key.text()
        if not api_key:
            QMessageBox.warning(self, "Validation", "API Key is empty.")
            return
        
        self.gemini_validate_button.setEnabled(False)
        self.gemini_validate_button.setText("Validating...")
        
        def validation_thread_task():
            from backend.translate import validate_gemini_key
            valid, message = validate_gemini_key(api_key, self.app.log_status)
            
            # Update UI in main thread
            from PySide6.QtCore import QMetaObject, Qt, Q_ARG
            QMetaObject.invokeMethod(
                self, "_update_gemini_validation_ui", 
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(bool, valid),
                Q_ARG(str, message)
            )
        
        # Run in separate thread
        import threading
        thread = threading.Thread(target=validation_thread_task)
        thread.daemon = True
        thread.start()
    
    def validate_openai_key(self):
        """Validate the OpenAI API key."""
        api_key = self.openai_api_key.text()
        if not api_key:
            QMessageBox.warning(self, "Validation", "API Key is empty.")
            return
        
        self.openai_validate_button.setEnabled(False)
        self.openai_validate_button.setText("Validating...")
        
        def validation_thread_task():
            from backend.translate import validate_openai_key
            valid, message = validate_openai_key(api_key, self.app.log_status)
            
            # Update UI in main thread
            from PySide6.QtCore import QMetaObject, Qt, Q_ARG
            QMetaObject.invokeMethod(
                self, "_update_openai_validation_ui", 
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(bool, valid),
                Q_ARG(str, message)
            )
        
        # Run in separate thread
        import threading
        thread = threading.Thread(target=validation_thread_task)
        thread.daemon = True
        thread.start()
    
    def validate_anthropic_key(self):
        """Validate the Anthropic API key."""
        api_key = self.anthropic_api_key.text()
        if not api_key:
            QMessageBox.warning(self, "Validation", "API Key is empty.")
            return
        
        self.anthropic_validate_button.setEnabled(False)
        self.anthropic_validate_button.setText("Validating...")
        
        def validation_thread_task():
            from backend.translate import validate_anthropic_key
            valid, message = validate_anthropic_key(api_key, self.app.log_status)
            
            # Update UI in main thread
            from PySide6.QtCore import QMetaObject, Qt, Q_ARG
            QMetaObject.invokeMethod(
                self, "_update_anthropic_validation_ui", 
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(bool, valid),
                Q_ARG(str, message)
            )
        
        # Run in separate thread
        import threading
        thread = threading.Thread(target=validation_thread_task)
        thread.daemon = True
        thread.start()
    
    def validate_deepseek_key(self):
        """Validate the DeepSeek API key."""
        api_key = self.deepseek_api_key.text()
        if not api_key:
            QMessageBox.warning(self, "Validation", "API Key is empty.")
            return
        
        self.deepseek_validate_button.setEnabled(False)
        self.deepseek_validate_button.setText("Validating...")
        
        def validation_thread_task():
            from backend.translate import validate_deepseek_key
            valid, message = validate_deepseek_key(api_key, self.app.log_status)
            
            # Update UI in main thread
            from PySide6.QtCore import QMetaObject, Qt, Q_ARG
            QMetaObject.invokeMethod(
                self, "_update_deepseek_validation_ui", 
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(bool, valid),
                Q_ARG(str, message)
            )
        
        # Run in separate thread
        import threading
        thread = threading.Thread(target=validation_thread_task)
        thread.daemon = True
        thread.start()
    
    @Slot(bool, str)
    def _update_gemini_validation_ui(self, valid, message):
        self.gemini_validate_button.setEnabled(True)
        self.gemini_validate_button.setText("Validate")
        
        if valid:
            QMessageBox.information(self, "Validation", "Gemini API key is valid!")
        else:
            QMessageBox.warning(self, "Validation", f"Gemini API key validation failed: {message}")
    
    @Slot(bool, str)
    def _update_openai_validation_ui(self, valid, message):
        self.openai_validate_button.setEnabled(True)
        self.openai_validate_button.setText("Validate")
        
        if valid:
            QMessageBox.information(self, "Validation", "OpenAI API key is valid!")
        else:
            QMessageBox.warning(self, "Validation", f"OpenAI API key validation failed: {message}")
    
    @Slot(bool, str)
    def _update_anthropic_validation_ui(self, valid, message):
        self.anthropic_validate_button.setEnabled(True)
        self.anthropic_validate_button.setText("Validate")
        
        if valid:
            QMessageBox.information(self, "Validation", "Anthropic API key is valid!")
        else:
            QMessageBox.warning(self, "Validation", f"Anthropic API key validation failed: {message}")
    
    @Slot(bool, str)
    def _update_deepseek_validation_ui(self, valid, message):
        self.deepseek_validate_button.setEnabled(True)
        self.deepseek_validate_button.setText("Validate")
        
        if valid:
            QMessageBox.information(self, "Validation", "DeepSeek API key is valid!")
        else:
            QMessageBox.warning(self, "Validation", f"DeepSeek API key validation failed: {message}") 