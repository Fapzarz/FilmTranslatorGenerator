import tkinter as tk
from tkinter import messagebox
import re
import os # Diperlukan untuk os.path.basename di apply_and_save_subtitle_style

# Konstanta mungkin diperlukan jika tidak diakses melalui app
# from config import SUBTITLE_FONTS, SUBTITLE_COLORS, etc. (jika diperlukan langsung)

def format_srt_with_style(app, srt_content, style_dict):
    """Apply styling to SRT content.
    'app' is the AppGUI instance (for log_status).
    'style_dict' is a dictionary containing style parameters.
    """
    try:
        font = style_dict.get('font', 'Arial')
        color = style_dict.get('color', 'white')
        size = style_dict.get('size', '16')
        # Position styling in SRT is complex and often player-dependent;
        # ASS/SSA is better for this. Basic SRT doesn't have reliable position tags.
        # outline_color = style_dict.get('outline_color', 'black')
        # outline_width = style_dict.get('outline_width', '1')
        # bg_color = style_dict.get('bg_color', 'transparent')
        # bg_opacity = style_dict.get('bg_opacity', '0')

        # Basic SRT styling using <font> tags.
        # More advanced styling (outline, background) is often not well-supported
        # directly in SRT files across all players. For maximum compatibility,
        # styling is kept simple or users should use formats like ASS.

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
        if hasattr(app, 'log_status'):
            app.log_status(f"Error applying style to SRT: {e}", level="ERROR")
        return srt_content  # Return original content on error

def apply_and_save_subtitle_style(app):
    """Apply the current subtitle style settings from UI to the selected video's data.
    'app' is the AppGUI instance.
    """
    try:
        selected_indices = app.video_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "Please select a video from the queue.")
            return
            
        raw_listbox_item = app.video_listbox.get(selected_indices[0])
        # Extract basename robustly, assuming format "[Status] basename" or just "basename"
        filepath_basename = raw_listbox_item.split("] ", 1)[-1]

        actual_filepath = next((fp for fp in app.video_queue if os.path.basename(fp) == filepath_basename), None)
        
        if not actual_filepath or not os.path.exists(actual_filepath):
            messagebox.showinfo("Error", "Cannot find the selected video file.")
            return
            
        file_data = app.processed_file_data.get(actual_filepath)
        if not file_data or not file_data.get('output_content'):
            messagebox.showinfo("Info", "Please process the video first to generate subtitles.")
            return
            
        current_style = {
            'font': app.subtitle_font_var.get(),
            'color': app.subtitle_color_var.get(),
            'size': app.subtitle_size_var.get(),
            'position': app.subtitle_position_var.get(), # Keep for potential future use, though not applied to SRT directly
            'outline_color': app.subtitle_outline_color_var.get(),
            'outline_width': app.subtitle_outline_width_var.get(),
            'bg_color': app.subtitle_bg_color_var.get(),
            'bg_opacity': app.subtitle_bg_opacity_var.get()
        }
        file_data['subtitle_style'] = current_style
        app.processed_file_data[actual_filepath] = file_data
        
        messagebox.showinfo("Success", "Subtitle styling has been set for the selected video. It will be applied when saving SRT or previewing.")
        app.log_status(f"Subtitle style updated for {filepath_basename}.")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to apply subtitle style: {e}")
        if hasattr(app, 'log_status'):
            app.log_status(f"Error applying subtitle style: {e}", level="ERROR")

def refresh_subtitle_style_preview(app, event=None):
    """Update the subtitle preview canvas based on current style settings from UI.
    'app' is the AppGUI instance.
    """
    try:
        font_name = app.subtitle_font_var.get()
        # Ensure font_size is an integer, provide a default if conversion fails
        try:
            font_size_str = app.subtitle_size_var.get()
            font_size = int(font_size_str) if font_size_str else 16 # Default if empty
        except ValueError:
            font_size = 16 # Default on error
            if hasattr(app, 'log_status'):
                app.log_status(f"Invalid font size value: {font_size_str}. Using default 16.", level="WARNING")

        text_color = app.subtitle_color_var.get()
        position = app.subtitle_position_var.get() # Vertical position
        
        # Ensure outline_width is an integer
        try:
            outline_width_str = app.subtitle_outline_width_var.get()
            outline_width = int(outline_width_str) if outline_width_str else 0
        except ValueError:
            outline_width = 0
            if hasattr(app, 'log_status'):
                app.log_status(f"Invalid outline width value: {outline_width_str}. Using default 0.", level="WARNING")

        outline_color = app.subtitle_outline_color_var.get()
        bg_color = app.subtitle_bg_color_var.get()
        
        # Ensure bg_opacity is an integer
        try:
            bg_opacity_str = app.subtitle_bg_opacity_var.get()
            bg_opacity = int(bg_opacity_str) if bg_opacity_str else 0
        except ValueError:
            bg_opacity = 0
            if hasattr(app, 'log_status'):
                app.log_status(f"Invalid background opacity value: {bg_opacity_str}. Using default 0.", level="WARNING")

        canvas = app.preview_canvas
        canvas_width = canvas.winfo_width() or 300 
        canvas_height = canvas.winfo_height() or 100
        
        x_pos = canvas_width / 2
        
        if position == "top":
            y_pos = canvas_height * 0.20 # Adjusted for better top placement
        elif position == "middle":
            y_pos = canvas_height * 0.50
        else:  # bottom (default)
            y_pos = canvas_height * 0.80 # Adjusted for better bottom placement
        
        canvas.delete("all")
        preview_text = "Sample Subtitle Text"
        
        # Font tuple for Tkinter
        font_config = (font_name, font_size)

        # --- Background Rendering (simplified) ---
        if bg_color != "transparent" and bg_color and bg_opacity > 0:
            # For simplicity, draw a semi-transparent rectangle based on text metrics (approximate)
            # Tkinter doesn't directly support text background opacity easily.
            # This creates a rectangle behind the text.
            try:
                # Approximate text bounding box (more accurate would be to use font.measure)
                # This is a rough estimate.
                text_width_approx = font_size * len(preview_text) * 0.6 
                text_height_approx = font_size * 1.5

                bg_rect_x1 = x_pos - text_width_approx / 2 - 5 # padding
                bg_rect_y1 = y_pos - text_height_approx / 2 - 3 # padding
                bg_rect_x2 = x_pos + text_width_approx / 2 + 5 # padding
                bg_rect_y2 = y_pos + text_height_approx / 2 + 3 # padding

                # Create a stipple pattern for transparency if opacity < 100
                # For a more robust solution, one might draw on an intermediate transparent image.
                stipple_pattern = ""
                if 0 < bg_opacity < 25: stipple_pattern = 'gray12'
                elif 25 <= bg_opacity < 50: stipple_pattern = 'gray25'
                elif 50 <= bg_opacity < 75: stipple_pattern = 'gray50'
                elif 75 <= bg_opacity < 100: stipple_pattern = 'gray75'
                
                if bg_opacity > 0 : # Only draw if some opacity
                     canvas.create_rectangle(
                        bg_rect_x1, bg_rect_y1, bg_rect_x2, bg_rect_y2,
                        fill=bg_color if bg_opacity == 100 else bg_color, # Fill color
                        outline="", # No outline for the bg box itself
                        stipple=stipple_pattern if bg_opacity < 100 else ""
                    )
            except Exception as e_bg:
                if hasattr(app, 'log_status'):
                    app.log_status(f"Error rendering subtitle preview background: {e_bg}", level="WARNING")


        # --- Outline Rendering ---
        if outline_width > 0 and outline_color:
            # Draw text multiple times with offset for outline effect
            offsets = []
            for i in range(-outline_width, outline_width + 1):
                for j in range(-outline_width, outline_width + 1):
                    if i != 0 or j != 0: # Don't draw center for outline
                         # Simple square outline for now
                        if abs(i) == outline_width or abs(j) == outline_width:
                            offsets.append((i, j))
            
            # More controlled offsets for a cleaner look
            if outline_width == 1:
                offsets = [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]
            elif outline_width == 2:
                 offsets = [(-2,-2), (-2,2), (2,-2), (2,2), (-2,0), (2,0), (0,-2), (0,2),
                            (-1,-2), (1,-2), (-2,-1), (2,-1), (-1,2), (1,2), (-2,1), (2,1)]
            # Add more complex offsets for larger widths if needed
            
            for dx, dy in offsets:
                canvas.create_text(
                    x_pos + dx, y_pos + dy, 
                    text=preview_text, 
                    fill=outline_color, 
                    font=font_config,
                    anchor="center"
                )
        
        # --- Main Text Rendering ---
        canvas.create_text(
            x_pos, y_pos, 
            text=preview_text, 
            fill=text_color, 
            font=font_config,
            anchor="center"
        )
        
        if hasattr(app, 'log_status'):
            app.log_status(f"Updated subtitle preview: {font_name}, size {font_size}, color {text_color}")
            
    except Exception as e:
        if hasattr(app, 'log_status'):
            app.log_status(f"Error updating subtitle preview: {e}", level="ERROR") 