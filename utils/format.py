"""
Time formatting and subtitle conversion utilities.
"""

def format_time_srt(seconds):
    """Converts seconds to SRT time format HH:MM:SS,ms."""
    millis = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    minutes = seconds // 60
    seconds %= 60
    hours = minutes // 60
    minutes %= 60
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

def format_time_vtt(seconds):
    """Converts seconds to WebVTT time format HH:MM:SS.ms."""
    millis = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    minutes = seconds // 60
    seconds %= 60
    hours = minutes // 60
    minutes %= 60
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"

def create_srt_content(translated_segments):
    """Generates SRT formatted string from translated segments."""
    srt_content = ""
    for i, segment in enumerate(translated_segments):
        start_time = max(0, segment['start'])
        end_time = max(start_time, segment['end'])

        start_str = format_time_srt(start_time)
        end_str = format_time_srt(end_time)
        text = segment['text']
        srt_content += f"{i+1}\n"
        srt_content += f"{start_str} --> {end_str}\n"
        srt_content += f"{text}\n\n"
    return srt_content

def create_vtt_content(translated_segments):
    """Generates WebVTT formatted string from translated segments."""
    vtt_content = "WEBVTT\n\n"
    for i, segment in enumerate(translated_segments):
        start_time = max(0, segment['start'])
        end_time = max(start_time, segment['end'])
        
        start_str = format_time_vtt(start_time)
        end_str = format_time_vtt(end_time)
        text = segment['text']
        
        vtt_content += f"{i+1}\n"
        vtt_content += f"{start_str} --> {end_str}\n"
        vtt_content += f"{text}\n\n"
    
    return vtt_content

def create_txt_content(translated_segments):
    """Generates plain text from translated segments."""
    txt_content = ""
    for segment in translated_segments:
        start_time = max(0, segment['start'])
        end_time = max(start_time, segment['end'])
        
        start_str = format_time_srt(start_time)
        end_str = format_time_srt(end_time)
        text = segment['text']
        
        txt_content += f"[{start_str} --> {end_str}] {text}\n"
    
    return txt_content

def format_output(segments, output_format):
    """Format segments according to the selected output format."""
    if output_format == "srt":
        return create_srt_content(segments)
    elif output_format == "vtt":
        return create_vtt_content(segments)
    elif output_format == "txt":
        return create_txt_content(segments)
    else:
        # Default to SRT
        return create_srt_content(segments) 