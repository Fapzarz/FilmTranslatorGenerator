import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox

# Assuming APP_TITLE and get_default_config might be needed from config.py
# If other constants are needed, they should be imported here or passed as arguments.
from config import APP_TITLE, get_default_config, GEMINI_MODELS, OPENAI_MODELS # Added necessary imports

def collect_project_data(app):
    """Collects all necessary data for saving a project."""
    project_data = {
        'video_queue': app.video_queue,
        'processed_file_data': app.processed_file_data,
        'settings': {
            'translation_provider': app.translation_provider_var.get(),
            'gemini_api_key': app.gemini_api_key_var.get(),
            'gemini_model': app.gemini_model_var.get(),
            'openai_api_key': app.openai_api_key_var.get(),
            'openai_model': app.openai_model_var.get(),
            'anthropic_api_key': app.anthropic_api_key_var.get(),
            'anthropic_model': app.anthropic_model_var.get(),
            'deepseek_api_key': app.deepseek_api_key_var.get(),
            'target_language': app.target_language.get(),
            'whisper_model': app.whisper_model_name_var.get(),
            'device': app.device_var.get(),
            'compute_type': app.compute_type_var.get(),
            'theme': app.theme_var.get(),
            'accent_color': app.accent_color_var.get(),
            'batch_size': app.batch_size_var.get(),
            'output_format': app.output_format_var.get(),
            'preview_setting': app.preview_var.get(),
            'auto_save_setting': app.auto_save_var.get(),
            'gemini_temperature': app.gemini_temperature_var.get(),
            'gemini_top_p': app.gemini_top_p_var.get(),
            'gemini_top_k': app.gemini_top_k_var.get(),
            'extensive_logging': app.extensive_logging_var.get(),
            'subtitle_font': app.subtitle_font_var.get(),
            'subtitle_color': app.subtitle_color_var.get(),
            'subtitle_size': app.subtitle_size_var.get(),
            'subtitle_position': app.subtitle_position_var.get(),
            'subtitle_outline_color': app.subtitle_outline_color_var.get(),
            'subtitle_outline_width': app.subtitle_outline_width_var.get(),
            'subtitle_bg_color': app.subtitle_bg_color_var.get(),
            'subtitle_bg_opacity': app.subtitle_bg_opacity_var.get()
        }
    }
    return project_data

def save_project_logic(app, filepath):
    """Saves the current project data to the given filepath."""
    if not filepath:
        return False
    try:
        data_to_save = collect_project_data(app)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4)
        app.current_project_path = filepath
        app.log_status(f"Project saved successfully to: {filepath}")
        app.root.title(f"{APP_TITLE} - {os.path.basename(filepath)}")
        app._update_queue_statistics() # Update stats after saving
        return True
    except Exception as e:
        app.log_status(f"Error saving project: {e}")
        messagebox.showerror("Save Project Error", f"Failed to save project file: {e}")
        return False

def save_project(app):
    """Saves the current project. If no path is set, calls save_project_as_dialog."""
    if app.current_project_path:
        save_project_logic(app, app.current_project_path)
    else:
        save_project_as_dialog(app)

def save_project_as_dialog(app):
    """Prompts the user for a filepath and saves the project."""
    filepath = filedialog.asksaveasfilename(
        title="Save Project As",
        defaultextension=".ftgproj",
        filetypes=[("Film Translator Generator Project", "*.ftgproj"), ("All Files", "*.*")]
    )
    if filepath:
        save_project_logic(app, filepath)

def clear_current_project_state(app):
    """Clears the current project state before loading a new one."""
    app.video_queue.clear()
    app.processed_file_data.clear()
    app.video_listbox.delete(0, tk.END)
    
    app.transcribed_segments = None
    app.translated_segments = None
    app.current_output = None
    app.current_processing_video = None
    app.current_project_path = None

    app.update_video_preview(None)
    app.display_output("")
    if 'original' in app.text_widgets:
        app.text_widgets['original'].configure(state='normal'); app.text_widgets['original'].delete(1.0, tk.END); app.text_widgets['original'].configure(state='disabled')
    if 'translated' in app.text_widgets:
        app.text_widgets['translated'].configure(state='normal'); app.text_widgets['translated'].delete(1.0, tk.END); app.text_widgets['translated'].configure(state='disabled')
    if 'editor_text' in app.text_widgets:
        app.text_widgets['editor_text'].configure(state='disabled'); app.text_widgets['editor_text'].delete(1.0, tk.END)
    
    app.progress_bar.stop()
    app.progress_bar.config(mode='determinate', value=0)
    app.progress_status.config(text="Ready")
    app.root.title(APP_TITLE)
    app.log_status("Cleared current project state.")
    app._update_queue_statistics()

def load_project_logic(app, filepath):
    """Loads project data from the given filepath and restores state."""
    if not filepath or not os.path.exists(filepath):
        messagebox.showerror("Load Project Error", "File not found or invalid path.")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
    except Exception as e:
        app.log_status(f"Error loading project file {filepath}: {e}")
        messagebox.showerror("Load Project Error", f"Failed to load or parse project file: {e}")
        return False

    clear_current_project_state(app)

    try:
        app.video_queue = project_data.get('video_queue', [])
        app.processed_file_data = project_data.get('processed_file_data', {})
        
        for video_path in app.video_queue:
            file_info = app.processed_file_data.get(video_path, {'status': 'Unknown'})
            status = file_info.get('status', 'Unknown')
            app.video_listbox.insert(tk.END, f"[{status}] {os.path.basename(video_path)}")

        settings = project_data.get('settings', {})
        defaults = get_default_config()

        app.translation_provider_var.set(settings.get('translation_provider', defaults['translation_provider']))
        app.gemini_api_key_var.set(settings.get('gemini_api_key', defaults['gemini_api_key']))
        app.openai_api_key_var.set(settings.get('openai_api_key', defaults['openai_api_key']))
        app.openai_model_var.set(settings.get('openai_model', defaults.get('openai_model', OPENAI_MODELS[0] if OPENAI_MODELS else '')))
        app.anthropic_api_key_var.set(settings.get('anthropic_api_key', defaults['anthropic_api_key']))
        app.anthropic_model_var.set(settings.get('anthropic_model', defaults['anthropic_model']))
        app.gemini_model_var.set(settings.get('gemini_model', defaults.get('gemini_model', GEMINI_MODELS[0] if GEMINI_MODELS else '')))
        app.deepseek_api_key_var.set(settings.get('deepseek_api_key', defaults['deepseek_api_key']))
        
        app.target_language.set(settings.get('target_language', defaults['target_language']))
        app.whisper_model_name_var.set(settings.get('whisper_model', defaults['whisper_model']))
        app.device_var.set(settings.get('device', defaults['device']))
        app.compute_type_var.set(settings.get('compute_type', defaults['compute_type']))
        app.theme_var.set(settings.get('theme', defaults['theme']))
        app.accent_color_var.set(settings.get('accent_color', defaults['accent_color']))
        app.batch_size_var.set(str(settings.get('batch_size', defaults['batch_size'])))
        app.output_format_var.set(settings.get('output_format', defaults['output_format']))
        app.preview_var.set(settings.get('preview_setting', defaults['preview'])) 
        app.auto_save_var.set(settings.get('auto_save_setting', defaults['auto_save']))
        app.gemini_temperature_var.set(float(settings.get('gemini_temperature', defaults['gemini_temperature'])))
        app.gemini_top_p_var.set(float(settings.get('gemini_top_p', defaults['gemini_top_p'])))
        app.gemini_top_k_var.set(int(settings.get('gemini_top_k', defaults['gemini_top_k'])))
        app.extensive_logging_var.set(settings.get('extensive_logging', defaults['extensive_logging']))
        
        # Subtitle style settings from project
        app.subtitle_font_var.set(settings.get('subtitle_font', defaults['subtitle_font']))
        app.subtitle_color_var.set(settings.get('subtitle_color', defaults['subtitle_color']))
        app.subtitle_size_var.set(settings.get('subtitle_size', defaults['subtitle_size']))
        app.subtitle_position_var.set(settings.get('subtitle_position', defaults['subtitle_position']))
        app.subtitle_outline_color_var.set(settings.get('subtitle_outline_color', defaults['subtitle_outline_color']))
        app.subtitle_outline_width_var.set(settings.get('subtitle_outline_width', defaults['subtitle_outline_width']))
        app.subtitle_bg_color_var.set(settings.get('subtitle_bg_color', defaults['subtitle_bg_color']))
        app.subtitle_bg_opacity_var.set(settings.get('subtitle_bg_opacity', defaults['subtitle_bg_opacity']))

        app._apply_theme()
        app.update_compute_types()
        app._update_translation_settings_ui()
        app.update_subtitle_preview() # Update subtitle preview after loading style settings
            
        app.current_project_path = filepath
        app.root.title(f"{APP_TITLE} - {os.path.basename(filepath)}")
        app.log_status(f"Project loaded successfully from: {filepath}")

        if app.video_listbox.size() > 0:
            app.video_listbox.selection_set(0)
            app.on_video_select_in_queue()
        app._update_queue_statistics()
        return True

    except Exception as e:
        app.log_status(f"Error applying loaded project data: {e}")
        messagebox.showerror("Load Project Error", f"Error restoring project state: {e}")
        clear_current_project_state(app) # Attempt to clear again
        return False

def load_project_dialog(app):
    """Prompts the user to select a project file and loads it."""
    filepath = filedialog.askopenfilename(
        title="Load Project",
        defaultextension=".ftgproj",
        filetypes=[("Film Translator Generator Project", "*.ftgproj"), ("All Files", "*.*")]
    )
    if filepath:
        load_project_logic(app, filepath) 