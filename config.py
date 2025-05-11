"""
Configuration settings and constants for Film Translator Generator.
"""
import os
import torch

# --- Configuration File ---
CONFIG_FILE = "config.json"

# --- Constants ---
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
DEVICES = ["cuda", "cpu"]
COMPUTE_TYPES = {
    "cuda": ["float16", "int8_float16", "int8"],  # Common types for CUDA
    "cpu": ["int8", "float32"]  # Common types for CPU
}
LANGUAGES = [
    "English", "Indonesian", "Spanish", "French", "German",
    "Japanese", "Chinese", "Korean", "Russian", "Portuguese",
    "Italian", "Arabic", "Hindi", "Turkish", "Vietnamese",
    "Thai", "Dutch", "Swedish", "Polish", "Czech", "Greek",
    "Finnish", "Romanian", "Hungarian", "Danish"
]

# Theme settings
THEMES = ["light", "dark"]
ACCENT_COLORS = ["blue", "green", "orange", "purple", "pink"]

# --- Advanced Settings ---
DEFAULT_BATCH_SIZE = 500
OUTPUT_FORMATS = ["srt", "txt", "vtt"]
PREVIEW_OPTIONS = ["On", "Off"]
AUTO_SAVE_OPTIONS = ["On", "Off"]

# --- App Info ---
APP_VERSION = "2.1"
APP_TITLE = f"Film Translator Generator v{APP_VERSION}"
GITHUB_URL = "https://github.com/Fapzarz/FilmTranslatorGenerator"

# --- Gemini API specific settings ---
DEFAULT_GEMINI_TEMPERATURE = 0.2
DEFAULT_GEMINI_TOP_P = 0.95
DEFAULT_GEMINI_TOP_K = 40
DEFAULT_EXTENSIVE_LOGGING = "Off"

def get_default_config():
    """Return the default configuration settings."""
    return {
        'gemini_api_key': '',
        'target_language': 'English',
        'whisper_model': 'large-v2',
        'device': 'cuda' if torch.cuda.is_available() else 'cpu',
        'compute_type': 'float16' if torch.cuda.is_available() else 'int8',
        'theme': 'dark',
        'accent_color': 'blue',
        'batch_size': DEFAULT_BATCH_SIZE,
        'output_format': 'srt',
        'preview': 'On',
        'auto_save': 'Off',
        'gemini_temperature': DEFAULT_GEMINI_TEMPERATURE,
        'gemini_top_p': DEFAULT_GEMINI_TOP_P,
        'gemini_top_k': DEFAULT_GEMINI_TOP_K,
        'extensive_logging': DEFAULT_EXTENSIVE_LOGGING
    } 