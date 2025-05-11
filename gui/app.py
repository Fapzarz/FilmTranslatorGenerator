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
    OPENAI_MODELS, ANTHROPIC_MODELS, DEEPSEEK_MODEL # Added ANTHROPIC_MODELS, DEEPSEEK_MODEL
)
from backend.transcribe import transcribe_video, load_whisper_model
from backend.translate import translate_text
from utils.format import format_output
from utils.media import extract_video_thumbnail, play_video_preview, get_video_info
from gui.components import create_advanced_settings_dialog, create_about_dialog, create_notebook, create_progress_frame

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
        self._load_config()
        self.update_compute_types()
        
        # Update theme based on loaded config
        self._apply_theme()

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
        file_menu.add_command(label="Add Video(s) to Queue", command=self.add_videos_to_queue)
        file_menu.add_command(label="Load Project", command=self.load_project_dialog)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_command(label="Save Project As...", command=self.save_project_as_dialog)
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
        """Create the main application frame and widgets with an Adobe-like panel layout."""
        main_frame = ttk.Frame(self.root, padding="5") # Reduced main padding
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Main Horizontal Paned Window (Left: Queue/Controls, Right: Settings/WorkArea) ---
        main_paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True)

        # --- Left Pane: Queue Management & Processing Control ---
        left_pane_container = ttk.Frame(main_paned_window, padding="5")
        # Add with a default width, user can resize. Let's give it about 30-35% initially.
        main_paned_window.add(left_pane_container, weight=1) 

        queue_control_panel = ttk.LabelFrame(left_pane_container, text="File Queue & Processing", padding="10")
        queue_control_panel.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        queue_management_frame = ttk.Frame(queue_control_panel) 
        queue_management_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.video_listbox = tk.Listbox(queue_management_frame, height=8, selectmode=tk.SINGLE)
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5), pady=5)

        listbox_scrollbar = ttk.Scrollbar(queue_management_frame, orient=tk.VERTICAL, command=self.video_listbox.yview)
        listbox_scrollbar.pack(side=tk.LEFT, fill=tk.Y, pady=5)
        self.video_listbox.config(yscrollcommand=listbox_scrollbar.set)

        queue_buttons_frame = ttk.Frame(queue_management_frame)
        queue_buttons_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5,0), pady=5)

        add_button = ttk.Button(queue_buttons_frame, text="Add Video(s)", command=self.add_videos_to_queue)
        add_button.pack(fill=tk.X, pady=2)
        remove_button = ttk.Button(queue_buttons_frame, text="Remove Selected", command=self.remove_selected_video_from_queue)
        remove_button.pack(fill=tk.X, pady=2)
        clear_button = ttk.Button(queue_buttons_frame, text="Clear Queue", command=self.clear_video_queue)
        clear_button.pack(fill=tk.X, pady=2)

        # Define progress_action_frame and its components first
        progress_action_frame, self.progress_bar, self.progress_status, self.generate_button = create_progress_frame(
            queue_control_panel, self.start_processing 
        )
        # We will pack it later, after stats_frame

        # --- Queue Statistics Frame ---
        stats_frame = ttk.LabelFrame(queue_control_panel, text="Queue Statistics", padding="5")
        stats_frame.pack(fill=tk.X, padx=5, pady=(5,0)) # Removed 'before' as we pack progress_action_frame after

        ttk.Label(stats_frame, textvariable=self.stat_total_files).pack(anchor='w', padx=5)
        ttk.Label(stats_frame, textvariable=self.stat_processed_files).pack(anchor='w', padx=5)
        ttk.Label(stats_frame, textvariable=self.stat_pending_files).pack(anchor='w', padx=5)
        ttk.Label(stats_frame, textvariable=self.stat_failed_files).pack(anchor='w', padx=5)

        # Now pack progress_action_frame below stats_frame
        progress_action_frame.pack(fill=tk.X, padx=5, pady=(5,5)) # Adjusted padding slightly
        
        # --- Right Pane: Settings, Preview, and Main Work Area (Notebook) ---
        right_pane_container = ttk.Frame(main_paned_window, padding="5")
        main_paned_window.add(right_pane_container, weight=2) # Give more weight/space to the right pane

        # Container for settings panels (top part of right_pane_container)
        top_right_settings_area = ttk.Frame(right_pane_container)
        top_right_settings_area.pack(fill=tk.X, pady=(0,5))

        # Panel 2.1: Selected Item Preview & Global Settings (will be inside top_right_settings_area)
        settings_preview_panel = ttk.LabelFrame(top_right_settings_area, text="Preview & Translation Setup", padding="10")
        settings_preview_panel.pack(fill=tk.X, padx=2, pady=2)
        
        preview_sub_panel = ttk.LabelFrame(settings_preview_panel, text="Selected Video Preview", padding="5")
        preview_sub_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5, ipadx=5, ipady=5) # Added some internal padding
        
        self.thumbnail_label = ttk.Label(preview_sub_panel) 
        self.thumbnail_label.pack(pady=5, padx=5)
        self.thumbnail_placeholder = ttk.Label(preview_sub_panel, text="Select a video from queue") 
        self.thumbnail_placeholder.pack(pady=5, padx=5)
        
        self.video_info_frame = ttk.Frame(preview_sub_panel) 
        self.video_info_frame.pack(fill=tk.X, padx=5, pady=5)
        self.video_duration_label = ttk.Label(self.video_info_frame, text="Duration: N/A")
        self.video_duration_label.pack(side=tk.LEFT, padx=5)
        self.video_size_label = ttk.Label(self.video_info_frame, text="Size: N/A")
        self.video_size_label.pack(side=tk.LEFT, padx=20)
        
        translation_settings_sub_panel = ttk.Frame(settings_preview_panel, padding="5")
        translation_settings_sub_panel.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        # --- Translation Provider Selection ---
        provider_selection_frame = ttk.Frame(translation_settings_sub_panel)
        provider_selection_frame.pack(fill=tk.X, padx=5, pady=3)
        ttk.Label(provider_selection_frame, text="Provider:").pack(side=tk.LEFT, padx=(0,5), anchor='w')
        self.provider_combobox = ttk.Combobox(
            provider_selection_frame, 
            textvariable=self.translation_provider_var, 
            values=TRANSLATION_PROVIDERS, 
            state="readonly", 
            width=15 # Adjusted width
        )
        self.provider_combobox.pack(side=tk.LEFT, padx=5)
        self.provider_combobox.bind("<<ComboboxSelected>>", self._update_translation_settings_ui)

        # --- Frame for Provider-Specific Settings (API Key, Model, etc.) ---
        self.provider_details_frame = ttk.Frame(translation_settings_sub_panel)
        self.provider_details_frame.pack(fill=tk.X, expand=True, padx=5, pady=(5,0))

        # Initial call to populate based on default/loaded provider
        # This will be called again in _load_config after variables are set

        # --- Common Translation Settings (Language, Output Format) ---
        common_settings_frame = ttk.Frame(translation_settings_sub_panel)
        common_settings_frame.pack(fill=tk.X, padx=5, pady=3)

        lang_frame = ttk.Frame(common_settings_frame)
        lang_frame.pack(fill=tk.X, pady=(0,3))
        ttk.Label(lang_frame, text="Target Language:").pack(side=tk.LEFT, padx=(0,5), anchor='w')
        self.language_combobox = ttk.Combobox(lang_frame, textvariable=self.target_language, 
                                             values=LANGUAGES, state="readonly", width=18)
        self.language_combobox.pack(side=tk.LEFT, padx=5)
        
        format_frame = ttk.Frame(common_settings_frame)
        format_frame.pack(fill=tk.X)
        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT, padx=(0,5), anchor='w')
        self.format_combobox = ttk.Combobox(format_frame, textvariable=self.output_format_var,
                                          values=OUTPUT_FORMATS, state="readonly", width=10)
        self.format_combobox.pack(side=tk.LEFT, padx=5)
        
        # Panel 2.2: Whisper Settings (also in top_right_settings_area, below or beside settings_preview_panel)
        # For simplicity, let's pack it below settings_preview_panel within top_right_settings_area
        whisper_frame = ttk.LabelFrame(top_right_settings_area, text="Whisper Transcription Settings", padding="10")
        whisper_frame.pack(fill=tk.X, padx=2, pady=(5,2)) # Added some top padding
        
        settings_frame_whisper = ttk.Frame(whisper_frame) 
        settings_frame_whisper.pack(fill=tk.X, padx=5, pady=5)
        
        # Using grid for Whisper settings for more compact layout
        ttk.Label(settings_frame_whisper, text="Model:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.model_combobox = ttk.Combobox(settings_frame_whisper, textvariable=self.whisper_model_name_var, 
                                         values=WHISPER_MODELS, state="readonly", width=12)
        self.model_combobox.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        
        ttk.Label(settings_frame_whisper, text="Device:").grid(row=0, column=2, padx=5, pady=3, sticky="w")
        self.device_combobox = ttk.Combobox(settings_frame_whisper, textvariable=self.device_var, 
                                          values=DEVICES, state="readonly", width=8)
        self.device_combobox.grid(row=0, column=3, padx=5, pady=3, sticky="w")
        self.device_combobox.bind("<<ComboboxSelected>>", self.update_compute_types)
        
        ttk.Label(settings_frame_whisper, text="Compute Type:").grid(row=0, column=4, padx=5, pady=3, sticky="w")
        self.compute_type_combobox = ttk.Combobox(settings_frame_whisper, textvariable=self.compute_type_var, 
                                                state="readonly", width=10)
        self.compute_type_combobox.grid(row=0, column=5, padx=5, pady=3, sticky="w")
        # Allow columns to expand if needed
        for i in range(6): settings_frame_whisper.columnconfigure(i, weight=1)
        
        # --- Main Work Area: Notebook (bottom part of right_pane_container) ---
        self.notebook, self.text_widgets = create_notebook(right_pane_container) # Parent is now right_pane_container
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=(5,2)) # Added some top padding
        
        # Connect the handlers for notebook widgets (ensure this is done after create_notebook)
        self.text_widgets['copy_button'].config(command=self.copy_to_clipboard)
        self.text_widgets['save_button'].config(command=self.save_output_file)
        self.text_widgets['preview_sub_button'].config(command=self.preview_with_subtitles)
        self.text_widgets['save_editor_button'].config(command=self.apply_editor_changes)
        
        self.video_listbox.bind('<<ListboxSelect>>', self.on_video_select_in_queue)
        
        # Status bar (remains at the bottom of the root window)
        status_bar = ttk.Frame(self.root) # Parent is self.root
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
        
        video_path = self.video_listbox.get(selected_indices[0]) # Get path from listbox item
        
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("Error", "The selected video path is invalid.")
            return
            
        play_video_preview(video_path, self.log_status)
    
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
        self._update_queue_statistics() # Update statistics display

        if self.video_listbox.size() > 0:
            self.video_listbox.selection_set(0) # Select the first item
            self.on_video_select_in_queue() # Trigger UI update for the selection

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
                'openai_api_key': self.openai_api_key_var.get(),
                'anthropic_api_key': self.anthropic_api_key_var.get(),
                'deepseek_api_key': self.deepseek_api_key_var.get(),
                'openai_model': self.openai_model_var.get(),
                'anthropic_model': self.anthropic_model_var.get(),
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
                'processed_file_data_history': self.processed_file_data
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            self.log_status("Saved settings to config.")
        except Exception as e:
            self.log_status(f"Warning: Could not save config file: {e}")

    def add_videos_to_queue(self):
        """Prompts user to select one or more video files and adds them to the queue."""
        filepaths = filedialog.askopenfilenames(
            title="Select Video File(s)",
            filetypes=(("Video Files", "*.mp4 *.avi *.mkv *.mov *.webm"), ("All Files", "*.*"))
        )
        if filepaths:
            for filepath in filepaths:
                if filepath not in self.video_queue:
                    self.video_queue.append(filepath)
                    self.processed_file_data[filepath] = {'status': 'Pending', 'transcribed_segments': None, 'translated_segments': None, 'output_content': None}
                    self.video_listbox.insert(tk.END, f"[Pending] {os.path.basename(filepath)}")
                    self.log_status(f"Added to queue: {filepath}")
                else:
                    self.log_status(f"Already in queue: {filepath}")
            self.log_status(f"{len(filepaths)} video(s) selected. Queue size: {len(self.video_queue)}")
            if self.video_listbox.size() > 0 and not self.video_listbox.curselection():
                self.video_listbox.selection_set(0) # Select first item if none selected
                self.on_video_select_in_queue() # Trigger preview update
            self._update_queue_statistics() # Update stats

    def on_video_select_in_queue(self, event=None):
        """Handles selection change in the video queue listbox."""
        selected_indices = self.video_listbox.curselection()
        if not selected_indices:
            self.update_video_preview(None) # Clear preview
            self.display_output("") # Clear output tabs
            self.text_widgets['original'].configure(state='normal'); self.text_widgets['original'].delete(1.0, tk.END); self.text_widgets['original'].configure(state='disabled')
            self.text_widgets['translated'].configure(state='normal'); self.text_widgets['translated'].delete(1.0, tk.END); self.text_widgets['translated'].configure(state='disabled')
            self.text_widgets['editor_text'].configure(state='disabled'); self.text_widgets['editor_text'].delete(1.0, tk.END) # Clear and disable editor
            return

        raw_listbox_item = self.video_listbox.get(selected_indices[0])
        # Extract filepath from listbox item (e.g., from "[Pending] filename.mp4")
        # This assumes basename does not contain "]"
        if "]" in raw_listbox_item:
            filepath_basename = raw_listbox_item.split("] ", 1)[1]
            # Find full path from basename (less robust if multiple files with same name from different dirs)
            # A better way is to store full paths and find it, or store an index map.
            # For now, we rely on self.video_queue order matching listbox order if no reordering.
            # This will break if listbox content and self.video_queue get out of sync.
            # Let's find the actual path from self.video_queue based on basename
            actual_filepath = next((fp for fp in self.video_queue if os.path.basename(fp) == filepath_basename), None)
            if not actual_filepath: # Fallback if basename matching failed
                 actual_filepath = self.video_queue[selected_indices[0]] # Assuming direct index match as a fallback
        else: # Should not happen with new format
            actual_filepath = raw_listbox_item

        # Schedule the UI update to allow the event loop to process other events (like paned window dragging)
        self.root.after(50, lambda fp=actual_filepath: self._handle_video_selection_update(fp))

    def _handle_video_selection_update(self, actual_filepath):
        """Handles the actual UI updates after a video selection, called via root.after()."""
        if actual_filepath and os.path.exists(actual_filepath):
            self.update_video_preview(actual_filepath)
            file_data = self.processed_file_data.get(actual_filepath)
            if file_data and file_data['status'] in ['Done', 'Error_Translation', 'Error_Transcription', 'Error_Generic'] and file_data.get('translated_segments'):
                self.display_output(file_data.get('output_content', ""))
                self.transcribed_segments = file_data.get('transcribed_segments') 
                self.translated_segments = file_data.get('translated_segments')   
                self.update_comparison_view()
                self._load_segments_to_editor(self.translated_segments) 
                if self.translated_segments:
                    self.text_widgets['editor_text'].configure(state='normal')
                else:
                    self.text_widgets['editor_text'].configure(state='disabled')
            elif file_data: 
                self.display_output(f"Video selected: {os.path.basename(actual_filepath)}\\nStatus: {file_data['status']}")
                self.text_widgets['original'].configure(state='normal'); self.text_widgets['original'].delete(1.0, tk.END); self.text_widgets['original'].configure(state='disabled')
                self.text_widgets['translated'].configure(state='normal'); self.text_widgets['translated'].delete(1.0, tk.END); self.text_widgets['translated'].configure(state='disabled')
                self.text_widgets['editor_text'].configure(state='disabled'); self.text_widgets['editor_text'].delete(1.0, tk.END)
            else: 
                self.display_output(f"No data found for {os.path.basename(actual_filepath)}.")
                self.text_widgets['editor_text'].configure(state='disabled'); self.text_widgets['editor_text'].delete(1.0, tk.END)
        else: 
            self.update_video_preview(None) 
            self.display_output("")
            self.text_widgets['original'].configure(state='normal'); self.text_widgets['original'].delete(1.0, tk.END); self.text_widgets['original'].configure(state='disabled')
            self.text_widgets['translated'].configure(state='normal'); self.text_widgets['translated'].delete(1.0, tk.END); self.text_widgets['translated'].configure(state='disabled')
            self.text_widgets['editor_text'].configure(state='disabled'); self.text_widgets['editor_text'].delete(1.0, tk.END)
        # self._update_queue_statistics() # This is already called at the end of on_video_select_in_queue if needed

    def remove_selected_video_from_queue(self):
        """Removes the selected video from the queue."""
        selected_indices = self.video_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "Please select a video from the queue to remove.")
            return
        
        index_to_remove = selected_indices[0]
        filepath_to_remove = self.video_queue.pop(index_to_remove) # Remove from internal list first
        
        self.video_listbox.delete(index_to_remove)
        if filepath_to_remove in self.processed_file_data:
            del self.processed_file_data[filepath_to_remove]
        self.log_status(f"Removed from queue: {filepath_to_remove}")
        
        if self.video_listbox.size() > 0:
            if index_to_remove < self.video_listbox.size():
                 self.video_listbox.selection_set(index_to_remove)
            else:
                 self.video_listbox.selection_set(self.video_listbox.size() - 1)
            self.on_video_select_in_queue()
        else: # Queue is now empty
            self.update_video_preview(None)
            self.display_output("")
            self.text_widgets['original'].configure(state='normal'); self.text_widgets['original'].delete(1.0, tk.END); self.text_widgets['original'].configure(state='disabled')
            self.text_widgets['translated'].configure(state='normal'); self.text_widgets['translated'].delete(1.0, tk.END); self.text_widgets['translated'].configure(state='disabled')
            self.text_widgets['editor_text'].configure(state='disabled'); self.text_widgets['editor_text'].delete(1.0, tk.END)
        self._update_queue_statistics() # Update stats

    def clear_video_queue(self):
        """Clears all videos from the queue."""
        if not self.video_queue:
            messagebox.showinfo("Info", "Queue is already empty.")
            return
        
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the entire video queue?"):
            self.video_queue.clear()
            self.processed_file_data.clear()
            self.video_listbox.delete(0, tk.END)
            self.log_status("Video queue cleared.")
            self.update_video_preview(None)
            self.display_output("")
            self.text_widgets['original'].configure(state='normal'); self.text_widgets['original'].delete(1.0, tk.END); self.text_widgets['original'].configure(state='disabled')
            self.text_widgets['translated'].configure(state='normal'); self.text_widgets['translated'].delete(1.0, tk.END); self.text_widgets['translated'].configure(state='disabled')
            self.text_widgets['editor_text'].configure(state='disabled'); self.text_widgets['editor_text'].delete(1.0, tk.END)
            self._update_queue_statistics() # Update stats
    
    def update_video_preview(self, video_path):
        """Update video thumbnail and information for the given path."""
        # This function will now be called when a video is selected in the listbox,
        # or after a video is processed to show its specific preview.
        # For now, it's just called from add_videos_to_queue (indirectly, if we re-enable auto-preview or selection update)
        # and remove_selected_video_from_queue (to clear preview).
        if not video_path: # Clear preview if no path
            self.thumbnail_label.config(image=None)
            self.thumbnail_label.image = None
            self.thumbnail_placeholder.pack() # Show placeholder
            self.video_duration_label.config(text="Duration: N/A")
            self.video_size_label.config(text="Size: N/A")
            return

        try:
            # Clear current thumbnail
            self.thumbnail_placeholder.pack_forget()
            self.thumbnail_label.config(image=None)
            
            # Extract and display thumbnail
            thumbnail = extract_video_thumbnail(video_path)
            if thumbnail:
                self.thumbnail_label.config(image=thumbnail)
                self.thumbnail_label.image = thumbnail  # Keep a reference to prevent garbage collection
                self.thumbnail_label.pack()
                self.thumbnail_placeholder.pack_forget()
            else:
                self.thumbnail_label.pack_forget()
                self.thumbnail_placeholder.pack()
            
            # Get video info
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
            return # Skip verbose messages if extensive logging is off

        status_text = self.text_widgets['log']
        status_text.configure(state='normal')  # Enable writing
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        status_text.see(tk.END)  # Scroll to the bottom
        status_text.configure(state='disabled')  # Disable writing
        self.root.update_idletasks()  # Force GUI update
        
        # Update status bar
        self.status_label.config(text=message)

    def display_output(self, content):
        """Displays content in the output area."""
        output_text = self.text_widgets['output']
        output_text.configure(state='normal')
        output_text.delete(1.0, tk.END)  # Clear previous content
        output_text.insert(tk.END, content)
        output_text.configure(state='disabled')
        self.current_output = content

    def update_comparison_view(self):
        """Update the comparison view with original and translated text."""
        if not self.transcribed_segments or not self.translated_segments:
            return
            
        # Format original text
        original_content = ""
        for i, segment in enumerate(self.transcribed_segments):
            start_time = f"{int(segment['start'] // 60):02}:{int(segment['start'] % 60):02}"
            end_time = f"{int(segment['end'] // 60):02}:{int(segment['end'] % 60):02}"
            text = segment['text']
            original_content += f"#{i+1} [{start_time} → {end_time}]\n{text}\n\n"
            
        # Format translated text
        translated_content = ""
        for i, segment in enumerate(self.translated_segments):
            # Fixed time formatting to match the original segments
            start_time = f"{int(segment['start'] // 60):02}:{int(segment['start'] % 60):02}"
            end_time = f"{int(segment['end'] // 60):02}:{int(segment['end'] % 60):02}"
            text = segment['text']
            translated_content += f"#{i+1} [{start_time} → {end_time}]\n{text}\n\n"
            
        # Update text widgets
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

        # Assuming self.video_queue and listbox are in sync by index for path retrieval
        # This part needs to be more robust or use the stored full path from self.processed_file_data
        # For now, let's get the path from self.video_queue which should be reliable.
        original_video_path = self.video_queue[selected_indices[0]]
        
        file_data = self.processed_file_data.get(original_video_path)

        if not file_data or not file_data.get('output_content'):
            messagebox.showinfo("Info", "No output to save for the selected video. Please process it first.")
            return

        current_output_for_saving = file_data['output_content']
        output_format = self.output_format_var.get() # Global output format for now
        
        if original_video_path:
            base, _ = os.path.splitext(original_video_path)
            default_filename = f"{base}.{output_format}"
        else: # Should not happen if selection is required
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
        # Update status message
        self.progress_status.config(text=message)
        
        # Update progress bar appearance based on state
        if is_error:
            # Error state - use red color if possible
            self.progress_bar.stop()
            self.progress_status.config(foreground="red")
            
        elif is_complete:
            # Completed state - fill the bar
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate', value=100)
            self.progress_status.config(foreground="green")
            
        else:
            # In-progress state - use indeterminate animation
            if self.progress_bar['mode'] != 'indeterminate':
                self.progress_bar.config(mode='indeterminate')
                self.progress_bar.start(10)
            self.progress_status.config(foreground="")  # Reset to default
        
        # Update UI
        self.root.update_idletasks()

    def _load_whisper_model_sync(self):
        """Loads the faster-whisper model based on selected settings."""
        # Get current settings from GUI
        model_name = self.whisper_model_name_var.get()
        device = self.device_var.get()
        compute_type = self.compute_type_var.get()

        # Check if model needs reloading (different settings or not loaded)
        if self.whisper_model and hasattr(self.whisper_model, 'model') and \
           self.whisper_model.model_size == model_name and \
           self.whisper_model.device == device and \
           self.whisper_model.compute_type == compute_type:
            self.log_status("Whisper model already loaded with correct settings.")
            return True

        # Release previous model if settings changed
        if self.whisper_model:
            self.log_status("Releasing previous Whisper model due to setting change...")
            try:
                del self.whisper_model
                self.whisper_model = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()
                self.log_status("Previous model released.")
            except Exception as e:
                self.log_status(f"Warning: Error releasing previous model - {e}")

        # Load the new model
        try:
            self.whisper_model = load_whisper_model(model_name, device, compute_type, self.log_status)
            return True
        except Exception as e:
            self.log_status(f"Error loading Whisper model: {e}")
            messagebox.showerror("Faster-Whisper Error", f"Failed to load model: {e}\nCheck CUDA/cuDNN setup and compute capability.")
            self.whisper_model = None
            return False

    def process_video_thread(self):
        """Runs the transcription and translation in a separate thread for files in the queue."""
        
        original_button_text = self.generate_button.cget("text")
        self.generate_button.config(text="Processing...", state=tk.DISABLED)

        for video_idx, video_file in enumerate(self.video_queue):
            if self.processed_file_data[video_file]['status'] == 'Done':
                self.log_status(f"Skipping {os.path.basename(video_file)}, already processed.")
                continue

            self.current_processing_video = video_file
            self.video_listbox.delete(video_idx)
            self.video_listbox.insert(video_idx, f"[Processing] {os.path.basename(video_file)}")
            self.video_listbox.selection_clear(0, tk.END)
            self.video_listbox.selection_set(video_idx)
            self.video_listbox.see(video_idx)
            self.root.update_idletasks()
            self._update_queue_statistics()

            self.transcribed_segments = None
            self.translated_segments = None
            self.current_output = None

            try:  # Main try for processing a single video file
                self.update_progress(f"Starting ({video_idx+1}/{len(self.video_queue)}): {os.path.basename(video_file)}...")
                self.log_status(f"--- Starting Process for {os.path.basename(video_file)} ({video_idx+1}/{len(self.video_queue)}) ---")
                if video_idx == self.video_listbox.curselection()[0] if self.video_listbox.curselection() else False:
                    self.display_output("")

                self.processed_file_data[video_file]['status'] = 'Processing_Whisper'
                
                                # Initial checks
                api_key_val = self.gemini_api_key_var.get()
                target_lang_val = self.target_language.get()

                if not video_file or not os.path.exists(video_file):
                    self.log_status(f"Error: Video file not found: {video_file}")
                    self.update_progress(f"Error: File not found {os.path.basename(video_file)}", is_error=True)
                    self.processed_file_data[video_file]['status'] = 'Error_FileNotFound'
                    continue
                
                if not ((self.translation_provider_var.get() == "Gemini" and api_key_val) or
                        (self.translation_provider_var.get() == "OpenAI" and self.openai_api_key_var.get()) or
                        (self.translation_provider_var.get() == "Anthropic" and self.anthropic_api_key_var.get()) or
                        (self.translation_provider_var.get() == "DeepSeek" and self.deepseek_api_key_var.get())):
                    # Simplified API key check: if selected provider needs a key and it's missing.
                    missing_key_provider = self.translation_provider_var.get()
                    messagebox.showerror("Error", f"API Key for {missing_key_provider} is missing.")
                    self.log_status(f"Error: API Key for {missing_key_provider} missing. Halting queue.")
                    self.update_progress(f"Error: API Key for {missing_key_provider} missing", is_error=True)
                    self.processed_file_data[video_file]['status'] = 'Error_Config'
                    break  # Stop queue processing for missing API key

                if not target_lang_val:
                    messagebox.showerror("Error", "Please select a target language.")
                    self.log_status("Error: Target language not selected. Halting queue.")
                    self.update_progress("Error: No target language", is_error=True)
                    self.processed_file_data[video_file]['status'] = 'Error_Config'
                    break  # Stop queue processing

                # All initial checks passed, proceed with core processing
                self._save_config()  # Save general app settings

                try:  # For batch_size conversion
                    batch_size = int(self.batch_size_var.get())
                    if batch_size <= 0:
                        batch_size = get_default_config()['batch_size']
                except (ValueError, TypeError):
                    batch_size = get_default_config()['batch_size']

                self.update_progress(f"Loading Whisper model for {os.path.basename(video_file)}...")
                if not self._load_whisper_model_sync():
                    self.log_status(f"--- Process Failed (Whisper Model Load) for {os.path.basename(video_file)} ---")
                    self.update_progress("Failed to load Whisper model", is_error=True)
                    self.processed_file_data[video_file]['status'] = 'Error_WhisperModel'
                    continue  # Skip to next file
                
                # Whisper model loaded, proceed to transcription
                self.update_progress(f"Transcribing {os.path.basename(video_file)}...")
                self.log_status(f"Starting transcription for {os.path.basename(video_file)}...")
                self.processed_file_data[video_file]['status'] = 'Transcribing'
                transcribed_segments = transcribe_video(self.whisper_model, video_file, self.log_status)
                self.processed_file_data[video_file]['transcribed_segments'] = transcribed_segments
                self.transcribed_segments = transcribed_segments

                if not transcribed_segments:
                    self.log_status(f"--- Process Failed (Transcription) for {os.path.basename(video_file)} ---")
                    self.update_progress(f"Transcription failed for {os.path.basename(video_file)}", is_error=True)
                    self.processed_file_data[video_file]['status'] = 'Error_Transcription'
                    continue
                
                segments_count = len(transcribed_segments)
                self.update_progress(f"Transcribed {segments_count} segments for {os.path.basename(video_file)}")
                self.log_status(f"Transcription completed for {os.path.basename(video_file)} with {segments_count} segments")

                # Proceed to translation only if transcription was successful
                self.update_progress(f"Translating {os.path.basename(video_file)} to {target_lang_val}...")
                self.log_status(f"Starting translation for {os.path.basename(video_file)} to {target_lang_val}...")
                self.processed_file_data[video_file]['status'] = 'Translating'
                
                selected_provider = self.translation_provider_var.get()
                provider_config = {
                    'name': selected_provider,
                }
                
                # Add provider-specific configurations
                if selected_provider == "Gemini":
                    provider_config['gemini_api_key'] = self.gemini_api_key_var.get()
                    provider_config['gemini_temperature'] = self.gemini_temperature_var.get()
                    provider_config['gemini_top_p'] = self.gemini_top_p_var.get()
                    provider_config['gemini_top_k'] = self.gemini_top_k_var.get()
                elif selected_provider == "OpenAI":
                    provider_config['openai_api_key'] = self.openai_api_key_var.get()
                    provider_config['openai_model'] = self.openai_model_var.get()
                elif selected_provider == "Anthropic":
                    provider_config['anthropic_api_key'] = self.anthropic_api_key_var.get()
                    provider_config['anthropic_model'] = self.anthropic_model_var.get()
                elif selected_provider == "DeepSeek":
                    provider_config['deepseek_api_key'] = self.deepseek_api_key_var.get()
                    # DeepSeek model is fixed

                translated_segments = translate_text(
                    provider_config, transcribed_segments, target_lang_val,
                    self.log_status, batch_size
                )
                self.processed_file_data[video_file]['translated_segments'] = translated_segments
                self.translated_segments = translated_segments
                
                if not translated_segments:
                    self.log_status(f"--- Process Failed (Translation) for {os.path.basename(video_file)} ---")
                    self.update_progress(f"Translation failed for {os.path.basename(video_file)}", is_error=True)
                    self.processed_file_data[video_file]['status'] = 'Error_Translation'
                    continue
                
                # Translation successful, format output
                output_format_val = self.output_format_var.get()
                self.update_progress(f"Formatting output ({output_format_val}) for {os.path.basename(video_file)}...")
                self.log_status(f"Creating output in {output_format_val} for {os.path.basename(video_file)}...")
                current_output_for_file = format_output(translated_segments, output_format_val)
                self.processed_file_data[video_file]['output_content'] = current_output_for_file
                self.current_output = current_output_for_file
                
                if video_idx == self.video_listbox.curselection()[0] if self.video_listbox.curselection() else False:
                    self.display_output(current_output_for_file)
                self.update_comparison_view()
                
                if self.auto_save_var.get() == "On":
                    self.update_progress(f"Auto-saving output for {os.path.basename(video_file)}...")
                    base, _ = os.path.splitext(video_file)
                    auto_save_path = f"{base}.{output_format_val}"
                    try:
                        with open(auto_save_path, 'w', encoding='utf-8') as f:
                            f.write(current_output_for_file)
                        self.log_status(f"Auto-saved: {auto_save_path}")
                    except Exception as e_save:
                        self.log_status(f"Error auto-saving {auto_save_path}: {e_save}")
                
                self.log_status(f"--- Process Finished Successfully for {os.path.basename(video_file)} ---")
                self.update_progress(f"Completed: {os.path.basename(video_file)}", is_complete=True)
                self.processed_file_data[video_file]['status'] = 'Done'
            
            except Exception as e:  # Catch-all for the current video file processing
                error_msg = str(e)
                self.log_status(f"Unhandled error processing {os.path.basename(video_file)}: {error_msg}")
                messagebox.showerror("Processing Error", f"An unexpected error occurred with {os.path.basename(video_file)}: {error_msg}")
                self.processed_file_data.setdefault(video_file, {})  # Ensure dict entry exists
                if not self.processed_file_data[video_file].get('status', '').startswith('Error_'):
                    self.processed_file_data[video_file]['status'] = 'Error_Generic'
                # If it was already an Error_Config, Error_FileNotFound etc., it remains that.
            
            finally:  # This finally block executes for each video file in the loop
                # Update listbox with the final status for this item
                final_status = self.processed_file_data.get(video_file, {}).get('status', 'Error_Unknown')
                # Check if item still exists in listbox (it might if error was before listbox update)
                if video_idx < self.video_listbox.size() and self.video_listbox.get(video_idx).startswith("[Processing]"):
                    self.video_listbox.delete(video_idx)
                    self.video_listbox.insert(video_idx, f"[{final_status}] {os.path.basename(video_file)}")
                
                self._update_queue_statistics()
                self.current_processing_video = None
                if video_idx < self.video_listbox.size():
                    self.video_listbox.selection_clear(0, tk.END)
                    self.video_listbox.selection_set(video_idx)
                    self.video_listbox.see(video_idx)
                self.on_video_select_in_queue()
                gc.collect()  # Clean up memory after each file
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

        # After the loop finishes (or breaks due to API key/target lang error)
        self.generate_button.config(text=original_button_text, state=tk.NORMAL)
        self.update_progress("Queue processing finished." if not self.current_processing_video else "Queue processing interrupted.", is_complete=not self.current_processing_video)
        self.log_status("--- Queue Processing Finished ---")
        self._update_queue_statistics()  # Final stat update
        self.current_processing_video = None

    def start_processing(self):
        """Starts the processing in a new thread to avoid freezing the GUI."""
        if not self.video_queue:
            messagebox.showinfo("Info", "Video queue is empty. Please add videos to process.")
            return
        processing_thread = threading.Thread(target=self.process_video_thread, daemon=True)
        processing_thread.start() 

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

    def _load_segments_to_editor(self, segments):
        """Formats and loads subtitle segments into the editor text widget."""
        editor = self.text_widgets['editor_text']
        editor.configure(state='normal')
        editor.delete(1.0, tk.END)

        if not segments:
            editor.insert(tk.END, "No subtitle segments to display or edit.")
            editor.configure(state='disabled')
            return

        for i, segment in enumerate(segments):
            start_time_val = segment.get('start')
            end_time_val = segment.get('end')
            start_time = self._format_timestamp(start_time_val)
            end_time = self._format_timestamp(end_time_val)
            text = segment.get('text', '').strip()
            
            editor.insert(tk.END, f"Segment: {i+1}\n")
            editor.insert(tk.END, f"Time: {start_time} --> {end_time}\n")
            editor.insert(tk.END, f"Text: {text}\n\n")
        
        # Editor is already set to normal if segments exist by on_video_select_in_queue
        # editor.configure(state='normal') 

    def _parse_edited_text_to_segments(self, edited_text_content):
        """Parses the content from the editor back into a list of segment dictionaries."""
        new_segments = []
        # Regex for one segment block: captures num, start_ts, end_ts, and multi-line text
        # Text capture is non-greedy and stops before the next "Segment:" or end of string
        segment_pattern = re.compile(r"Segment: (\d+)\s*Time: ([\d:,]+) --> ([\d:,]+)\s*Text: (.*?)(?=\nSegment: |\Z)", re.DOTALL | re.MULTILINE)
        
        time_regex = re.compile(r"(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2}),(\d{1,3})")

        def parse_time(ts_str):
            match = time_regex.fullmatch(ts_str.strip())
            if not match:
                self.log_status(f"Warning: Could not parse timestamp string: '{ts_str}'")
                return None
            
            groups = match.groups()
            hours = int(groups[0]) if groups[0] else 0
            minutes = int(groups[1])
            seconds = int(groups[2])
            ms = int(groups[3])
            return hours * 3600 + minutes * 60 + seconds + ms / 1000.0

        for match in segment_pattern.finditer(edited_text_content):
            try:
                num_str, start_str, end_str, text_content = match.groups()
                
                start_time = parse_time(start_str)
                end_time = parse_time(end_str)
                text = text_content.strip()
                
                if start_time is None or end_time is None:
                    self.log_status(f"Skipping segment {num_str} due to time parsing error.")
                    # Here, you might want to try and find the original segment by number
                    # and add it back if parsing its timestamps fails, to avoid data loss.
                    # For now, we just skip.
                    continue
                
                if start_time > end_time:
                    self.log_status(f"Warning: Segment {num_str} start time ({start_str}) is after end time ({end_str}). Adjusting end time.")
                    # Simple fix: make end time equal to start time + a small duration, or just use start time.
                    # This needs a more robust handling strategy or user feedback.
                    # For now, let's make end_time = start_time if this happens.
                    end_time = start_time 

                new_segments.append({'start': start_time, 'end': end_time, 'text': text})
            except Exception as e:
                self.log_status(f"Error parsing segment block (Num: {match.group(1) if match else 'N/A'}). Error: {e}")
                continue 
                
        return new_segments

    def apply_editor_changes(self):
        """Applies changes from the subtitle editor to the current video's data."""
        selected_indices = self.video_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "No video selected in the queue to apply changes to.")
            return

        current_video_path = self.video_queue[selected_indices[0]]
        if not current_video_path or current_video_path not in self.processed_file_data:
            messagebox.showerror("Error", "Selected video data not found.")
            return
        
        file_data = self.processed_file_data[current_video_path]
        # Ensure there are translated_segments to edit from, even if status is error post-translation
        if not file_data.get('translated_segments'): 
             messagebox.showinfo("Info", "No translation data exists for this video to edit.")
             return

        editor_content = self.text_widgets['editor_text'].get(1.0, tk.END)
        if not editor_content.strip():
            if messagebox.askyesno("Confirm Clear Subtitles", "Editor is empty. Do you want to remove all subtitles for this item?"):
                edited_segments = []
            else:
                return # User cancelled clearing
        else:
            try:
                edited_segments = self._parse_edited_text_to_segments(editor_content)
                if not edited_segments and editor_content.strip(): 
                    messagebox.showwarning("Parsing Error", "Could not parse any segments from the editor. Check format. Changes not applied.")
                    return
            except Exception as e_parse:
                self.log_status(f"Critical error parsing editor content: {e_parse}")
                messagebox.showerror("Parsing Error", f"Failed to parse editor content: {e_parse}. Changes not applied.")
                return
        
        # Update the stored segments
        file_data['translated_segments'] = edited_segments
        # self.translated_segments should be updated when on_video_select_in_queue is called OR if this is the selected item
        if self.video_listbox.get(selected_indices[0]).endswith(os.path.basename(current_video_path)):
             self.translated_segments = edited_segments

        # Regenerate the output format (e.g., SRT)
        output_format_val = self.output_format_var.get()
        new_output_content = format_output(edited_segments, output_format_val)
        file_data['output_content'] = new_output_content
        if self.video_listbox.get(selected_indices[0]).endswith(os.path.basename(current_video_path)):
            self.current_output = new_output_content

        # Refresh displays for the currently selected item
        self.display_output(new_output_content)
        self.update_comparison_view() 
        # self._load_segments_to_editor(edited_segments) # Re-load to show cleaned format (optional)
        
        self.log_status(f"Changes applied to subtitles for {os.path.basename(current_video_path)}. Save via 'Save As...'.")
        messagebox.showinfo("Changes Applied", f"Subtitle changes for {os.path.basename(current_video_path)} have been applied. You can now save the updated subtitle file using the 'Save As...' button in the 'Output' tab.")
        # Keep editor enabled
        self.text_widgets['editor_text'].configure(state='normal') 

    def _collect_project_data(self):
        """Collects all necessary data for saving a project."""
        project_data = {
            'video_queue': self.video_queue,
            'processed_file_data': self.processed_file_data,
            'settings': {
                'translation_provider': self.translation_provider_var.get(),
                'gemini_api_key': self.gemini_api_key_var.get(),
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
                'batch_size': self.batch_size_var.get(),
                'output_format': self.output_format_var.get(),
                'preview_setting': self.preview_var.get(),
                'auto_save_setting': self.auto_save_var.get(),
                'gemini_temperature': self.gemini_temperature_var.get(),
                'gemini_top_p': self.gemini_top_p_var.get(),
                'gemini_top_k': self.gemini_top_k_var.get(),
                'extensive_logging': self.extensive_logging_var.get()
            }
        }
        return project_data

    def save_project_logic(self, filepath):
        """Saves the current project data to the given filepath."""
        if not filepath:
            return False
        try:
            data_to_save = self._collect_project_data()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4)
            self.current_project_path = filepath
            self.log_status(f"Project saved successfully to: {filepath}")
            self.root.title(f"{APP_TITLE} - {os.path.basename(filepath)}")
            self._update_queue_statistics() # Update stats after saving
            return True
        except Exception as e:
            self.log_status(f"Error saving project: {e}")
            messagebox.showerror("Save Project Error", f"Failed to save project file: {e}")
            return False

    def save_project(self):
        """Saves the current project. If no path is set, calls save_project_as_dialog."""
        if self.current_project_path:
            self.save_project_logic(self.current_project_path)
        else:
            self.save_project_as_dialog()

    def save_project_as_dialog(self):
        """Prompts the user for a filepath and saves the project."""
        filepath = filedialog.asksaveasfilename(
            title="Save Project As",
            defaultextension=".ftgproj",
            filetypes=[("Film Translator Generator Project", "*.ftgproj"), ("All Files", "*.*")]
        )
        if filepath:
            self.save_project_logic(filepath)

    def _clear_current_project_state(self):
        """Clears the current project state before loading a new one."""
        self.video_queue.clear()
        self.processed_file_data.clear()
        self.video_listbox.delete(0, tk.END)
        
        self.transcribed_segments = None
        self.translated_segments = None
        self.current_output = None
        self.current_processing_video = None
        self.current_project_path = None # Clear current project path

        # Clear UI displays
        self.update_video_preview(None)
        self.display_output("")
        if 'original' in self.text_widgets: # Ensure widget exists
            self.text_widgets['original'].configure(state='normal'); self.text_widgets['original'].delete(1.0, tk.END); self.text_widgets['original'].configure(state='disabled')
        if 'translated' in self.text_widgets:
            self.text_widgets['translated'].configure(state='normal'); self.text_widgets['translated'].delete(1.0, tk.END); self.text_widgets['translated'].configure(state='disabled')
        if 'editor_text' in self.text_widgets:
            self.text_widgets['editor_text'].configure(state='disabled'); self.text_widgets['editor_text'].delete(1.0, tk.END)
        
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate', value=0)
        self.progress_status.config(text="Ready")
        self.root.title(APP_TITLE) # Reset window title
        self.log_status("Cleared current project state.")
        self._update_queue_statistics() # Ensure stats are updated after clearing

    def load_project_logic(self, filepath):
        """Loads project data from the given filepath and restores state."""
        if not filepath or not os.path.exists(filepath):
            messagebox.showerror("Load Project Error", "File not found or invalid path.")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
        except Exception as e:
            self.log_status(f"Error loading project file {filepath}: {e}")
            messagebox.showerror("Load Project Error", f"Failed to load or parse project file: {e}")
            return False

        self._clear_current_project_state() # Clear before loading

        try:
            self.video_queue = project_data.get('video_queue', [])
            self.processed_file_data = project_data.get('processed_file_data', {})
            
            # Repopulate listbox
            for video_path in self.video_queue:
                file_info = self.processed_file_data.get(video_path, {'status': 'Unknown'})
                status = file_info.get('status', 'Unknown')
                self.video_listbox.insert(tk.END, f"[{status}] {os.path.basename(video_path)}")

            # Restore settings
            settings = project_data.get('settings', {})
            defaults = get_default_config() # For fallback if a setting is missing

            self.translation_provider_var.set(settings.get('translation_provider', defaults['translation_provider']))
            self.gemini_api_key_var.set(settings.get('gemini_api_key', defaults['gemini_api_key']))
            self.openai_api_key_var.set(settings.get('openai_api_key', defaults['openai_api_key']))
            self.openai_model_var.set(settings.get('openai_model', defaults.get('openai_model', OPENAI_MODELS[0] if OPENAI_MODELS else '')))
            self.anthropic_api_key_var.set(settings.get('anthropic_api_key', defaults['anthropic_api_key']))
            self.anthropic_model_var.set(settings.get('anthropic_model', defaults['anthropic_model']))
            self.deepseek_api_key_var.set(settings.get('deepseek_api_key', defaults['deepseek_api_key']))
            
            self.target_language.set(settings.get('target_language', defaults['target_language']))
            self.whisper_model_name_var.set(settings.get('whisper_model', defaults['whisper_model']))
            self.device_var.set(settings.get('device', defaults['device']))
            self.compute_type_var.set(settings.get('compute_type', defaults['compute_type']))
            self.theme_var.set(settings.get('theme', defaults['theme']))
            self.accent_color_var.set(settings.get('accent_color', defaults['accent_color']))
            self.batch_size_var.set(str(settings.get('batch_size', defaults['batch_size'])))
            self.output_format_var.set(settings.get('output_format', defaults['output_format']))
            self.preview_var.set(settings.get('preview_setting', defaults['preview'])) 
            self.auto_save_var.set(settings.get('auto_save_setting', defaults['auto_save']))
            self.gemini_temperature_var.set(float(settings.get('gemini_temperature', defaults['gemini_temperature'])))
            self.gemini_top_p_var.set(float(settings.get('gemini_top_p', defaults['gemini_top_p'])))
            self.gemini_top_k_var.set(int(settings.get('gemini_top_k', defaults['gemini_top_k'])))
            self.extensive_logging_var.set(settings.get('extensive_logging', defaults['extensive_logging']))
            
            self._apply_theme() # Apply loaded theme
            self.update_compute_types() # Update compute types based on loaded device
            self._update_translation_settings_ui() # Update UI based on loaded provider
            
            self.current_project_path = filepath
            self.root.title(f"{APP_TITLE} - {os.path.basename(filepath)}")
            self.log_status(f"Project loaded successfully from: {filepath}")

            if self.video_listbox.size() > 0:
                self.video_listbox.selection_set(0)
                self.on_video_select_in_queue() # Update UI for the first item
            self._update_queue_statistics() # Update stats after loading
            return True

        except Exception as e:
            self.log_status(f"Error applying loaded project data: {e}")
            messagebox.showerror("Load Project Error", f"Error restoring project state: {e}")
            # Attempt to clear again to prevent inconsistent state
            self._clear_current_project_state()
            return False

    def load_project_dialog(self):
        """Prompts the user to select a project file and loads it."""
        # TODO: Add a check for unsaved changes in the current project
        # if self.current_project_path or self.video_queue: #簡易的な変更チェック
        #     if not messagebox.askyesno("Load Project", "You have an open project or items in the queue. Any unsaved changes will be lost. Continue?"):
        #         return

        filepath = filedialog.askopenfilename(
            title="Load Project",
            defaultextension=".ftgproj",
            filetypes=[("Film Translator Generator Project", "*.ftgproj"), ("All Files", "*.*")]
        )
        if filepath:
            self.load_project_logic(filepath) 

    def _update_queue_statistics(self):
        """Updates the queue statistics display based on current project data."""
        total = len(self.video_queue)
        processed = 0
        pending = 0
        failed = 0

        for video_path in self.video_queue:
            file_data = self.processed_file_data.get(video_path)
            if file_data:
                status = file_data.get('status')
                if status == 'Done':
                    processed += 1
                elif status == 'Pending':
                    pending += 1
                elif status and 'Error' in status:
                    failed += 1
                # 'Processing' and other intermediate states could also be counted if needed
                # For now, they are implicitly part of (total - processed - failed - pending)
            else: # Should not happen if processed_file_data is kept in sync with video_queue
                pending +=1 # Assume pending if no specific data (e.g. right after adding)

        self.stat_total_files.set(f"Total Files: {total}")
        self.stat_processed_files.set(f"Processed: {processed}")
        self.stat_pending_files.set(f"Pending: {pending}")
        self.stat_failed_files.set(f"Failed: {failed}")

    def _update_queue_statistics(self):
        """Updates the queue statistics display based on current project data."""
        total = len(self.video_queue)
        processed = 0
        pending = 0
        failed = 0

        for video_path in self.video_queue:
            file_data = self.processed_file_data.get(video_path)
            if file_data:
                status = file_data.get('status')
                if status == 'Done':
                    processed += 1
                elif status == 'Pending':
                    pending += 1
                elif status and 'Error' in status:
                    failed += 1
                # 'Processing' and other intermediate states could also be counted if needed
                # For now, they are implicitly part of (total - processed - failed - pending)
            else: 
                pending +=1 

        self.stat_total_files.set(f"Total Files: {total}")
        self.stat_processed_files.set(f"Processed: {processed}")
        self.stat_pending_files.set(f"Pending: {pending}")
        self.stat_failed_files.set(f"Failed: {failed}") 

    def _update_translation_settings_ui(self, event=None):
        """Dynamically update translation settings UI based on selected provider."""
        # Clear previous provider-specific widgets
        for widget in self.provider_details_frame.winfo_children():
            widget.destroy()

        provider = self.translation_provider_var.get()
        
        # Common width for API key entries and model comboboxes
        api_key_width = 30 
        model_combo_width = 28

        if provider == "Gemini":
            gemini_frame = ttk.Frame(self.provider_details_frame)
            gemini_frame.pack(fill=tk.X, pady=2)
            ttk.Label(gemini_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Entry(gemini_frame, textvariable=self.gemini_api_key_var, width=api_key_width, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True)
            # Gemini specific params (temperature, top_p, top_k) are in Advanced Settings dialog for now.

        elif provider == "OpenAI":
            openai_frame = ttk.Frame(self.provider_details_frame)
            openai_frame.pack(fill=tk.X, pady=2)
            
            key_frame = ttk.Frame(openai_frame)
            key_frame.pack(fill=tk.X, pady=(0,3))
            ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Entry(key_frame, textvariable=self.openai_api_key_var, width=api_key_width, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            model_frame = ttk.Frame(openai_frame)
            model_frame.pack(fill=tk.X)
            ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Combobox(
                model_frame, 
                textvariable=self.openai_model_var, 
                values=OPENAI_MODELS, 
                state="readonly", 
                width=model_combo_width
            ).pack(side=tk.LEFT)

        elif provider == "Anthropic":
            anthropic_frame = ttk.Frame(self.provider_details_frame)
            anthropic_frame.pack(fill=tk.X, pady=2)

            key_frame = ttk.Frame(anthropic_frame)
            key_frame.pack(fill=tk.X, pady=(0,3))
            ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Entry(key_frame, textvariable=self.anthropic_api_key_var, width=api_key_width, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True)

            model_frame = ttk.Frame(anthropic_frame)
            model_frame.pack(fill=tk.X)
            ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Combobox(
                model_frame, 
                textvariable=self.anthropic_model_var, 
                values=ANTHROPIC_MODELS, 
                state="readonly", 
                width=model_combo_width
            ).pack(side=tk.LEFT)
            
        elif provider == "DeepSeek":
            deepseek_frame = ttk.Frame(self.provider_details_frame)
            deepseek_frame.pack(fill=tk.X, pady=2)
            ttk.Label(deepseek_frame, text="API Key:").pack(side=tk.LEFT, padx=(0,5))
            ttk.Entry(deepseek_frame, textvariable=self.deepseek_api_key_var, width=api_key_width, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True)
            # DeepSeek model is fixed (DEEPSEEK_MODEL from config), so no model selection here.