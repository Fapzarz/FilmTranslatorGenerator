"""
Manages the video queue functionality for the Film Translator Generator Qt Edition.
"""
import os
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import QUrl

from utils.validators import validate_video_file, validate_path_exists

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
                # Validate file is a valid video
                valid, error_message = validate_video_file(p)
                if valid:
                    filepaths_to_process.append(p)
                else:
                    self.app.log_status(f"Skipping invalid video file: {os.path.basename(p)} - {error_message}", "WARNING")
            
            if not filepaths_to_process:
                self.app.log_status("No valid video files found in the provided items.", "WARNING")
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
        skipped_count = 0
        invalid_count = 0
        
        for filepath in filepaths_to_process:
            # Normalize path for consistent storage and comparison
            normalized_filepath = os.path.normpath(filepath)
            
            # Perform extra validation on the filepath
            valid, error_message = validate_video_file(normalized_filepath)
            if not valid:
                self.app.log_status(f"Skipping invalid file: {os.path.basename(normalized_filepath)} - {error_message}", "WARNING")
                invalid_count += 1
                continue
                
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
                self.app.log_status(f"Added to queue: {os.path.basename(normalized_filepath)}")
                added_count += 1
            else:
                self.app.log_status(f"Already in queue: {os.path.basename(normalized_filepath)}")
                skipped_count += 1
        
        # Report results
        if added_count > 0:
            self.app.log_status(f"{added_count} video(s) added. Queue size: {len(self.app.video_queue)}")
            if invalid_count > 0:
                self.app.log_status(f"{invalid_count} invalid video(s) skipped.", "WARNING")
            if skipped_count > 0:
                self.app.log_status(f"{skipped_count} duplicate video(s) skipped.", "INFO")
                
            # Select first video if none selected
            if self.app.video_listbox.count() > 0 and self.app.video_listbox.currentRow() == -1:
                self.app.video_listbox.setCurrentRow(0)
                self.on_video_select_in_queue()  # Trigger preview update
        elif not file_paths_to_add:  # Only show if it was from dialog and nothing was added
            if invalid_count > 0:
                QMessageBox.warning(
                    self.app,
                    "Invalid Videos",
                    f"{invalid_count} video(s) could not be added due to invalid format or other issues."
                )
            else:
                self.app.log_status("No new videos selected or added.")
        
        self.update_queue_statistics()  # Update stats
    
    def on_video_select_in_queue(self):
        """Handles selection change in the video queue listbox."""
        current_row = self.app.video_listbox.currentRow()
        if current_row == -1 or current_row >= len(self.app.video_queue):
            # Clear all displays
            if hasattr(self.app, 'preview_manager'):
                self.app.preview_manager.update_video_preview_info(None)
            
            # Clear output display
            self.app.output_text.clear()
            self.app.original_text.clear()
            self.app.translated_text.clear()
            self.app.editor_text.clear()
            return
        
        # Get selected video path
        try:
            actual_filepath = self.app.video_queue[current_row]
        except IndexError:
            self.app.log_status("Error accessing video at selected index.", "ERROR")
            return
            
        # Validate the file still exists
        valid, error = validate_path_exists(actual_filepath)
        if not valid:
            self.app.log_status(f"Selected video not found: {error}", "WARNING")
            QMessageBox.warning(
                self.app,
                "Missing Video",
                f"The selected video file could not be found:\n{actual_filepath}\n\nIt may have been moved or deleted."
            )
        
        # Delay the update slightly to allow UI to respond
        self._handle_video_selection_update(actual_filepath)
    
    def _handle_video_selection_update(self, actual_filepath):
        """Handles the actual UI updates after a video selection."""
        # Verify file exists before proceeding
        valid, _ = validate_path_exists(actual_filepath)
        if valid:
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
        
        # Safety check to ensure we don't go out of bounds
        segment_count = min(len(self.app.transcribed_segments), len(self.app.translated_segments))
        
        for i in range(segment_count):
            orig = self.app.transcribed_segments[i]
            trans = self.app.translated_segments[i]
            
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
            try:
                seconds = float(seconds)
                minutes, seconds = divmod(int(seconds), 60)
                hours, minutes = divmod(minutes, 60)
                return f"{hours:02}:{minutes:02}:{seconds:02}"
            except (ValueError, TypeError):
                return "00:00:00"  # Default if time is invalid
        
        return f"[{format_time(start_time)} - {format_time(end_time)}]"
    
    def remove_selected_video_from_queue(self):
        """Removes the selected video from the queue."""
        current_row = self.app.video_listbox.currentRow()
        if current_row == -1:
            QMessageBox.information(self.app, "Remove Video", "Please select a video to remove.")
            return
        
        try:
            # Get the video filepath
            filepath = self.app.video_queue[current_row]
            
            # Remove from the queue and clear data
            del self.app.video_queue[current_row]
            if filepath in self.app.processed_file_data:
                del self.app.processed_file_data[filepath]
                
            # Remove from the listbox
            self.app.video_listbox.takeItem(current_row)
            
            # Update status
            self.app.log_status(f"Removed from queue: {os.path.basename(filepath)}")
            
            # Update statistics
            self.update_queue_statistics()
            
            # Select next item if available
            if self.app.video_listbox.count() > 0:
                next_row = min(current_row, self.app.video_listbox.count() - 1)
                self.app.video_listbox.setCurrentRow(next_row)
                self.on_video_select_in_queue()
            else:
                # If queue is empty, clear displays
                if hasattr(self.app, 'preview_manager'):
                    self.app.preview_manager.update_video_preview_info(None)
                
                self.app.output_text.clear()
                self.app.original_text.clear()
                self.app.translated_text.clear()
                self.app.editor_text.clear()
        except IndexError:
            self.app.log_status("Error removing video: Invalid index", "ERROR")
    
    def clear_video_queue(self):
        """Clears all videos from the queue."""
        if not self.app.video_queue:
            self.app.log_status("Queue is already empty.")
            return
            
        # Ask for confirmation
        response = QMessageBox.question(
            self.app,
            "Clear Queue",
            f"Are you sure you want to clear all {len(self.app.video_queue)} videos from the queue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if response != QMessageBox.Yes:
            return
        
        # Clear the queue
        self.app.video_queue.clear()
        self.app.processed_file_data.clear()
        self.app.video_listbox.clear()
        
        # Clear displays
        if hasattr(self.app, 'preview_manager'):
            self.app.preview_manager.update_video_preview_info(None)
        
        self.app.output_text.clear()
        self.app.original_text.clear()
        self.app.translated_text.clear()
        self.app.editor_text.clear()
        
        # Update status
        self.app.log_status("Video queue cleared.")
        
        # Update statistics
        self.update_queue_statistics()
    
    def update_queue_statistics(self):
        """Updates the statistics labels in the UI."""
        total_files = len(self.app.video_queue)
        
        # Count files by status
        processed_files = 0
        pending_files = 0
        failed_files = 0
        
        for filepath in self.app.video_queue:
            file_data = self.app.processed_file_data.get(filepath, {})
            status = file_data.get('status', 'Pending')
            
            if status == 'Done':
                processed_files += 1
            elif status in ['Error_Translation', 'Error_Transcription', 'Error_Generic']:
                failed_files += 1
            else:  # 'Pending', 'Processing', etc.
                pending_files += 1
        
        # Update the statistics labels
        if hasattr(self.app, 'stat_total_files'):
            self.app.stat_total_files.setText(f"Total Files: {total_files}")
        if hasattr(self.app, 'stat_processed_files'):
            self.app.stat_processed_files.setText(f"Processed: {processed_files}")
        if hasattr(self.app, 'stat_pending_files'):
            self.app.stat_pending_files.setText(f"Pending: {pending_files}")
        if hasattr(self.app, 'stat_failed_files'):
            self.app.stat_failed_files.setText(f"Failed: {failed_files}") 