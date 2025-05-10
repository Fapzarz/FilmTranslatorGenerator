"""
Text translation functionality using Google Gemini API.
"""
import re
import google.generativeai as genai
from config import DEFAULT_BATCH_SIZE

def translate_text_gemini(api_key, text_segments, target_language, status_callback, batch_size=DEFAULT_BATCH_SIZE):
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
    num_batches = (total_segments + batch_size - 1) // batch_size  # Calculate number of batches
    mismatch_tolerance = 10  # Allow +/- 10 segments difference

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
                if cleaned_line:  # Only add non-empty lines
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