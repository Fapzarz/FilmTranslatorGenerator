"""
Manages subtitle editing functionality for the Film Translator Generator Qt Edition.
"""
import os
from PySide6.QtWidgets import QMessageBox

from utils.format import format_output

class EditorManager:
    def __init__(self, app_instance):
        """
        Initialize the EditorManager.
        
        Args:
            app_instance: The main QtAppGUI instance
        """
        self.app = app_instance
    
    def load_segments_to_editor(self, segments):
        """Loads subtitle segments into the editor text widget."""
        if not segments:
            self.app.log_status("Editor: No segments to load into editor.", "VERBOSE")
            self.app.editor_text.clear()
            return
        
        editor_content = ""
        for i, segment in enumerate(segments):
            start_time = self._format_timestamp(segment['start'])
            end_time = self._format_timestamp(segment['end'])
            text = segment['text'].strip()
            editor_content += f"{i+1}\n{start_time} --> {end_time}\n{text}\n\n"
        
        self.app.editor_text.setText(editor_content)
        self.app.log_status("Segments loaded into editor.", "INFO")
    
    def save_editor_changes(self):
        """Saves the changes from the subtitle editor back to the app.translated_segments."""
        content = self.app.editor_text.toPlainText().strip()
        
        if not self.app.translated_segments:
            self.app.log_status("Editor: Original translated segments not found. Cannot map changes.", "ERROR")
            QMessageBox.critical(self.app, "Save Error", "Cannot save changes: original segment data is missing.")
            return
        
        new_segments = []
        lines = content.split('\n\n')  # Split by double newline
        
        original_segment_count = len(self.app.translated_segments)
        parsed_segment_count = 0
        
        for block in lines:
            if not block.strip():
                continue
            
            parts = block.strip().split('\n')
            if len(parts) < 3:
                self.app.log_status(f"Editor: Skipping malformed block: {parts}", "WARNING")
                continue
            
            try:
                # We rely on order rather than index from text
                time_parts = parts[1].split('-->')
                
                # Find corresponding original segment by order
                if parsed_segment_count < original_segment_count:
                    original_segment = self.app.translated_segments[parsed_segment_count]
                    new_text = '\n'.join(parts[2:]).strip()  # Join remaining lines as text
                    
                    new_segments.append({
                        'start': original_segment['start'],  # Keep original timing
                        'end': original_segment['end'],      # Keep original timing
                        'text': new_text
                    })
                    parsed_segment_count += 1
                else:
                    self.app.log_status(f"Editor: Extra segment data found in editor beyond original count: {' '.join(parts)}", "WARNING")
            
            except ValueError as e:
                self.app.log_status(f"Editor: Error parsing segment block: {parts}. Error: {e}", "ERROR")
                QMessageBox.critical(self.app, "Parse Error", f"Error parsing edited segment: {parts[0] if parts else 'Unknown'}. Please check format.")
                return  # Stop processing on error
        
        if parsed_segment_count == 0 and content:  # Content was there but nothing parsed
            QMessageBox.critical(self.app, "Save Error", "Could not parse any segments from the editor. Please check the format (ID\nTIMESTAMPS\nTEXT\n\n...).")
            return
        
        # Update app's translated_segments
        self.app.translated_segments = new_segments
        
        # Re-format the output for the main output tab
        output_format_to_use = self.app.output_format
        formatted_output = format_output(self.app.translated_segments, output_format_to_use, self._format_timestamp)
        
        # Update the processed_file_data for the currently selected video
        current_video_path = None
        current_row = self.app.video_listbox.currentRow()
        if current_row != -1 and current_row < len(self.app.video_queue):
            current_video_path = self.app.video_queue[current_row]
        
        # Update the main output tab and processed_file_data
        if current_video_path:
            file_data = self.app.processed_file_data.get(current_video_path)
            if file_data:
                file_data['translated_segments'] = self.app.translated_segments  # Update segments
                # Apply styling if SRT format and style exists
                if output_format_to_use == "srt" and file_data.get('subtitle_style') and hasattr(self.app, 'subtitle_styler'):
                    styled_output = self.app.subtitle_styler.format_srt_with_style(formatted_output, file_data['subtitle_style'])
                    self.app.output_text.setText(styled_output)
                    file_data['output_content'] = styled_output
                else:
                    self.app.output_text.setText(formatted_output)
                    file_data['output_content'] = formatted_output
            else:
                self.app.output_text.setText(formatted_output)
        else:
            # No video selected, just update the main output display
            self.app.output_text.setText(formatted_output)
        
        self.app.log_status("Subtitle changes applied from editor.", "INFO")
        if current_video_path:
            QMessageBox.information(
                self.app, 
                "Changes Applied", 
                f"Subtitle changes for {os.path.basename(current_video_path)} have been applied. "
                f"You can save the updated subtitle file or save the project."
            )
    
    def _format_timestamp(self, seconds):
        """Format a timestamp in seconds to SRT format (HH:MM:SS,mmm)."""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}" 