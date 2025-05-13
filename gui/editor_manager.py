import os
import tkinter as tk
from tkinter import messagebox

from utils.format import format_output # For apply_editor_changes
from gui import subtitle_styler # Corrected: Import the subtitle_styler module from gui

# Note: 'app' in these functions refers to the instance of AppGUI

def load_segments_to_editor(app, segments):
    """Loads subtitle segments into the editor text widget."""
    if not hasattr(app, 'text_widgets') or 'editor' not in app.text_widgets:
        app.log_status("Editor: Editor widget not found, cannot load segments.", "ERROR")
        return

    if not segments:
        app.log_status("Editor: No segments to load into editor.", "VERBOSE")
        editor = app.text_widgets['editor']
        editor.configure(state='normal')
        editor.delete(1.0, tk.END)
        editor.configure(state='disabled')
        return

    editor_content = ""
    for i, segment in enumerate(segments):
        start_time = app._format_timestamp(segment['start']) # Use app instance for _format_timestamp
        end_time = app._format_timestamp(segment['end'])
        text = segment['text'].strip() # Ensure text is stripped
        editor_content += f"{i+1}\\n{start_time} --> {end_time}\\n{text}\\n\\n"

    editor = app.text_widgets['editor']
    editor.configure(state='normal')
    editor.delete(1.0, tk.END)
    editor.insert(tk.END, editor_content)
    # Do not disable here if we want it to be immediately editable
    # editor.configure(state='disabled') 
    app.log_status("Segments loaded into editor.", "INFO")

def save_editor_changes(app):
    """Saves the changes from the subtitle editor back to the app.translated_segments."""
    if not hasattr(app, 'text_widgets') or 'editor' not in app.text_widgets:
        app.log_status("Editor: Editor widget not found, cannot save changes.", "ERROR")
        return
    
    editor = app.text_widgets['editor']
    content = editor.get(1.0, tk.END).strip()
    
    if not app.translated_segments: # Should ideally have original segments to map to
        app.log_status("Editor: Original translated segments not found. Cannot map changes.", "ERROR")
        messagebox.showerror("Save Error", "Cannot save changes: original segment data is missing.")
        return

    new_segments = []
    lines = content.split('\\n\\n') # Split by double newline
    
    original_segment_count = len(app.translated_segments)
    parsed_segment_count = 0

    for block in lines:
        if not block.strip():
            continue
        
        parts = block.strip().split('\\n')
        if len(parts) < 3:
            app.log_status(f"Editor: Skipping malformed block: {parts}", "WARNING")
            continue
            
        try:
            # segment_index = int(parts[0].strip()) -1 # Assuming 1-based index in editor
            # We should rely on order rather than index from text, to handle deletions/additions better.
            # For now, let's assume a direct mapping and replacement based on order.
            # A more robust solution would involve proper segment ID management or diffing.

            # Re-parse timestamps (SRT format) - this is simplified and might need more robust parsing
            # Example: 00:00:21,490 --> 00:00:22,830
            time_parts = parts[1].split('-->')
            # For simplicity, we are taking the text and assuming the original start/end times remain
            # This means the editor currently only allows text modification, not timing.
            # If timing can be edited, this parsing logic needs to be much more robust.
            
            # Find corresponding original segment by order
            if parsed_segment_count < original_segment_count:
                original_segment = app.translated_segments[parsed_segment_count]
                new_text = '\\n'.join(parts[2:]).strip() # Join remaining lines as text
                
                new_segments.append({
                    'start': original_segment['start'], # Keep original timing
                    'end': original_segment['end'],     # Keep original timing
                    'text': new_text
                })
                parsed_segment_count += 1
            else:
                app.log_status(f"Editor: Extra segment data found in editor beyond original count: {' '.join(parts)}", "WARNING")
                # Optionally, allow adding new segments if supported
                # For now, we only update existing ones by order.

        except ValueError as e:
            app.log_status(f"Editor: Error parsing segment block: {parts}. Error: {e}", "ERROR")
            messagebox.showerror("Parse Error", f"Error parsing edited segment: {parts[0] if parts else 'Unknown'}. Please check format.")
            return # Stop processing on error

    if parsed_segment_count == 0 and content: # Content was there but nothing parsed
        messagebox.showerror("Save Error", "Could not parse any segments from the editor. Please check the format (ID\\nTIMESTAMPS\\nTEXT\\n\\n...).")
        return
        
    # Update app's translated_segments
    app.translated_segments = new_segments
    
    # Re-format the output for the main output tab
    output_format_to_use = app.output_format_var.get() # Get current output format
    formatted_output = format_output(app.translated_segments, output_format_to_use, app._format_timestamp) # Use app instance for _format_timestamp

    # Update the processed_file_data for the currently selected video
    current_video_path = None
    selected_indices = app.video_listbox.curselection()
    if selected_indices:
        listbox_index = selected_indices[0]
        if listbox_index < len(app.video_queue):
            current_video_path = app.video_queue[listbox_index]

    # Update the main output tab and processed_file_data
    if current_video_path:
        file_data = app.processed_file_data.get(current_video_path)
        if file_data:
            file_data['translated_segments'] = app.translated_segments # Update segments
            # Apply styling if SRT format and style exists
            if output_format_to_use == "srt" and file_data.get('subtitle_style'):
                styled_output = subtitle_styler.format_srt_with_style(app, formatted_output, file_data['subtitle_style'])
                app.display_output(styled_output)
                file_data['output_content'] = styled_output
            else:
                app.display_output(formatted_output)
                file_data['output_content'] = formatted_output
        else:
            # This case should ideally not happen if a video is selected and processed
            app.display_output(formatted_output) 
    else:
        # No video selected, just update the main output display (though this is less likely context for editor save)
        app.display_output(formatted_output)

    app.log_status("Subtitle changes applied from editor.", "INFO")
    if current_video_path :
      messagebox.showinfo("Changes Applied", f"Subtitle changes for {os.path.basename(current_video_path)} have been applied. You can save the updated subtitle file or save the project.")
    
    # Keep editor enabled for further edits
    if hasattr(app, 'text_widgets') and 'editor' in app.text_widgets:
        app.text_widgets['editor'].configure(state='normal')