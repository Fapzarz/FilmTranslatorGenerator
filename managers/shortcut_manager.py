"""
Manages keyboard shortcuts for the Film Translator Generator Qt Edition.
Also contains validator functions for input validation.
"""
import os
import re
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import Qt

class ShortcutManager:
    def __init__(self, app_instance):
        """
        Initialize the ShortcutManager.
        
        Args:
            app_instance: The main QtAppGUI instance
        """
        self.app = app_instance
        self.shortcuts = {}
        self.setup_shortcuts()
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts for the application."""
        # Dictionary mapping shortcut names to function and key sequence
        shortcuts_config = {
            'add_video': {
                'key': 'Ctrl+O',
                'func': self.app.add_videos_to_queue,
                'description': 'Add videos to queue'
            },
            'process_video': {
                'key': 'F5',
                'func': self.app.process_selected_video,
                'description': 'Process selected video'
            },
            'save_output': {
                'key': 'Ctrl+S',
                'func': self.app.save_output_file,
                'description': 'Save subtitle file'
            },
            'save_project': {
                'key': 'Ctrl+Shift+S',
                'func': self.app.save_project,
                'description': 'Save project'
            },
            'load_project': {
                'key': 'Ctrl+Shift+O',
                'func': self.app.load_project,
                'description': 'Load project'
            },
            'copy_output': {
                'key': 'Ctrl+C',
                'func': self.app.copy_to_clipboard,
                'description': 'Copy output to clipboard'
            },
            'preview_with_subs': {
                'key': 'Ctrl+P',
                'func': lambda: self.app.preview_manager.preview_video_with_subtitles(),
                'description': 'Preview with subtitles'
            },
            'save_editor': {
                'key': 'Ctrl+E',
                'func': self.app.save_editor_changes,
                'description': 'Save subtitle editor changes'
            },
        }
        
        # Create shortcuts
        for name, config in shortcuts_config.items():
            shortcut = QShortcut(QKeySequence(config['key']), self.app)
            shortcut.activated.connect(config['func'])
            self.shortcuts[name] = {
                'shortcut': shortcut,
                'key': config['key'],
                'func': config['func'],
                'description': config['description']
            }
            self.app.log_status(f"Registered shortcut: {config['key']} for {config['description']}")
    
    def get_shortcuts_info(self):
        """
        Returns information about registered shortcuts.
        
        Returns:
            list: List of dictionaries containing shortcut information
        """
        return [
            {
                'name': name,
                'key': info['key'],
                'description': info['description']
            }
            for name, info in self.shortcuts.items()
        ]
    
    def update_shortcut(self, name, new_key):
        """
        Update a shortcut with a new key sequence.
        
        Args:
            name (str): The name of the shortcut to update
            new_key (str): The new key sequence
            
        Returns:
            bool: True if successful, False otherwise
        """
        if name not in self.shortcuts:
            return False
        
        try:
            # Delete old shortcut
            old_shortcut = self.shortcuts[name]['shortcut']
            old_shortcut.setEnabled(False)
            old_shortcut.deleteLater()
            
            # Create new shortcut
            new_shortcut = QShortcut(QKeySequence(new_key), self.app)
            new_shortcut.activated.connect(self.shortcuts[name]['func'])
            
            # Update shortcuts dictionary
            self.shortcuts[name]['shortcut'] = new_shortcut
            self.shortcuts[name]['key'] = new_key
            
            self.app.log_status(f"Updated shortcut: {name} to {new_key}")
            return True
        except Exception as e:
            self.app.log_status(f"Error updating shortcut: {e}", "ERROR")
            return False
    
    # Input validators
    @staticmethod
    def validate_gemini_key(api_key):
        """
        Validate the Gemini API key format.
        
        Args:
            api_key (str): The API key to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not api_key or len(api_key) < 10:
            return False
            
        # Google API keys typically start with "AI"
        if not api_key.startswith("AI"):
            return False
            
        # Simple length and character check
        valid_chars = re.match(r'^[A-Za-z0-9_-]+$', api_key)
        return bool(valid_chars)
    
    @staticmethod
    def validate_openai_key(api_key):
        """
        Validate the OpenAI API key format.
        
        Args:
            api_key (str): The API key to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not api_key or len(api_key) < 10:
            return False
            
        # OpenAI API keys start with "sk-"
        if not api_key.startswith("sk-"):
            return False
            
        # Check length and valid characters
        valid_chars = re.match(r'^[A-Za-z0-9_-]+$', api_key)
        return bool(valid_chars)
    
    @staticmethod
    def validate_anthropic_key(api_key):
        """
        Validate the Anthropic API key format.
        
        Args:
            api_key (str): The API key to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not api_key or len(api_key) < 10:
            return False
            
        # Anthropic API keys usually start with "sk-ant"
        if not api_key.startswith("sk-ant"):
            return False
            
        # Check for valid characters
        valid_chars = re.match(r'^[A-Za-z0-9_-]+$', api_key)
        return bool(valid_chars)
    
    @staticmethod
    def validate_deepseek_key(api_key):
        """
        Validate the DeepSeek API key format.
        
        Args:
            api_key (str): The API key to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not api_key or len(api_key) < 10:
            return False
        
        # DeepSeek API keys might not have a standard format
        # So we'll just check for valid characters and length
        valid_chars = re.match(r'^[A-Za-z0-9_-]+$', api_key)
        return bool(valid_chars)
    
    def open_shortcut_dialog(self):
        """Open the shortcut configuration dialog."""
        # This would be implemented with a proper dialog
        # For now just display a message
        QMessageBox.information(
            self.app,
            "Keyboard Shortcuts",
            "\n".join([f"{info['key']}: {info['description']}" for _, info in self.shortcuts.items()])
        )
        self.app.log_status("Shortcut dialog opened.") 