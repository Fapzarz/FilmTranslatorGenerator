"""
Main GUI application class for Film Translator Generator.
"""
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Listbox, Scrollbar, Canvas # Explicitly import Listbox etc. if tk aliasing is removed for root
from tkinterdnd2 import TkinterDnD, DND_FILES # Import TkinterDnD
import threading
from datetime import datetime
import torch
import gc
import sv_ttk
import tempfile # For temporary subtitle file
import subprocess # For opening video with subtitles more reliably
import sys # For platform-specific operations
# import re # No longer directly used in AppGUI after editor refactor

from config import (
    APP_TITLE, CONFIG_FILE, get_default_config, LANGUAGES, 
    WHISPER_MODELS, DEVICES, COMPUTE_TYPES, OUTPUT_FORMATS, 
    GITHUB_URL, APP_VERSION, TRANSLATION_PROVIDERS, 
    OPENAI_MODELS, ANTHROPIC_MODELS, DEEPSEEK_MODEL, GEMINI_MODELS,
    SUBTITLE_FONTS, SUBTITLE_COLORS, SUBTITLE_SIZES, SUBTITLE_POSITIONS,
    SUBTITLE_OUTLINE_COLORS, SUBTITLE_OUTLINE_WIDTHS, SUBTITLE_BG_COLORS, SUBTITLE_BG_OPACITY,
    DEFAULT_SHORTCUTS # Import DEFAULT_SHORTCUTS
)
from backend.transcribe import transcribe_video, load_whisper_model
from backend.translate import translate_text
# Import validation functions
from backend.translate import validate_gemini_key, validate_openai_key, validate_anthropic_key 
from utils.format import format_output
from utils.media import extract_video_thumbnail, play_video_preview, get_video_info
from gui.components import create_advanced_settings_dialog, create_about_dialog, create_shortcut_settings_dialog # Import create_shortcut_settings_dialog
from gui.main_layout import create_left_pane, create_right_pane
from gui import project_manager
from gui import queue_manager
from gui import video_processor
from gui import subtitle_styler
from gui import editor_manager
from gui.shortcut_manager import ShortcutManager # Import ShortcutManager
from gui.preview_manager import PreviewManager # Import PreviewManager

class AppGUI:
    def __init__(self): # Removed root_master argument
        self.root = TkinterDnD.Tk() # Always create TkinterDnD.Tk() as the root
        self.root.title(APP_TITLE)
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Ensure tkinter is available for other widgets, can use tk.StringVar directly etc.
        # Or keep 'import tkinter as tk' if preferred and just use TkinterDnD.Tk() for root.
        # For now, assuming direct use of ttk.Frame, tk.StringVar etc. is fine.
        
        sv_ttk.set_theme("dark")
        
        self.video_queue = []
        self.processed_file_data = {}
        self.current_processing_video = None
        self.selected_video_in_queue = tk.StringVar() # tk needed here
        self.current_project_path = None
        
        self.stat_total_files = tk.StringVar(value="Total Files: 0")
        self.stat_processed_files = tk.StringVar(value="Processed: 0")
        self.stat_pending_files = tk.StringVar(value="Pending: 0")
        self.stat_failed_files = tk.StringVar(value="Failed: 0")
        self.extensive_logging_var = tk.StringVar()
        self.translation_provider_var = tk.StringVar()
        
        self.gemini_api_key_var = tk.StringVar()
        self.openai_api_key_var = tk.StringVar() 
        self.anthropic_api_key_var = tk.StringVar()
        self.deepseek_api_key_var = tk.StringVar()
        self.gemini_model_var = tk.StringVar()
        
        self.openai_model_var = tk.StringVar() 
        self.anthropic_model_var = tk.StringVar()

        self.target_language = tk.StringVar()
        self.whisper_model_name_var = tk.StringVar()
        self.device_var = tk.StringVar()
        self.compute_type_var = tk.StringVar()
        self.theme_var = tk.StringVar(value="dark")
        self.accent_color_var = tk.StringVar(value="blue")
        self.batch_size_var = tk.StringVar()
        self.output_format_var = tk.StringVar(value="srt")
        self.preview_var = tk.StringVar(value="On")
        self.auto_save_var = tk.StringVar(value="Off")
        
        self.gemini_temperature_var = tk.DoubleVar() # tk needed here
        self.gemini_top_p_var = tk.DoubleVar()
        self.gemini_top_k_var = tk.IntVar()
        
        self.subtitle_font_var = tk.StringVar(value=SUBTITLE_FONTS[0])
        self.subtitle_color_var = tk.StringVar(value=SUBTITLE_COLORS[0])
        self.subtitle_size_var = tk.StringVar(value=SUBTITLE_SIZES[2])
        self.subtitle_position_var = tk.StringVar(value=SUBTITLE_POSITIONS[0])
        self.subtitle_outline_color_var = tk.StringVar(value=SUBTITLE_OUTLINE_COLORS[0])
        self.subtitle_outline_width_var = tk.StringVar(value=SUBTITLE_OUTLINE_WIDTHS[1])
        self.subtitle_bg_color_var = tk.StringVar(value=SUBTITLE_BG_COLORS[0])
        self.subtitle_bg_opacity_var = tk.StringVar(value=SUBTITLE_BG_OPACITY[0])
        
        self.style = ttk.Style()
        self.style.configure("Accent.TButton", font=("", 10, "bold"))
        
        self.whisper_model = None
        # self.app_shortcuts = {} # Removed: Handled by ShortcutManager
        
        self.transcribed_segments = None
        self.translated_segments = None
        self.current_output = None
        
        self.api_key_status_labels = {}
        
        self.shortcut_manager = ShortcutManager(self) # Initialize ShortcutManager
        self.preview_manager = PreviewManager(self) # Initialize PreviewManager

        self.create_menu()
        self.create_main_frame()
        
        # Configure commands for buttons returned by create_notebook from components
        if hasattr(self, 'text_widgets'):
            if 'copy_button' in self.text_widgets and self.text_widgets['copy_button']:
                self.text_widgets['copy_button'].config(command=self.copy_to_clipboard)
            if 'save_button' in self.text_widgets and self.text_widgets['save_button']:
                self.text_widgets['save_button'].config(command=self.save_output_file)
            if 'preview_sub_button' in self.text_widgets and self.text_widgets['preview_sub_button']:
                self.text_widgets['preview_sub_button'].config(command=self.preview_manager.preview_video_with_subtitles)
            if 'save_editor_button' in self.text_widgets and self.text_widgets['save_editor_button']:
                # Assuming editor_manager.save_editor_changes(self) is the correct method signature
                self.text_widgets['save_editor_button'].config(command=lambda: editor_manager.save_editor_changes(self))

        self._load_config() # This will call shortcut_manager.load_shortcuts
        # self._bind_shortcuts() # Removed: Called by shortcut_manager or after its loading
        self.shortcut_manager.bind_shortcuts() # Bind shortcuts after loading config via shortcut_manager
        self.update_compute_types()
        
        subtitle_styler.refresh_subtitle_style_preview(self)
        
        self._apply_theme()

        queue_manager.update_queue_statistics(self)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """Handle application closing: save config and quit."""
        self.log_status("Application closing. Saving configuration...")
        self._save_config() # Save current settings and history
        self.root.quit() # Proceed to close the application
    
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Add Video(s) to Queue", command=lambda: queue_manager.add_videos_to_queue(self))
        file_menu.add_command(label="Load Project", command=lambda: project_manager.load_project_dialog(self))
        file_menu.add_command(label="Save Project", command=lambda: project_manager.save_project(self))
        file_menu.add_command(label="Save Project As...", command=lambda: project_manager.save_project_as_dialog(self))
        file_menu.add_separator()
        file_menu.add_command(label="Save Subtitles", command=lambda: self.save_output_file())
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        
        # Theme submenu
        theme_menu = tk.Menu(settings_menu, tearoff=0)
        for theme in ["light", "dark"]:
            theme_menu.add_radiobutton(label=theme.capitalize(), 
                                      variable=self.theme_var, 
                                      value=theme,
                                      command=self._apply_theme)
        settings_menu.add_cascade(label="Theme", menu=theme_menu)
        
        # Advanced settings
        settings_menu.add_command(label="Advanced Settings", command=self.open_advanced_settings)
        settings_menu.add_command(label="Keyboard Shortcuts...", command=self.shortcut_manager.open_shortcut_settings) # Use ShortcutManager method
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Documentation", command=lambda: self.open_github())
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_frame(self):
        """Create the main application frame and widgets with a fixed, non-resizable Adobe-like panel layout."""
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        main_container = ttk.Frame(main_frame)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Configure column weights for fixed proportions
        main_container.columnconfigure(0, weight=10) # User's preferred weight from previous edit
        main_container.columnconfigure(1, weight=70) # User's preferred weight from previous edit
        main_container.rowconfigure(0, weight=1)

        # Create left and right panes using functions from main_layout
        create_left_pane(self, main_container)
        create_right_pane(self, main_container)
        
        # Status bar (remains at the bottom of the root window)
        status_bar = ttk.Frame(self.root)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=(0,5))
        
        self.status_label = ttk.Label(status_bar, text="Ready", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5)
    
    def open_advanced_settings(self):
        """Open advanced settings dialog"""
        settings = {
            'batch_size_var': self.batch_size_var,
            'preview_var': self.preview_var,
            'auto_save_var': self.auto_save_var,
            'accent_color_var': self.accent_color_var,
            'gemini_temperature_var': self.gemini_temperature_var,
            'gemini_top_p_var': self.gemini_top_p_var,
            'gemini_top_k_var': self.gemini_top_k_var,
            'extensive_logging_var': self.extensive_logging_var, 
            'translation_provider_var': self.translation_provider_var,
            'gemini_api_key_var': self.gemini_api_key_var,
            'gemini_model_var': self.gemini_model_var, # Added Gemini model var
            'openai_api_key_var': self.openai_api_key_var,        
            'openai_model_var': self.openai_model_var,            
            'anthropic_api_key_var': self.anthropic_api_key_var,
            'anthropic_model_var': self.anthropic_model_var,
            'deepseek_api_key_var': self.deepseek_api_key_var,
            'save_callback': self._save_config,
            'update_translation_ui_callback': self._update_translation_settings_ui
        }
        create_advanced_settings_dialog(self.root, settings)
    
    def show_about(self):
        """Show about dialog"""
        create_about_dialog(self.root)
    
    def open_github(self):
        """Open the GitHub repository page"""
        import webbrowser
        webbrowser.open(GITHUB_URL)
    
    def _apply_theme(self):
        """Apply the selected theme to the application and refresh preview if needed."""
        selected_video_path = None
        if hasattr(self, 'video_listbox') and self.video_listbox.curselection():
            selected_indices = self.video_listbox.curselection()
            if selected_indices:
                # Ensure the index is valid for self.video_queue
                listbox_index = selected_indices[0]
                if listbox_index < len(self.video_queue):
                    selected_video_path = self.video_queue[listbox_index]

        theme = self.theme_var.get()
        sv_ttk.set_theme(theme)
        self.log_status(f"Theme changed to {theme}")

        # Restore preview if a video was selected
        if selected_video_path and hasattr(self, 'preview_manager'):
            self.log_status(f"Refreshing preview for {os.path.basename(selected_video_path)} after theme change.", "VERBOSE")
            self.preview_manager.update_video_preview_info(selected_video_path)
    
    def _restore_video_preview_if_selected(self):
        """Restores the video preview (thumbnail and info) if a video is currently selected in the queue."""
        selected_video_path = None
        if hasattr(self, 'video_listbox') and self.video_listbox.curselection():
            selected_indices = self.video_listbox.curselection()
            if selected_indices:
                listbox_index = selected_indices[0]
                # Ensure the index is valid for self.video_queue before accessing
                if listbox_index < len(self.video_queue):
                    selected_video_path = self.video_queue[listbox_index]
        
        if selected_video_path and hasattr(self, 'preview_manager'):
            # self.log_status(f"Restoring preview for {os.path.basename(selected_video_path)} due to UI update.", "VERBOSE")
            self.preview_manager.update_video_preview_info(selected_video_path)

    def copy_to_clipboard(self):
        """Copy output text to clipboard"""
        content = self.text_widgets['output'].get(1.0, tk.END)
        if not content.strip():
            messagebox.showinfo("Info", "No output to copy.")
            return
            
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_label.config(text="Output copied to clipboard")
        self.log_status("Output copied to clipboard")
    
    def update_compute_types(self, event=None):
        """Updates the compute type combobox based on the selected device."""
        selected_device = self.device_var.get()
        valid_compute_types = COMPUTE_TYPES.get(selected_device, [])
        self.compute_type_combobox['values'] = valid_compute_types
        # Try to keep the current selection if valid, otherwise set to the first valid type
        current_compute_type = self.compute_type_var.get()
        if current_compute_type not in valid_compute_types:
            if valid_compute_types:
                self.compute_type_var.set(valid_compute_types[0])
            else:
                self.compute_type_var.set("")  # Clear if no valid types

    def _load_config(self):
        """Load configuration from JSON file or use defaults."""
        defaults = get_default_config()
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
            else:
                config_data = defaults
        except Exception as e:
            self.log_status(f"Error loading config: {e}. Using defaults.", level="ERROR")
            config_data = defaults

        # Load main settings
        self.translation_provider_var.set(config_data.get('translation_provider', defaults['translation_provider']))
        self.gemini_api_key_var.set(config_data.get('gemini_api_key', defaults['gemini_api_key']))
        self.openai_api_key_var.set(config_data.get('openai_api_key', defaults['openai_api_key']))
        self.anthropic_api_key_var.set(config_data.get('anthropic_api_key', defaults['anthropic_api_key']))
        self.deepseek_api_key_var.set(config_data.get('deepseek_api_key', defaults['deepseek_api_key']))
        
        self.openai_model_var.set(config_data.get('openai_model', defaults['openai_model']))
        self.anthropic_model_var.set(config_data.get('anthropic_model', defaults['anthropic_model']))
        self.gemini_model_var.set(config_data.get('gemini_model', defaults.get('gemini_model', GEMINI_MODELS[0] if GEMINI_MODELS else ''))) # Load Gemini model
        
        self.target_language.set(config_data.get('target_language', defaults['target_language']))
        self.whisper_model_name_var.set(config_data.get('whisper_model', defaults['whisper_model']))
        self.device_var.set(config_data.get('device', defaults['device']))
        self.compute_type_var.set(config_data.get('compute_type', defaults['compute_type']))
        self.theme_var.set(config_data.get('theme', defaults['theme']))
        self.accent_color_var.set(config_data.get('accent_color', defaults['accent_color']))
        self.batch_size_var.set(str(config_data.get('batch_size', defaults['batch_size'])))
        self.output_format_var.set(config_data.get('output_format', defaults['output_format']))
        self.preview_var.set(config_data.get('preview', defaults['preview']))
        self.auto_save_var.set(config_data.get('auto_save', defaults['auto_save']))
        self.gemini_temperature_var.set(float(config_data.get('gemini_temperature', defaults['gemini_temperature'])))
        self.gemini_top_p_var.set(float(config_data.get('gemini_top_p', defaults['gemini_top_p'])))
        self.gemini_top_k_var.set(int(config_data.get('gemini_top_k', defaults['gemini_top_k'])))
        self.extensive_logging_var.set(config_data.get('extensive_logging', defaults['extensive_logging']))

        # Load subtitle style settings
        self.subtitle_font_var.set(config_data.get('subtitle_font', defaults['subtitle_font']))
        self.subtitle_color_var.set(config_data.get('subtitle_color', defaults['subtitle_color']))
        self.subtitle_size_var.set(config_data.get('subtitle_size', defaults['subtitle_size']))
        self.subtitle_position_var.set(config_data.get('subtitle_position', defaults['subtitle_position']))
        self.subtitle_outline_color_var.set(config_data.get('subtitle_outline_color', defaults['subtitle_outline_color']))
        self.subtitle_outline_width_var.set(config_data.get('subtitle_outline_width', defaults['subtitle_outline_width']))
        self.subtitle_bg_color_var.set(config_data.get('subtitle_bg_color', defaults['subtitle_bg_color']))
        self.subtitle_bg_opacity_var.set(config_data.get('subtitle_bg_opacity', defaults['subtitle_bg_opacity']))

        # Load keyboard shortcuts - Handled by ShortcutManager
        self.shortcut_manager.load_shortcuts(config_data, defaults) # Delegate to ShortcutManager

        # Load persisted queue and processed data
        self.video_queue = config_data.get('video_queue_history', [])
        self.processed_file_data = config_data.get('processed_file_data_history', {})

        # Repopulate listbox from loaded history
        self.video_listbox.delete(0, tk.END) # Clear existing items
        for video_path in self.video_queue:
            file_info = self.processed_file_data.get(video_path, {'status': 'Unknown'}) # Default if somehow missing
            status = file_info.get('status', 'Unknown')
            self.video_listbox.insert(tk.END, f"[{status}] {os.path.basename(video_path)}")
        
        self.theme_var.set(config_data.get('theme', defaults['theme']))
        self._apply_theme() # Apply theme after loading
        self.update_compute_types() # Update compute types based on device
        self._update_translation_settings_ui() # IMPORTANT: Update UI after loading provider and keys
        # self._update_queue_statistics() # Moved to after __init__ fully completes

        if self.video_listbox.size() > 0:
            self.video_listbox.selection_set(0) # Select the first item
            queue_manager.on_video_select_in_queue(self) # Trigger UI update for the selection
            # self.on_video_select_in_queue() # OLD CALL

    def _save_config(self):
        """Save current configuration to JSON file."""
        try:
            # Try to convert batch_size to int
            try:
                batch_size = int(self.batch_size_var.get())
                if batch_size <= 0:
                    batch_size = get_default_config()['batch_size']
            except (ValueError, TypeError):
                batch_size = get_default_config()['batch_size']
                self.batch_size_var.set(str(batch_size))
            
            config_data = {
                'translation_provider': self.translation_provider_var.get(),
                'gemini_api_key': self.gemini_api_key_var.get(),
                'gemini_model': self.gemini_model_var.get(), # Save Gemini model
                'openai_api_key': self.openai_api_key_var.get(),
                'openai_model': self.openai_model_var.get(),
                'anthropic_api_key': self.anthropic_api_key_var.get(),
                'anthropic_model': self.anthropic_model_var.get(),
                'deepseek_api_key': self.deepseek_api_key_var.get(),
                'target_language': self.target_language.get(),
                'whisper_model': self.whisper_model_name_var.get(),
                'device': self.device_var.get(),
                'compute_type': self.compute_type_var.get(),
                'theme': self.theme_var.get(),
                'accent_color': self.accent_color_var.get(),
                'batch_size': batch_size,
                'output_format': self.output_format_var.get(),
                'preview': self.preview_var.get(),
                'auto_save': self.auto_save_var.get(),
                'gemini_temperature': self.gemini_temperature_var.get(),
                'gemini_top_p': self.gemini_top_p_var.get(),
                'gemini_top_k': self.gemini_top_k_var.get(),
                'extensive_logging': self.extensive_logging_var.get(),
                # Persist queue and processed data history
                'video_queue_history': self.video_queue,
                'processed_file_data_history': self.processed_file_data,
                'subtitle_font': self.subtitle_font_var.get(),
                'subtitle_color': self.subtitle_color_var.get(),
                'subtitle_size': self.subtitle_size_var.get(),
                'subtitle_position': self.subtitle_position_var.get(),
                'subtitle_outline_color': self.subtitle_outline_color_var.get(),
                'subtitle_outline_width': self.subtitle_outline_width_var.get(),
                'subtitle_bg_color': self.subtitle_bg_color_var.get(),
                'subtitle_bg_opacity': self.subtitle_bg_opacity_var.get(),
                'shortcuts': self.shortcut_manager.get_shortcuts_for_saving() # Delegate to ShortcutManager
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            self.log_status("Saved settings to config.")
        except Exception as e:
            self.log_status(f"Warning: Could not save config file: {e}")
    
    def log_status(self, message, level="INFO"):
        """Appends a message to the status text area with timestamp, respects extensive logging setting."""
        if level == "VERBOSE" and self.extensive_logging_var.get() != "On":
            return

        # Log to console always for now, or a more robust internal log if needed
        # print(f"LOG [{level}] {datetime.now().strftime("%H:%M:%S")}: {message}")

        if hasattr(self, 'text_widgets') and 'log' in self.text_widgets:
            status_text = self.text_widgets['log']
            status_text.configure(state='normal')
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_text.insert(tk.END, f"[{timestamp}] {message}\n")
            status_text.see(tk.END)
            status_text.configure(state='disabled')
        
        if hasattr(self, 'root'): # Check if root window exists
            self.root.update_idletasks()
        
        # Safely update status_label if it exists
        if hasattr(self, 'status_label') and self.status_label is not None:
            self.status_label.config(text=message)

    def display_output(self, content):
        """Displays content in the output area."""
        output_text = self.text_widgets['output']
        output_text.configure(state='normal')
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, content)
        output_text.configure(state='disabled')
        self.current_output = content

    def update_comparison_view(self):
        """Update the comparison view with original and translated text."""
        if not self.transcribed_segments or not self.translated_segments:
            return
            
        original_content = ""
        for i, segment in enumerate(self.transcribed_segments):
            start_time = f"{int(segment['start'] // 60):02}:{int(segment['start'] % 60):02}"
            end_time = f"{int(segment['end'] // 60):02}:{int(segment['end'] % 60):02}"
            text = segment['text']
            original_content += f"#{i+1} [{start_time} → {end_time}]\n{text}\n\n"
            
        translated_content = ""
        for i, segment in enumerate(self.translated_segments):
            start_time = f"{int(segment['start'] // 60):02}:{int(segment['start'] % 60):02}"
            end_time = f"{int(segment['end'] // 60):02}:{int(segment['end'] % 60):02}"
            text = segment['text']
            translated_content += f"#{i+1} [{start_time} → {end_time}]\n{text}\n\n"
            
        original_text = self.text_widgets['original']
        original_text.configure(state='normal')
        original_text.delete(1.0, tk.END)
        original_text.insert(tk.END, original_content)
        original_text.configure(state='disabled')
        
        translated_text = self.text_widgets['translated']
        translated_text.configure(state='normal')
        translated_text.delete(1.0, tk.END)
        translated_text.insert(tk.END, translated_content)
        translated_text.configure(state='disabled')

    def save_output_file(self):
        """Asks user where to save the output file based on selected format for the currently selected/processed video."""
        selected_indices = self.video_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "Please select a processed video from the queue to save its subtitles.")
            return

        original_video_path = self.video_queue[selected_indices[0]]
        file_data = self.processed_file_data.get(original_video_path)

        if not file_data or not file_data.get('output_content'):
            messagebox.showinfo("Info", "No output to save for the selected video. Please process it first.")
            return

        current_output_for_saving = file_data['output_content']
        output_format = self.output_format_var.get()
        
        if output_format == "srt" and file_data.get('subtitle_style'):
            current_output_for_saving = subtitle_styler.format_srt_with_style(self, current_output_for_saving, file_data['subtitle_style'])
            self.log_status("Applied subtitle styling to the saved file")
        
        if original_video_path:
            base, _ = os.path.splitext(original_video_path)
            default_filename = f"{base}.{output_format}"
        else:
            default_filename = f"subtitles.{output_format}"

        filepath_to_save = filedialog.asksaveasfilename(
            title=f"Save {output_format.upper()} File for {os.path.basename(original_video_path)}",
            defaultextension=f".{output_format}",
            initialfile=default_filename,
            filetypes=[(f"{output_format.upper()} File", f"*.{output_format}"), ("All Files", "*.*")]
        )
        
        if filepath_to_save:
            try:
                with open(filepath_to_save, 'w', encoding='utf-8') as f:
                    f.write(current_output_for_saving)
                self.log_status(f"File saved: {filepath_to_save}")
            except Exception as e:
                self.log_status(f"Error saving file {filepath_to_save}: {e}")
                messagebox.showerror("Save Error", f"Failed to save file: {e}")

    def update_progress(self, message, is_error=False, is_complete=False):
        """Update progress status and bar appearance."""
        self.progress_status.config(text=message)
        
        if is_error:
            self.progress_bar.stop()
            self.progress_status.config(foreground="red")
        elif is_complete:
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate', value=100)
            self.progress_status.config(foreground="green")
        else:
            if self.progress_bar['mode'] != 'indeterminate':
                self.progress_bar.config(mode='indeterminate')
                self.progress_bar.start(10)
            self.progress_status.config(foreground="")
        
        self.root.update_idletasks()

    def _format_timestamp(self, seconds):
        """Helper to format seconds to HH:MM:SS,ms or MM:SS,ms if hours are zero."""
        if seconds is None or not isinstance(seconds, (int, float)):
             self.log_status(f"Invalid seconds value for timestamp: {seconds}")
             return "00:00:00,000"
        sec = int(seconds)
        ms = int(round((seconds - sec) * 1000))
        hours = sec // 3600
        minutes = (sec % 3600) // 60
        secs = sec % 60
        # Correct ms rounding that might make it 1000
        if ms >= 1000:
            secs += 1
            ms = 0
            if secs >= 60:
                minutes +=1
                secs = 0
                if minutes >= 60:
                    hours +=1
                    minutes = 0

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"
        return f"{minutes:02d}:{secs:02d},{ms:03d}"

    def _handle_drop_files(self, event):
        """Handles files dropped onto the registered drop target (video_listbox)."""
        raw_paths_string = event.data
        self.log_status(f"Files dropped (raw string): {raw_paths_string}", "VERBOSE")

        # Use tk.splitlist to correctly parse paths, especially those with spaces
        # which are often enclosed in {}.
        try:
            # self.root is TkinterDnD.Tk(), so self.root.tk should be the Tcl interpreter instance
            parsed_file_paths = self.root.tk.splitlist(raw_paths_string)
        except tk.TclError as e:
            self.log_status(f"Error parsing dropped files using tk.splitlist: {e}", "ERROR")
            parsed_file_paths = [] # Fallback or error state
        
        if not parsed_file_paths and raw_paths_string: # If splitlist failed but there was data
            # Fallback to simple split if raw_paths_string doesn't look like a tcl list
            # This is a less robust fallback.
            if '{' not in raw_paths_string and '}' not in raw_paths_string:
                 parsed_file_paths = raw_paths_string.split()
                 self.log_status(f"Used fallback split for dropped files: {parsed_file_paths}", "WARNING")


        if parsed_file_paths:
            self.log_status(f"Parsed dropped files: {parsed_file_paths}", "INFO")
            # Pass the list of file paths to the existing queue manager function
            queue_manager.add_videos_to_queue(self, file_paths_to_add=list(parsed_file_paths)) # Ensure it's a list
        else:
            self.log_status("No valid file paths found in drop event after parsing.", "WARNING")

    def _validate_api_key_for_provider(self, provider_name, api_key_var, status_label):
        """Validates the API key for the given provider in a separate thread."""
        api_key = api_key_var.get()
        if not api_key:
            status_label.config(text="Key is empty", foreground="orange")
            return

        status_label.config(text="Validating...", foreground="blue")
        self.root.update_idletasks() # Ensure UI update

        def validation_thread_task():
            is_valid = False
            message = "Validation Error"
            
            try:
                if provider_name == "Gemini":
                    is_valid, message = validate_gemini_key(api_key, self.log_status)
                elif provider_name == "OpenAI":
                    is_valid, message = validate_openai_key(api_key, self.log_status)
                elif provider_name == "Anthropic":
                    is_valid, message = validate_anthropic_key(api_key, self.log_status)
                else:
                    message = "Unknown provider for validation."
            except Exception as e:
                message = f"Error: {str(e)[:50]}" # Show a concise error
                self.log_status(f"API Key validation failed for {provider_name}: {e}", "ERROR")

            # Update UI from the main thread
            def update_ui():
                if is_valid:
                    status_label.config(text=message, foreground="green")
                else:
                    status_label.config(text=message, foreground="red")
            
            self.root.after(0, update_ui)

        # Run in a separate thread to avoid freezing the UI
        threading.Thread(target=validation_thread_task, daemon=True).start()

    def _update_translation_settings_ui(self, event=None):
        """Update the translation settings UI based on the selected provider."""
        for widget in self.provider_details_frame.winfo_children():
            widget.destroy()
        self.api_key_status_labels.clear() # Clear old status labels

        provider = self.translation_provider_var.get()
        
        if provider == "Gemini":
            key_frame = ttk.Frame(self.provider_details_frame)
            key_frame.pack(fill=tk.X, pady=3)
            ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,2))
            ttk.Entry(key_frame, textvariable=self.gemini_api_key_var, width=30, show="•").pack(side=tk.LEFT, padx=(0,2), fill=tk.X, expand=True)
            
            status_label_gemini = ttk.Label(key_frame, text="Not Validated", width=15, anchor="w")
            status_label_gemini.pack(side=tk.LEFT, padx=(2,2))
            self.api_key_status_labels["Gemini"] = status_label_gemini
            
            ttk.Button(key_frame, text="Validate", width=8,
                       command=lambda p="Gemini", k=self.gemini_api_key_var, s=status_label_gemini: 
                       self._validate_api_key_for_provider(p, k, s)).pack(side=tk.LEFT, padx=(2,0))

            model_frame = ttk.Frame(self.provider_details_frame)
            model_frame.pack(fill=tk.X, pady=3)
            ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Combobox(model_frame, textvariable=self.gemini_model_var, values=GEMINI_MODELS, state="readonly", width=38).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
        elif provider == "OpenAI":
            key_frame = ttk.Frame(self.provider_details_frame)
            key_frame.pack(fill=tk.X, pady=3)
            ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,2))
            ttk.Entry(key_frame, textvariable=self.openai_api_key_var, width=30, show="•").pack(side=tk.LEFT, padx=(0,2), fill=tk.X, expand=True)

            status_label_openai = ttk.Label(key_frame, text="Not Validated", width=15, anchor="w")
            status_label_openai.pack(side=tk.LEFT, padx=(2,2))
            self.api_key_status_labels["OpenAI"] = status_label_openai

            ttk.Button(key_frame, text="Validate", width=8,
                       command=lambda p="OpenAI", k=self.openai_api_key_var, s=status_label_openai:
                       self._validate_api_key_for_provider(p, k, s)).pack(side=tk.LEFT, padx=(2,0))
            
            model_frame = ttk.Frame(self.provider_details_frame)
            model_frame.pack(fill=tk.X, pady=3)
            ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Combobox(model_frame, textvariable=self.openai_model_var, values=OPENAI_MODELS, state="readonly", width=38).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
        elif provider == "Anthropic":
            key_frame = ttk.Frame(self.provider_details_frame)
            key_frame.pack(fill=tk.X, pady=3)
            ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,2))
            ttk.Entry(key_frame, textvariable=self.anthropic_api_key_var, width=30, show="•").pack(side=tk.LEFT, padx=(0,2), fill=tk.X, expand=True)

            status_label_anthropic = ttk.Label(key_frame, text="Not Validated", width=15, anchor="w")
            status_label_anthropic.pack(side=tk.LEFT, padx=(2,2))
            self.api_key_status_labels["Anthropic"] = status_label_anthropic

            ttk.Button(key_frame, text="Validate", width=8,
                       command=lambda p="Anthropic", k=self.anthropic_api_key_var, s=status_label_anthropic:
                       self._validate_api_key_for_provider(p, k, s)).pack(side=tk.LEFT, padx=(2,0))

            model_frame = ttk.Frame(self.provider_details_frame)
            model_frame.pack(fill=tk.X, pady=3)
            ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Combobox(model_frame, textvariable=self.anthropic_model_var, values=ANTHROPIC_MODELS, state="readonly", width=38).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
        elif provider == "DeepSeek":
            key_frame = ttk.Frame(self.provider_details_frame)
            key_frame.pack(fill=tk.X, pady=3)
            ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,2))
            # DeepSeek key validation might not be possible with a simple model list if it uses OpenAI client strictly.
            # For now, no validation button for DeepSeek unless a specific lightweight call is known.
            ttk.Entry(key_frame, textvariable=self.deepseek_api_key_var, width=40, show="•").pack(side=tk.LEFT, padx=(0,2), fill=tk.X, expand=True)
            # If a validation method for DeepSeek is added, the button and label can be included here.
            
            model_frame = ttk.Frame(self.provider_details_frame)
            model_frame.pack(fill=tk.X, pady=3)
            ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Label(model_frame, text=DEEPSEEK_MODEL, width=25).pack(side=tk.LEFT, padx=5)

    def _handle_apply_new_shortcuts(self, new_shortcuts):
        """Handles applying new shortcuts from the settings dialog via ShortcutManager and saves config."""
        self.shortcut_manager.apply_new_shortcuts_from_dialog(new_shortcuts)
        self._save_config() # Save the entire application configuration
        self.log_status("AppGUI: Configuration saved after shortcut update.", "INFO")