"""
Manages video processing functionality for the Film Translator Generator Qt Edition.
"""
import os
import threading
import gc
import torch
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QTimer, QObject, Signal, QCoreApplication, Qt

from config import get_default_config
from backend.transcribe import transcribe_video, load_whisper_model
from backend.translate import translate_text
from utils.format import format_output

# Helper class to safely update UI from a worker thread
class ProcessSignals(QObject):
    update_progress = Signal(str, int, bool, bool)
    update_ui = Signal(object)
    process_finished = Signal()

class VideoProcessor:
    def __init__(self, app_instance):
        """
        Initialize the VideoProcessor.
        
        Args:
            app_instance: The main QtAppGUI instance
        """
        self.app = app_instance
        self.processing_thread = None
        self.signals = ProcessSignals()
        
        # Connect signals
        self.signals.update_progress.connect(self._update_progress_ui)
        self.signals.update_ui.connect(self._update_ui)
        self.signals.process_finished.connect(self._process_finished)
    
    def _update_ui(self, callback):
        """Execute a UI update callback in the main thread."""
        callback()
    
    def load_whisper_model_sync(self):
        """
        Loads the faster-whisper model based on selected settings.
        This function is called by process_video_thread.
        Returns True if model loaded successfully, False otherwise.
        """
        model_name = self.app.whisper_model_name
        device = self.app.device
        compute_type = self.app.compute_type
        
        if hasattr(self.app, 'whisper_model') and self.app.whisper_model and \
           hasattr(self.app.whisper_model, 'model') and \
           self.app.whisper_model.model_size == model_name and \
           self.app.whisper_model.device == device and \
           self.app.whisper_model.compute_type == compute_type:
            self.app.log_status("Whisper model already loaded with correct settings.")
            return True
        
        if hasattr(self.app, 'whisper_model') and self.app.whisper_model:
            self.app.log_status("Releasing previous Whisper model due to setting change...")
            try:
                del self.app.whisper_model
                self.app.whisper_model = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()
                self.app.log_status("Previous model released.")
            except Exception as e:
                self.app.log_status(f"Warning: Error releasing previous model - {e}")
        
        try:
            self.app.whisper_model = load_whisper_model(model_name, device, compute_type, self.app.log_status)
            return True
        except Exception as e:
            self.app.log_status(f"Error loading Whisper model: {e}", "ERROR")
            # We can't directly show a message box from a worker thread
            # Use signals to show the message in the main thread
            self.signals.update_ui.emit(lambda: QMessageBox.critical(
                self.app, 
                "Faster-Whisper Error", 
                f"Failed to load model: {e}\nCheck CUDA/cuDNN setup and compute capability."
            ))
            self.app.whisper_model = None
            return False
    
    def process_video_thread(self):
        """Runs the transcription and translation in a separate thread for files in the queue."""
        # Store original button state to restore later
        original_button_text = self.app.process_button.text()
        
        # Update UI in the main thread
        self.signals.update_ui.emit(lambda: self._update_button_state("Processing...", False))
        
        for video_idx, video_file in enumerate(self.app.video_queue):
            if self.app.processed_file_data[video_file]['status'] == 'Done':
                self.app.log_status(f"Skipping {os.path.basename(video_file)}, already processed.")
                continue
            
            self.app.current_processing_video = video_file
            
            # Update UI in the main thread
            self.signals.update_ui.emit(lambda idx=video_idx, vf=video_file: self._update_queue_item(idx, vf))
            
            try:
                self.signals.update_progress.emit(
                    f"Starting ({video_idx+1}/{len(self.app.video_queue)}): {os.path.basename(video_file)}...", 
                    0, False, False
                )
                self.app.log_status(f"--- Starting Process for {os.path.basename(video_file)} ({video_idx+1}/{len(self.app.video_queue)}) ---")
                
                # Use signals to update UI elements in the main thread
                if video_idx == self.app.video_listbox.currentRow():
                    self.signals.update_ui.emit(lambda: self.app.output_text.clear())
                
                self.app.processed_file_data[video_file]['status'] = 'Processing_Whisper'
                
                # Config checks
                if not video_file or not os.path.exists(video_file):
                    self.app.log_status(f"Error: Video file not found: {video_file}", "ERROR")
                    self.signals.update_progress.emit(
                        f"Error: File not found {os.path.basename(video_file)}", 
                        0, True, False
                    )
                    self.app.processed_file_data[video_file]['status'] = 'Error_FileNotFound'
                    continue
                
                provider_name = self.app.translation_provider
                api_key_ok = False
                if provider_name == "Gemini":
                    api_key_ok = bool(self.app.gemini_api_key)
                elif provider_name == "OpenAI":
                    api_key_ok = bool(self.app.openai_api_key)
                elif provider_name == "Anthropic":
                    api_key_ok = bool(self.app.anthropic_api_key)
                elif provider_name == "DeepSeek":
                    api_key_ok = bool(self.app.deepseek_api_key)
                
                if not api_key_ok:
                    self.signals.update_ui.emit(lambda pn=provider_name: self._show_error_message(
                        "Error", f"API Key for {pn} is missing."
                    ))
                    self.app.log_status(f"Error: API Key for {provider_name} missing. Halting queue.", "ERROR")
                    self.signals.update_progress.emit(
                        f"Error: API Key for {provider_name} missing", 
                        0, True, False
                    )
                    self.app.processed_file_data[video_file]['status'] = 'Error_Config'  # Mark current file
                    break  # Halt queue
                
                if not self.app.target_language:
                    self.signals.update_ui.emit(lambda: self._show_error_message(
                        "Error", "Please select a target language."
                    ))
                    self.app.log_status("Error: Target language not selected. Halting queue.", "ERROR")
                    self.signals.update_progress.emit("Error: No target language", 0, True, False)
                    self.app.processed_file_data[video_file]['status'] = 'Error_Config'  # Mark current file
                    break  # Halt queue
                
                self.signals.update_ui.emit(lambda: self.app._save_config())  # Save settings in main thread
                
                try:  # Batch size conversion
                    batch_size = int(self.app.batch_size)
                    if batch_size <= 0:
                        batch_size = get_default_config()['batch_size']
                except (ValueError, TypeError):
                    batch_size = get_default_config()['batch_size']  # Fallback to default
                
                # Transcription
                self.signals.update_progress.emit(
                    f"Loading Whisper model for {os.path.basename(video_file)}...", 
                    20, False, False
                )
                if not self.load_whisper_model_sync():
                    self.app.log_status(f"--- Process Failed (Whisper Model Load) for {os.path.basename(video_file)} ---", "ERROR")
                    self.signals.update_progress.emit("Failed to load Whisper model", 0, True, False)
                    self.app.processed_file_data[video_file]['status'] = 'Error_WhisperModel'
                    continue
                
                self.signals.update_progress.emit(
                    f"Transcribing {os.path.basename(video_file)}...", 
                    30, False, False
                )
                self.app.log_status(f"Starting transcription for {os.path.basename(video_file)}...")
                self.app.processed_file_data[video_file]['status'] = 'Transcribing'
                
                transcribed_segments = transcribe_video(self.app.whisper_model, video_file, self.app.log_status)
                self.app.processed_file_data[video_file]['transcribed_segments'] = transcribed_segments
                
                if not transcribed_segments:
                    self.app.log_status(f"Transcription resulted in no segments for {os.path.basename(video_file)}.", "WARNING")
                    self.signals.update_progress.emit(
                        f"No segments from transcription: {os.path.basename(video_file)}", 
                        0, True, False
                    )
                    self.app.processed_file_data[video_file]['status'] = 'Error_TranscriptionEmpty'
                    if video_idx == self.app.video_listbox.currentRow():
                        error_msg = f"Transcription failed for {os.path.basename(video_file)}: No segments."
                        self.signals.update_ui.emit(lambda msg=error_msg: self._update_ui_after_error(msg))
                    continue
                
                self.app.log_status("Transcription complete.")
                # Update UI only if this is the selected video
                if video_idx == self.app.video_listbox.currentRow():
                    self.app.transcribed_segments = transcribed_segments  # Update AppGUI instance for current selection
                    self.signals.update_ui.emit(lambda: self._update_comparison_view())
                
                # Translation
                self.app.processed_file_data[video_file]['status'] = 'Translating'
                self.signals.update_progress.emit(
                    f"Translating {os.path.basename(video_file)}...", 
                    60, False, False
                )
                self.app.log_status(f"Starting translation for {os.path.basename(video_file)}...")
                
                provider_config_for_translation = {
                    'name': provider_name,
                    'gemini_api_key': self.app.gemini_api_key,
                    'gemini_temperature': self.app.gemini_temperature,
                    'gemini_top_p': self.app.gemini_top_p,
                    'gemini_top_k': self.app.gemini_top_k,
                    'gemini_model': self.app.gemini_model,
                    'openai_api_key': self.app.openai_api_key,
                    'openai_model': self.app.openai_model,
                    'anthropic_api_key': self.app.anthropic_api_key,
                    'anthropic_model': self.app.anthropic_model,
                    'deepseek_api_key': self.app.deepseek_api_key
                    # DeepSeek model is fixed, no var needed here for the call itself
                }
                
                translated_segments = translate_text(
                    provider_config_for_translation, transcribed_segments, self.app.target_language,
                    self.app.log_status, batch_size
                )
                
                if translated_segments is None:
                    self.app.log_status(f"Translation failed for {os.path.basename(video_file)} (provider: {provider_name}).", "ERROR")
                    self.signals.update_progress.emit(
                        f"Translation error: {os.path.basename(video_file)}", 
                        0, True, False
                    )
                    self.app.processed_file_data[video_file]['status'] = 'Error_TranslationAPI'
                    if video_idx == self.app.video_listbox.currentRow():
                        error_msg = f"Translation failed for {os.path.basename(video_file)}."
                        self.signals.update_ui.emit(lambda msg=error_msg: self._update_ui_after_error(msg))
                    continue
                
                self.app.processed_file_data[video_file]['translated_segments'] = translated_segments
                self.app.log_status("Translation complete.")
                
                # Formatting Output
                output_format_val = self.app.output_format
                self.app.processed_file_data[video_file]['status'] = 'FormattingOutput'
                self.signals.update_progress.emit(
                    f"Formatting output ({output_format_val}) for {os.path.basename(video_file)}...", 
                    80, False, False
                )
                self.app.log_status(f"Formatting output for {os.path.basename(video_file)} in {output_format_val}...")
                
                output_content = format_output(translated_segments, output_format_val)
                self.app.processed_file_data[video_file]['output_content'] = output_content
                
                # Update UI if this is the selected video
                if video_idx == self.app.video_listbox.currentRow():
                    self.signals.update_ui.emit(lambda ts=transcribed_segments, trs=translated_segments, oc=output_content: 
                                              self._update_ui_after_success(ts, trs, oc))
                
                # Auto Save
                if self.app.auto_save_enabled == "On" or self.app.auto_save_enabled is True:
                    base_name, _ = os.path.splitext(video_file)
                    auto_save_path = f"{base_name}.{output_format_val}"
                    try:
                        with open(auto_save_path, "w", encoding="utf-8") as f:
                            f.write(output_content)
                        self.app.log_status(f"Auto-saved subtitle to {auto_save_path}")
                    except Exception as e_save:
                        self.app.log_status(f"Error auto-saving {auto_save_path}: {e_save}", "WARNING")
                
                self.app.log_status(f"--- Process Finished Successfully for {os.path.basename(video_file)} ---")
                self.signals.update_progress.emit(
                    f"Completed: {os.path.basename(video_file)}", 
                    100, False, True
                )
                self.app.processed_file_data[video_file]['status'] = 'Done'
            
            except Exception as e:  # Catch-all for errors during a single file's processing
                error_msg = str(e)
                self.app.log_status(f"Unhandled error processing {os.path.basename(video_file)}: {error_msg}", "CRITICAL")
                self.signals.update_ui.emit(lambda vf=video_file, err=error_msg: self._show_error_message(
                    "Processing Error", 
                    f"An unexpected error occurred with {os.path.basename(vf)}: {err}"
                ))
                # Ensure 'status' exists before trying to check if it starts with 'Error_'
                self.app.processed_file_data.setdefault(video_file, {})
                if not self.app.processed_file_data[video_file].get('status', '').startswith('Error_'):
                    self.app.processed_file_data[video_file]['status'] = 'Error_Generic'
            
            finally:  # Per-file finally block
                final_status = self.app.processed_file_data.get(video_file, {}).get('status', 'Error_Unknown')
                # Update listbox item with final status for this file
                self.signals.update_ui.emit(lambda idx=video_idx, fs=final_status, vf=video_file: 
                                          self._update_listbox_final_status(idx, fs, vf))
        
        # Queue processing is finished
        self.signals.process_finished.emit()
    
    def _update_listbox_final_status(self, idx, status, video_file):
        """Updates the listbox item with the final status (called in main thread)."""
        if idx < self.app.video_listbox.count() and self.app.video_listbox.item(idx) and \
           self.app.video_listbox.item(idx).text().startswith("[Processing]"):
            self.app.video_listbox.item(idx).setText(f"[{status}] {os.path.basename(video_file)}")
    
    def _update_button_state(self, text, enabled):
        """Updates the button state (called in main thread)."""
        self.app.process_button.setText(text)
        self.app.process_button.setEnabled(enabled)
    
    def _update_queue_item(self, idx, video_file):
        """Updates a queue item (called in main thread)."""
        # Update listbox item
        item = self.app.video_listbox.item(idx)
        if item:
            item.setText(f"[Processing] {os.path.basename(video_file)}")
        
        self.app.video_listbox.setCurrentRow(idx)
        if hasattr(self.app, 'queue_manager'):
            self.app.queue_manager.update_queue_statistics()
    
    def _show_error_message(self, title, message):
        """Shows an error message (called in main thread)."""
        QMessageBox.critical(self.app, title, message)
    
    def _update_ui_after_error(self, error_msg):
        """Updates UI after an error (called in main thread)."""
        self.app.output_text.setText(error_msg)
        self.app.transcribed_segments = None  # Clear for UI
        self.app.translated_segments = None   # Clear for UI
        
        # Update comparison view
        if hasattr(self.app, 'queue_manager'):
            self.app.queue_manager._update_comparison_view()
        
        # Clear editor
        if hasattr(self.app, 'editor_manager'):
            self.app.editor_manager.load_segments_to_editor(None)
    
    def _update_ui_after_success(self, transcribed_segments, translated_segments, output_content):
        """Updates UI after successful processing (called in main thread)."""
        self.app.transcribed_segments = transcribed_segments
        self.app.translated_segments = translated_segments
        self.app.current_output = output_content
        self.app.output_text.setText(output_content)
        
        if hasattr(self.app, 'queue_manager'):
            self.app.queue_manager._update_comparison_view()
        
        if hasattr(self.app, 'editor_manager'):
            self.app.editor_manager.load_segments_to_editor(translated_segments)
    
    def _update_comparison_view(self):
        """Updates the comparison view (called in main thread)."""
        if hasattr(self.app, 'queue_manager'):
            self.app.queue_manager._update_comparison_view()
    
    def _process_finished(self):
        """Called when process is finished (called in main thread)."""
        self.app.process_button.setText("Process Selected Video")
        self.app.process_button.setEnabled(True)
        self.app.current_processing_video = None
        if hasattr(self.app, 'queue_manager'):
            self.app.queue_manager.update_queue_statistics()
        self.app.log_status("Processing queue completed.")
        self.processing_thread = None
    
    def start_processing(self):
        """Start the video processing operation in a new thread."""
        if self.processing_thread and self.processing_thread.is_alive():
            self.app.log_status("Process is already running!", "WARNING")
            return
        
        if not self.app.video_queue:
            QMessageBox.warning(self.app, "Warning", "Please add videos to the queue first.")
            return
        
        selected_idx = self.app.video_listbox.currentRow()
        if selected_idx == -1:
            QMessageBox.warning(self.app, "Warning", "Please select a video from the queue.")
            return
        
        # Check first for API key
        provider_name = self.app.translation_provider
        api_key_missing = False
        
        if provider_name == "Gemini":
            api_key_missing = not bool(self.app.gemini_api_key)
        elif provider_name == "OpenAI":
            api_key_missing = not bool(self.app.openai_api_key)
        elif provider_name == "Anthropic":
            api_key_missing = not bool(self.app.anthropic_api_key)
        elif provider_name == "DeepSeek":
            api_key_missing = not bool(self.app.deepseek_api_key)
        
        if api_key_missing:
            # Show a comprehensive dialog with instructions
            msg = QMessageBox(self.app)
            msg.setWindowTitle("API Key Required")
            msg.setIcon(QMessageBox.Warning)
            
            message = f"""
<h3>API Key Missing for {provider_name}</h3>
<p>You need to configure an API key for {provider_name} before processing videos.</p>

<p><b>How to get an API key:</b></p>
<ul>
"""
            
            if provider_name == "Gemini":
                message += """
    <li>Go to <a href='https://makersuite.google.com/app/apikey'>Google AI Studio</a></li>
    <li>Sign in with your Google account</li>
    <li>Get API key from the API Keys section</li>
"""
            elif provider_name == "OpenAI":
                message += """
    <li>Go to <a href='https://platform.openai.com/api-keys'>OpenAI Platform</a></li>
    <li>Sign in or create an account</li>
    <li>Create a new API key from your dashboard</li>
"""
            elif provider_name == "Anthropic":
                message += """
    <li>Go to <a href='https://console.anthropic.com/'>Anthropic Console</a></li>
    <li>Sign in or create an account</li>
    <li>Navigate to API Keys section and create a key</li>
"""
            elif provider_name == "DeepSeek":
                message += """
    <li>Go to <a href='https://platform.deepseek.com/api-keys'>DeepSeek Platform</a></li>
    <li>Sign in or create an account</li>
    <li>Create a new API key from your dashboard</li>
"""
            
            message += """
</ul>

<p><b>To configure your API key:</b></p>
<ol>
    <li>Click on "Settings" in the menu</li>
    <li>Select "Advanced Settings"</li>
    <li>Enter your API key in the appropriate field</li>
    <li>Click "Save" or "Apply"</li>
</ol>

<p>Would you like to open Advanced Settings now?</p>
"""
            
            msg.setText(message)
            msg.setTextFormat(Qt.RichText)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            
            result = msg.exec()
            if result == QMessageBox.Yes:
                # Open advanced settings dialog
                self.app.open_advanced_settings()
            return
        
        # Continue with video processing if API key is present
        self.processing_thread = threading.Thread(target=self.process_video_thread)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        # Update UI 
        self.app.process_button.setText("Processing...")
        self.app.process_button.setEnabled(False)
    
    def update_progress(self, message, percentage=0, is_error=False, is_complete=False):
        """Updates the progress bar and status message."""
        # Use signals to update UI from the worker thread
        self.signals.update_progress.emit(message, percentage, is_error, is_complete)
    
    def _update_progress_ui(self, message, percentage, is_error, is_complete):
        """Updates UI elements for progress directly from the main thread."""
        self.app.progress_status.setText(message)
        
        if is_error:
            self.app.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
            self.app.progress_bar.setValue(100)  # Show full but red for error
        elif is_complete:
            self.app.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
            self.app.progress_bar.setValue(100)  # Show full green for completion
        else:
            self.app.progress_bar.setStyleSheet("")  # Default style
            self.app.progress_bar.setValue(percentage)  # Set actual percentage 