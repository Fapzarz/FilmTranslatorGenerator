"""
Manages video and subtitle preview functionalities for the Film Translator Generator.
"""
import os
import tkinter as tk
from tkinter import messagebox
import tempfile
import subprocess
import sys

# Import utility functions directly
from utils.media import extract_video_thumbnail, get_video_info, play_video_preview

# Assuming these are still needed and will be accessed via app instance or passed if not directly available
# from utils.media import extract_video_thumbnail, play_video_preview, get_video_info
# from gui import subtitle_styler # Will be app.subtitle_styler

class PreviewManager:
    def __init__(self, app_instance):
        """
        Initializes the PreviewManager.

        Args:
            app_instance: The main AppGUI instance.
        """
        self.app = app_instance

    def update_video_preview_info(self, video_path):
        """Update video thumbnail and information for the given path in the AppGUI."""
        if not video_path:  # Clear preview if no path
            if hasattr(self.app, 'thumbnail_label') and self.app.thumbnail_label:
                self.app.thumbnail_label.config(image=None)
                self.app.thumbnail_label.image = None
            if hasattr(self.app, 'thumbnail_placeholder') and self.app.thumbnail_placeholder:
                 self.app.thumbnail_placeholder.pack() # Show placeholder
            if hasattr(self.app, 'video_duration_label') and self.app.video_duration_label:
                self.app.video_duration_label.config(text="Duration: N/A")
            if hasattr(self.app, 'video_size_label') and self.app.video_size_label:
                self.app.video_size_label.config(text="Size: N/A")
            return

        try:
            if hasattr(self.app, 'thumbnail_placeholder') and self.app.thumbnail_placeholder:
                self.app.thumbnail_placeholder.pack_forget()
            if hasattr(self.app, 'thumbnail_label') and self.app.thumbnail_label:
                self.app.thumbnail_label.config(image=None)
            
            # Assuming get_video_info and extract_video_thumbnail are methods on app or globally available
            # For now, let's assume they are part of app.utils.media or similar and AppGUI imports them
            thumbnail = extract_video_thumbnail(video_path) # Call imported function directly
            if thumbnail and hasattr(self.app, 'thumbnail_label') and self.app.thumbnail_label:
                self.app.thumbnail_label.config(image=thumbnail)
                self.app.thumbnail_label.image = thumbnail # Keep a reference!
                self.app.thumbnail_label.pack()
                if hasattr(self.app, 'thumbnail_placeholder') and self.app.thumbnail_placeholder:
                    self.app.thumbnail_placeholder.pack_forget()
            elif hasattr(self.app, 'thumbnail_label') and self.app.thumbnail_label: # No thumbnail found
                self.app.thumbnail_label.pack_forget()
                if hasattr(self.app, 'thumbnail_placeholder') and self.app.thumbnail_placeholder:
                    self.app.thumbnail_placeholder.pack()
            
            video_info = get_video_info(video_path) # Call imported function directly
            if hasattr(self.app, 'video_duration_label') and self.app.video_duration_label:
                self.app.video_duration_label.config(text=f"Duration: {video_info['duration']}")
            if hasattr(self.app, 'video_size_label') and self.app.video_size_label:
                self.app.video_size_label.config(text=f"Size: {video_info['size']}")
            
        except Exception as e:
            self.app.log_status(f"PreviewManager: Error updating video preview info: {e}", "ERROR")
            if hasattr(self.app, 'thumbnail_label') and self.app.thumbnail_label: self.app.thumbnail_label.pack_forget()
            if hasattr(self.app, 'thumbnail_placeholder') and self.app.thumbnail_placeholder: self.app.thumbnail_placeholder.pack()
            if hasattr(self.app, 'video_duration_label') and self.app.video_duration_label: self.app.video_duration_label.config(text="Duration: N/A")
            if hasattr(self.app, 'video_size_label') and self.app.video_size_label: self.app.video_size_label.config(text="Size: N/A")

    def preview_selected_video(self):
        """Preview the selected video file from the queue (if one is selected and processed/valid)."""
        selected_indices = self.app.video_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select a video from the queue to preview.", parent=self.app.root)
            return
        
        selected_listbox_index = selected_indices[0]
        if selected_listbox_index >= len(self.app.video_queue):
            messagebox.showerror("Error", "Selected video not found in internal queue. Please check selection.", parent=self.app.root)
            return
            
        actual_video_path = self.app.video_queue[selected_listbox_index]
        
        if not actual_video_path or not os.path.exists(actual_video_path):
            messagebox.showerror("Error", f"The selected video path is invalid or file does not exist: {actual_video_path}", parent=self.app.root)
            return
        
        play_video_preview(actual_video_path, self.app.log_status) # Call imported function, pass log_status from app

    def preview_video_with_subtitles(self):
        """Saves the current output of the selected video as a temporary subtitle file and attempts to open the video with it."""
        selected_indices = self.app.video_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select a video from the queue to preview.", parent=self.app.root)
            return
        
        selected_listbox_index = selected_indices[0]
        if selected_listbox_index >= len(self.app.video_queue):
            messagebox.showerror("Error", "Selected video not found in internal queue. Please re-add.", parent=self.app.root)
            return
            
        video_path = self.app.video_queue[selected_listbox_index]
        file_data = self.app.processed_file_data.get(video_path)

        if not file_data or not file_data.get('output_content'):
            messagebox.showinfo("Info", f"No subtitles generated for {os.path.basename(video_path)} to preview.", parent=self.app.root)
            return

        current_output_for_preview = file_data['output_content']
        output_format = self.app.output_format_var.get()
        temp_subtitle_path = ""

        try:
            if output_format == "srt" and file_data.get('subtitle_style') and hasattr(self.app, 'subtitle_styler'):
                self.app.log_status(f"PreviewManager: Applying subtitle styling for preview")
                style = file_data['subtitle_style']
                styled_output = self.app.subtitle_styler.format_srt_with_style(self.app, current_output_for_preview, style)
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
                else: # Linux and other Unix-like
                    try:
                        subprocess.Popen(["vlc", video_path, f"--sub-file={temp_subtitle_path}"])
                        self.app.log_status(f"PreviewManager: Attempting to open {os.path.basename(video_path)} with VLC and subtitles...")
                        player_opened = True
                    except FileNotFoundError:
                        self.app.log_status("PreviewManager: VLC not found for subtitle preview on Linux.")
                
                if player_opened:
                    self.app.log_status(f"PreviewManager: Video preview with subtitles initiated for {os.path.basename(video_path)}.")
                else: # Fallback to opening video without subtitles if specific player with subs failed
                    self.app.log_status(f"PreviewManager: Could not open with subtitles directly. Opening video: {os.path.basename(video_path)}.", "WARNING")
                    if os.name == 'nt': os.startfile(video_path)
                    elif sys.platform == 'darwin': subprocess.Popen(["open", video_path])
                    else: subprocess.Popen(["xdg-open", video_path])

            except Exception as e_open:
                self.app.log_status(f"PreviewManager: Could not automatically open {os.path.basename(video_path)} with subtitles: {e_open}. Opening video directly.", "ERROR")
                if os.name == 'nt': os.startfile(video_path)
                elif sys.platform == 'darwin': subprocess.Popen(["open", video_path])
                else: subprocess.Popen(["xdg-open", video_path])

        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to create temp subtitle or open {os.path.basename(video_path)}: {e}", parent=self.app.root)
            self.app.log_status(f"PreviewManager: Error during subtitle preview for {os.path.basename(video_path)}: {e}", "ERROR")
        finally:
            if temp_subtitle_path and os.path.exists(temp_subtitle_path):
                try:
                    os.remove(temp_subtitle_path)
                    self.app.log_status(f"PreviewManager: Cleaned up temporary subtitle file: {temp_subtitle_path}", "VERBOSE")
                except OSError as e_remove:
                    self.app.log_status(f"PreviewManager: Could not remove temp subtitle {os.path.basename(temp_subtitle_path)} ({temp_subtitle_path}): {e_remove}. May need manual cleanup.", "WARNING") 