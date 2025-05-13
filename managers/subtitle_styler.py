"""
Manages subtitle styling functionality for the Film Translator Generator Qt Edition.
"""
import os
import re
from PySide6.QtWidgets import QMessageBox

class SubtitleStyler:
    def __init__(self, app_instance):
        """
        Initialize the SubtitleStyler.
        
        Args:
            app_instance: The main QtAppGUI instance
        """
        self.app = app_instance
        
        # Connect UI signals for subtitle styling elements
        if hasattr(self.app, 'subtitle_font_combo'):
            self.app.subtitle_font_combo.currentTextChanged.connect(self.update_subtitle_font)
        
        if hasattr(self.app, 'subtitle_color_combo'):
            self.app.subtitle_color_combo.currentTextChanged.connect(self.update_subtitle_color)
        
        if hasattr(self.app, 'subtitle_size_combo'):
            self.app.subtitle_size_combo.currentTextChanged.connect(self.update_subtitle_size)
        
        if hasattr(self.app, 'subtitle_position_combo'):
            self.app.subtitle_position_combo.currentTextChanged.connect(self.update_subtitle_position)
    
    def update_subtitle_font(self, font):
        """Update the subtitle font setting."""
        self.app.subtitle_font = font
        self.app.log_status(f"Subtitle font updated to: {font}")
    
    def update_subtitle_color(self, color):
        """Update the subtitle color setting."""
        self.app.subtitle_color = color
        self.app.log_status(f"Subtitle color updated to: {color}")
    
    def update_subtitle_size(self, size):
        """Update the subtitle size setting."""
        self.app.subtitle_size = size
        self.app.log_status(f"Subtitle size updated to: {size}")
    
    def update_subtitle_position(self, position):
        """Update the subtitle position setting."""
        self.app.subtitle_position = position
        self.app.log_status(f"Subtitle position updated to: {position}")
    
    def format_srt_with_style(self, srt_content, style_dict):
        """
        Apply styling to SRT content.
        
        Args:
            srt_content: The SRT content to style
            style_dict: A dictionary containing style parameters
            
        Returns:
            The styled SRT content
        """
        try:
            font = style_dict.get('font', 'Arial')
            color = style_dict.get('color', 'white')
            size = style_dict.get('size', '16')
            
            styled_lines = []
            
            # Regular expression to match SRT entries (number, timestamps, text)
            # Handles potential \r\n or \n line endings
            srt_pattern = re.compile(r'(\d+)\r?\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\r?\n((?:.+\r?\n?)+)')
            
            position_in_text = 0
            for match in srt_pattern.finditer(srt_content):
                num, start, end, text = match.groups()
                
                # Preserve original line breaks in the text
                text_lines = text.strip().splitlines()
                styled_text_lines = []
                for line in text_lines:
                    # Apply font tag to each line of text within a segment
                    styled_text_lines.append(f'<font face="{font}" color="{color}" size="{size}">{line.strip()}</font>')
                
                styled_text_segment = "\n".join(styled_text_lines)
                
                styled_entry = f"{num}\n{start} --> {end}\n{styled_text_segment}\n"
                styled_lines.append(styled_entry)
                
                position_in_text = match.end()
            
            # Append any remaining text after the last match (e.g., metadata, comments if any)
            if position_in_text < len(srt_content):
                styled_lines.append(srt_content[position_in_text:])
            
            return "\n".join(styled_lines)
        
        except Exception as e:
            self.app.log_status(f"Error applying style to SRT: {e}", "ERROR")
            return srt_content  # Return original content on error
    
    def apply_subtitle_style(self):
        """
        Apply the current subtitle style settings to the selected video's data.
        """
        try:
            current_row = self.app.video_listbox.currentRow()
            if current_row == -1:
                QMessageBox.information(self.app, "Info", "Please select a video from the queue.")
                return
            
            # Get the selected video from the queue
            if current_row >= len(self.app.video_queue):
                QMessageBox.critical(self.app, "Error", "Invalid selection in queue.")
                return
            
            actual_filepath = self.app.video_queue[current_row]
            
            if not actual_filepath or not os.path.exists(actual_filepath):
                QMessageBox.critical(self.app, "Error", "Cannot find the selected video file.")
                return
            
            file_data = self.app.processed_file_data.get(actual_filepath)
            if not file_data or not file_data.get('output_content'):
                QMessageBox.information(self.app, "Info", "Please process the video first to generate subtitles.")
                return
            
            # Update subtitle style settings from the UI
            self.app.subtitle_font = self.app.subtitle_font_combo.currentText()
            self.app.subtitle_color = self.app.subtitle_color_combo.currentText()
            self.app.subtitle_size = self.app.subtitle_size_combo.currentText()
            self.app.subtitle_position = self.app.subtitle_position_combo.currentText()
            
            current_style = {
                'font': self.app.subtitle_font,
                'color': self.app.subtitle_color,
                'size': self.app.subtitle_size,
                'position': self.app.subtitle_position,
                'outline_color': self.app.subtitle_outline_color,
                'outline_width': self.app.subtitle_outline_width,
                'bg_color': self.app.subtitle_bg_color,
                'bg_opacity': self.app.subtitle_bg_opacity
            }
            file_data['subtitle_style'] = current_style
            self.app.processed_file_data[actual_filepath] = file_data
            
            # If output is displayed, refresh it with the new styling
            if file_data.get('output_content') and hasattr(self.app, 'output_text'):
                styled_output = self.format_srt_with_style(file_data['output_content'], current_style)
                self.app.output_text.setPlainText(styled_output)
            
            QMessageBox.information(
                self.app, 
                "Success", 
                "Subtitle styling has been applied to the selected video."
            )
            self.app.log_status(f"Subtitle style updated for {os.path.basename(actual_filepath)}.")
            
        except Exception as e:
            QMessageBox.critical(self.app, "Error", f"Failed to apply subtitle style: {e}")
            self.app.log_status(f"Error applying subtitle style: {e}", "ERROR")
    
    def update_subtitle_style_preview(self):
        """
        Update subtitle preview based on current style settings.
        """
        try:
            # Get a sample subtitle text to preview
            sample_text = "This is a subtitle preview text."
            
            # Create a styled sample
            style = {
                'font': self.app.subtitle_font,
                'color': self.app.subtitle_color,
                'size': self.app.subtitle_size,
                'position': self.app.subtitle_position
            }
            
            # In a real implementation, this would update a preview widget
            # For now we just log the change
            self.app.log_status(f"Subtitle style preview updated: {style}")
        except Exception as e:
            self.app.log_status(f"Error updating subtitle preview: {e}", "ERROR") 