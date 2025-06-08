"""
Utility functions for input validation across the application.
"""
import os
import re
import json
from pathlib import Path

# Validasi file dan direktori
def validate_path_exists(path):
    """
    Validate that a path exists.
    
    Args:
        path: Path to validate
        
    Returns:
        Tuple of (boolean is_valid, string error_message)
    """
    if not path:
        return False, "Path cannot be empty"
    
    try:
        path_obj = Path(path)
        if path_obj.exists():
            return True, ""
        return False, f"Path does not exist: {path}"
    except Exception as e:
        return False, f"Invalid path format: {e}"

def validate_local_model_directory(path):
    """Validate local translation model directory."""
    valid, error = validate_path_exists(path)
    if not valid:
        return valid, error
    required_file = Path(path) / "config.json"
    if not required_file.exists():
        return False, "Model directory must contain config.json"
    return True, ""

def validate_file_extension(filepath, allowed_extensions):
    """
    Validate that a file has an allowed extension.
    
    Args:
        filepath: Path to validate
        allowed_extensions: List of allowed extensions (e.g., ['.mp4', '.avi'])
        
    Returns:
        Tuple of (boolean is_valid, string error_message)
    """
    if not filepath:
        return False, "Filepath cannot be empty"
    
    try:
        path_obj = Path(filepath)
        extension = path_obj.suffix.lower()
        if extension in allowed_extensions:
            return True, ""
        return False, f"File extension {extension} is not supported. Allowed: {', '.join(allowed_extensions)}"
    except Exception as e:
        return False, f"Invalid filepath format: {e}"

# Validasi API Keys
def validate_api_key_format(api_key, provider):
    """
    Basic format validation for API keys by provider.
    
    Args:
        api_key: API key to validate
        provider: Provider name (gemini, openai, anthropic, deepseek)
        
    Returns:
        Tuple of (boolean is_valid, string error_message)
    """
    if not api_key:
        return False, "API key cannot be empty"
    
    # Known API key patterns by provider
    patterns = {
        'gemini': r'^AIza[0-9A-Za-z_-]{35}$',  # Google API key pattern
        'openai': r'^sk-[0-9A-Za-z]{48}$',     # OpenAI API key pattern
        'anthropic': r'^sk-ant-[0-9A-Za-z]{48}$', # Anthropic API key pattern
        'deepseek': r'^sk-[0-9A-Za-z]{40,}$'   # DeepSeek pattern (less specific)
    }
    
    # Use provider pattern if available, otherwise general check
    if provider.lower() in patterns:
        pattern = patterns[provider.lower()]
        if re.match(pattern, api_key):
            return True, ""
        return False, f"Invalid {provider} API key format"
    
    # General check for API keys - at least 20 chars with special chars
    if len(api_key) < 20:
        return False, "API key too short"
    
    if not re.search(r'[0-9A-Za-z_-]', api_key):
        return False, "API key must contain alphanumeric characters"
    
    return True, ""

# Validasi nilai parameter
def validate_float_range(value, min_value, max_value, param_name):
    """
    Validate that a float is within a specified range.
    
    Args:
        value: Float value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        param_name: Name of parameter (for error message)
        
    Returns:
        Tuple of (boolean is_valid, string error_message)
    """
    try:
        float_value = float(value)
        if min_value <= float_value <= max_value:
            return True, ""
        return False, f"{param_name} must be between {min_value} and {max_value}"
    except ValueError:
        return False, f"{param_name} must be a valid number"

def validate_int_range(value, min_value, max_value, param_name):
    """
    Validate that an integer is within a specified range.
    
    Args:
        value: Integer value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        param_name: Name of parameter (for error message)
        
    Returns:
        Tuple of (boolean is_valid, string error_message)
    """
    try:
        int_value = int(value)
        if min_value <= int_value <= max_value:
            return True, ""
        return False, f"{param_name} must be between {min_value} and {max_value}"
    except ValueError:
        return False, f"{param_name} must be a valid integer"

# Validasi JSON dan Project
def validate_json_structure(json_data, required_fields):
    """
    Validate that a JSON object has all required fields.
    
    Args:
        json_data: JSON object to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (boolean is_valid, string error_message)
    """
    if not json_data:
        return False, "Empty JSON data"
    
    missing_fields = []
    for field in required_fields:
        if field not in json_data:
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, ""

def validate_project_file(filepath):
    """
    Validate that a project file has the correct structure.
    
    Args:
        filepath: Path to project file
        
    Returns:
        Tuple of (boolean is_valid, string error_message)
    """
    # Check path exists
    valid, error = validate_path_exists(filepath)
    if not valid:
        return valid, error
    
    # Check extension
    valid, error = validate_file_extension(filepath, ['.ftgproj'])
    if not valid:
        return valid, error
    
    # Check file can be parsed as JSON
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
            
        # Check required fields
        required_fields = ['video_queue', 'processed_file_data', 'settings']
        valid, error = validate_json_structure(project_data, required_fields)
        if not valid:
            return valid, error
            
        # Check settings has required fields
        required_settings = ['target_language', 'whisper_model', 'device']
        valid, error = validate_json_structure(project_data.get('settings', {}), required_settings)
        if not valid:
            return valid, f"Invalid settings structure: {error}"
            
        return True, ""
    except json.JSONDecodeError:
        return False, "File is not valid JSON"
    except Exception as e:
        return False, f"Error validating project file: {e}"

# Validasi Video
def validate_video_file(filepath):
    """
    Validate that a file is a supported video format.
    
    Args:
        filepath: Path to video file
        
    Returns:
        Tuple of (boolean is_valid, string error_message)
    """
    # Supported video extensions
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']
    
    # Check path exists
    valid, error = validate_path_exists(filepath)
    if not valid:
        return valid, error
    
    # Check extension
    valid, error = validate_file_extension(filepath, video_extensions)
    if not valid:
        return valid, error
    
    # Basic file size check
    try:
        size = os.path.getsize(filepath)
        if size < 1024:  # Smaller than 1KB is suspicious for a video
            return False, "File is too small to be a valid video"
        return True, ""
    except Exception as e:
        return False, f"Error checking video file: {e}" 