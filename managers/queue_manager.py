"""
Manages the video queue functionality for the Film Translator Generator Qt Edition.
"""
import os
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import QUrl

class QueueManager:
    def __init__(self, app_instance):
        """
        Initialize the QueueManager.
        
        Args:
            app_instance: The main QtAppGUI instance
        """
        self.app = app_instance
    
    def load_queue_from_config(self):
        """Populates the video queue from loaded configuration data."""
        self.app.video_listbox.clear() # Clear existing items
        # Ensure video_queue is populated from processed_file_data keys in QtAppGUI._load_config
        # or decide on a single source of truth for the queue items on load.
        
        for filepath in self.app.video_queue: # Assumes app.video_queue is already correctly populated
            file_data = self.app.processed_file_data.get(filepath, {})
            status = file_data.get('status', 'Pending') # Default to Pending if not found
            self.app.video_listbox.addItem(f"[{status}] {os.path.basename(filepath)}")
        
        self.update_queue_statistics()
        if self.app.video_listbox.count() > 0:
            self.app.video_listbox.setCurrentRow(0)
            self.on_video_select_in_queue() # Trigger selection update for the first item

    def add_videos_to_queue(self, file_paths_to_add=None):
        """Adds one or more video files to the queue, either from a dialog or a provided list."""
        filepaths_to_process = []
        if file_paths_to_add:
            # Filter for valid files if provided directly (e.g., from drag-drop)
            for p in file_paths_to_add:
                if os.path.isfile(p):
                    filepaths_to_process.append(p)
                else:
                    self.app.log_status(f"Skipping non-file path from drop: {p}", "WARNING")
            if not filepaths_to_process:
                self.app.log_status("No valid files found in the dropped items.", "INFO")
                return  # No valid files to add from the provided list
        else:
            # Fallback to file dialog if no paths are provided directly
            filepaths_to_process, _ = QFileDialog.getOpenFileNames(
                self.app,
                "Select Video File(s)",
                "",
                "Video Files (*.mp4 *.avi *.mkv *.mov *.webm);;All Files (*)"
            )
        
        if not filepaths_to_process:  # If still no filepaths (dialog cancelled or list was empty/invalid)
            return
        
        added_count = 0
        for filepath in filepaths_to_process:
            # Normalize path for consistent storage and comparison
            normalized_filepath = os.path.normpath(filepath)
            if normalized_filepath not in self.app.video_queue:
                self.app.video_queue.append(normalized_filepath)
                self.app.processed_file_data[normalized_filepath] = {
                    'status': 'Pending',
                    'transcribed_segments': None,
                    'translated_segments': None,
                    'output_content': None,
                    'subtitle_style': None  # Initialize with no specific style
                }
                self.app.video_listbox.addItem(f"[Pending] {os.path.basename(normalized_filepath)}")
                self.app.log_status(f"Added to queue: {normalized_filepath}")
                added_count += 1
            else:
                self.app.log_status(f"Already in queue: {normalized_filepath}")
        
        if added_count > 0:
            self.app.log_status(f"{added_count} new video(s) added. Queue size: {len(self.app.video_queue)}")
            if self.app.video_listbox.count() > 0 and self.app.video_listbox.currentRow() == -1:
                self.app.video_listbox.setCurrentRow(0)
                self.on_video_select_in_queue()  # Trigger preview update
        elif not file_paths_to_add:  # Only show if it was from dialog and nothing was added
            self.app.log_status("No new videos selected or added.")
        
        self.update_queue_statistics()  # Update stats
    
    def on_video_select_in_queue(self):
        """Handles selection change in the video queue listbox."""
        current_row = self.app.video_listbox.currentRow()
        if current_row == -1:
            # Clear all displays
            if hasattr(self.app, 'preview_manager'):
                self.app.preview_manager.update_video_preview_info(None)
            
            # Clear output display
            self.app.output_text.clear()
            self.app.original_text.clear()
            self.app.translated_text.clear()
            self.app.editor_text.clear()
            return
        
        # Get selected video information
        selected_item = self.app.video_listbox.item(current_row).text()
        if "]" in selected_item:
            filepath_basename = selected_item.split("] ", 1)[1]
            actual_filepath = next((fp for fp in self.app.video_queue if os.path.basename(fp) == filepath_basename), None)
            if not actual_filepath:
                actual_filepath = self.app.video_queue[current_row]
        else:
            actual_filepath = selected_item
        
        # Delay the update slightly to allow UI to respond
        self._handle_video_selection_update(actual_filepath)
    
    def _handle_video_selection_update(self, actual_filepath):
        """Handles the actual UI updates after a video selection."""
        if actual_filepath and os.path.exists(actual_filepath):
            # Update preview (if a preview system is in place)
            if hasattr(self.app, 'preview_manager'):
                self.app.preview_manager.update_video_preview_info(actual_filepath)
            
            # Update output areas based on processed data
            file_data = self.app.processed_file_data.get(actual_filepath)
            if file_data and file_data['status'] in ['Done', 'Error_Translation', 'Error_Transcription', 'Error_Generic'] and file_data.get('translated_segments'):
                # Display output content
                self.app.output_text.setText(file_data.get('output_content', ""))
                
                # Update segments data for the main app if needed (e.g., for comparison tab)
                self.app.transcribed_segments = file_data.get('transcribed_segments')
                self.app.translated_segments = file_data.get('translated_segments')
                
                # Update comparison view
                self._update_comparison_view()
                
                # Load segments to the main UI's simple editor if it exists
                if hasattr(self.app, 'editor_manager'): # And if the editor is still part of the main UI
                    self.app.editor_manager.load_segments_to_editor(self.app.translated_segments)
            elif file_data:
                # Show basic info if not fully processed or no segments
                self.app.output_text.setText(f"Video selected: {os.path.basename(actual_filepath)}\nStatus: {file_data['status']}")
                
                # Clear comparison and editor areas
                self.app.original_text.clear()
                self.app.translated_text.clear()
                self.app.editor_text.clear()
            else:
                # No data found for this file
                self.app.output_text.setText(f"No data found for {os.path.basename(actual_filepath)}.")
                
                # Clear comparison and editor areas
                self.app.original_text.clear()
                self.app.translated_text.clear()
                self.app.editor_text.clear()
        else:
            # Invalid filepath, clear preview and text areas
            if hasattr(self.app, 'preview_manager'):
                self.app.preview_manager.update_video_preview_info(None)
            
            self.app.output_text.clear()
            self.app.original_text.clear()
            self.app.translated_text.clear()
            self.app.editor_text.clear()
    
    def _update_comparison_view(self):
        """Updates the comparison view with transcribed and translated segments."""
        if not self.app.transcribed_segments or not self.app.translated_segments:
            self.app.original_text.clear()
            self.app.translated_text.clear()
            return
        
        # Build comparison text
        original_text = ""
        translated_text = ""
        
        for i, (orig, trans) in enumerate(zip(self.app.transcribed_segments, self.app.translated_segments)):
            orig_text = orig['text'] if 'text' in orig else orig.get('content', '')
            trans_text = trans['text'] if 'text' in trans else trans.get('content', '')
            
            start_time = orig.get('start', 0)
            end_time = orig.get('end', 0)
            
            time_str = self._format_time_for_display(start_time, end_time)
            original_text += f"{time_str}: {orig_text}\n\n"
            translated_text += f"{time_str}: {trans_text}\n\n"
        
        # Update text widgets
        self.app.original_text.setText(original_text)
        self.app.translated_text.setText(translated_text)
    
    def _format_time_for_display(self, start_time, end_time):
        """Format time values for display in comparison view."""
        def format_time(seconds):
            minutes, seconds = divmod(int(seconds), 60)
            hours, minutes = divmod(minutes, 60)
            return f"{hours:02}:{minutes:02}:{seconds:02}"
        
        return f"[{format_time(start_time)} - {format_time(end_time)}]"
    
    def remove_selected_video_from_queue(self):
        """Removes the selected video from the queue."""
        current_row = self.app.video_listbox.currentRow()
        if current_row == -1:
            QMessageBox.information(self.app, "Info", "Please select a video from the queue to remove.")
            return
        
        filepath_to_remove = self.app.video_queue.pop(current_row)
        
        self.app.video_listbox.takeItem(current_row)
        if filepath_to_remove in self.app.processed_file_data:
            del self.app.processed_file_data[filepath_to_remove]
        self.app.log_status(f"Removed from queue: {filepath_to_remove}")
        
        # Select new item if available
        if self.app.video_listbox.count() > 0:
            if current_row < self.app.video_listbox.count():
                self.app.video_listbox.setCurrentRow(current_row)
            else:
                self.app.video_listbox.setCurrentRow(self.app.video_listbox.count() - 1)
            self.on_video_select_in_queue()
        else:
            # Clear all displays if queue is empty
            if hasattr(self.app, 'preview_manager'):
                self.app.preview_manager.update_video_preview_info(None)
            
            # Clear output display
            self.app.output_text.clear()
            self.app.original_text.clear()
            self.app.translated_text.clear()
            self.app.editor_text.clear()
        
        self.update_queue_statistics()
    
    def clear_video_queue(self):
        """Clears all videos from the queue."""
        if not self.app.video_queue:
            QMessageBox.information(self.app, "Info", "Queue is already empty.")
            return
        
        reply = QMessageBox.question(
            self.app, 
            "Confirm Clear",
            "Are you sure you want to clear the entire video queue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.app.video_queue.clear()
            self.app.processed_file_data.clear()
            self.app.video_listbox.clear()
            self.app.log_status("Video queue cleared.")
            
            # Clear all displays
            if hasattr(self.app, 'preview_manager'):
                self.app.preview_manager.update_video_preview_info(None)
            
            # Clear output display
            self.app.output_text.clear()
            self.app.original_text.clear()
            self.app.translated_text.clear()
            self.app.editor_text.clear()
            
            self.update_queue_statistics()
    
    def update_queue_statistics(self):
        """Updates the queue statistics display based on current project data."""
        total = len(self.app.video_queue)
        processed = 0
        pending = 0
        failed = 0
        
        for video_path in self.app.video_queue:
            file_data = self.app.processed_file_data.get(video_path)
            if file_data:
                status = file_data.get('status')
                if status == 'Done':
                    processed += 1
                elif status == 'Pending':
                    pending += 1
                elif status and 'Error' in status:
                    failed += 1
            else:
                pending += 1
        
        # Update statistics labels
        self.app.stat_total_files.setText(f"Total Files: {total}")
        self.app.stat_processed_files.setText(f"Processed: {processed}")
        self.app.stat_pending_files.setText(f"Pending: {pending}")
        self.app.stat_failed_files.setText(f"Failed: {failed}") 