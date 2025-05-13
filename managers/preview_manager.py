"""
Manages video and subtitle preview functionalities for the Film Translator Generator Qt Edition.
"""
import os
import tempfile
import subprocess
import sys
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QUrl
from PySide6.QtGui import QPixmap

from utils.media import extract_video_thumbnail, get_video_info

class PreviewManager:
    def __init__(self, app_instance):
        """
        Initializes the PreviewManager.
        
        Args:
            app_instance: The main QtAppGUI instance.
        """
        self.app = app_instance
    
    def update_video_preview_info(self, video_path):
        """Update video information and load it into the media player."""
        if not video_path:
            # Clear media player
            self.app.media_player.stop()
            self.app.media_player.setSource(QUrl())
            
            # Clear video info
            self.app.video_duration_label.setText("Duration: N/A")
            self.app.video_size_label.setText("Size: N/A")
            return
        
        try:
            # Get video info
            video_info = get_video_info(video_path)
            
            # Update video info display
            self.app.video_duration_label.setText(f"Duration: {video_info['duration']}")
            self.app.video_size_label.setText(f"Size: {video_info['size']}")
            
            # Set the video source for the media player
            self.app.media_player.setSource(QUrl.fromLocalFile(video_path))
            
        except Exception as e:
            self.app.log_status(f"PreviewManager: Error updating video preview info: {e}", "ERROR")
            self.app.video_duration_label.setText("Duration: N/A")
            self.app.video_size_label.setText("Size: N/A")
    
    def preview_selected_video(self):
        """Preview the selected video file in the integrated player."""
        current_row = self.app.video_listbox.currentRow()
        if current_row == -1:
            QMessageBox.warning(self.app, "Error", "Please select a video from the queue to preview.")
            return
        
        if current_row >= len(self.app.video_queue):
            QMessageBox.warning(self.app, "Error", "Selected video not found in internal queue. Please check selection.")
            return
        
        actual_video_path = self.app.video_queue[current_row]
        
        if not actual_video_path or not os.path.exists(actual_video_path):
            QMessageBox.warning(self.app, "Error", f"The selected video path is invalid or file does not exist: {actual_video_path}")
            return
        
        # Make sure the video widget is set as the output for the media player
        self.app.media_player.setVideoOutput(self.app.video_widget)
        
        # Set the video source and play
        self.app.media_player.setSource(QUrl.fromLocalFile(actual_video_path))
        self.app.media_player.play()
    
    def preview_video_with_subtitles(self):
        """Saves the current output as a temporary subtitle file and attempts to open the video with it."""
        current_row = self.app.video_listbox.currentRow()
        if current_row == -1:
            QMessageBox.warning(self.app, "Error", "Please select a video from the queue to preview.")
            return
        
        if current_row >= len(self.app.video_queue):
            QMessageBox.warning(self.app, "Error", "Selected video not found in internal queue. Please re-add.")
            return
        
        video_path = self.app.video_queue[current_row]
        file_data = self.app.processed_file_data.get(video_path)
        
        if not file_data or not file_data.get('output_content'):
            QMessageBox.information(self.app, "Info", f"No subtitles generated for {os.path.basename(video_path)} to preview.")
            return
        
        current_output_for_preview = file_data['output_content']
        output_format = self.app.output_format
        temp_subtitle_path = ""
        
        try:
            if output_format == "srt" and file_data.get('subtitle_style') and hasattr(self.app, 'subtitle_styler'):
                self.app.log_status(f"PreviewManager: Applying subtitle styling for preview")
                style = file_data['subtitle_style']
                styled_output = self.app.subtitle_styler.format_srt_with_style(current_output_for_preview, style)
                current_output_for_preview = styled_output
            
            with tempfile.NamedTemporaryFile(mode="w", suffix=f".{output_format}", delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(current_output_for_preview)
                temp_subtitle_path = tmp_file.name
            
            self.app.log_status(f"PreviewManager: Temporary subtitle file for {os.path.basename(video_path)}: {temp_subtitle_path}")
            
            # Platform-specific video opening logic
            player_opened = False
            try:
                if os.name == 'nt':
                    try:
                        subprocess.Popen(["vlc", video_path, f"--sub-file={temp_subtitle_path}"])
                        self.app.log_status(f"PreviewManager: Attempting to open {os.path.basename(video_path)} with VLC and subtitles...")
                        player_opened = True
                    except FileNotFoundError:
                        self.app.log_status("PreviewManager: VLC not found or failed for subtitle preview, trying os.startfile...")
                        # os.startfile might not support --sub-file, so this is video only
                elif sys.platform == 'darwin':
                    subprocess.Popen(["open", "-a", "VLC", video_path, "--args", f"--sub-file={temp_subtitle_path}"])
                    self.app.log_status(f"PreviewManager: Attempting to open {os.path.basename(video_path)} with VLC and subtitles on macOS...")
                    player_opened = True
                else:  # Linux and other Unix-like
                    try:
                        subprocess.Popen(["vlc", video_path, f"--sub-file={temp_subtitle_path}"])
                        self.app.log_status(f"PreviewManager: Attempting to open {os.path.basename(video_path)} with VLC and subtitles...")
                        player_opened = True
                    except FileNotFoundError:
                        self.app.log_status("PreviewManager: VLC not found for subtitle preview on Linux.")
                
                if player_opened:
                    self.app.log_status(f"PreviewManager: Video preview with subtitles initiated for {os.path.basename(video_path)}.")
                else:  # Fallback to opening video without subtitles if specific player with subs failed
                    self.app.log_status(f"PreviewManager: Could not open with subtitles directly. Opening video: {os.path.basename(video_path)}.", "WARNING")
                    if os.name == 'nt':
                        os.startfile(video_path)
                    elif sys.platform == 'darwin':
                        subprocess.Popen(["open", video_path])
                    else:
                        subprocess.Popen(["xdg-open", video_path])
            
            except Exception as e_open:
                self.app.log_status(f"PreviewManager: Could not automatically open {os.path.basename(video_path)} with subtitles: {e_open}. Opening video directly.", "ERROR")
                if os.name == 'nt':
                    os.startfile(video_path)
                elif sys.platform == 'darwin':
                    subprocess.Popen(["open", video_path])
                else:
                    subprocess.Popen(["xdg-open", video_path])
        
        except Exception as e:
            QMessageBox.warning(self.app, "Preview Error", f"Failed to create temp subtitle or open {os.path.basename(video_path)}: {e}")
            self.app.log_status(f"PreviewManager: Error during subtitle preview for {os.path.basename(video_path)}: {e}", "ERROR")
        finally:
            if temp_subtitle_path and os.path.exists(temp_subtitle_path):
                try:
                    # Schedule file for deletion to ensure it's properly closed first
                    # In Qt we could use a QTimer.singleShot to delay deletion
                    os.remove(temp_subtitle_path)
                    self.app.log_status(f"PreviewManager: Cleaned up temporary subtitle file: {temp_subtitle_path}", "VERBOSE")
                except OSError as e_remove:
                    self.app.log_status(f"PreviewManager: Could not remove temp subtitle {os.path.basename(temp_subtitle_path)} ({temp_subtitle_path}): {e_remove}. May need manual cleanup.", "WARNING") 