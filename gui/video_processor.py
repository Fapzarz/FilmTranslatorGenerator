import os
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import gc
import torch

from config import get_default_config
from backend.transcribe import transcribe_video, load_whisper_model
from backend.translate import translate_text
from utils.format import format_output
from gui import queue_manager # For queue_manager.update_queue_statistics and on_video_select_in_queue
from gui import editor_manager # Import editor_manager

# Note: 'app' in these functions refers to the instance of AppGUI

def load_whisper_model_sync(app):
    """Loads the faster-whisper model based on selected settings.
    This function is called by process_video_thread.
    Returns True if model loaded successfully, False otherwise.
    """
    model_name = app.whisper_model_name_var.get()
    device = app.device_var.get()
    compute_type = app.compute_type_var.get()

    if app.whisper_model and hasattr(app.whisper_model, 'model') and \
       app.whisper_model.model_size == model_name and \
       app.whisper_model.device == device and \
       app.whisper_model.compute_type == compute_type:
        app.log_status("Whisper model already loaded with correct settings.")
        return True

    if app.whisper_model:
        app.log_status("Releasing previous Whisper model due to setting change...")
        try:
            del app.whisper_model
            app.whisper_model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            app.log_status("Previous model released.")
        except Exception as e:
            app.log_status(f"Warning: Error releasing previous model - {e}")

    try:
        app.whisper_model = load_whisper_model(model_name, device, compute_type, app.log_status)
        return True
    except Exception as e:
        app.log_status(f"Error loading Whisper model: {e}", level="ERROR")
        messagebox.showerror("Faster-Whisper Error", f"Failed to load model: {e}\nCheck CUDA/cuDNN setup and compute capability.")
        app.whisper_model = None
        return False

def process_video_thread(app):
    """Runs the transcription and translation in a separate thread for files in the queue."""
    original_button_text = app.generate_button.cget("text")
    app.generate_button.config(text="Processing...", state=tk.DISABLED)

    for video_idx, video_file in enumerate(app.video_queue):
        if app.processed_file_data[video_file]['status'] == 'Done':
            app.log_status(f"Skipping {os.path.basename(video_file)}, already processed.")
            continue

        app.current_processing_video = video_file
        app.video_listbox.delete(video_idx)
        app.video_listbox.insert(video_idx, f"[Processing] {os.path.basename(video_file)}")
        app.video_listbox.selection_clear(0, tk.END)
        app.video_listbox.selection_set(video_idx)
        app.video_listbox.see(video_idx)
        app.root.update_idletasks()
        queue_manager.update_queue_statistics(app)

        # Reset per-file results in AppGUI instance if they are for the currently selected item
        # This is to ensure UI consistency if a file is reprocessed.
        # The main data is in app.processed_file_data
        # if app.video_queue[app.video_listbox.curselection()[0] if app.video_listbox.curselection() else -1] == video_file:
        # No, this is not needed here as these are set based on successful processing below.

        try:
            app.update_progress(f"Starting ({video_idx+1}/{len(app.video_queue)}): {os.path.basename(video_file)}...")
            app.log_status(f"--- Starting Process for {os.path.basename(video_file)} ({video_idx+1}/{len(app.video_queue)}) ---")
            
            # Clear output only if the currently processed video is the one selected in the UI
            if video_idx == (app.video_listbox.curselection()[0] if app.video_listbox.curselection() else -1):
                app.display_output("") # Clear output tabs for the currently processing selected video

            app.processed_file_data[video_file]['status'] = 'Processing_Whisper'
            
            # Config checks
            api_key_val = app.gemini_api_key_var.get() # Example for Gemini, similar for others
            target_lang_val = app.target_language.get()

            if not video_file or not os.path.exists(video_file):
                app.log_status(f"Error: Video file not found: {video_file}", level="ERROR")
                app.update_progress(f"Error: File not found {os.path.basename(video_file)}", is_error=True)
                app.processed_file_data[video_file]['status'] = 'Error_FileNotFound'
                continue
            
            provider_name = app.translation_provider_var.get()
            api_key_ok = False
            if provider_name == "Gemini":
                api_key_ok = bool(app.gemini_api_key_var.get())
            elif provider_name == "OpenAI":
                api_key_ok = bool(app.openai_api_key_var.get())
            elif provider_name == "Anthropic":
                api_key_ok = bool(app.anthropic_api_key_var.get())
            elif provider_name == "DeepSeek":
                api_key_ok = bool(app.deepseek_api_key_var.get())

            if not api_key_ok:
                messagebox.showerror("Error", f"API Key for {provider_name} is missing.")
                app.log_status(f"Error: API Key for {provider_name} missing. Halting queue.", level="ERROR")
                app.update_progress(f"Error: API Key for {provider_name} missing", is_error=True)
                app.processed_file_data[video_file]['status'] = 'Error_Config' # Mark current file
                break # Halt queue

            if not target_lang_val:
                messagebox.showerror("Error", "Please select a target language.")
                app.log_status("Error: Target language not selected. Halting queue.", level="ERROR")
                app.update_progress("Error: No target language", is_error=True)
                app.processed_file_data[video_file]['status'] = 'Error_Config' # Mark current file
                break # Halt queue

            app._save_config() # Save current settings before processing

            try: # Batch size conversion
                batch_size = int(app.batch_size_var.get())
                if batch_size <= 0:
                    batch_size = get_default_config()['batch_size']
            except (ValueError, TypeError):
                batch_size = get_default_config()['batch_size'] # Fallback to default

            # Transcription
            app.update_progress(f"Loading Whisper model for {os.path.basename(video_file)}...")
            if not load_whisper_model_sync(app): # Call the local version
                app.log_status(f"--- Process Failed (Whisper Model Load) for {os.path.basename(video_file)} ---", level="ERROR")
                app.update_progress("Failed to load Whisper model", is_error=True)
                app.processed_file_data[video_file]['status'] = 'Error_WhisperModel'
                continue
            
            app.update_progress(f"Transcribing {os.path.basename(video_file)}...")
            app.log_status(f"Starting transcription for {os.path.basename(video_file)}...")
            app.processed_file_data[video_file]['status'] = 'Transcribing'
            
            transcribed_segments = transcribe_video(app.whisper_model, video_file, app.log_status)
            app.processed_file_data[video_file]['transcribed_segments'] = transcribed_segments

            if not transcribed_segments:
                app.log_status(f"Transcription resulted in no segments for {os.path.basename(video_file)}.", level="WARNING")
                app.update_progress(f"No segments from transcription: {os.path.basename(video_file)}", is_error=True) # Consider this an error for flow
                app.processed_file_data[video_file]['status'] = 'Error_TranscriptionEmpty'
                if video_idx == (app.video_listbox.curselection()[0] if app.video_listbox.curselection() else -1):
                    app.display_output(f"Transcription failed for {os.path.basename(video_file)}: No segments.")
                    app.transcribed_segments = None # Clear for UI
                    app.translated_segments = None  # Clear for UI
                    app.update_comparison_view() 
                    editor_manager.load_segments_to_editor(app, None) 
                continue

            app.log_status("Transcription complete.")
            # Update UI only if this is the selected video
            if video_idx == (app.video_listbox.curselection()[0] if app.video_listbox.curselection() else -1):
                app.transcribed_segments = transcribed_segments # Update AppGUI instance for current selection
                app.update_comparison_view()

            # Translation
            app.processed_file_data[video_file]['status'] = 'Translating'
            app.update_progress(f"Translating {os.path.basename(video_file)}...")
            app.log_status(f"Starting translation for {os.path.basename(video_file)}...")
            
            provider_config_for_translation = {
                'name': provider_name,
                'gemini_api_key': app.gemini_api_key_var.get(),
                'gemini_temperature': app.gemini_temperature_var.get(),
                'gemini_top_p': app.gemini_top_p_var.get(),
                'gemini_top_k': app.gemini_top_k_var.get(),
                'gemini_model': app.gemini_model_var.get(), 
                'openai_api_key': app.openai_api_key_var.get(),
                'openai_model': app.openai_model_var.get(),
                'anthropic_api_key': app.anthropic_api_key_var.get(),
                'anthropic_model': app.anthropic_model_var.get(),
                'deepseek_api_key': app.deepseek_api_key_var.get()
                # DeepSeek model is fixed, no var needed here for the call itself
            }

            translated_segments = translate_text(
                provider_config_for_translation, transcribed_segments, target_lang_val,
                app.log_status, batch_size
            )

            if translated_segments is None: 
                app.log_status(f"Translation failed for {os.path.basename(video_file)} (provider: {provider_name}).", level="ERROR")
                app.update_progress(f"Translation error: {os.path.basename(video_file)}", is_error=True)
                app.processed_file_data[video_file]['status'] = 'Error_TranslationAPI' 
                if video_idx == (app.video_listbox.curselection()[0] if app.video_listbox.curselection() else -1):
                    app.display_output(f"Translation failed for {os.path.basename(video_file)}.") 
                    app.translated_segments = None # Clear for UI
                    app.update_comparison_view() 
                    editor_manager.load_segments_to_editor(app, None)
                continue

            app.processed_file_data[video_file]['translated_segments'] = translated_segments
            app.log_status("Translation complete.")

            # Formatting Output
            output_format_val = app.output_format_var.get()
            app.processed_file_data[video_file]['status'] = 'FormattingOutput'
            app.update_progress(f"Formatting output ({output_format_val}) for {os.path.basename(video_file)}...")
            app.log_status(f"Formatting output for {os.path.basename(video_file)} in {output_format_val}...")

            output_content = format_output(translated_segments, output_format_val)
            app.processed_file_data[video_file]['output_content'] = output_content

            # Update UI if this is the selected video
            if video_idx == (app.video_listbox.curselection()[0] if app.video_listbox.curselection() else -1):
                app.transcribed_segments = transcribed_segments # Ensure it's set from this processing pass
                app.translated_segments = translated_segments   
                app.current_output = output_content             
                app.display_output(app.current_output)
                app.update_comparison_view()
                editor_manager.load_segments_to_editor(app, app.translated_segments)
            
            # Auto Save
            if app.auto_save_var.get() == "On":
                base_name, _ = os.path.splitext(video_file)
                auto_save_path = f"{base_name}.{output_format_val}" 
                try:
                    with open(auto_save_path, "w", encoding="utf-8") as f:
                        f.write(output_content)
                    app.log_status(f"Auto-saved subtitle to {auto_save_path}")
                except Exception as e_save:
                    app.log_status(f"Error auto-saving {auto_save_path}: {e_save}", level="WARNING")
            
            app.log_status(f"--- Process Finished Successfully for {os.path.basename(video_file)} ---")
            app.update_progress(f"Completed: {os.path.basename(video_file)}", is_complete=True)
            app.processed_file_data[video_file]['status'] = 'Done'
        
        except Exception as e: # Catch-all for errors during a single file's processing
            error_msg = str(e)
            app.log_status(f"Unhandled error processing {os.path.basename(video_file)}: {error_msg}", level="CRITICAL")
            messagebox.showerror("Processing Error", f"An unexpected error occurred with {os.path.basename(video_file)}: {error_msg}")
            # Ensure 'status' exists before trying to check if it starts with 'Error_'
            app.processed_file_data.setdefault(video_file, {}) 
            if not app.processed_file_data[video_file].get('status', '').startswith('Error_'):
                app.processed_file_data[video_file]['status'] = 'Error_Generic'
        
        finally: # Per-file finally block
            final_status = app.processed_file_data.get(video_file, {}).get('status', 'Error_Unknown')
            # Update listbox item with final status for this file
            if video_idx < app.video_listbox.size() and app.video_listbox.get(video_idx).startswith("[Processing]"):
                app.video_listbox.delete(video_idx)
                app.video_listbox.insert(video_idx, f"[{final_status}] {os.path.basename(video_file)}")
            
            queue_manager.update_queue_statistics(app)
            app.current_processing_video = None # Clear after this file is done or failed

            # If the processed file is the one currently selected, refresh its UI display
            if video_idx == (app.video_listbox.curselection()[0] if app.video_listbox.curselection() else -1):
                queue_manager.on_video_select_in_queue(app) # Refresh UI for the selected (and just processed) item
            
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    # After the loop finishes (or breaks due to global config error)
    app.generate_button.config(text=original_button_text, state=tk.NORMAL)
    # Check if any file was being processed when loop ended (current_processing_video might be set if 'break' was hit)
    processing_interrupted = any(
        data.get('status', '').startswith('Processing') or data.get('status') == 'Error_Config' 
        for data in app.processed_file_data.values()
    ) or app.current_processing_video # If break happens current_processing_video will be set

    if processing_interrupted:
        app.update_progress("Queue processing interrupted.", is_complete=False, is_error=True) # Indicate error if interrupted
        app.log_status("--- Queue Processing Interrupted ---", level="WARNING")
    else:
        app.update_progress("Queue processing finished.", is_complete=True)
        app.log_status("--- Queue Processing Finished ---")
    
    queue_manager.update_queue_statistics(app) # Final stat update
    app.current_processing_video = None # Ensure it's cleared

def start_processing(app):
    """Starts the processing in a new thread to avoid freezing the GUI."""
    if not app.video_queue:
        messagebox.showinfo("Info", "Video queue is empty. Please add videos to process.")
        return
    
    # Simple check: ensure at least one file is not 'Done'
    pending_files = [f for f in app.video_queue if app.processed_file_data.get(f, {}).get('status') != 'Done']
    if not pending_files:
        messagebox.showinfo("Info", "All files in the queue are already processed.")
        return

    processing_thread = threading.Thread(target=lambda: process_video_thread(app), daemon=True)
    processing_thread.start() 