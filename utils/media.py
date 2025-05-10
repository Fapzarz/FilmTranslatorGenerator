"""
Video and media handling utilities.
"""
import os
import platform
import subprocess
from PIL import Image, ImageTk

def play_video_preview(video_path, callback=None):
    """Play video preview using system default player."""
    try:
        if platform.system() == 'Windows':
            os.startfile(video_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', video_path))
        else:  # Linux
            subprocess.call(('xdg-open', video_path))
        if callback:
            callback(f"Playing video preview: {os.path.basename(video_path)}")
        return True
    except Exception as e:
        if callback:
            callback(f"Error playing video preview: {e}")
        return False

def extract_video_thumbnail(video_path, size=(300, 170)):
    """Extract thumbnail from video file using OpenCV."""
    try:
        import cv2
        # Open the video file
        video = cv2.VideoCapture(video_path)
        
        # Check if video opened successfully
        if not video.isOpened():
            return None
            
        # Read the first frame
        success, frame = video.read()
        if not success:
            return None
            
        # Jump to 10% of the video duration for a better thumbnail
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames > 0:
            target_frame = int(total_frames * 0.1)  # 10% into the video
            video.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            success, frame = video.read()
            if not success:
                # If seeking failed, reopen and get first frame
                video = cv2.VideoCapture(video_path)
                success, frame = video.read()
        
        # Close the video file
        video.release()
        
        if not success:
            return None
            
        # Convert from BGR to RGB (PIL uses RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize the frame
        frame_resized = cv2.resize(frame_rgb, size)
        
        # Convert to PIL Image
        img = Image.fromarray(frame_resized)
        
        return ImageTk.PhotoImage(img)
    except Exception as e:
        # Silent failure - just return None
        return None

def get_video_info(video_path):
    """Get video information such as duration and file size."""
    info = {
        'duration': 'N/A',
        'duration_seconds': 0,
        'size': 'N/A',
        'size_bytes': 0,
        'size_mb': 0
    }
    
    try:
        # Get file size
        file_size_bytes = os.path.getsize(video_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        info['size_bytes'] = file_size_bytes
        info['size_mb'] = file_size_mb
        info['size'] = f"{file_size_mb:.2f} MB"
        
        # Get video duration using OpenCV
        import cv2
        video = cv2.VideoCapture(video_path)
        if video.isOpened():
            # Get frame count and FPS to calculate duration
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = video.get(cv2.CAP_PROP_FPS)
            
            if frame_count > 0 and fps > 0:
                duration_seconds = frame_count / fps
                info['duration_seconds'] = duration_seconds
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                info['duration'] = f"{minutes}m {seconds}s"
            
            video.release()
    except Exception as e:
        # Silent failure - leave info as-is
        pass
    
    return info 