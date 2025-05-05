import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import tkinter.ttk as ttk # Import ttk for Combobox
import threading
import os
from faster_whisper import WhisperModel # Import faster_whisper
import google.generativeai as genai
import time # To create unique filenames
import re # Import regex for parsing batch response

# --- Language List ---
# Add more languages as needed
LANGUAGES = [
    "English", "Indonesian", "Spanish", "French", "German",
    "Japanese", "Chinese", "Korean", "Russian", "Portuguese",
    "Italian", "Arabic", "Hindi", "Turkish"
]

# --- Backend Functions ---

def transcribe_video(model_instance, video_path, status_callback):
    """Transcribes the video file using the provided faster-whisper model instance (VAD disabled)."""
    if not model_instance:
        status_callback("Error: Faster-Whisper model instance not provided.")
        return None

    try:
        status_callback(f"Starting transcription (faster-whisper, VAD disabled) for: {os.path.basename(video_path)}...")
        # Disable VAD filter
        segments_iterator, info = model_instance.transcribe(
            video_path,
            beam_size=5,
            vad_filter=False # Disable VAD filter
        )

        status_callback(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")

        # Collect segments from the iterator into a list of dictionaries
        segments_list = []
        status_callback("Processing segments...")
        last_update_time = time.time()
        count = 0
        for segment in segments_iterator:
            segments_list.append({
                'start': segment.start,
                'end': segment.end,
                'text': segment.text
            })
            count += 1
            # Update status periodically to show progress
            current_time = time.time()
            if current_time - last_update_time > 2: # Update every 2 seconds
                status_callback(f"Processed {count} segments...")
                last_update_time = current_time

        status_callback(f"Transcription finished. Total segments: {len(segments_list)}")
        return segments_list

    except FileNotFoundError:
        status_callback(f"Error: Video file not found at '{video_path}'.")
        return None
    except Exception as e:
        # Catch potential CTranslate2/CUDA errors
        status_callback(f"Error during transcription: {e}")
        if "CUDA out of memory" in str(e):
             status_callback("CUDA out of memory. Try closing other GPU-intensive applications or consider using a smaller model or different compute_type (e.g., int8_float16).")
        elif "Could not load library cudnn64_8.dll" in str(e) or "cublasLt64_11.dll" in str(e):
             status_callback("CUDA/cuDNN library error. Ensure CUDA Toolkit and cuDNN are installed correctly and compatible with PyTorch/CTranslate2.")
        return None

def translate_text_gemini(api_key, text_segments, target_language, status_callback, batch_size=500): # Changed batch_size to 500
    """Translates text segments using Gemini API in batches with ultra-strict prompt."""
    if not api_key:
        status_callback("Error: Gemini API Key is missing.")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
        status_callback(f"Configured Gemini. Translating to {target_language}...")
    except Exception as e:
        status_callback(f"Error configuring Gemini: {e}")
        return None

    translated_segments = []
    total_segments = len(text_segments)
    num_batches = (total_segments + batch_size - 1) // batch_size # Calculate number of batches
    mismatch_tolerance = 10 # Allow +/- 10 segments difference

    for i in range(0, total_segments, batch_size):
        batch_num = (i // batch_size) + 1
        status_callback(f"Processing batch {batch_num}/{num_batches} (segments {i+1}-{min(i+batch_size, total_segments)})... ")

        batch = text_segments[i:i+batch_size]
        if not batch:
            continue

        # --- Ultra-Strict Prompt for Batch --- 
        prompt_lines = [
            f"Translate the following numbered dialogue segments into {target_language}."
            f"Output ONLY the raw translated text for each number, starting directly with number 1."
            f"Do NOT include any introductory phrases, explanations, greetings, or any text other than the numbered translations."
            f"Example: If input is '1. Hello\n2. Goodbye', output should be '1. Halo\n2. Selamat tinggal' (for Indonesian) and nothing else.\n"
        ]
        for j, segment in enumerate(batch):
            cleaned_text = segment['text'].strip().replace('\n', ' ')
            prompt_lines.append(f"{j+1}. {cleaned_text}")

        prompt_lines.append("\nYour entire response must be ONLY the numbered list of translations.")
        batch_prompt = "\n".join(prompt_lines)

        try:
            response = model.generate_content(batch_prompt)
            response_text = response.text.strip()

            # Attempt to parse the numbered list response
            # Simple split by newline, assuming Gemini follows instructions
            translated_texts = response_text.split('\n')

            # Basic validation and cleanup
            parsed_translations = []
            for line in translated_texts:
                # Try to remove potential numbering like "1. ", "1) ", etc.
                cleaned_line = re.sub(r"^\s*\d+[\.\)]\s*", "", line).strip()
                if cleaned_line: # Only add non-empty lines
                    parsed_translations.append(cleaned_line)

            # --- Modified Mismatch Check --- 
            expected_count = len(batch)
            actual_count = len(parsed_translations)
            lower_bound = expected_count - mismatch_tolerance
            upper_bound = expected_count + mismatch_tolerance

            # Check if the actual count is within the tolerance range
            if lower_bound <= actual_count <= upper_bound:
                # If not an exact match, log a warning but proceed
                if actual_count != expected_count:
                    status_callback(f"Warning: Batch {batch_num} - Slight mismatch (expected {expected_count}, got {actual_count}). Proceeding.")
                
                # Use the minimum of expected/actual count to avoid index errors
                count_to_use = min(expected_count, actual_count)
                for j in range(count_to_use):
                    translated_segments.append({
                        'start': batch[j]['start'],
                        'end': batch[j]['end'],
                        'text': parsed_translations[j]
                    })
                status_callback(f"Batch {batch_num}/{num_batches} processed (with tolerance). Got {actual_count}/{expected_count} segments.")
            else:
                # Fallback if outside tolerance
                status_callback(f"Warning: Batch {batch_num} - Mismatch outside tolerance (expected {expected_count}, got {actual_count}). Falling back to individual translation.")
                # --- Ultra-Strict Prompt for Fallback (Individual) --- 
                for k, segment in enumerate(batch):
                    try:
                        # Use an ultra-strict prompt for individual fallback
                        fallback_prompt = (
                            f"Translate the following dialogue segment into {target_language}. "
                            f"Output ONLY the raw translated text. "
                            f"Do NOT include any introductory phrases, explanations, or any text other than the translation itself.\n\n"
                            f"Dialogue: {segment['text'].strip()}"
                        )
                        fallback_response = model.generate_content(fallback_prompt)
                        fallback_text = fallback_response.text.strip()
                        translated_segments.append({
                            'start': segment['start'],
                            'end': segment['end'],
                            'text': fallback_text
                        })
                    except Exception as fallback_e:
                        status_callback(f"Error translating segment {i+k+1} individually: {fallback_e}. Skipping.")
                        # Append original or error message if needed
                        translated_segments.append({
                            'start': segment['start'],
                            'end': segment['end'],
                            'text': f"[Translation Error] {segment['text']}"
                        })

        except Exception as e:
            status_callback(f"Error processing batch {batch_num}: {e}. Attempting individual fallback...")
            # --- Ultra-Strict Prompt for Fallback (Batch Error) --- 
            for k, segment in enumerate(batch):
                 try:
                     # Use the same ultra-strict individual prompt here too
                     fallback_prompt = (
                         f"Translate the following dialogue segment into {target_language}. "
                         f"Output ONLY the raw translated text. "
                         f"Do NOT include any introductory phrases, explanations, or any text other than the translation itself.\n\n"
                         f"Dialogue: {segment['text'].strip()}"
                     )
                     fallback_response = model.generate_content(fallback_prompt)
                     fallback_text = fallback_response.text.strip()
                     translated_segments.append({
                         'start': segment['start'],
                         'end': segment['end'],
                         'text': fallback_text
                     })
                 except Exception as fallback_e:
                     status_callback(f"Error translating segment {i+k+1} individually: {fallback_e}. Skipping.")
                     translated_segments.append({
                         'start': segment['start'],
                         'end': segment['end'],
                         'text': f"[Translation Error] {segment['text']}"
                     })

    status_callback("Translation finished.")
    # Ensure the number of translated segments matches the original
    if len(translated_segments) != total_segments:
        status_callback(f"Warning: Final segment count mismatch (expected {total_segments}, got {len(translated_segments)}). Some segments might be missing or duplicated.")
        # Pad with error messages if needed, though the fallback should handle most cases
        while len(translated_segments) < total_segments:
             # This is a basic padding, might not align correctly with time
             translated_segments.append({'start': 0, 'end': 0, 'text': '[Missing Translation]'}) 

    return translated_segments

def format_time_srt(seconds):
    """Converts seconds to SRT time format HH:MM:SS,ms."""
    millis = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    minutes = seconds // 60
    seconds %= 60
    hours = minutes // 60
    minutes %= 60
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

def create_srt_content(translated_segments):
    """Generates SRT formatted string from translated segments."""
    srt_content = ""
    for i, segment in enumerate(translated_segments):
        # Remove the start time offset calculation
        start_time = segment['start']
        end_time = segment['end']

        # Ensure start time is not negative (shouldn't happen with Whisper, but good practice)
        start_time = max(0, start_time)
        # Ensure end time is after start time
        end_time = max(start_time, end_time)

        start_str = format_time_srt(start_time)
        end_str = format_time_srt(end_time)
        text = segment['text']
        srt_content += f"{i+1}\n"
        srt_content += f"{start_str} --> {end_str}\n"
        srt_content += f"{text}\n\n"
    return srt_content

# --- GUI Class ---

class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Film Translator Generator")
        self.root.geometry("600x550") # Adjusted size

        self.video_path = tk.StringVar()
        self.api_key = tk.StringVar()
        self.target_language = tk.StringVar(value="English") # Default target language
        self.whisper_model = None # Initialize whisper_model as None
        self.whisper_model_name = "large-v2" # Changed model
        self.compute_type = "float16" # Use float16 for RTX 3070
        self.device = "cuda" # Use GPU

        # --- Widgets ---
        # File Selection
        tk.Label(root, text="Video File:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(root, textvariable=self.video_path, width=50).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        tk.Button(root, text="Browse...", command=self.browse_file).grid(row=0, column=2, padx=5, pady=5)

        # API Key
        tk.Label(root, text="Gemini API Key:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(root, textvariable=self.api_key, width=50, show="*").grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Target Language (Changed to Combobox)
        tk.Label(root, text="Target Language:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.language_combobox = ttk.Combobox(root, textvariable=self.target_language, values=LANGUAGES, state="readonly")
        self.language_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.language_combobox.set("English") # Set default value

        # Action Button
        self.generate_button = tk.Button(root, text="Generate Subtitles", command=self.start_processing)
        self.generate_button.grid(row=3, column=0, columnspan=3, padx=5, pady=10)

        # Status/Log Area
        tk.Label(root, text="Status:").grid(row=4, column=0, padx=5, pady=5, sticky="nw")
        self.status_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10, width=70)
        self.status_text.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.status_text.configure(state='disabled') # Make read-only initially

        # SRT Output Area (Optional: could be a save button instead)
        tk.Label(root, text="SRT Output:").grid(row=6, column=0, padx=5, pady=5, sticky="nw")
        self.srt_output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10, width=70)
        self.srt_output_text.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.srt_output_text.configure(state='disabled')

        # Configure grid resizing
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(5, weight=1) # Status area expands
        self.root.grid_rowconfigure(7, weight=1) # SRT area expands

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=(("Video Files", "*.mp4 *.avi *.mkv *.mov"), ("All Files", "*.*"))
        )
        if filepath:
            self.video_path.set(filepath)
            self.log_status(f"Selected file: {filepath}")

    def log_status(self, message):
        """Appends a message to the status text area."""
        self.status_text.configure(state='normal') # Enable writing
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END) # Scroll to the bottom
        self.status_text.configure(state='disabled') # Disable writing
        self.root.update_idletasks() # Force GUI update

    def display_srt(self, srt_content):
        """Displays SRT content in the output area."""
        self.srt_output_text.configure(state='normal')
        self.srt_output_text.delete(1.0, tk.END) # Clear previous content
        self.srt_output_text.insert(tk.END, srt_content)
        self.srt_output_text.configure(state='disabled')

    def save_srt_file(self, srt_content):
        """Asks user where to save the SRT file."""
        if not srt_content:
            self.log_status("No SRT content to save.")
            return

        original_video_path = self.video_path.get()
        if original_video_path:
            base, _ = os.path.splitext(original_video_path)
            default_filename = base + ".srt"
        else:
            default_filename = "subtitles.srt"

        filepath = filedialog.asksaveasfilename(
            title="Save SRT File",
            defaultextension=".srt",
            initialfile=default_filename,
            filetypes=(("SubRip Subtitle", "*.srt"), ("All Files", "*.*"))
        )
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                self.log_status(f"SRT file saved to: {filepath}")
            except Exception as e:
                self.log_status(f"Error saving SRT file: {e}")
                messagebox.showerror("Save Error", f"Failed to save SRT file: {e}")

    def _load_whisper_model_sync(self):
        """Loads the faster-whisper model synchronously, updating status. Returns True on success."""
        if self.whisper_model:
            return True

        self.log_status(f"Loading/Downloading faster-whisper model ('{self.whisper_model_name}')...")
        self.log_status(f"(Device: {self.device}, Compute Type: {self.compute_type})")
        self.log_status("(This might take a while on first run, especially for large models...)")
        try:
            # Load using faster_whisper.WhisperModel
            self.whisper_model = WhisperModel(
                self.whisper_model_name,
                device=self.device,
                compute_type=self.compute_type
            )
            self.log_status("Faster-Whisper model loaded successfully.")
            return True
        except Exception as e:
            self.log_status(f"Error loading faster-whisper model: {e}")
            if "requirement failed: cuda >= 11.0" in str(e):
                 self.log_status("CUDA version requirement not met. Please ensure you have CUDA Toolkit 11.0 or higher installed.")
            elif "Could not load library cudnn64_8.dll" in str(e):
                 self.log_status("cuDNN library not found or incompatible. Ensure cuDNN is installed correctly for your CUDA version.")
            messagebox.showerror("Faster-Whisper Error", f"Failed to load model: {e}\nCheck CUDA/cuDNN setup and compute capability.")
            self.whisper_model = None
            return False

    def process_video_thread(self):
        """Runs the transcription and translation in a separate thread."""
        self.generate_button.config(state=tk.DISABLED)
        self.log_status("--- Starting Process ---")
        self.display_srt("")

        video_file = self.video_path.get()
        api_key_val = self.api_key.get()
        target_lang_val = self.target_language.get()

        if not video_file or not os.path.exists(video_file):
            messagebox.showerror("Error", "Please select a valid video file.")
            self.log_status("Error: Invalid video file selected.")
            self.generate_button.config(state=tk.NORMAL)
            return

        if not api_key_val:
            messagebox.showerror("Error", "Please enter your Gemini API Key.")
            self.log_status("Error: Gemini API Key missing.")
            self.generate_button.config(state=tk.NORMAL)
            return

        if not target_lang_val:
            messagebox.showerror("Error", "Please select a target language.")
            self.log_status("Error: Target language not selected.")
            self.generate_button.config(state=tk.NORMAL)
            return

        if not self._load_whisper_model_sync():
            self.log_status("--- Process Failed (Whisper Model Load) ---")
            self.generate_button.config(state=tk.NORMAL)
            return

        transcribed_segments = transcribe_video(self.whisper_model, video_file, self.log_status)

        if not transcribed_segments:
            self.log_status("--- Process Failed (Transcription) ---")
            self.generate_button.config(state=tk.NORMAL)
            return

        translated_segments = translate_text_gemini(api_key_val, transcribed_segments, target_lang_val, self.log_status)
        if not translated_segments:
            self.log_status("--- Process Failed (Translation) ---")
            self.generate_button.config(state=tk.NORMAL)
            return

        self.log_status("Creating SRT content...") # Removed 'with start time adjustment'
        # Call create_srt_content without the offset argument
        srt_result = create_srt_content(translated_segments)
        self.log_status("SRT content created.")

        self.display_srt(srt_result)
        self.save_srt_file(srt_result)

        self.log_status("--- Process Finished ---")
        self.generate_button.config(state=tk.NORMAL)

    def start_processing(self):
        """Starts the processing in a new thread to avoid freezing the GUI."""
        processing_thread = threading.Thread(target=self.process_video_thread, daemon=True)
        processing_thread.start()

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()

