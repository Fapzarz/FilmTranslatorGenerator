"""
Audio transcription functionality using Faster-Whisper.
"""
import time
from faster_whisper import WhisperModel

def transcribe_video(model_instance, video_path, status_callback):
    """Transcribes the video file using the provided faster-whisper model instance (VAD disabled)."""
    if not model_instance:
        status_callback("Error: Faster-Whisper model instance not provided.")
        return None

    try:
        status_callback(f"Starting transcription (faster-whisper, VAD disabled) for: {video_path.split('/')[-1].split('\\')[-1]}...")
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

def load_whisper_model(model_name, device, compute_type, status_callback=None):
    """Load a Whisper model with the specified settings."""
    try:
        if status_callback:
            status_callback(f"Loading/Downloading faster-whisper model ('{model_name}')...")
            status_callback(f"(Device: {device}, Compute Type: {compute_type})")
            status_callback("(This might take a while on first run or model change...)")
            
        model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type
        )
        
        if status_callback:
            status_callback("Faster-Whisper model loaded successfully.")
        
        return model
    except Exception as e:
        error_msg = f"Error loading faster-whisper model: {e}"
        if status_callback:
            status_callback(error_msg)
            if "requirement failed: cuda >= 11.0" in str(e):
                status_callback("CUDA version requirement not met. Please ensure you have CUDA Toolkit 11.0 or higher installed.")
            elif "Could not load library cudnn64_8.dll" in str(e):
                status_callback("cuDNN library not found or incompatible. Ensure cuDNN is installed correctly for your CUDA version.")
        
        raise RuntimeError(error_msg) from e 