"""
Main GUI application class for Film Translator Generator.
"""
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from datetime import datetime
import torch
import gc
import sv_ttk
import tempfile # For temporary subtitle file
import subprocess # For opening video with subtitles more reliably
import sys # For platform-specific operations
import re # For parsing editor content later

from config import (
    APP_TITLE, CONFIG_FILE, get_default_config, LANGUAGES, 
    WHISPER_MODELS, DEVICES, COMPUTE_TYPES, OUTPUT_FORMATS, 
    GITHUB_URL, APP_VERSION, TRANSLATION_PROVIDERS, 
    OPENAI_MODELS, ANTHROPIC_MODELS, DEEPSEEK_MODEL, GEMINI_MODELS, # Added GEMINI_MODELS
    # Add subtitle style constants
    SUBTITLE_FONTS, SUBTITLE_COLORS, SUBTITLE_SIZES, SUBTITLE_POSITIONS,
    SUBTITLE_OUTLINE_COLORS, SUBTITLE_OUTLINE_WIDTHS, SUBTITLE_BG_COLORS, SUBTITLE_BG_OPACITY
)
from backend.transcribe import transcribe_video, load_whisper_model
from backend.translate import translate_text
from utils.format import format_output
from utils.media import extract_video_thumbnail, play_video_preview, get_video_info
from gui.components import create_advanced_settings_dialog, create_about_dialog
from gui.main_layout import create_left_pane, create_right_pane
# Import project management functions
from gui import project_manager
# Import queue management functions
from gui import queue_manager
# Import video processing functions
from gui import video_processor
# Import subtitle styling functions
from gui import subtitle_styler
# Import editor management functions
from gui import editor_manager

class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("900x700")  # Larger size for modern UI
        self.root.minsize(800, 600)    # Set minimum window size
        
        # Apply modern theme
        sv_ttk.set_theme("dark")  # Start with dark theme
        
        # Initialize variables
        self.video_queue = []  # List to store video file paths
        self.processed_file_data = {} # Stores status and results per file path
        self.current_processing_video = None # Path of the video currently being processed
        self.selected_video_in_queue = tk.StringVar() 
        self.current_project_path = None # Path to the currently open project file
        
        # Statistics Variables
        self.stat_total_files = tk.StringVar(value="Total Files: 0")
        self.stat_processed_files = tk.StringVar(value="Processed: 0")
        self.stat_pending_files = tk.StringVar(value="Pending: 0")
        self.stat_failed_files = tk.StringVar(value="Failed: 0")
        self.extensive_logging_var = tk.StringVar() # For extensive logging setting
        self.translation_provider_var = tk.StringVar() # New var for translation provider
        
        self.gemini_api_key_var = tk.StringVar() # Renamed from self.api_key for clarity
        self.openai_api_key_var = tk.StringVar() 
        self.anthropic_api_key_var = tk.StringVar() # New for Anthropic API Key
        self.deepseek_api_key_var = tk.StringVar() # New for DeepSeek API Key
        self.gemini_model_var = tk.StringVar() # New for Gemini model selection
        
        self.openai_model_var = tk.StringVar() 
        self.anthropic_model_var = tk.StringVar() # New for Anthropic model

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
        
        self.gemini_temperature_var = tk.DoubleVar()
        self.gemini_top_p_var = tk.DoubleVar()
        self.gemini_top_k_var = tk.IntVar()
        
        # Subtitle style variables
        self.subtitle_font_var = tk.StringVar(value=SUBTITLE_FONTS[0])
        self.subtitle_color_var = tk.StringVar(value=SUBTITLE_COLORS[0])
        self.subtitle_size_var = tk.StringVar(value=SUBTITLE_SIZES[2])  # Default to a medium size (index 2)
        self.subtitle_position_var = tk.StringVar(value=SUBTITLE_POSITIONS[0])
        self.subtitle_outline_color_var = tk.StringVar(value=SUBTITLE_OUTLINE_COLORS[0])
        self.subtitle_outline_width_var = tk.StringVar(value=SUBTITLE_OUTLINE_WIDTHS[1])  # Default width of 1
        self.subtitle_bg_color_var = tk.StringVar(value=SUBTITLE_BG_COLORS[0])
        self.subtitle_bg_opacity_var = tk.StringVar(value=SUBTITLE_BG_OPACITY[0])
        
        # Configure button style
        self.style = ttk.Style()
        self.style.configure("Accent.TButton", font=("", 10, "bold"))
        
        # Model instance
        self.whisper_model = None
        
        # Results storage
        self.transcribed_segments = None
        self.translated_segments = None
        self.current_output = None
        
        # Create main frame structure
        self.create_menu()
        self.create_main_frame()
        
        # Load configuration
        self._load_config() # This will also call _update_translation_settings_ui
        self.update_compute_types() # Ensure this is called after device_var is set by _load_config
        
        # Update subtitle preview with loaded settings
        subtitle_styler.refresh_subtitle_style_preview(self) # Call after canvas is created and settings loaded
        
        # Update theme based on loaded config
        self._apply_theme() # Ensure theme is applied

        # Update queue statistics on startup after loading config/project
        queue_manager.update_queue_statistics(self)

        # Set up save on exit
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
        """Apply the selected theme to the application"""
        theme = self.theme_var.get()
        sv_ttk.set_theme(theme)
        self.log_status(f"Theme changed to {theme}")
    
    def preview_video(self):
        """Preview the selected video file from the queue (if one is selected and processed/valid)."""
        selected_indices = self.video_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select a video from the queue to preview.")
            return
        
        # Get the actual full path of the selected video
        selected_listbox_index = selected_indices[0]
        if selected_listbox_index >= len(self.video_queue):
            messagebox.showerror("Error", "Selected video not found in internal queue. Please check selection.")
            return
            
        actual_video_path = self.video_queue[selected_listbox_index] # Get full path from video_queue
        
        if not actual_video_path or not os.path.exists(actual_video_path):
            messagebox.showerror("Error", f"The selected video path is invalid or file does not exist: {actual_video_path}")
            return
            
        play_video_preview(actual_video_path, self.log_status)
    
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
                'subtitle_bg_opacity': self.subtitle_bg_opacity_var.get()
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            self.log_status("Saved settings to config.")
        except Exception as e:
            self.log_status(f"Warning: Could not save config file: {e}")
    
    def update_video_preview(self, video_path):
        """Update video thumbnail and information for the given path."""
        if not video_path: # Clear preview if no path
            self.thumbnail_label.config(image=None)
            self.thumbnail_label.image = None
            self.thumbnail_placeholder.pack() # Show placeholder
            self.video_duration_label.config(text="Duration: N/A")
            self.video_size_label.config(text="Size: N/A")
            return

        try:
            self.thumbnail_placeholder.pack_forget()
            self.thumbnail_label.config(image=None)
            
            thumbnail = extract_video_thumbnail(video_path)
            if thumbnail:
                self.thumbnail_label.config(image=thumbnail)
                self.thumbnail_label.image = thumbnail
                self.thumbnail_label.pack()
                self.thumbnail_placeholder.pack_forget()
            else:
                self.thumbnail_label.pack_forget()
                self.thumbnail_placeholder.pack()
            
            video_info = get_video_info(video_path)
            self.video_duration_label.config(text=f"Duration: {video_info['duration']}")
            self.video_size_label.config(text=f"Size: {video_info['size']}")
            
        except Exception as e:
            self.log_status(f"Error updating video preview: {e}")
            self.thumbnail_label.pack_forget()
            self.thumbnail_placeholder.pack()
            self.video_duration_label.config(text="Duration: N/A")
            self.video_size_label.config(text="Size: N/A")

    def log_status(self, message, level="INFO"):
        """Appends a message to the status text area with timestamp, respects extensive logging setting."""
        if level == "VERBOSE" and self.extensive_logging_var.get() != "On":
            return

        status_text = self.text_widgets['log']
        status_text.configure(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        status_text.see(tk.END)
        status_text.configure(state='disabled')
        self.root.update_idletasks()
        
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

    def preview_with_subtitles(self):
        """Saves the current output of the selected video as a temporary subtitle file and attempts to open the video with it."""
        
        selected_indices = self.video_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select a video from the queue to preview.")
            return
        
        # Get the actual full path of the selected video
        # The listbox stores "status + basename". We need the full path from video_queue
        selected_listbox_index = selected_indices[0]
        if selected_listbox_index >= len(self.video_queue): # Should not happen if listbox and video_queue are in sync
            messagebox.showerror("Error", "Selected video not found in internal queue. Please re-add.")
            return
            
        video_path = self.video_queue[selected_listbox_index] # Get full path
        
        file_data = self.processed_file_data.get(video_path)

        if not file_data or not file_data.get('output_content'):
            messagebox.showinfo("Info", f"No subtitles generated for {os.path.basename(video_path)} to preview.")
            return

        current_output_for_preview = file_data['output_content']
        output_format = self.output_format_var.get() # Global output format
        temp_subtitle_path = ""

        try:
            # Check if we need to apply styling
            if output_format == "srt" and file_data.get('subtitle_style'):
                # Only SRT and VTT support styling - for now just implement SRT
                self.log_status(f"Applying subtitle styling for preview")
                style = file_data['subtitle_style']
                
                # Apply style to the SRT content
                styled_output = subtitle_styler.format_srt_with_style(self, current_output_for_preview, style)
                current_output_for_preview = styled_output
            
            with tempfile.NamedTemporaryFile(mode="w", suffix=f".{output_format}", delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(current_output_for_preview)
                temp_subtitle_path = tmp_file.name
            
            self.log_status(f"Temporary subtitle file for {os.path.basename(video_path)}: {temp_subtitle_path}")

            try:
                if os.name == 'nt': 
                    try:
                        subprocess.Popen(["vlc", video_path, f"--sub-file={temp_subtitle_path}"])
                        self.log_status(f"Attempting to open {os.path.basename(video_path)} with VLC and subtitles...")
                    except FileNotFoundError:
                        self.log_status("VLC not found or failed, trying os.startfile...")
                        os.startfile(video_path) 
                elif sys.platform == 'darwin': 
                    subprocess.Popen(["open", video_path, "--args", "--sub-file", temp_subtitle_path]) 
                    self.log_status(f"Attempting to open {os.path.basename(video_path)} with subtitles on macOS...")
                else: 
                    try:
                        subprocess.Popen(["vlc", video_path, f"--sub-file={temp_subtitle_path}"])
                        self.log_status(f"Attempting to open {os.path.basename(video_path)} with VLC and subtitles...")
                    except FileNotFoundError:
                        self.log_status("VLC not found or failed, trying xdg-open...")
                        subprocess.Popen(["xdg-open", video_path])
                self.log_status(f"Showing video preview: {os.path.basename(video_path)} with subtitles.")

            except Exception as e_open:
                self.log_status(f"Could not automatically open {os.path.basename(video_path)} with subtitles: {e_open}. Opening video directly.")
                if os.name == 'nt': os.startfile(video_path)
                elif sys.platform == 'darwin': subprocess.Popen(["open", video_path])
                else: subprocess.Popen(["xdg-open", video_path])

        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to create temp subtitle or open {os.path.basename(video_path)}: {e}")
            self.log_status(f"Error during subtitle preview for {os.path.basename(video_path)}: {e}")
        finally:
            if temp_subtitle_path and os.path.exists(temp_subtitle_path):
                 self.log_status(f"Note: Temp subtitle {os.path.basename(temp_subtitle_path)} for {os.path.basename(video_path)} may need cleanup.")
                 pass
    
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

    def _update_translation_settings_ui(self, event=None):
        """Update the translation settings UI based on the selected provider."""
        # Clear previous provider settings
        for widget in self.provider_details_frame.winfo_children():
            widget.destroy()

        provider = self.translation_provider_var.get()
        
        if provider == "Gemini":
            # API key field
            key_frame = ttk.Frame(self.provider_details_frame)
            key_frame.pack(fill=tk.X, pady=3)
            ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Entry(key_frame, textvariable=self.gemini_api_key_var, width=40, show="•").pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # Model field - changed to Combobox
            model_frame = ttk.Frame(self.provider_details_frame)
            model_frame.pack(fill=tk.X, pady=3)
            ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT, padx=(0,5))
            # ttk.Label(model_frame, text="gemini-2.5-flash-preview-04-17", width=25).pack(side=tk.LEFT, padx=5) # Old label
            ttk.Combobox(model_frame, textvariable=self.gemini_model_var, values=GEMINI_MODELS, state="readonly", width=25).pack(side=tk.LEFT, padx=5)
            
        elif provider == "OpenAI":
            # API key field
            key_frame = ttk.Frame(self.provider_details_frame)
            key_frame.pack(fill=tk.X, pady=3)
            ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Entry(key_frame, textvariable=self.openai_api_key_var, width=40, show="•").pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # Model dropdown
            model_frame = ttk.Frame(self.provider_details_frame)
            model_frame.pack(fill=tk.X, pady=3)
            ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Combobox(model_frame, textvariable=self.openai_model_var, values=OPENAI_MODELS, state="readonly", width=25).pack(side=tk.LEFT, padx=5)
            
        elif provider == "Anthropic":
            # API key field
            key_frame = ttk.Frame(self.provider_details_frame)
            key_frame.pack(fill=tk.X, pady=3)
            ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Entry(key_frame, textvariable=self.anthropic_api_key_var, width=40, show="•").pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # Model dropdown
            model_frame = ttk.Frame(self.provider_details_frame)
            model_frame.pack(fill=tk.X, pady=3)
            ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Combobox(model_frame, textvariable=self.anthropic_model_var, values=ANTHROPIC_MODELS, state="readonly", width=25).pack(side=tk.LEFT, padx=5)
            
        elif provider == "DeepSeek":
            # API key field
            key_frame = ttk.Frame(self.provider_details_frame)
            key_frame.pack(fill=tk.X, pady=3)
            ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Entry(key_frame, textvariable=self.deepseek_api_key_var, width=40, show="•").pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # Model field (non-editable as only one model is supported currently)
            model_frame = ttk.Frame(self.provider_details_frame)
            model_frame.pack(fill=tk.X, pady=3)
            ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Label(model_frame, text=DEEPSEEK_MODEL, width=25).pack(side=tk.LEFT, padx=5)