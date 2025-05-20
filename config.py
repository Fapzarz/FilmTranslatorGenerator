"""
Configuration settings and constants for Film Translator Generator.
"""
import os
import torch
import json

# --- Configuration File ---
CONFIG_FILE = "config.json"

# --- Constants ---
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
DEVICES = ["cuda", "cpu"]
COMPUTE_TYPES = {
    "cuda": ["float16", "int8_float16", "int8"],  # Common types for CUDA
    "cpu": ["int8", "float32"]  # Common types for CPU
}
TRANSLATION_PROVIDERS = ["Gemini", "OpenAI", "Anthropic", "DeepSeek"]
OPENAI_MODELS = [
    # family GPT-4.1 – flagship terkini (rilis 14 Apr 2025)
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    # family GPT-4o – multimodal (teks-visi-audio)
    "gpt-4o",          # snapshot 2024-11-20 GA
    "gpt-4o-mini",     # snapshot 2024-07-18 GA
    # turbo generasi sebelumnya (masih dijaga kompatibel)
    "gpt-4-turbo-2024-04-09",
    # seri 3.5 yang paling ringan & murah
    "gpt-3.5-turbo"
]

# Anthropic Models list
ANTHROPIC_MODELS = [
    # flagship terbaru hybrid-reasoning
    "claude-3-opus-20240229", # Moved Opus to top as a common high-end choice
    "claude-3-5-sonnet-20240620", # Claude 3.5 Sonnet (replacing the one with 20241022 as it's more standard)
    # The user provided list seems to have future dates, using common existing ones for now.
    "claude-3-7-sonnet-20250219", # User provided, seems like a future model
    "claude-3-5-sonnet-20241022", # User provided, less common naming
    "claude-3-5-haiku-20241022",  # User provided, less common naming
]

# DeepSeek Model (fixed for now)
DEEPSEEK_MODEL = "deepseek-chat"

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
APP_NAME = "Film Translator Generator"
APP_TITLE = f"{APP_NAME} 3.0.0-RC1"
APP_VERSION = "3.0.0-RC1"
GITHUB_URL = "https://github.com/Fapzarz/FilmTranslatorGenerator"

# --- Default Keyboard Shortcuts ---
# Format: "ActionName": "ShortcutString"
# ShortcutString format: e.g., "Control-o", "Alt-F4", "Shift-Return"
# Gunakan nama key seperti yang dikenal Tkinter: 
# https://www.tcl.tk/man/tcl8.6/TkCmd/keysyms.htm (tanpa prefix XK_)
# Modifier: Control, Mod1 (Alt), Shift, Mod2, Mod3, Mod4, Mod5, Lock, Extended
DEFAULT_SHORTCUTS = {
    "add_videos_to_queue": "Control-o",         # O untuk Open/Add
    "remove_selected_video": "Delete",
    "clear_video_queue": "Control-Shift-Delete",
    "start_processing": "Control-p",          # P untuk Process
    "save_project": "Control-s",              # S untuk Save
    "save_project_as": "Control-Shift-S",
    "load_project": "Control-l",              # L untuk Load
    "save_subtitles": "Control-Alt-S",
    "copy_output_to_clipboard": "Control-c",
    "apply_editor_changes": "Control-Return", # Atau Control-E (Execute/Enter)
    "open_advanced_settings": "Control-comma", # Koma sering digunakan untuk settings
    "show_about_dialog": "F1", 
    "exit_application": "Alt-F4" # Hati-hati dengan ini, mungkin lebih baik tidak ada default atau yang tidak mudah terpicu
}

# --- Gemini API specific settings ---
DEFAULT_GEMINI_TEMPERATURE = 0.2
DEFAULT_GEMINI_TOP_P = 0.95
DEFAULT_GEMINI_TOP_K = 40
DEFAULT_EXTENSIVE_LOGGING = "Off"
DEFAULT_TRANSLATION_PROVIDER = "Gemini"
DEFAULT_OPENAI_API_KEY = ""
DEFAULT_ANTHROPIC_API_KEY = ""
DEFAULT_DEEPSEEK_API_KEY = ""
DEFAULT_OPENAI_MODEL = OPENAI_MODELS[0] if OPENAI_MODELS else "gpt-3.5-turbo"
DEFAULT_ANTHROPIC_MODEL = ANTHROPIC_MODELS[0] if ANTHROPIC_MODELS else "claude-3-opus-20240229"

# --- Gemini Models ---
GEMINI_MODELS = ["gemini-2.5-flash-preview-04-17", "gemini-2.5-pro-exp-03-25"]
DEFAULT_GEMINI_MODEL = GEMINI_MODELS[0] # Default to flash model

# --- Subtitle Style Constants ---
SUBTITLE_FONTS = ["Arial", "Helvetica", "Times New Roman", "Verdana", "Tahoma", "Impact"]
SUBTITLE_COLORS = ["white", "yellow", "cyan", "lime", "pink", "lightgray"]
SUBTITLE_SIZES = ["12", "14", "16", "18", "20", "22", "24", "28", "32"]
SUBTITLE_POSITIONS = ["bottom", "middle", "top"] # More descriptive
SUBTITLE_OUTLINE_COLORS = ["black", "white", "darkgray", "red", "blue"]
SUBTITLE_OUTLINE_WIDTHS = ["0", "1", "2", "3", "4"] # '0' for no outline
SUBTITLE_BG_COLORS = ["transparent", "black", "darkgray", "white", "blue"]
SUBTITLE_BG_OPACITY = ["0", "25", "50", "75", "100"] # Percentage based

# --- Default Subtitle Style Settings ---
DEFAULT_SUBTITLE_FONT = SUBTITLE_FONTS[0]
DEFAULT_SUBTITLE_COLOR = SUBTITLE_COLORS[0]
DEFAULT_SUBTITLE_SIZE = SUBTITLE_SIZES[2] # e.g., "16"
DEFAULT_SUBTITLE_POSITION = SUBTITLE_POSITIONS[0]
DEFAULT_SUBTITLE_OUTLINE_COLOR = SUBTITLE_OUTLINE_COLORS[0]
DEFAULT_SUBTITLE_OUTLINE_WIDTH = SUBTITLE_OUTLINE_WIDTHS[1] # e.g., "1"
DEFAULT_SUBTITLE_BG_COLOR = SUBTITLE_BG_COLORS[0]
DEFAULT_SUBTITLE_BG_OPACITY = SUBTITLE_BG_OPACITY[0]

def get_default_config():
    """Return the default configuration settings."""
    return {
        'translation_provider': DEFAULT_TRANSLATION_PROVIDER,
        'gemini_api_key': '',
        'openai_api_key': DEFAULT_OPENAI_API_KEY,
        'anthropic_api_key': DEFAULT_ANTHROPIC_API_KEY,
        'deepseek_api_key': DEFAULT_DEEPSEEK_API_KEY,
        'openai_model': DEFAULT_OPENAI_MODEL,
        'anthropic_model': DEFAULT_ANTHROPIC_MODEL,
        'gemini_model': DEFAULT_GEMINI_MODEL, 
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
        'extensive_logging': DEFAULT_EXTENSIVE_LOGGING,
        'subtitle_font': DEFAULT_SUBTITLE_FONT,
        'subtitle_color': DEFAULT_SUBTITLE_COLOR,
        'subtitle_size': DEFAULT_SUBTITLE_SIZE,
        'subtitle_position': DEFAULT_SUBTITLE_POSITION,
        'subtitle_outline_color': DEFAULT_SUBTITLE_OUTLINE_COLOR,
        'subtitle_outline_width': DEFAULT_SUBTITLE_OUTLINE_WIDTH,
        'subtitle_bg_color': DEFAULT_SUBTITLE_BG_COLOR,
        'subtitle_bg_opacity': DEFAULT_SUBTITLE_BG_OPACITY,
        'shortcuts': DEFAULT_SHORTCUTS.copy(),  # Tambahkan shortcut ke default config
        'keys_encrypted': False  # Flag untuk menandakan belum dienkripsi
    }

def load_config():
    """
    Load configuration from the config file.
    If the file doesn't exist, create it with default values.
    
    Returns:
        dict: Configuration settings
    """
    # Try to import crypto utilities if available
    try:
        from utils.crypto import decrypt_data, is_encrypted
        crypto_available = True
    except ImportError:
        crypto_available = False
    
    config = get_default_config()
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                
            # Check if API keys are encrypted
            keys_encrypted = loaded_config.get('keys_encrypted', False)
            
            # If keys are encrypted and crypto module is available
            if keys_encrypted and crypto_available:
                # Decrypt API keys if present and encrypted
                if loaded_config.get('gemini_api_key'):
                    try:
                        loaded_config['gemini_api_key'] = decrypt_data(loaded_config['gemini_api_key'])
                    except Exception:
                        loaded_config['gemini_api_key'] = ""  # Reset if decryption fails
                        
                if loaded_config.get('openai_api_key'):
                    try:
                        loaded_config['openai_api_key'] = decrypt_data(loaded_config['openai_api_key'])
                    except Exception:
                        loaded_config['openai_api_key'] = ""
                        
                if loaded_config.get('anthropic_api_key'):
                    try:
                        loaded_config['anthropic_api_key'] = decrypt_data(loaded_config['anthropic_api_key'])
                    except Exception:
                        loaded_config['anthropic_api_key'] = ""
                        
                if loaded_config.get('deepseek_api_key'):
                    try:
                        loaded_config['deepseek_api_key'] = decrypt_data(loaded_config['deepseek_api_key'])
                    except Exception:
                        loaded_config['deepseek_api_key'] = ""
                
            # Update config with loaded values
            config.update(loaded_config)
    except Exception as e:
        print(f"Error loading config: {e}")
        save_config(config)  # Reset with default configuration
        
    return config

def save_config(config):
    """
    Save configuration to the config file.
    
    Args:
        config (dict): Configuration settings to save
    """
    # Try to import crypto utilities if available
    try:
        from utils.crypto import encrypt_data, is_encrypted
        crypto_available = True
    except ImportError:
        crypto_available = False
    
    # Create a copy of the config to modify
    config_to_save = config.copy()
    
    # If crypto module is available, encrypt API keys
    if crypto_available:
        # Only encrypt if the keys are not already encrypted
        if not is_encrypted(config_to_save.get('gemini_api_key', "")) and config_to_save.get('gemini_api_key'):
            config_to_save['gemini_api_key'] = encrypt_data(config_to_save['gemini_api_key'])
            
        if not is_encrypted(config_to_save.get('openai_api_key', "")) and config_to_save.get('openai_api_key'):
            config_to_save['openai_api_key'] = encrypt_data(config_to_save['openai_api_key'])
            
        if not is_encrypted(config_to_save.get('anthropic_api_key', "")) and config_to_save.get('anthropic_api_key'):
            config_to_save['anthropic_api_key'] = encrypt_data(config_to_save['anthropic_api_key'])
            
        if not is_encrypted(config_to_save.get('deepseek_api_key', "")) and config_to_save.get('deepseek_api_key'):
            config_to_save['deepseek_api_key'] = encrypt_data(config_to_save['deepseek_api_key'])
        
        # Mark that keys are encrypted
        config_to_save['keys_encrypted'] = True
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_to_save, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}") 