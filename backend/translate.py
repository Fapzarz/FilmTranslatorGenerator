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

def _translate_with_gemini(gemini_api_key, text_segments, target_language, status_callback, batch_size, gemini_temperature, gemini_top_p, gemini_top_k):
    """Translates text segments using Gemini API."""
    if not gemini_api_key:
        status_callback("Error: Gemini API Key is missing.", level="ERROR")
        return None
    try:
        genai.configure(api_key=gemini_api_key)
        # Consider making model name configurable if more Gemini models are supported
        model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
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

def _translate_with_deepseek(deepseek_api_key, deepseek_model_name, text_segments, target_language, status_callback, batch_size_setting):
    """Translates text segments using DeepSeek API (via OpenAI compatible endpoint), segment by segment."""
    if not deepseek_api_key:
        status_callback("Error: DeepSeek API Key is missing.", level="ERROR")
        return None

    try:
        # DeepSeek uses an OpenAI-compatible API
        client = openai.OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com/v1" # or "https://api.deepseek.com"
        )
        status_callback(f"Configured DeepSeek with model: {deepseek_model_name}. Translating to {target_language}...", level="INFO")
    except Exception as e:
        status_callback(f"Error configuring DeepSeek client: {e}", level="ERROR")
        return None

    translated_segments = []
    total_segments = len(text_segments)

    # For DeepSeek, we'll also process segment by segment similar to OpenAI for now.
    # Batching could be explored later if needed, by adapting Gemini's batching logic.
    for i, segment in enumerate(text_segments):
        status_callback(f"Processing segment {i+1}/{total_segments} with DeepSeek ({deepseek_model_name})...", level="INFO")
        text_to_translate = segment['text'].strip()
        if not text_to_translate:
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': ''
            })
            continue

        # Prompt for DeepSeek (can be similar to OpenAI's)
        # It's good practice to specify the role clearly.
        system_prompt = f"You are a precise language translator. Translate the user's text to {target_language}. Output ONLY the translated text. Do not add any explanations, introductions, or conversational phrases."
        user_prompt = f"Translate to {target_language}: {text_to_translate}"
        
        status_callback(f"VERBOSE: Sending prompt to DeepSeek for segment {i+1}: {user_prompt[:100]}...", level="VERBOSE")

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=deepseek_model_name, # e.g., "deepseek-chat"
                temperature=0.1, # Lower for direct translation
                # max_tokens can be set if needed
            )
            translated_text = chat_completion.choices[0].message.content.strip()
            status_callback(f"VERBOSE: Received response from DeepSeek for segment {i+1}: {translated_text[:100]}...", level="VERBOSE")
            
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': translated_text
            })

        except openai.APIError as e_api: # DeepSeek might raise OpenAI compatible errors
            status_callback(f"DeepSeek API Error on segment {i+1}: {e_api}. Skipping.", level="ERROR")
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': f"[DeepSeek API Error] {segment['text']}"
            })
        except Exception as e_generic:
            status_callback(f"Generic error with DeepSeek on segment {i+1}: {e_generic}. Skipping.", level="ERROR")
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': f"[DeepSeek Translation Error] {segment['text']}"
            })
            
    status_callback("DeepSeek translation finished.", level="INFO")
    return translated_segments

def _translate_with_anthropic(anthropic_api_key, anthropic_model_name, text_segments, target_language, status_callback, batch_size_setting):
    """Translates text segments using Anthropic Claude API, segment by segment."""
    if not anthropic_api_key:
        status_callback("Error: Anthropic API Key is missing.", level="ERROR")
        return None

    try:
        client = anthropic.Anthropic(api_key=anthropic_api_key)
        status_callback(f"Configured Anthropic Claude with model: {anthropic_model_name}. Translating to {target_language}...", level="INFO")
    except Exception as e:
        status_callback(f"Error configuring Anthropic client: {e}", level="ERROR")
        return None

    translated_segments = []
    total_segments = len(text_segments)

    for i, segment in enumerate(text_segments):
        status_callback(f"Processing segment {i+1}/{total_segments} with Anthropic ({anthropic_model_name})...", level="INFO")
        text_to_translate = segment['text'].strip()
        if not text_to_translate:
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': '' 
            })
            continue

        # Anthropic's prompt structure can be a bit different.
        # Claude works well with a direct instruction in the user message.
        # System prompts are also supported and can be used for overall instructions.
        # For simple translation, a direct user message is often sufficient.
        # Example: client.messages.create(model="...", max_tokens=..., messages=[{"role": "user", "content": "Translate...
        
        prompt_content = f"Translate the following text into {target_language}. Output ONLY the translated text itself, without any additional explanations, introductions, or conversational phrases.\\n\\nText to translate: {text_to_translate}"
        
        status_callback(f"VERBOSE: Sending prompt to Anthropic for segment {i+1}: {prompt_content[:100]}...", level="VERBOSE")

        try:
            # Anthropic API expects messages in a list.
            # For single turn, it's one user message.
            # The system prompt can be added as a top-level parameter 'system'
            message = client.messages.create(
                model=anthropic_model_name,
                max_tokens=1024, # Adjust as needed, this is a common default
                messages=[
                    {
                        "role": "user",
                        "content": prompt_content
                    }
                ],
                temperature=0.1, # Lower for more direct translation
                # Other parameters like top_p, top_k can be added if needed.
            )
            # The response structure is a list of content blocks. For text, it's usually the first one.
            translated_text = ""
            if message.content and isinstance(message.content, list) and len(message.content) > 0:
                if hasattr(message.content[0], 'text'):
                    translated_text = message.content[0].text.strip()
            
            status_callback(f"VERBOSE: Received response from Anthropic for segment {i+1}: {translated_text[:100]}...", level="VERBOSE")
            
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': translated_text
            })

        except anthropic.APIError as e_api:
            status_callback(f"Anthropic API Error on segment {i+1}: {e_api}. Skipping.", level="ERROR")
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': f"[Anthropic API Error] {segment['text']}"
            })
        except Exception as e_generic:
            status_callback(f"Generic error with Anthropic on segment {i+1}: {e_generic}. Skipping.", level="ERROR")
            translated_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': f"[Anthropic Translation Error] {segment['text']}"
            })
            
    status_callback("Anthropic translation finished.", level="INFO")
    return translated_segments 

def translate_text(provider_config, text_segments, target_language, status_callback, batch_size_setting):
    """General function to translate text based on the selected provider."""
    provider = provider_config.get('name')
    status_callback(f"Translation initiated with provider: {provider}", level="INFO")

    if provider == "Gemini":
        return _translate_with_gemini(
            gemini_api_key=provider_config.get('gemini_api_key'),
            text_segments=text_segments,
            target_language=target_language,
            status_callback=status_callback,
            batch_size=batch_size_setting, # Use the general batch size setting
            gemini_temperature=provider_config.get('gemini_temperature', 0.2), # Default if not in provider_config
            gemini_top_p=provider_config.get('gemini_top_p', 0.95),
            gemini_top_k=provider_config.get('gemini_top_k', 40)
        )
    elif provider == "OpenAI":
        return _translate_with_openai(
            openai_api_key=provider_config.get('openai_api_key'),
            openai_model_name=provider_config.get('openai_model', OPENAI_MODELS[0] if OPENAI_MODELS else "gpt-3.5-turbo"), # Default model
            text_segments=text_segments,
            target_language=target_language,
            status_callback=status_callback,
            batch_size_setting=batch_size_setting # Pass batch_size_setting
        )
    elif provider == "DeepSeek":
        return _translate_with_deepseek(
            deepseek_api_key=provider_config.get('deepseek_api_key'),
            deepseek_model_name=DEEPSEEK_MODEL, # Fixed model from config
            text_segments=text_segments,
            target_language=target_language,
            status_callback=status_callback,
            batch_size_setting=batch_size_setting 
        )
    elif provider == "Anthropic":
        return _translate_with_anthropic(
            anthropic_api_key=provider_config.get('anthropic_api_key'),
            anthropic_model_name=provider_config.get('anthropic_model', ANTHROPIC_MODELS[0] if ANTHROPIC_MODELS else "claude-3-opus-20240229"),
            text_segments=text_segments,
            target_language=target_language,
            status_callback=status_callback,
            batch_size_setting=batch_size_setting
        )
    # elif provider == "Local Model":
    #     # return _translate_with_local_model(...)
    else:
        status_callback(f"Error: Unknown translation provider '{provider}'.", level="ERROR")
        return None 