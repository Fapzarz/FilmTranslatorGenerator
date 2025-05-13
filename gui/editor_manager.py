import tkinter as tk
from tkinter import messagebox
import re
import os # Might be needed if any path operations occur, good to have if app methods use it.

from utils.format import format_output # For apply_editor_changes

# Note: 'app' in these functions refers to the instance of AppGUI

def load_segments_to_editor(app, segments):
    """Formats and loads subtitle segments into the editor text widget.
    'app' is the AppGUI instance.
    'segments' is the list of subtitle segments.
    """
    editor = app.text_widgets['editor_text']
    editor.configure(state='normal')
    editor.delete(1.0, tk.END)

    if not segments:
        editor.insert(tk.END, "No subtitle segments to display or edit.")
        # State will be set to disabled by the calling context if needed (e.g., on_video_select)
        return

    for i, segment in enumerate(segments):
        start_time_val = segment.get('start')
        end_time_val = segment.get('end')
        # _format_timestamp is a method of AppGUI, so call it via app instance
        start_time = app._format_timestamp(start_time_val) 
        end_time = app._format_timestamp(end_time_val)
        text = segment.get('text', '').strip()
        
        editor.insert(tk.END, f"Segment: {i+1}\n")
        editor.insert(tk.END, f"Time: {start_time} --> {end_time}\n")
        editor.insert(tk.END, f"Text: {text}\n\n")
    
    # The editor state (normal/disabled) should be managed by the calling function
    # based on whether there are segments and if editing is allowed.


def parse_edited_text_to_segments(app, edited_text_content):
    """Parses the content from the editor back into a list of segment dictionaries.
    'app' is the AppGUI instance (for logging).
    """
    new_segments = []
    segment_pattern = re.compile(r"Segment: (\d+)\s*Time: ([\d:,]+) --> ([\d:,]+)\s*Text: (.*?)(?=\nSegment: |\Z)", re.DOTALL | re.MULTILINE)
    time_regex = re.compile(r"(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2}),(\d{1,3})")

    def parse_time(ts_str): # Inner helper function
        match = time_regex.fullmatch(ts_str.strip())
        if not match:
            app.log_status(f"Warning: Could not parse timestamp string: '{ts_str}'")
            return None
        
        groups = match.groups()
        hours = int(groups[0]) if groups[0] else 0
        minutes = int(groups[1])
        seconds = int(groups[2])
        ms = int(groups[3])
        return hours * 3600 + minutes * 60 + seconds + ms / 1000.0

    for match in segment_pattern.finditer(edited_text_content):
        try:
            num_str, start_str, end_str, text_content = match.groups()
            
            start_time = parse_time(start_str)
            end_time = parse_time(end_str)
            text = text_content.strip()
            
            if start_time is None or end_time is None:
                app.log_status(f"Skipping segment {num_str} due to time parsing error.")
                continue
            
            if start_time > end_time:
                app.log_status(f"Warning: Segment {num_str} start time ({start_str}) is after end time ({end_str}). Adjusting end time.")
                end_time = start_time 

            new_segments.append({'start': start_time, 'end': end_time, 'text': text})
        except Exception as e:
            app.log_status(f"Error parsing segment block (Num: {match.group(1) if match else 'N/A'}). Error: {e}")
            continue 
            
    return new_segments

def apply_editor_changes(app):
    """Applies changes from the subtitle editor to the current video's data.
    'app' is the AppGUI instance.
    """
    selected_indices = app.video_listbox.curselection()
    if not selected_indices:
        messagebox.showerror("Error", "No video selected in the queue to apply changes to.")
        return

    # Ensure video_queue is not empty and index is valid
    if not app.video_queue or selected_indices[0] >= len(app.video_queue):
        messagebox.showerror("Error", "Selected video index is out of bounds.")
        return
    current_video_path = app.video_queue[selected_indices[0]]
    
    if not current_video_path or current_video_path not in app.processed_file_data:
        messagebox.showerror("Error", "Selected video data not found.")
        return
    
    file_data = app.processed_file_data[current_video_path]
    if not file_data.get('translated_segments'): 
        messagebox.showinfo("Info", "No translation data exists for this video to edit.")
        return

    editor_content = app.text_widgets['editor_text'].get(1.0, tk.END)
    edited_segments = [] # Default to empty list

    if not editor_content.strip():
        if messagebox.askyesno("Confirm Clear Subtitles", "Editor is empty. Do you want to remove all subtitles for this item?"):
            pass # edited_segments is already []
        else:
            return # User cancelled clearing
    else:
        try:
            edited_segments = parse_edited_text_to_segments(app, editor_content) # Call the local function
            if not edited_segments and editor_content.strip(): 
                messagebox.showwarning("Parsing Error", "Could not parse any segments from the editor. Check format. Changes not applied.")
                return
        except Exception as e_parse:
            app.log_status(f"Critical error parsing editor content: {e_parse}", level="ERROR")
            messagebox.showerror("Parsing Error", f"Failed to parse editor content: {e_parse}. Changes not applied.")
            return
    
    file_data['translated_segments'] = edited_segments
    
    # Update AppGUI instance variables if this is the currently selected and displayed item
    # This ensures the main app object has the latest data for comparison view, etc.
    if app.selected_video_in_queue.get() == current_video_path: 
         app.translated_segments = edited_segments

    output_format_val = app.output_format_var.get()
    new_output_content = format_output(edited_segments, output_format_val) # from utils.format
    file_data['output_content'] = new_output_content
    
    if app.selected_video_in_queue.get() == current_video_path: 
        app.current_output = new_output_content
        app.display_output(new_output_content)
        app.update_comparison_view()
        # Optionally, reload the editor to show the cleaned/parsed version
        load_segments_to_editor(app, edited_segments) 
    
    app.log_status(f"Changes applied to subtitles for {os.path.basename(current_video_path)}. Save via 'Save Output' or project save.")
    messagebox.showinfo("Changes Applied", f"Subtitle changes for {os.path.basename(current_video_path)} have been applied. You can save the updated subtitle file or save the project.")
    app.text_widgets['editor_text'].configure(state='normal') 