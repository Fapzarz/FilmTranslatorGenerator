"""
UI components for Film Translator Generator.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import webbrowser

from config import APP_VERSION, GITHUB_URL, THEMES, ACCENT_COLORS, PREVIEW_OPTIONS, AUTO_SAVE_OPTIONS

def create_advanced_settings_dialog(parent, settings):
    """Create advanced settings dialog."""
    dialog = tk.Toplevel(parent)
    dialog.title("Advanced Settings")
    dialog.geometry("400x300")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # Settings frame
    settings_frame = ttk.Frame(dialog, padding="10")
    settings_frame.pack(fill=tk.BOTH, expand=True)
    
    # Batch size
    batch_frame = ttk.Frame(settings_frame)
    batch_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(batch_frame, text="Translation Batch Size:").pack(side=tk.LEFT, padx=5)
    ttk.Entry(batch_frame, textvariable=settings['batch_size_var'], width=10).pack(side=tk.LEFT, padx=5)
    
    # Auto-preview
    preview_frame = ttk.Frame(settings_frame)
    preview_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(preview_frame, text="Auto-Preview Video:").pack(side=tk.LEFT, padx=5)
    ttk.Combobox(preview_frame, textvariable=settings['preview_var'], 
               values=PREVIEW_OPTIONS, state="readonly", width=10).pack(side=tk.LEFT, padx=5)
    
    # Auto-save
    save_frame = ttk.Frame(settings_frame)
    save_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(save_frame, text="Auto-Save Output:").pack(side=tk.LEFT, padx=5)
    ttk.Combobox(save_frame, textvariable=settings['auto_save_var'], 
               values=AUTO_SAVE_OPTIONS, state="readonly", width=10).pack(side=tk.LEFT, padx=5)
    
    # Accent color
    accent_frame = ttk.Frame(settings_frame)
    accent_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(accent_frame, text="Accent Color:").pack(side=tk.LEFT, padx=5)
    ttk.Combobox(accent_frame, textvariable=settings['accent_color_var'], 
               values=ACCENT_COLORS, state="readonly", width=10).pack(side=tk.LEFT, padx=5)
    
    # Buttons
    button_frame = ttk.Frame(settings_frame)
    button_frame.pack(fill=tk.X, padx=5, pady=10)
    
    ttk.Button(button_frame, text="Save", 
             command=lambda: [settings['save_callback'](), dialog.destroy()]).pack(side=tk.RIGHT, padx=5)
    ttk.Button(button_frame, text="Cancel", 
             command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    return dialog

def create_about_dialog(parent):
    """Create about dialog."""
    dialog = tk.Toplevel(parent)
    dialog.title("About Film Translator Generator")
    dialog.geometry("400x300")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    
    # About content
    frame = ttk.Frame(dialog, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text=f"Film Translator Generator v{APP_VERSION}", 
            font=("", 14, "bold")).pack(pady=10)
    
    ttk.Label(frame, text="A desktop application for generating translated subtitles from videos",
            wraplength=350).pack(pady=5)
    
    ttk.Label(frame, text="Uses Faster-Whisper and Google Gemini API",
            wraplength=350).pack(pady=5)
    
    ttk.Button(frame, text="Visit GitHub", 
             command=lambda: webbrowser.open(GITHUB_URL)).pack(pady=10)
    
    ttk.Button(frame, text="Close", command=dialog.destroy).pack(pady=5)
    
    return dialog

def create_progress_frame(parent, on_generate_click):
    """Create progress bar frame with action button."""
    frame = ttk.Frame(parent)
    
    # Progress bar frame
    progress_frame = ttk.Frame(frame)
    progress_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
    
    progress_status = ttk.Label(progress_frame, text="Ready")
    progress_status.pack(fill=tk.X, pady=(0, 3), anchor="w")
    
    progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='indeterminate')
    progress_bar.pack(fill=tk.X)
    
    generate_button = ttk.Button(frame, text="Generate Subtitles", 
                               command=on_generate_click, style="Accent.TButton")
    generate_button.pack(side=tk.LEFT, padx=5)
    
    return frame, progress_bar, progress_status, generate_button

def create_notebook(parent):
    """Create notebook with tabs for log, output, and comparison."""
    notebook = ttk.Notebook(parent)
    
    # Status/Log tab
    log_frame = ttk.Frame(notebook)
    notebook.add(log_frame, text="Log")
    
    status_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10)
    status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    status_text.configure(state='disabled')
    
    # Output tab
    output_frame = ttk.Frame(notebook)
    notebook.add(output_frame, text="Output")
    
    output_actions = ttk.Frame(output_frame)
    output_actions.pack(fill=tk.X, padx=5, pady=5)
    
    # Create output actions
    copy_button = ttk.Button(output_actions, text="Copy to Clipboard")
    copy_button.pack(side=tk.LEFT, padx=5)
    
    save_button = ttk.Button(output_actions, text="Save As...")
    save_button.pack(side=tk.LEFT, padx=5)
    
    output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=10)
    output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    output_text.configure(state='disabled')
    
    # Comparison tab
    comparison_frame = ttk.Frame(notebook)
    notebook.add(comparison_frame, text="Original vs Translation")
    
    # Create a PanedWindow for side-by-side comparison
    paned = ttk.PanedWindow(comparison_frame, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Original text frame (left side)
    original_frame = ttk.LabelFrame(paned, text="Original Transcription")
    paned.add(original_frame, weight=1)
    
    original_text = scrolledtext.ScrolledText(original_frame, wrap=tk.WORD, height=10)
    original_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    original_text.configure(state='disabled')
    
    # Translated text frame (right side)
    translated_frame = ttk.LabelFrame(paned, text="Translated Text")
    paned.add(translated_frame, weight=1)
    
    translated_text = scrolledtext.ScrolledText(translated_frame, wrap=tk.WORD, height=10)
    translated_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    translated_text.configure(state='disabled')
    
    return notebook, {
        'log': status_text,
        'output': output_text,
        'original': original_text,
        'translated': translated_text,
        'copy_button': copy_button,
        'save_button': save_button
    } 