"""
Video and media handling utilities.
"""
import os
import platform
import subprocess
from PIL import Image
import sys
import tempfile
from pathlib import Path
from datetime import timedelta
import json

def play_video_preview(video_path, subtitle_path=None):
    """
    Play a video preview using the system's default player or a specific player.
    
    Args:
        video_path (str): Path to the video file
        subtitle_path (str, optional): Path to the subtitle file
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(video_path):
        return False
    
    try:
        # Try to use VLC for better subtitle support if available
        if subtitle_path and os.path.exists(subtitle_path):
            try:
                if os.name == 'nt':  # Windows
                    subprocess.Popen(['vlc', video_path, f'--sub-file={subtitle_path}'])
                elif sys.platform == 'darwin':  # macOS
                    subprocess.Popen(['open', '-a', 'VLC', video_path, '--args', f'--sub-file={subtitle_path}'])
                else:  # Linux and others
                    subprocess.Popen(['vlc', video_path, f'--sub-file={subtitle_path}'])
                return True
            except FileNotFoundError:
                # VLC not found, fall back to default player
                pass
        
        # Fall back to system default player
        if os.name == 'nt':  # Windows
            os.startfile(video_path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', video_path])
        else:  # Linux and others
            subprocess.Popen(['xdg-open', video_path])
        
        return True
    
    except Exception as e:
        print(f"Error playing video preview: {e}")
        return False

def extract_video_thumbnail(video_path, output_path=None, timestamp=5.0):
    """
    Extract a thumbnail from a video file.
    
    Args:
        video_path (str): Path to the video file
        output_path (str, optional): Path to save the thumbnail
        timestamp (float, optional): Timestamp in seconds to extract the frame
        
    Returns:
        str: Path to the thumbnail image or None if extraction failed
    """
    if not os.path.exists(video_path):
            return None
            
    try:
        if output_path is None:
            # Create temporary file with jpg extension
            temp_handle, output_path = tempfile.mkstemp(suffix='.jpg')
            os.close(temp_handle)  # Close the file handle
        
        cmd = [
            'ffmpeg', 
            '-ss', str(timestamp), 
            '-i', video_path, 
            '-vframes', '1', 
            '-q:v', '2', 
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Check if the thumbnail was created successfully
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        else:
            return None
            
    except Exception as e:
        print(f"Error extracting thumbnail: {e}")
        # Clean up if there was an error
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        return None

def get_video_info(video_path):
    """
    Get basic video information using ffprobe.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        dict: Dictionary with video information including duration, size, codecs, and bitrate.
    """
    if not os.path.exists(video_path):
        return {
        'duration': 'N/A',
        'size': 'N/A',
            'width': 'N/A', 
            'height': 'N/A', 
            'format': 'N/A',
            'video_codec': 'N/A',
            'audio_codec': 'N/A',
            'bitrate': 'N/A'
    }
    
    try:
        # Get general format information (includes duration, bitrate)
        cmd_format = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration,bit_rate', 
            '-of', 'json', 
            video_path
        ]
        result_format = subprocess.run(cmd_format, capture_output=True, text=True, check=False)
        format_data = json.loads(result_format.stdout).get('format', {})
        
        duration_seconds_str = format_data.get('duration', '0')
        duration_seconds = float(duration_seconds_str) if duration_seconds_str else 0
        duration_formatted = str(timedelta(seconds=int(duration_seconds)))
        
        bitrate_str = format_data.get('bit_rate', 'N/A')
        if bitrate_str != 'N/A':
            bitrate_kbps = int(bitrate_str) / 1000
            bitrate_formatted = f"{bitrate_kbps:.0f} kbps"
        else:
            bitrate_formatted = 'N/A'

        # Get video stream information (codec, dimensions)
        cmd_video_stream = [
            'ffprobe', 
            '-v', 'error', 
            '-select_streams', 'v:0', 
            '-show_entries', 'stream=codec_name,width,height', 
            '-of', 'json', 
            video_path
        ]
        result_video_stream = subprocess.run(cmd_video_stream, capture_output=True, text=True, check=False)
        video_stream_data = json.loads(result_video_stream.stdout).get('streams', [{}])[0]
        
        video_codec = video_stream_data.get('codec_name', 'N/A')
        width = video_stream_data.get('width', 'N/A')
        height = video_stream_data.get('height', 'N/A')
        dimensions = f"{width}x{height}" if width != 'N/A' and height != 'N/A' else 'N/A'

        # Get audio stream information (codec)
        cmd_audio_stream = [
            'ffprobe', 
            '-v', 'error', 
            '-select_streams', 'a:0', 
            '-show_entries', 'stream=codec_name', 
            '-of', 'json', 
            video_path
        ]
        result_audio_stream = subprocess.run(cmd_audio_stream, capture_output=True, text=True, check=False)
        # Handle cases where there might be no audio stream or ffprobe output is empty/malformed
        try:
            audio_stream_data = json.loads(result_audio_stream.stdout).get('streams', [{}])[0]
            audio_codec = audio_stream_data.get('codec_name', 'N/A')
        except (json.JSONDecodeError, IndexError):
            audio_codec = 'N/A' # Default if audio stream info is missing or problematic

        # Get file size
        file_size_bytes = os.path.getsize(video_path)
        if file_size_bytes < 1024 * 1024:  # Less than 1MB
            file_size = f"{file_size_bytes / 1024:.1f} KB"
        else:
            file_size = f"{file_size_bytes / (1024 * 1024):.1f} MB"
        
        # Get file format/extension
        file_extension = os.path.splitext(video_path)[1].lower()
        
        return {
            'duration': duration_formatted,
            'duration_seconds': duration_seconds,
            'size': file_size,
            'dimensions': dimensions,
            'format': file_extension[1:],  # Remove the dot
            'video_codec': video_codec.upper(), # Standardize to uppercase
            'audio_codec': audio_codec.upper(), # Standardize to uppercase
            'bitrate': bitrate_formatted
        }
    
    except Exception as e:
        # Fallback for any error during ffprobe execution or parsing
        file_size_bytes = os.path.getsize(video_path)
        if file_size_bytes < 1024 * 1024:
            file_size = f"{file_size_bytes / 1024:.1f} KB"
        else:
            file_size = f"{file_size_bytes / (1024 * 1024):.1f} MB"

        return {
            'duration': 'Error', 
            'size': file_size, 
            'dimensions': 'Error', 
            'video_codec': 'Error',
            'audio_codec': 'Error',
            'bitrate': 'Error',
            'format': os.path.splitext(video_path)[1].lower()[1:],
            'error': str(e)
        }

def convert_video_format(input_path, output_format, output_path=None):
    """
    Convert a video to a different format.
    
    Args:
        input_path (str): Path to the input video file
        output_format (str): Target format (e.g., 'mp4', 'webm')
        output_path (str, optional): Path to save the converted video
        
    Returns:
        str: Path to the converted video or None if conversion failed
    """
    if not os.path.exists(input_path):
        return None
    
    try:
        if output_path is None:
            # Create output path with new extension
            input_dir = os.path.dirname(input_path)
            input_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(input_dir, f"{input_name}.{output_format}")
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',  # Video codec
            '-c:a', 'aac',  # Audio codec
            '-strict', 'experimental',
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Check if the conversion was successful
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        else:
            return None
    
    except Exception as e:
        print(f"Error converting video: {e}")
        # Clean up if there was an error
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        return None

def diagnose_video_playback(video_path):
    """
    Run diagnostics on a video file to check if it's playable.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        dict: Diagnostic information about the video
    """
    result = {
        'exists': False,
        'readable': False,
        'valid_format': False,
        'has_video_stream': False,
        'has_audio_stream': False,
        'playable': False,
        'issues': []
    }
    
    # Check if file exists
    if not os.path.exists(video_path):
        result['issues'].append("File does not exist")
        return result
    
    result['exists'] = True
    
    # Check if file is readable
    try:
        with open(video_path, 'rb') as f:
            f.read(1024)  # Try to read first 1KB
            result['readable'] = True
    except Exception as e:
        result['issues'].append(f"File is not readable: {e}")
        return result
    
    # Check format using ffprobe
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_format',
            '-show_streams',
            '-print_format', 'json',
            video_path
        ]
        probe_result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if probe_result.returncode != 0:
            result['issues'].append(f"ffprobe failed: {probe_result.stderr}")
            return result
        
        import json
        info = json.loads(probe_result.stdout)
        
        # Check if format is recognized
        if 'format' in info:
            result['valid_format'] = True
            result['format_info'] = info['format'].get('format_name', 'unknown')
        else:
            result['issues'].append("Format not recognized")
        
        # Check for video and audio streams
        if 'streams' in info:
            for stream in info['streams']:
                if stream.get('codec_type') == 'video':
                    result['has_video_stream'] = True
                    result['video_codec'] = stream.get('codec_name', 'unknown')
                    result['video_resolution'] = f"{stream.get('width', '?')}x{stream.get('height', '?')}"
                
                if stream.get('codec_type') == 'audio':
                    result['has_audio_stream'] = True
                    result['audio_codec'] = stream.get('codec_name', 'unknown')
            
            if not result['has_video_stream']:
                result['issues'].append("No video stream found")
        else:
            result['issues'].append("No streams information found")
        
        # If we have valid format and video stream, it should be playable
        if result['valid_format'] and result['has_video_stream']:
            result['playable'] = True
        
    except Exception as e:
        result['issues'].append(f"Error analyzing video: {e}")
    
    return result 