"""
Text translation functionality using Google Gemini API.
"""
import re
import google.generativeai as genai
import openai # Import OpenAI library
import anthropic # Import Anthropic library
from config import (
    DEFAULT_BATCH_SIZE, 
    OPENAI_MODELS, 
    ANTHROPIC_MODELS, # Added ANTHROPIC_MODELS
    DEEPSEEK_MODEL # Added DEEPSEEK_MODEL
)

# Placeholder for API key storage/retrieval if not passed directly
# For now, API keys are expected to be passed in provider_config

# --- API Key Validation Functions ---

def validate_gemini_key(api_key, status_callback):
    """Validates the Gemini API key by trying to list models."""
    if not api_key:
        return False, "API Key is empty."
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models()]
        if not models: # Should ideally return some models
            return False, "Key configured, but no models found (check permissions/key)."
        status_callback("Gemini API Key appears valid (models listed).", "VERBOSE")
        return True, "Valid"
    except Exception as e:
        error_message = f"Gemini Key Validation Error: {str(e)}"
        status_callback(error_message, "ERROR")
        # More specific error checking can be added here if needed
        if "API_KEY_INVALID" in str(e) or "PERMISSION_DENIED" in str(e) or "authentication" in str(e).lower():
            return False, "Invalid API Key."
        return False, f"Validation Error: {str(e)[:100]}" # Truncate long errors

def validate_openai_key(api_key, status_callback):
    """Validates the OpenAI API key by trying to list models."""
    if not api_key:
        return False, "API Key is empty."
    try:
        client = openai.OpenAI(api_key=api_key)
        client.models.list() # This call will fail if the key is invalid
        status_callback("OpenAI API Key appears valid (models listed).", "VERBOSE")
        return True, "Valid"
    except openai.AuthenticationError:
        status_callback("OpenAI AuthenticationError: Invalid API Key.", "ERROR")
        return False, "Invalid API Key."
    except openai.APIConnectionError as e:
        status_callback(f"OpenAI APIConnectionError: {e}", "ERROR")
        return False, "Connection Error."
    except openai.RateLimitError as e:
        status_callback(f"OpenAI RateLimitError: {e}", "ERROR")
        return False, "Rate Limit Exceeded." # Key might be valid but hitting limits
    except openai.APIError as e: # Catch other OpenAI API errors
        status_callback(f"OpenAI APIError: {e}", "ERROR")
        return False, f"API Error: {str(e)[:100]}"
    except Exception as e: # Catch any other unexpected errors
        error_message = f"OpenAI Key Validation Error: {str(e)}"
        status_callback(error_message, "ERROR")
        return False, f"Validation Error: {str(e)[:100]}"

def validate_anthropic_key(api_key, status_callback):
    """Validates the Anthropic API key by a lightweight operation (e.g., count_tokens)."""
    if not api_key:
        return False, "API Key is empty."
    try:
        client = anthropic.Anthropic(api_key=api_key)
        # Using count_tokens as a very lightweight call to check client initialization and basic auth
        client.count_tokens("test") 
        status_callback("Anthropic API Key appears valid (client initialized).", "VERBOSE")
        return True, "Valid"
    except anthropic.AuthenticationError:
        status_callback("Anthropic AuthenticationError: Invalid API Key.", "ERROR")
        return False, "Invalid API Key."
    except anthropic.APIConnectionError as e:
        status_callback(f"Anthropic APIConnectionError: {e}", "ERROR")
        return False, "Connection Error."
    except anthropic.RateLimitError as e:
        status_callback(f"Anthropic RateLimitError: {e}", "ERROR")
        return False, "Rate Limit Exceeded."
    except anthropic.APIError as e: # Catch other Anthropic API errors
        status_callback(f"Anthropic APIError: {e}", "ERROR")
        return False, f"API Error: {str(e)[:100]}"
    except Exception as e: # Catch any other unexpected errors
        error_message = f"Anthropic Key Validation Error: {str(e)}"
        status_callback(error_message, "ERROR")
        return False, f"Validation Error: {str(e)[:100]}"

# --- End API Key Validation Functions ---

def _translate_with_gemini(gemini_api_key, gemini_model_name, text_segments, target_language, status_callback, batch_size, gemini_temperature, gemini_top_p, gemini_top_k):
    """Translates text segments using Gemini API."""
    if not gemini_api_key:
        status_callback("Error: Gemini API Key is missing.", level="ERROR")
        return None
    try:
        genai.configure(api_key=gemini_api_key)
        # Consider making model name configurable if more Gemini models are supported
        model = genai.GenerativeModel(gemini_model_name)
        generation_config = genai.types.GenerationConfig(
            temperature=gemini_temperature,
            top_p=gemini_top_p,
            top_k=gemini_top_k
        )
        status_callback(f"Configured Gemini. Translating to {target_language}...", level="INFO")
    except Exception as e:
        status_callback(f"Error configuring Gemini: {e}", level="ERROR")
        return None

    translated_segments = []
    total_segments = len(text_segments)
    num_batches = (total_segments + batch_size - 1) // batch_size
    mismatch_tolerance = 10

    for i in range(0, total_segments, batch_size):
        batch_num = (i // batch_size) + 1
        status_callback(f"Processing batch {batch_num}/{num_batches} with Gemini... ", level="INFO")
        batch = text_segments[i:i+batch_size]
        if not batch:
            continue

        prompt_lines = [
            f"Translate the following numbered dialogue segments into {target_language}."
            f"IMPORTANT: You must ONLY translate the text content. Do not modify any numbers, timestamps, or formatting."
            f"Output ONLY the raw translated text for each number, starting directly with number 1."
            f"Do NOT include any introductory phrases, explanations, greetings, timestamps, or any text other than the numbered translations."
            f"Example: If input is '1. Hello\n2. Goodbye', output should be '1. Halo\n2. Selamat tinggal' (for Indonesian) and nothing else.\n"
        ]
        for j, segment in enumerate(batch):
            cleaned_text = segment['text'].strip().replace('\n', ' ')
            prompt_lines.append(f"{j+1}. {cleaned_text}")
        prompt_lines.append("\nYour entire response must be ONLY the numbered list of translations with NO timestamps or formatting.")
        batch_prompt = "\n".join(prompt_lines)

        try:
            status_callback(f"VERBOSE: Sending prompt to Gemini for batch {batch_num}:\n{batch_prompt[:200]}...", level="VERBOSE")
            response = model.generate_content(batch_prompt, generation_config=generation_config)
            response_text = response.text.strip()
            status_callback(f"VERBOSE: Received response from Gemini for batch {batch_num}:\n{response_text[:200]}...", level="VERBOSE")

            translated_texts = response_text.split('\n')
            parsed_translations = []
            for line in translated_texts:
                # More strict cleaning to remove any potential timestamps that might have been generated
                cleaned_line = re.sub(r"^\s*\d+[\.\)]\s*", "", line).strip()
                # Remove any timestamp-like patterns that might have been included
                cleaned_line = re.sub(r"\d{1,2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2},\d{3}", "", cleaned_line).strip()
                if cleaned_line: 
                    parsed_translations.append(cleaned_line)

            expected_count = len(batch)
            actual_count = len(parsed_translations)
            
            if not (expected_count - mismatch_tolerance <= actual_count <= expected_count + mismatch_tolerance):
                status_callback(f"Warning: Gemini Batch {batch_num} - Mismatch outside tolerance (expected {expected_count}, got {actual_count}). Falling back to individual.", level="WARNING")
                raise ValueError("Batch translation mismatch, fallback needed") # Trigger fallback in except block
            else:
                # This block executes if the mismatch is within tolerance or there is no mismatch
                if actual_count != expected_count:
                    status_callback(f"Warning: Gemini Batch {batch_num} - Slight mismatch (expected {expected_count}, got {actual_count}). Proceeding with tolerance.", level="WARNING")
                
                count_to_use = min(expected_count, actual_count)
                for j in range(count_to_use):
                    # Preserve the original timestamps exactly
                    translated_segments.append({
                        'start': batch[j]['start'],
                        'end': batch[j]['end'],
                        'text': parsed_translations[j]
                    })
                status_callback(f"Gemini Batch {batch_num}/{num_batches} processed. Got {actual_count}/{expected_count} segments.", level="INFO")

        except Exception as e_batch:
            status_callback(f"Error/Fallback for Gemini batch {batch_num}: {e_batch}. Attempting individual translation...", level="WARNING")
            for k, segment_item in enumerate(batch):
                try:
                    fallback_prompt = (
                        f"Translate the following dialogue segment into {target_language}. "
                        f"IMPORTANT: Translate ONLY the text content. Do not modify any formatting or add timestamps."
                        f"Output ONLY the raw translated text. Do NOT include any introductory phrases, explanations, or any text other than the translation itself.\n\n"
                        f"Dialogue: {segment_item['text'].strip()}"
                    )
                    status_callback(f"VERBOSE: Sending fallback prompt for segment {i+k+1} to Gemini...", level="VERBOSE")
                    fallback_response = model.generate_content(fallback_prompt, generation_config=generation_config)
                    fallback_text = fallback_response.text.strip()
                    # Clean any potential timestamp formatting that might have been added
                    fallback_text = re.sub(r"\d{1,2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2},\d{3}", "", fallback_text).strip()
                    status_callback(f"VERBOSE: Received fallback response for segment {i+k+1} from Gemini.", level="VERBOSE")
                    
                    # Preserve the original timestamps exactly
                    translated_segments.append({
                        'start': segment_item['start'], 
                        'end': segment_item['end'], 
                        'text': fallback_text
                    })
                except Exception as e_fallback:
                    status_callback(f"Error translating segment {i+k+1} individually with Gemini: {e_fallback}. Skipping.", level="ERROR")
                    translated_segments.append({
                        'start': segment_item['start'], 
                        'end': segment_item['end'], 
                        'text': f"[Translation Error] {segment_item['text']}"
                    })

    status_callback("Gemini translation finished.", level="INFO")
    if len(translated_segments) != total_segments:
        status_callback(f"Warning: Gemini final segment count mismatch (expected {total_segments}, got {len(translated_segments)}).", level="WARNING")
        # Basic padding logic here if needed
    return translated_segments

def _translate_with_openai(openai_api_key, openai_model_name, text_segments, target_language, status_callback, batch_size_setting):
    """Translates text segments using OpenAI API, segment by segment."""
    if not openai_api_key:
        status_callback("Error: OpenAI API Key is missing.", level="ERROR")
        return None

    try:
        client = openai.OpenAI(api_key=openai_api_key)
        status_callback(f"Configured OpenAI with model: {openai_model_name}. Translating to {target_language}...", level="INFO")
    except Exception as e:
        status_callback(f"Error configuring OpenAI client: {e}", level="ERROR")
        return None

    translated_segments = []
    total_segments = len(text_segments)

    for i, segment in enumerate(text_segments):
        status_callback(f"Processing segment {i+1}/{total_segments} with OpenAI...", level="INFO")
        text_to_translate = segment['text'].strip()
        if not text_to_translate:
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': '' # Empty input, empty output
            })
            continue

        # OpenAI prompt might need adjustment for best results.
        # Using a simple direct translation prompt for now.
        # System prompt could define the role and strict output format.
        system_prompt = f"You are a helpful assistant that translates text into {target_language}. Output ONLY the translated text, without any additional explanations, introductions, or conversational phrases."
        user_prompt = f"Translate the following text into {target_language}:\n\n{text_to_translate}"
        
        status_callback(f"VERBOSE: Sending prompt to OpenAI for segment {i+1}: {user_prompt[:100]}...", level="VERBOSE")

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                model=openai_model_name,
                temperature=0.1, # Lower temperature for more deterministic translation
                # max_tokens can be set if needed, but for short segments, it might not be critical
            )
            translated_text = chat_completion.choices[0].message.content.strip()
            status_callback(f"VERBOSE: Received response from OpenAI for segment {i+1}: {translated_text[:100]}...", level="VERBOSE")
            
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': translated_text
            })

        except openai.APIError as e_api:
            status_callback(f"OpenAI API Error on segment {i+1}: {e_api}. Skipping.", level="ERROR")
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': f"[OpenAI API Error] {segment['text']}"
            })
        except Exception as e_generic:
            status_callback(f"Generic error with OpenAI on segment {i+1}: {e_generic}. Skipping.", level="ERROR")
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': f"[OpenAI Translation Error] {segment['text']}"
            })
            
    status_callback("OpenAI translation finished.", level="INFO")
    return translated_segments

def _translate_with_deepseek(deepseek_api_key, text_segments, target_language, status_callback, batch_size_setting):
    """Translates text segments using DeepSeek API."""
    if not deepseek_api_key:
        status_callback("Error: DeepSeek API Key is missing.", level="ERROR")
        return None
    
    try:
        from deepseek import DeepSeekAI  # Import DeepSeek client
        client = DeepSeekAI(api_key=deepseek_api_key)
        status_callback(f"Configured DeepSeek. Translating to {target_language}...", level="INFO")
    except ImportError:
        status_callback("Error: DeepSeek Python package not found. Please install with 'pip install deepseek'", level="ERROR")
        return None
    except Exception as e:
        status_callback(f"Error configuring DeepSeek client: {e}", level="ERROR")
        return None
    
    translated_segments = []
    total_segments = len(text_segments)
    
    for i, segment in enumerate(text_segments):
        status_callback(f"Processing segment {i+1}/{total_segments} with DeepSeek...", level="INFO")
        text_to_translate = segment['text'].strip()
        if not text_to_translate:
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': ''  # Empty input, empty output
            })
            continue
        
        system_prompt = f"You are a helpful assistant that translates text into {target_language}. Output ONLY the translated text, without any additional explanations, introductions, or conversational phrases."
        user_prompt = f"Translate the following text into {target_language}:\n\n{text_to_translate}"
        
        status_callback(f"VERBOSE: Sending prompt to DeepSeek for segment {i+1}: {user_prompt[:100]}...", level="VERBOSE")
        
        try:
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,  # Using the default model from config
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1024
            )
            
            translated_text = response.choices[0].message.content.strip()
            status_callback(f"VERBOSE: Received response from DeepSeek for segment {i+1}: {translated_text[:100]}...", level="VERBOSE")
            
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': translated_text
            })
            
        except Exception as e:
            status_callback(f"Error translating segment {i+1} with DeepSeek: {e}", level="ERROR")
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': f"[Translation Error] {text_to_translate}"
            })
    
    status_callback("DeepSeek translation finished.", level="INFO")
    return translated_segments

def _translate_with_anthropic(anthropic_api_key, anthropic_model_name, text_segments, target_language, status_callback, batch_size_setting):
    """Translates text segments using Anthropic API."""
    if not anthropic_api_key:
        status_callback("Error: Anthropic API Key is missing.", level="ERROR")
        return None
    
    try:
        client = anthropic.Anthropic(api_key=anthropic_api_key)
        status_callback(f"Configured Anthropic with model: {anthropic_model_name}. Translating to {target_language}...", level="INFO")
    except Exception as e:
        status_callback(f"Error configuring Anthropic client: {e}", level="ERROR")
        return None
    
    translated_segments = []
    total_segments = len(text_segments)
    
    for i, segment in enumerate(text_segments):
        status_callback(f"Processing segment {i+1}/{total_segments} with Anthropic...", level="INFO")
        text_to_translate = segment['text'].strip()
        if not text_to_translate:
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': ''  # Empty input, empty output
            })
            continue
        
        system_prompt = f"You are a translator that translates text into {target_language}. Output ONLY the translated text."
        user_prompt = f"Translate the following text into {target_language}:\n\n{text_to_translate}"
        
        status_callback(f"VERBOSE: Sending prompt to Anthropic for segment {i+1}: {user_prompt[:100]}...", level="VERBOSE")
        
        try:
            message = client.messages.create(
                model=anthropic_model_name,
                max_tokens=1024,
                temperature=0.2,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            translated_text = message.content[0].text.strip()
            status_callback(f"VERBOSE: Received response from Anthropic for segment {i+1}: {translated_text[:100]}...", level="VERBOSE")
            
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': translated_text
            })
            
        except Exception as e:
            status_callback(f"Error translating segment {i+1} with Anthropic: {e}", level="ERROR")
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': f"[Translation Error] {text_to_translate}"
            })
    
    status_callback("Anthropic translation finished.", level="INFO")
    return translated_segments 

def translate_text(provider_config, text_segments, target_language, status_callback=None, batch_size_setting=None):
    """
    Translates the given text segments using the specified provider.
    
    Args:
        provider_config: Dictionary with provider settings
        text_segments: List of segments with 'start', 'end', and 'text' keys
        target_language: Language to translate to
        status_callback: Function to call for status updates
        batch_size_setting: Number of segments to process at once
    
    Returns:
        List of translated segments with original timestamps, or None on failure
    """
    if not callable(status_callback):
        # Create a no-op callback if none provided
        status_callback = lambda msg, level="INFO": None
    
    if not text_segments:
        status_callback("No segments to translate.", "WARNING")
        return None
    
    # Set default batch size if not provided
    batch_size = batch_size_setting or DEFAULT_BATCH_SIZE
    provider_name = provider_config.get('name')
    
    try:
        if provider_name == "Gemini":
            gemini_api_key = provider_config.get('gemini_api_key')
            gemini_model = provider_config.get('gemini_model')
            gemini_temperature = float(provider_config.get('gemini_temperature', 0.0))
            gemini_top_p = float(provider_config.get('gemini_top_p', 1.0))
            gemini_top_k = int(provider_config.get('gemini_top_k', 40))
            
            if not gemini_api_key:
                status_callback("Error: Gemini API key is missing.", "ERROR")
                return None
            
            status_callback(f"Starting translation with Gemini model '{gemini_model}' to {target_language}...", "INFO")
            return _translate_with_gemini(
                gemini_api_key, gemini_model, text_segments, target_language, 
                status_callback, batch_size, gemini_temperature, gemini_top_p, gemini_top_k
            )
        
        elif provider_name == "OpenAI":
            openai_api_key = provider_config.get('openai_api_key')
            openai_model = provider_config.get('openai_model')
            
            if not openai_api_key:
                status_callback("Error: OpenAI API key is missing.", "ERROR")
                return None
            
            status_callback(f"Starting translation with OpenAI model '{openai_model}' to {target_language}...", "INFO")
            return _translate_with_openai(
                openai_api_key, openai_model, text_segments, target_language, 
                status_callback, batch_size
            )
        
        elif provider_name == "Anthropic":
            anthropic_api_key = provider_config.get('anthropic_api_key')
            anthropic_model = provider_config.get('anthropic_model')
            
            if not anthropic_api_key:
                status_callback("Error: Anthropic API key is missing.", "ERROR")
                return None
            
            status_callback(f"Starting translation with Anthropic model '{anthropic_model}' to {target_language}...", "INFO")
            return _translate_with_anthropic(
                anthropic_api_key, anthropic_model, text_segments, target_language, 
                status_callback, batch_size
            )
        
        elif provider_name == "DeepSeek":
            deepseek_api_key = provider_config.get('deepseek_api_key')
            
            if not deepseek_api_key:
                status_callback("Error: DeepSeek API key is missing.", "ERROR")
                return None
            
            status_callback(f"Starting translation with DeepSeek model to {target_language}...", "INFO")
            return _translate_with_deepseek(
                deepseek_api_key, text_segments, target_language, 
                status_callback, batch_size
            )
        
        elif provider_name == "Local Model":
            status_callback("Local model translation not yet implemented.", "ERROR")
            return None
        
        else:
            status_callback(f"Unknown translation provider: {provider_name}", "ERROR")
            return None
    
    except Exception as e:
        status_callback(f"Translation error with {provider_name}: {e}", "ERROR")
        return None 