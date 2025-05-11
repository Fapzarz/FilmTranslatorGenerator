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
APP_VERSION = "2.1"
APP_TITLE = "Film Translator Generator"
GITHUB_URL = "https://github.com/Fapzarz/FilmTranslatorGenerator"

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
        # DeepSeek model is fixed for now, so no 'deepseek_model' entry here for user selection
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