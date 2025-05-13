"""
Manages keyboard shortcuts for the Film Translator Generator application.
This includes loading, saving, binding, and executing shortcut actions.
"""
import tkinter as tk
from config import DEFAULT_SHORTCUTS
from gui.components import create_shortcut_settings_dialog
# We need to import the managers if execute_shortcut_action calls them directly
# However, it's better if execute_shortcut_action calls methods on the app instance.
# from gui import queue_manager, project_manager, video_processor, editor_manager # Potentially

class ShortcutManager:
    def __init__(self, app_instance):
        """
        Initializes the ShortcutManager.

        Args:
            app_instance: The main AppGUI instance.
        """
        self.app = app_instance  # Reference to the main AppGUI instance
        self.app_shortcuts = {}  # Holds the current shortcuts {action_name: shortcut_string}

    def load_shortcuts(self, config_data, defaults):
        """Loads shortcut configurations from config_data or defaults."""
        loaded_shortcuts = config_data.get('shortcuts', defaults.get('shortcuts', DEFAULT_SHORTCUTS))
        if not isinstance(loaded_shortcuts, dict) or not all(isinstance(v, str) for v in loaded_shortcuts.values()):
            self.app.log_status("ShortcutManager: Invalid or missing shortcuts in config, using defaults.", "WARNING")
            self.app_shortcuts = DEFAULT_SHORTCUTS.copy()
        else:
            self.app_shortcuts = loaded_shortcuts
        
        # Ensure all default shortcut keys are present
        for key, value in DEFAULT_SHORTCUTS.items():
            if key not in self.app_shortcuts:
                self.app_shortcuts[key] = value
        self.app.log_status("ShortcutManager: Shortcuts loaded.", "VERBOSE")

    def get_shortcuts_for_saving(self):
        """Returns the current shortcut configuration for saving."""
        return self.app_shortcuts

    def bind_shortcuts(self):
        """Binds the configured shortcuts to their respective actions on the app's root window."""
        if not self.app_shortcuts:
            self.app.log_status("ShortcutManager: No shortcuts loaded or app_shortcuts not initialized, skipping binding.", "WARNING")
            return

        self.app.log_status("ShortcutManager: Binding application shortcuts...", "VERBOSE")
        for action_name, shortcut_key in self.app_shortcuts.items():
            if shortcut_key and isinstance(shortcut_key, str) and shortcut_key.strip():
                try:
                    final_bind_sequence = f"<{shortcut_key}>"
                    self.app.root.bind(final_bind_sequence, lambda event, name=action_name: self.execute_shortcut_action(name))
                    self.app.log_status(f"ShortcutManager: Bound shortcut {final_bind_sequence} to action '{action_name}'", "VERBOSE")
                except tk.TclError as e:
                    self.app.log_status(f"ShortcutManager: Error binding shortcut '{shortcut_key}' (as {final_bind_sequence}) for action '{action_name}': {e}", "ERROR")
                except Exception as e_generic:
                    self.app.log_status(f"ShortcutManager: Unexpected error binding shortcut '{shortcut_key}' for action '{action_name}': {e_generic}", "ERROR")
            elif shortcut_key: # If it's not a string or is an empty string but not None/empty
                self.app.log_status(f"ShortcutManager: Invalid or empty shortcut key '{shortcut_key}' for action '{action_name}'. Skipping.", "WARNING")

    def unbind_shortcuts(self):
        """
        Placeholder for unbinding shortcuts. 
        Currently relies on Tkinter replacing bindings on rebind.
        """
        self.app.log_status("ShortcutManager: Attempting to unbind old shortcuts (Tkinter might replace them automatically on rebind).", "VERBOSE")
        # If explicit unbinding is needed in the future:
        # Iterate over stored old shortcuts and call self.app.root.unbind(sequence)
        pass

    def execute_shortcut_action(self, action_name: str):
        """Executes the action associated with a triggered shortcut by calling methods on the AppGUI instance or its managers."""
        self.app.log_status(f"ShortcutManager: Executing shortcut action '{action_name}'", "VERBOSE")

        # Action mapping - calls methods on self.app or its managers
        # Assumes AppGUI (self.app) has the necessary methods or manager instances
        if action_name == "add_videos_to_queue":
            if hasattr(self.app, 'queue_manager'): self.app.queue_manager.add_videos_to_queue(self.app)
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "remove_selected_video":
            if hasattr(self.app, 'queue_manager'): self.app.queue_manager.remove_selected_video_from_queue(self.app)
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "clear_video_queue":
            if hasattr(self.app, 'queue_manager'): self.app.queue_manager.clear_video_queue(self.app)
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "start_processing":
            if hasattr(self.app, 'video_processor'): self.app.video_processor.start_processing_thread(self.app)
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "save_project":
            if hasattr(self.app, 'project_manager'): self.app.project_manager.save_project(self.app)
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "save_project_as":
            if hasattr(self.app, 'project_manager'): self.app.project_manager.save_project_as_dialog(self.app)
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "load_project":
            if hasattr(self.app, 'project_manager'): self.app.project_manager.load_project_dialog(self.app)
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "save_subtitles":
            if hasattr(self.app, 'save_output_file'): self.app.save_output_file()
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "copy_output_to_clipboard":
            if hasattr(self.app, 'copy_to_clipboard'): self.app.copy_to_clipboard()
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "apply_editor_changes":
            if hasattr(self.app, 'editor_manager') and hasattr(self.app.editor_manager, 'apply_and_save_all_editor_changes'):
                self.app.editor_manager.apply_and_save_all_editor_changes(self.app)
            elif hasattr(self.app, 'editor_manager') and hasattr(self.app.editor_manager, 'apply_editor_changes'):
                 self.app.editor_manager.apply_editor_changes(self.app)
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "open_advanced_settings":
            if hasattr(self.app, 'open_advanced_settings'): self.app.open_advanced_settings()
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "show_about_dialog":
            if hasattr(self.app, 'show_about'): self.app.show_about()
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        elif action_name == "exit_application":
            if hasattr(self.app, 'on_closing'): self.app.on_closing() # Ensures config is saved via AppGUI
            else: self.app.log_status(f"Handler for '{action_name}' not found.", "ERROR")
        else:
            self.app.log_status(f"ShortcutManager: Unknown shortcut action '{action_name}'", "WARNING")

    def open_shortcut_settings(self):
        """Opens the keyboard shortcut settings dialog."""
        create_shortcut_settings_dialog(
            self.app.root,
            self.app_shortcuts.copy(),  # Pass a copy to avoid direct modification before save
            self.app._handle_apply_new_shortcuts, # Callback to AppGUI method
            self.app.log_status
        )

    def apply_new_shortcuts_from_dialog(self, new_shortcuts):
        """
        Called by AppGUI after the shortcut dialog is saved.
        Updates internal shortcuts and rebinds them.
        Actual config saving is handled by AppGUI.
        """
        if not isinstance(new_shortcuts, dict):
            self.app.log_status("ShortcutManager: Failed to apply new shortcuts from dialog - invalid format.", "ERROR")
            return

        self.app.log_status("ShortcutManager: Applying new shortcut settings from dialog...", "INFO")
        self.app_shortcuts = new_shortcuts
        self.unbind_shortcuts()  # Unbind old ones
        self.bind_shortcuts()    # Rebind new ones
        self.app.log_status("ShortcutManager: Shortcut settings updated and re-bound.", "INFO") 