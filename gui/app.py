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

from config import APP_TITLE, CONFIG_FILE, get_default_config, LANGUAGES, WHISPER_MODELS, DEVICES, COMPUTE_TYPES, OUTPUT_FORMATS, GITHUB_URL
from backend.transcribe import transcribe_video, load_whisper_model
from backend.translate import translate_text_gemini
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
        self.video_path = tk.StringVar()
        self.api_key = tk.StringVar()
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
    
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Video", command=self.browse_file)
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
        """Create the main application frame and widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for input controls
        input_frame = ttk.LabelFrame(main_frame, text="Input Settings", padding="10")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # File selection with preview button
        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(file_frame, text="Video File:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(file_frame, textvariable=self.video_path, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Preview", command=self.preview_video).pack(side=tk.LEFT, padx=5)
        
        # Thumbnail display area
        self.thumbnail_frame = ttk.LabelFrame(input_frame, text="Video Preview", padding="5")
        self.thumbnail_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.thumbnail_label = ttk.Label(self.thumbnail_frame)
        self.thumbnail_label.pack(pady=5, padx=5)
        self.thumbnail_placeholder = ttk.Label(self.thumbnail_frame, text="No video selected")
        self.thumbnail_placeholder.pack(pady=5, padx=5)
        
        # Video info labels
        self.video_info_frame = ttk.Frame(self.thumbnail_frame)
        self.video_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.video_duration_label = ttk.Label(self.video_info_frame, text="Duration: N/A")
        self.video_duration_label.pack(side=tk.LEFT, padx=5)
        
        self.video_size_label = ttk.Label(self.video_info_frame, text="Size: N/A")
        self.video_size_label.pack(side=tk.LEFT, padx=20)
        
        # API Key
        api_frame = ttk.Frame(input_frame)
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(api_frame, text="Gemini API Key:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(api_frame, textvariable=self.api_key, width=50, show="*").pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Language selection
        lang_frame = ttk.Frame(input_frame)
        lang_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(lang_frame, text="Target Language:").pack(side=tk.LEFT, padx=5)
        self.language_combobox = ttk.Combobox(lang_frame, textvariable=self.target_language, 
                                             values=LANGUAGES, state="readonly", width=20)
        self.language_combobox.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(lang_frame, text="Output Format:").pack(side=tk.LEFT, padx=5)
        self.format_combobox = ttk.Combobox(lang_frame, textvariable=self.output_format_var,
                                          values=OUTPUT_FORMATS, state="readonly", width=10)
        self.format_combobox.pack(side=tk.LEFT, padx=5)
        
        # Whisper settings frame
        whisper_frame = ttk.LabelFrame(main_frame, text="Whisper Settings", padding="10")
        whisper_frame.pack(fill=tk.X, padx=5, pady=5)
        
        settings_frame = ttk.Frame(whisper_frame)
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Model selection
        ttk.Label(settings_frame, text="Model:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.model_combobox = ttk.Combobox(settings_frame, textvariable=self.whisper_model_name_var, 
                                         values=WHISPER_MODELS, state="readonly", width=12)
        self.model_combobox.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # Device selection
        ttk.Label(settings_frame, text="Device:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.device_combobox = ttk.Combobox(settings_frame, textvariable=self.device_var, 
                                          values=DEVICES, state="readonly", width=8)
        self.device_combobox.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        self.device_combobox.bind("<<ComboboxSelected>>", self.update_compute_types)
        
        # Compute type
        ttk.Label(settings_frame, text="Compute Type:").grid(row=0, column=4, padx=5, pady=2, sticky="w")
        self.compute_type_combobox = ttk.Combobox(settings_frame, textvariable=self.compute_type_var, 
                                                state="readonly", width=10)
        self.compute_type_combobox.grid(row=0, column=5, padx=5, pady=2, sticky="w")
        
        # Progress and action frame
        progress_action_frame, self.progress_bar, self.progress_status, self.generate_button = create_progress_frame(
            main_frame, self.start_processing
        )
        progress_action_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Notebook with tabs
        self.notebook, self.text_widgets = create_notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Connect the handlers
        self.text_widgets['copy_button'].config(command=self.copy_to_clipboard)
        self.text_widgets['save_button'].config(command=self.save_output_file)
        
        # Status bar
        status_bar = ttk.Frame(self.root)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(status_bar, text="Ready", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Add a version label at the right of the status bar
        version_label = ttk.Label(status_bar, text="v2.0", anchor=tk.E)
        version_label.pack(side=tk.RIGHT, padx=5)
    
    def open_advanced_settings(self):
        """Open advanced settings dialog"""
        settings = {
            'batch_size_var': self.batch_size_var,
            'preview_var': self.preview_var,
            'auto_save_var': self.auto_save_var,
            'accent_color_var': self.accent_color_var,
            'save_callback': self._save_config
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
        """Preview the selected video file"""
        video_path = self.video_path.get()
        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("Error", "Please select a valid video file first.")
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
        """Loads configuration from config.json."""
        defaults = get_default_config()
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                # Use loaded value or default if key is missing
                self.api_key.set(config_data.get('gemini_api_key', defaults['gemini_api_key']))
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
                self.log_status("Loaded settings from config.")
            else:
                # Set defaults if config file doesn't exist
                self.api_key.set(defaults['gemini_api_key'])
                self.target_language.set(defaults['target_language'])
                self.whisper_model_name_var.set(defaults['whisper_model'])
                self.device_var.set(defaults['device'])
                self.compute_type_var.set(defaults['compute_type'])
                self.theme_var.set(defaults['theme'])
                self.accent_color_var.set(defaults['accent_color'])
                self.batch_size_var.set(str(defaults['batch_size']))
                self.output_format_var.set(defaults['output_format'])
                self.preview_var.set(defaults['preview'])
                self.auto_save_var.set(defaults['auto_save'])
                self.log_status("Config file not found, using defaults.")

        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            self.log_status(f"Warning: Could not load config file: {e}. Using defaults.")
            # Ensure defaults are set even on error
            self.api_key.set(defaults['gemini_api_key'])
            self.target_language.set(defaults['target_language'])
            self.whisper_model_name_var.set(defaults['whisper_model'])
            self.device_var.set(defaults['device'])
            self.compute_type_var.set(defaults['compute_type'])
            self.theme_var.set(defaults['theme'])
            self.accent_color_var.set(defaults['accent_color'])
            self.batch_size_var.set(str(defaults['batch_size']))
            self.output_format_var.set(defaults['output_format'])
            self.preview_var.set(defaults['preview'])
            self.auto_save_var.set(defaults['auto_save'])

    def _save_config(self):
        """Saves current configuration to config.json."""
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
                'gemini_api_key': self.api_key.get(),
                'target_language': self.target_language.get(),
                'whisper_model': self.whisper_model_name_var.get(),
                'device': self.device_var.get(),
                'compute_type': self.compute_type_var.get(),
                'theme': self.theme_var.get(),
                'accent_color': self.accent_color_var.get(),
                'batch_size': batch_size,
                'output_format': self.output_format_var.get(),
                'preview': self.preview_var.get(),
                'auto_save': self.auto_save_var.get()
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            self.log_status("Saved settings to config.")
        except Exception as e:
            self.log_status(f"Warning: Could not save config file: {e}")

    def browse_file(self):
        """Prompts the user to select a video file and updates the display."""
        filepath = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=(("Video Files", "*.mp4 *.avi *.mkv *.mov"), ("All Files", "*.*"))
        )
        if filepath:
            self.video_path.set(filepath)
            self.log_status(f"Selected file: {filepath}")
            
            # Update video thumbnail and info
            self.update_video_preview(filepath)
            
            # Auto-preview if enabled
            if self.preview_var.get() == "On":
                self.preview_video()
    
    def update_video_preview(self, video_path):
        """Update video thumbnail and information."""
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

    def log_status(self, message):
        """Appends a message to the status text area with timestamp."""
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
            start_time = f"{int(segment['start'] // 60):02}:{int(segment['end'] // 60):02}"
            end_time = f"{int(segment['start'] % 60):02}:{int(segment['end'] % 60):02}"
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
        """Asks user where to save the output file based on selected format."""
        if not self.current_output:
            messagebox.showinfo("Info", "No output to save.")
            return

        output_format = self.output_format_var.get()
        original_video_path = self.video_path.get()
        
        if original_video_path:
            base, _ = os.path.splitext(original_video_path)
            default_filename = f"{base}.{output_format}"
        else:
            default_filename = f"subtitles.{output_format}"

        filepath = filedialog.asksaveasfilename(
            title=f"Save {output_format.upper()} File",
            defaultextension=f".{output_format}",
            initialfile=default_filename,
            filetypes=[(f"{output_format.upper()} File", f"*.{output_format}"), ("All Files", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.current_output)
                self.log_status(f"File saved to: {filepath}")
            except Exception as e:
                self.log_status(f"Error saving file: {e}")
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
        """Runs the transcription and translation in a separate thread."""
        try:
            # Disable button and start progress animation
            self.generate_button.config(state=tk.DISABLED)
            self.update_progress("Starting process...")
            
            self.log_status("--- Starting Process ---")
            self.display_output("")  # Clear previous output

            video_file = self.video_path.get()
            api_key_val = self.api_key.get()
            target_lang_val = self.target_language.get()

            # Input validation
            if not video_file or not os.path.exists(video_file):
                messagebox.showerror("Error", "Please select a valid video file.")
                self.log_status("Error: Invalid video file selected.")
                self.update_progress("Error: Invalid video file", is_error=True)
                return

            if not api_key_val:
                messagebox.showerror("Error", "Please enter your Gemini API Key.")
                self.log_status("Error: Gemini API Key missing.")
                self.update_progress("Error: API Key missing", is_error=True)
                return

            if not target_lang_val:
                messagebox.showerror("Error", "Please select a target language.")
                self.log_status("Error: Target language not selected.")
                self.update_progress("Error: No target language", is_error=True)
                return

            # Save current settings
            self._save_config()

            # Get batch size from settings
            try:
                batch_size = int(self.batch_size_var.get())
                if batch_size <= 0:
                    batch_size = get_default_config()['batch_size']
                    self.log_status(f"Warning: Invalid batch size. Using default: {batch_size}")
            except (ValueError, TypeError):
                batch_size = get_default_config()['batch_size']
                self.log_status(f"Warning: Invalid batch size. Using default: {batch_size}")

            # Load Whisper Model
            self.update_progress("Loading Whisper model...")
            if not self._load_whisper_model_sync():
                self.log_status("--- Process Failed (Whisper Model Load) ---")
                self.update_progress("Failed to load Whisper model", is_error=True)
                return

            # 1. Transcribe
            self.update_progress("Transcribing audio...")
            self.log_status("Starting transcription...")
            self.transcribed_segments = transcribe_video(self.whisper_model, video_file, self.log_status)

            if not self.transcribed_segments:
                self.log_status("--- Process Failed (Transcription) ---")
                self.update_progress("Transcription failed", is_error=True)
                return
                
            # Update progress
            segments_count = len(self.transcribed_segments)
            self.update_progress(f"Transcribed {segments_count} segments")
            self.log_status(f"Transcription completed with {segments_count} segments")

            # 2. Translate
            self.update_progress(f"Translating to {target_lang_val}...")
            self.log_status(f"Starting translation to {target_lang_val}...")
            self.translated_segments = translate_text_gemini(
                api_key_val, 
                self.transcribed_segments, 
                target_lang_val, 
                self.log_status,
                batch_size
            )
            
            if not self.translated_segments:
                self.log_status("--- Process Failed (Translation) ---")
                self.update_progress("Translation failed", is_error=True)
                return

            # 3. Format output
            output_format = self.output_format_var.get()
            self.update_progress(f"Formatting output in {output_format} format...")
            self.log_status(f"Creating output in {output_format} format...")
            self.current_output = format_output(self.translated_segments, output_format)
            self.display_output(self.current_output)
            
            # Update comparison view
            self.update_comparison_view()
            
            # Auto-save if enabled
            if self.auto_save_var.get() == "On":
                self.update_progress("Saving output...")
                self.save_output_file()
            
            self.log_status("--- Process Finished Successfully ---")
            self.update_progress("Process completed successfully", is_complete=True)
            
        except Exception as e:
            self.log_status(f"Error during processing: {e}")
            messagebox.showerror("Processing Error", f"An error occurred: {e}")
            self.update_progress(f"Error: {str(e)[:50]}...", is_error=True)
        finally:
            self.generate_button.config(state=tk.NORMAL)

    def start_processing(self):
        """Starts the processing in a new thread to avoid freezing the GUI."""
        processing_thread = threading.Thread(target=self.process_video_thread, daemon=True)
        processing_thread.start() 