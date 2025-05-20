"""
Manages project loading and saving functionality for the Film Translator Generator Qt Edition.
"""
import os
import json
from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QLineEdit

from config import (
    APP_TITLE, get_default_config, GEMINI_MODELS, OPENAI_MODELS
)
from utils.crypto import encrypt_data, decrypt_data, is_encrypted
from utils.validators import validate_project_file, validate_path_exists

class ProjectManager:
    def __init__(self, app_instance):
        """
        Initialize the ProjectManager.
        
        Args:
            app_instance: The main QtAppGUI instance
        """
        self.app = app_instance
        self.encryption_password = ""  # Optional password for extra security
        
    def set_encryption_password(self, password=None):
        """Set or prompt for encryption password."""
        if password is not None:
            self.encryption_password = password
            return
            
        # Prompt user for password if not provided
        password, ok = QInputDialog.getText(
            self.app,
            "Project Security", 
            "Enter password for API key encryption (leave blank for machine-based encryption):",
            QLineEdit.Password
        )
        if ok:
            self.encryption_password = password
            self.app.log_status("Encryption password set." if password else "Using machine-based encryption.")
            return True
        return False
        
    def collect_project_data(self):
        """Collects all necessary data for saving a project."""
        # Encrypt API keys before saving
        encrypted_gemini_key = encrypt_data(self.app.gemini_api_key, self.encryption_password) if self.app.gemini_api_key else ""
        encrypted_openai_key = encrypt_data(self.app.openai_api_key, self.encryption_password) if self.app.openai_api_key else ""
        encrypted_anthropic_key = encrypt_data(self.app.anthropic_api_key, self.encryption_password) if self.app.anthropic_api_key else ""
        encrypted_deepseek_key = encrypt_data(self.app.deepseek_api_key, self.encryption_password) if self.app.deepseek_api_key else ""
        
        project_data = {
            'video_queue': self.app.video_queue,
            'processed_file_data': self.app.processed_file_data,
            'settings': {
                'translation_provider': self.app.translation_provider,
                'gemini_api_key': encrypted_gemini_key,
                'gemini_model': self.app.gemini_model,
                'openai_api_key': encrypted_openai_key,
                'openai_model': self.app.openai_model,
                'anthropic_api_key': encrypted_anthropic_key,
                'anthropic_model': self.app.anthropic_model,
                'deepseek_api_key': encrypted_deepseek_key,
                'target_language': self.app.target_language,
                'whisper_model': self.app.whisper_model_name,
                'device': self.app.device,
                'compute_type': self.app.compute_type,
                'theme': self.app.theme,
                'accent_color': self.app.accent_color,
                'batch_size': self.app.batch_size,
                'output_format': self.app.output_format,
                'preview_setting': self.app.preview_enabled,
                'auto_save_setting': self.app.auto_save_enabled,
                'gemini_temperature': self.app.gemini_temperature,
                'gemini_top_p': self.app.gemini_top_p,
                'gemini_top_k': self.app.gemini_top_k,
                'subtitle_font': self.app.subtitle_font,
                'subtitle_color': self.app.subtitle_color,
                'subtitle_size': self.app.subtitle_size,
                'subtitle_position': self.app.subtitle_position,
                'subtitle_outline_color': self.app.subtitle_outline_color,
                'subtitle_outline_width': self.app.subtitle_outline_width,
                'subtitle_bg_color': self.app.subtitle_bg_color,
                'subtitle_bg_opacity': self.app.subtitle_bg_opacity,
                'keys_encrypted': True  # Flag to indicate encryption is used
            }
        }
        return project_data
    
    def save_project_logic(self, filepath):
        """Saves the current project data to the given filepath."""
        if not filepath:
            return False
            
        # Validate path
        valid, error = validate_path_exists(os.path.dirname(filepath))
        if not valid and os.path.dirname(filepath):  # Skip validation for current directory
            self.app.log_status(f"Invalid save location: {error}", "ERROR")
            QMessageBox.critical(self.app, "Save Error", f"Invalid save location: {error}")
            return False
            
        try:
            # Ensure we have a password set for encryption
            if not hasattr(self, 'encryption_password'):
                self.set_encryption_password()
                
            data_to_save = self.collect_project_data()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4)
            self.app.current_project_path = filepath
            self.app.log_status(f"Project saved successfully to: {filepath}")
            self.app.setWindowTitle(f"{APP_TITLE} - {os.path.basename(filepath)}")
            # Update stats after saving
            if hasattr(self.app, 'queue_manager'):
                self.app.queue_manager.update_queue_statistics()
            return True
        except Exception as e:
            self.app.log_status(f"Error saving project: {e}", "ERROR")
            QMessageBox.critical(self.app, "Save Project Error", f"Failed to save project file: {e}")
            return False
    
    def save_project(self):
        """Saves the current project. If no path is set, calls save_project_as."""
        if self.app.current_project_path:
            self.save_project_logic(self.app.current_project_path)
        else:
            self.save_project_as()
    
    def save_project_as(self):
        """Prompts the user for a filepath and saves the project."""
        filepath, _ = QFileDialog.getSaveFileName(
            self.app,
            "Save Project As",
            "",
            "Film Translator Generator Project (*.ftgproj);;All Files (*)"
        )
        if filepath:
            # Add extension if not present
            if not filepath.endswith(".ftgproj"):
                filepath += ".ftgproj"
            self.save_project_logic(filepath)
    
    def clear_current_project_state(self):
        """Clears the current project state before loading a new one."""
        self.app.video_queue.clear()
        self.app.processed_file_data.clear()
        self.app.video_listbox.clear()
        
        self.app.transcribed_segments = None
        self.app.translated_segments = None
        self.app.current_output = None
        self.app.current_processing_video = None
        self.app.current_project_path = None
        
        # Clear media player
        self.app.media_player.stop()
        
        # Clear text areas
        self.app.output_text.clear()
        self.app.original_text.clear()
        self.app.translated_text.clear()
        self.app.editor_text.clear()
        
        # Reset progress
        self.app.progress_bar.setValue(0)
        self.app.progress_status.setText("Ready")
        
        # Reset window title
        self.app.setWindowTitle(APP_TITLE)
        self.app.log_status("Cleared current project state.")
        
        # Update stats
        if hasattr(self.app, 'queue_manager'):
            self.app.queue_manager.update_queue_statistics()
    
    def load_project_logic(self, filepath):
        """Loads project data from the given filepath and restores state."""
        # Validate project file
        valid, error = validate_project_file(filepath)
        if not valid:
            self.app.log_status(f"Invalid project file: {error}", "ERROR")
            QMessageBox.critical(self.app, "Load Project Error", f"Invalid project file: {error}")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
        except Exception as e:
            self.app.log_status(f"Error loading project file {filepath}: {e}", "ERROR")
            QMessageBox.critical(self.app, "Load Project Error", f"Failed to load or parse project file: {e}")
            return False
        
        self.clear_current_project_state()
        
        try:
            self.app.video_queue = project_data.get('video_queue', [])
            self.app.processed_file_data = project_data.get('processed_file_data', {})
            
            # Validate video paths
            invalid_videos = []
            for i, video_path in enumerate(self.app.video_queue):
                valid, _ = validate_path_exists(video_path)
                if not valid:
                    invalid_videos.append((i, video_path))
            
            # Handle invalid video paths
            if invalid_videos:
                missing_videos = "\n".join([os.path.basename(path) for _, path in invalid_videos])
                response = QMessageBox.question(
                    self.app,
                    "Missing Videos",
                    f"The following videos were not found:\n{missing_videos}\n\nRemove them from the project?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if response == QMessageBox.Yes:
                    # Remove invalid videos (in reverse order to avoid index issues)
                    for idx, path in sorted(invalid_videos, reverse=True):
                        del self.app.video_queue[idx]
                        if path in self.app.processed_file_data:
                            del self.app.processed_file_data[path]
            
            # Update the video list
            for video_path in self.app.video_queue:
                file_info = self.app.processed_file_data.get(video_path, {'status': 'Unknown'})
                status = file_info.get('status', 'Unknown')
                self.app.video_listbox.addItem(f"[{status}] {os.path.basename(video_path)}")
            
            # Load settings
            settings = project_data.get('settings', {})
            defaults = get_default_config()
            
            # Check if keys are encrypted
            keys_encrypted = settings.get('keys_encrypted', False)
            
            # If keys are encrypted, prompt for password
            if keys_encrypted:
                self.set_encryption_password()
            
            # Apply settings
            self.app.translation_provider = settings.get('translation_provider', defaults['translation_provider'])
            
            # Process API keys - decrypt if necessary
            gemini_key = settings.get('gemini_api_key', defaults['gemini_api_key'])
            openai_key = settings.get('openai_api_key', defaults['openai_api_key'])
            anthropic_key = settings.get('anthropic_api_key', defaults['anthropic_api_key'])
            deepseek_key = settings.get('deepseek_api_key', defaults['deepseek_api_key'])
            
            if keys_encrypted:
                # Decrypt API keys
                self.app.gemini_api_key = decrypt_data(gemini_key, self.encryption_password) if gemini_key else ""
                self.app.openai_api_key = decrypt_data(openai_key, self.encryption_password) if openai_key else ""
                self.app.anthropic_api_key = decrypt_data(anthropic_key, self.encryption_password) if anthropic_key else ""
                self.app.deepseek_api_key = decrypt_data(deepseek_key, self.encryption_password) if deepseek_key else ""
            else:
                # Handle legacy projects without encryption
                self.app.gemini_api_key = gemini_key
                self.app.openai_api_key = openai_key
                self.app.anthropic_api_key = anthropic_key
                self.app.deepseek_api_key = deepseek_key
                
                # Offer to encrypt the keys
                if any([gemini_key, openai_key, anthropic_key, deepseek_key]):
                    response = QMessageBox.question(
                        self.app,
                        "Security Upgrade",
                        "This project contains unencrypted API keys. Would you like to encrypt them for better security?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    if response == QMessageBox.Yes:
                        self.set_encryption_password()
                        # Mark to save the project with encryption later
                        self.app.log_status("Security upgrade: API keys will be encrypted on next save.")
            
            self.app.openai_model = settings.get('openai_model', defaults.get('openai_model', OPENAI_MODELS[0] if OPENAI_MODELS else ''))
            self.app.anthropic_model = settings.get('anthropic_model', defaults['anthropic_model'])
            self.app.gemini_model = settings.get('gemini_model', defaults.get('gemini_model', GEMINI_MODELS[0] if GEMINI_MODELS else ''))
            
            self.app.target_language = settings.get('target_language', defaults['target_language'])
            self.app.whisper_model_name = settings.get('whisper_model', defaults['whisper_model'])
            self.app.device = settings.get('device', defaults['device'])
            self.app.compute_type = settings.get('compute_type', defaults['compute_type'])
            self.app.theme = settings.get('theme', defaults['theme'])
            self.app.accent_color = settings.get('accent_color', defaults['accent_color'])
            
            # Validate numeric values
            try:
                self.app.batch_size = int(settings.get('batch_size', defaults['batch_size']))
                self.app.gemini_temperature = float(settings.get('gemini_temperature', defaults['gemini_temperature']))
                self.app.gemini_top_p = float(settings.get('gemini_top_p', defaults['gemini_top_p']))
                self.app.gemini_top_k = int(settings.get('gemini_top_k', defaults['gemini_top_k']))
            except (ValueError, TypeError):
                self.app.log_status("Invalid numeric settings found, using defaults", "WARNING")
                self.app.batch_size = defaults['batch_size']
                self.app.gemini_temperature = defaults['gemini_temperature']
                self.app.gemini_top_p = defaults['gemini_top_p']
                self.app.gemini_top_k = defaults['gemini_top_k']
            
            self.app.output_format = settings.get('output_format', defaults['output_format'])
            self.app.preview_enabled = settings.get('preview_setting', defaults['preview'])
            self.app.auto_save_enabled = settings.get('auto_save_setting', defaults['auto_save'])
            
            # Subtitle style settings
            self.app.subtitle_font = settings.get('subtitle_font', defaults['subtitle_font'])
            self.app.subtitle_color = settings.get('subtitle_color', defaults['subtitle_color'])
            self.app.subtitle_size = settings.get('subtitle_size', defaults['subtitle_size'])
            self.app.subtitle_position = settings.get('subtitle_position', defaults['subtitle_position'])
            self.app.subtitle_outline_color = settings.get('subtitle_outline_color', defaults['subtitle_outline_color'])
            self.app.subtitle_outline_width = settings.get('subtitle_outline_width', defaults['subtitle_outline_width'])
            self.app.subtitle_bg_color = settings.get('subtitle_bg_color', defaults['subtitle_bg_color'])
            self.app.subtitle_bg_opacity = settings.get('subtitle_bg_opacity', defaults['subtitle_bg_opacity'])
            
            # Update UI components with loaded settings
            self.app.language_combo.setCurrentText(self.app.target_language)
            self.app.model_combo.setCurrentText(self.app.whisper_model_name)
            self.app.device_combo.setCurrentText(self.app.device)
            self.app.compute_type_combo.setCurrentText(self.app.compute_type)
            self.app.batch_size_spin.setValue(self.app.batch_size)
            self.app.output_format_combo.setCurrentText(self.app.output_format)
            
            # Update provider-specific UI elements if they exist
            if self.app.translation_provider_combo.findText(self.app.translation_provider) >= 0:
                self.app.translation_provider_combo.setCurrentText(self.app.translation_provider)
            
            # Update subtitle style UI elements
            if hasattr(self.app, 'subtitle_font_combo'):
                self.app.subtitle_font_combo.setCurrentText(self.app.subtitle_font)
            if hasattr(self.app, 'subtitle_color_combo'):
                self.app.subtitle_color_combo.setCurrentText(self.app.subtitle_color)
            if hasattr(self.app, 'subtitle_size_combo'):
                self.app.subtitle_size_combo.setCurrentText(self.app.subtitle_size)
            if hasattr(self.app, 'subtitle_position_combo'):
                self.app.subtitle_position_combo.setCurrentText(self.app.subtitle_position)
            
            # Apply theme
            if hasattr(self.app, 'apply_theme'):
                self.app.apply_theme(self.app.theme)
            
            # Set current project path
            self.app.current_project_path = filepath
            self.app.setWindowTitle(f"{APP_TITLE} - {os.path.basename(filepath)}")
            self.app.log_status(f"Project loaded from: {filepath}")
            
            # Update queue statistics
            if hasattr(self.app, 'queue_manager'):
                self.app.queue_manager.update_queue_statistics()
                
            return True
            
        except Exception as e:
            self.app.log_status(f"Error restoring project state: {e}", "ERROR")
            QMessageBox.critical(self.app, "Load Project Error", f"Failed to restore project state: {e}")
            return False
    
    def load_project(self):
        """Opens a file dialog to select and load a project file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self.app,
            "Load Project",
            "",
            "Film Translator Generator Project (*.ftgproj);;All Files (*)"
        )
        if filepath:
            self.load_project_logic(filepath) 