import os
import tkinter as tk
from tkinter import filedialog, messagebox
from gui import editor_manager # Import editor_manager

# Functions related to managing the video processing queue

def add_videos_to_queue(app):
    """Prompts user to select one or more video files and adds them to the queue."""
    filepaths = filedialog.askopenfilenames(
        title="Select Video File(s)",
        filetypes=(("Video Files", "*.mp4 *.avi *.mkv *.mov *.webm"), ("All Files", "*.*"))
    )
    if filepaths:
        for filepath in filepaths:
            if filepath not in app.video_queue:
                app.video_queue.append(filepath)
                app.processed_file_data[filepath] = {'status': 'Pending', 'transcribed_segments': None, 'translated_segments': None, 'output_content': None}
                app.video_listbox.insert(tk.END, f"[Pending] {os.path.basename(filepath)}")
                app.log_status(f"Added to queue: {filepath}")
            else:
                app.log_status(f"Already in queue: {filepath}")
        app.log_status(f"{len(filepaths)} video(s) selected. Queue size: {len(app.video_queue)}")
        if app.video_listbox.size() > 0 and not app.video_listbox.curselection():
            app.video_listbox.selection_set(0)
            on_video_select_in_queue(app) # Trigger preview update
        update_queue_statistics(app) # Update stats

def on_video_select_in_queue(app, event=None):
    """Handles selection change in the video queue listbox."""
    selected_indices = app.video_listbox.curselection()
    if not selected_indices:
        app.update_video_preview(None) # Clear preview
        app.display_output("") # Clear output tabs
        app.text_widgets['original'].configure(state='normal'); app.text_widgets['original'].delete(1.0, tk.END); app.text_widgets['original'].configure(state='disabled')
        app.text_widgets['translated'].configure(state='normal'); app.text_widgets['translated'].delete(1.0, tk.END); app.text_widgets['translated'].configure(state='disabled')
        app.text_widgets['editor_text'].configure(state='disabled'); app.text_widgets['editor_text'].delete(1.0, tk.END) # Clear and disable editor
        return

    raw_listbox_item = app.video_listbox.get(selected_indices[0])
    if "]" in raw_listbox_item:
        filepath_basename = raw_listbox_item.split("] ", 1)[1]
        actual_filepath = next((fp for fp in app.video_queue if os.path.basename(fp) == filepath_basename), None)
        if not actual_filepath:
             actual_filepath = app.video_queue[selected_indices[0]]
    else: 
        actual_filepath = raw_listbox_item

    app.root.after(50, lambda fp=actual_filepath: _handle_video_selection_update(app, fp))

def _handle_video_selection_update(app, actual_filepath):
    """Handles the actual UI updates after a video selection, called via root.after()."""
    if actual_filepath and os.path.exists(actual_filepath):
        app.update_video_preview(actual_filepath)
        file_data = app.processed_file_data.get(actual_filepath)
        if file_data and file_data['status'] in ['Done', 'Error_Translation', 'Error_Transcription', 'Error_Generic'] and file_data.get('translated_segments'):
            app.display_output(file_data.get('output_content', ""))
            app.transcribed_segments = file_data.get('transcribed_segments') 
            app.translated_segments = file_data.get('translated_segments')   
            app.update_comparison_view()
            editor_manager.load_segments_to_editor(app, app.translated_segments) 
            if app.translated_segments:
                app.text_widgets['editor_text'].configure(state='normal')
            else:
                app.text_widgets['editor_text'].configure(state='disabled')
        elif file_data: 
            app.display_output(f"Video selected: {os.path.basename(actual_filepath)}\nStatus: {file_data['status']}")
            app.text_widgets['original'].configure(state='normal'); app.text_widgets['original'].delete(1.0, tk.END); app.text_widgets['original'].configure(state='disabled')
            app.text_widgets['translated'].configure(state='normal'); app.text_widgets['translated'].delete(1.0, tk.END); app.text_widgets['translated'].configure(state='disabled')
            app.text_widgets['editor_text'].configure(state='disabled'); app.text_widgets['editor_text'].delete(1.0, tk.END)
        else: 
            app.display_output(f"No data found for {os.path.basename(actual_filepath)}.")
            app.text_widgets['editor_text'].configure(state='disabled'); app.text_widgets['editor_text'].delete(1.0, tk.END)
    else: 
        app.update_video_preview(None) 
        app.display_output("")
        app.text_widgets['original'].configure(state='normal'); app.text_widgets['original'].delete(1.0, tk.END); app.text_widgets['original'].configure(state='disabled')
        app.text_widgets['translated'].configure(state='normal'); app.text_widgets['translated'].delete(1.0, tk.END); app.text_widgets['translated'].configure(state='disabled')
        app.text_widgets['editor_text'].configure(state='disabled'); app.text_widgets['editor_text'].delete(1.0, tk.END)

def remove_selected_video_from_queue(app):
    """Removes the selected video from the queue."""
    selected_indices = app.video_listbox.curselection()
    if not selected_indices:
        messagebox.showinfo("Info", "Please select a video from the queue to remove.")
        return
    
    index_to_remove = selected_indices[0]
    filepath_to_remove = app.video_queue.pop(index_to_remove)
    
    app.video_listbox.delete(index_to_remove)
    if filepath_to_remove in app.processed_file_data:
        del app.processed_file_data[filepath_to_remove]
    app.log_status(f"Removed from queue: {filepath_to_remove}")
    
    if app.video_listbox.size() > 0:
        if index_to_remove < app.video_listbox.size():
             app.video_listbox.selection_set(index_to_remove)
        else:
             app.video_listbox.selection_set(app.video_listbox.size() - 1)
        on_video_select_in_queue(app)
    else: 
        app.update_video_preview(None)
        app.display_output("")
        app.text_widgets['original'].configure(state='normal'); app.text_widgets['original'].delete(1.0, tk.END); app.text_widgets['original'].configure(state='disabled')
        app.text_widgets['translated'].configure(state='normal'); app.text_widgets['translated'].delete(1.0, tk.END); app.text_widgets['translated'].configure(state='disabled')
        app.text_widgets['editor_text'].configure(state='disabled'); app.text_widgets['editor_text'].delete(1.0, tk.END)
    update_queue_statistics(app)

def clear_video_queue(app):
    """Clears all videos from the queue."""
    if not app.video_queue:
        messagebox.showinfo("Info", "Queue is already empty.")
        return
    
    if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the entire video queue?"):
        app.video_queue.clear()
        app.processed_file_data.clear()
        app.video_listbox.delete(0, tk.END)
        app.log_status("Video queue cleared.")
        app.update_video_preview(None)
        app.display_output("")
        app.text_widgets['original'].configure(state='normal'); app.text_widgets['original'].delete(1.0, tk.END); app.text_widgets['original'].configure(state='disabled')
        app.text_widgets['translated'].configure(state='normal'); app.text_widgets['translated'].delete(1.0, tk.END); app.text_widgets['translated'].configure(state='disabled')
        app.text_widgets['editor_text'].configure(state='disabled'); app.text_widgets['editor_text'].delete(1.0, tk.END)
        update_queue_statistics(app)

def update_queue_statistics(app):
    """Updates the queue statistics display based on current project data."""
    total = len(app.video_queue)
    processed = 0
    pending = 0
    failed = 0

    for video_path in app.video_queue:
        file_data = app.processed_file_data.get(video_path)
        if file_data:
            status = file_data.get('status')
            if status == 'Done':
                processed += 1
            elif status == 'Pending':
                pending += 1
            elif status and 'Error' in status:
                failed += 1
        else: 
            pending +=1 

    app.stat_total_files.set(f"Total Files: {total}")
    app.stat_processed_files.set(f"Processed: {processed}")
    app.stat_pending_files.set(f"Pending: {pending}")
    app.stat_failed_files.set(f"Failed: {failed}") 