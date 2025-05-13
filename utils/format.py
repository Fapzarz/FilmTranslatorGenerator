"""
Time formatting and subtitle conversion utilities.
"""

import os
import re

def format_time_srt(seconds):
    """
    Format time in seconds to SRT format (HH:MM:SS,mmm).
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Time formatted as HH:MM:SS,mmm
    """
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    seconds_remainder = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{seconds_remainder:02d},{milliseconds:03d}"

def format_time_vtt(seconds):
    """
    Format time in seconds to WebVTT format (HH:MM:SS.mmm).
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Time formatted as HH:MM:SS.mmm
    """
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    seconds_remainder = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{seconds_remainder:02d}.{milliseconds:03d}"

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

def format_output(segments, output_format, time_formatter=None):
    """
    Format segments into the specified subtitle format.
    
    Args:
        segments (list): List of segment dictionaries with 'start', 'end', and 'text'
        output_format (str): The output format ('srt', 'vtt', or 'txt')
        time_formatter (function, optional): Custom time formatting function
        
    Returns:
        str: Formatted subtitle content
    """
    if not segments:
        return ""
    
    output_format = output_format.lower()
    
    if output_format == "srt":
        return format_srt(segments, time_formatter)
    elif output_format == "vtt":
        return format_vtt(segments, time_formatter)
    elif output_format == "txt":
        return format_txt(segments)
    else:
        return f"Unsupported format: {output_format}"

def format_srt(segments, time_formatter=None):
    """
    Format segments into SRT format.
    
    Args:
        segments (list): List of segment dictionaries with 'start', 'end', and 'text'
        time_formatter (function, optional): Custom time formatting function
        
    Returns:
        str: SRT formatted subtitle content
    """
    if time_formatter is None:
        time_formatter = format_time_srt
        
    lines = []
    for i, segment in enumerate(segments):
        start_time = time_formatter(segment['start'])
        end_time = time_formatter(segment['end'])
        text = segment['text'].strip()
        
        lines.append(f"{i+1}")
        lines.append(f"{start_time} --> {end_time}")
        lines.append(f"{text}")
        lines.append("")  # Empty line between segments
    
    return "\n".join(lines)

def format_vtt(segments, time_formatter=None):
    """
    Format segments into WebVTT format.
    
    Args:
        segments (list): List of segment dictionaries with 'start', 'end', and 'text'
        time_formatter (function, optional): Custom time formatting function
        
    Returns:
        str: WebVTT formatted subtitle content
    """
    if time_formatter is None:
        time_formatter = format_time_vtt
    
    lines = ["WEBVTT", ""]  # WebVTT header
    
    for i, segment in enumerate(segments):
        start_time = time_formatter(segment['start'])
        end_time = time_formatter(segment['end'])
        text = segment['text'].strip()
        
        lines.append(f"{i+1}")
        lines.append(f"{start_time} --> {end_time}")
        lines.append(f"{text}")
        lines.append("")  # Empty line between segments
    
    return "\n".join(lines)

def format_txt(segments):
    """
    Format segments into plain text format.
    
    Args:
        segments (list): List of segment dictionaries with 'start', 'end', and 'text'
        
    Returns:
        str: Plain text formatted subtitle content
    """
    lines = []
    for segment in segments:
        text = segment['text'].strip()
        if text:
            lines.append(text)
    
    return "\n\n".join(lines)

def parse_srt(content):
    """
    Parse SRT content into a list of segments.
    
    Args:
        content (str): SRT content to parse
        
    Returns:
        list: List of segment dictionaries with 'start', 'end', and 'text'
    """
    segments = []
    
    # Regular expression to match SRT segments
    pattern = re.compile(r'(\d+)\r?\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\r?\n((?:.+\r?\n?)+)')
    
    for match in pattern.finditer(content):
        _, start_time, end_time, text = match.groups()
        
        # Parse start time
        start_parts = start_time.replace(',', ':').split(':')
        start_seconds = (int(start_parts[0]) * 3600) + (int(start_parts[1]) * 60) + int(start_parts[2]) + (int(start_parts[3]) / 1000)
        
        # Parse end time
        end_parts = end_time.replace(',', ':').split(':')
        end_seconds = (int(end_parts[0]) * 3600) + (int(end_parts[1]) * 60) + int(end_parts[2]) + (int(end_parts[3]) / 1000)
        
        segments.append({
            'start': start_seconds,
            'end': end_seconds,
            'text': text.strip()
        })
    
    return segments

def parse_vtt(content):
    """
    Parse WebVTT content into a list of segments.
    
    Args:
        content (str): WebVTT content to parse
        
    Returns:
        list: List of segment dictionaries with 'start', 'end', and 'text'
    """
    segments = []
    
    # Regular expression to match WebVTT segments
    pattern = re.compile(r'(?:\d+\r?\n)?(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\r?\n((?:.+\r?\n?)+)')
    
    for match in pattern.finditer(content):
        start_time, end_time, text = match.groups()
        
        # Parse start time
        start_parts = start_time.replace('.', ':').split(':')
        start_seconds = (int(start_parts[0]) * 3600) + (int(start_parts[1]) * 60) + int(start_parts[2]) + (int(start_parts[3]) / 1000)
        
        # Parse end time
        end_parts = end_time.replace('.', ':').split(':')
        end_seconds = (int(end_parts[0]) * 3600) + (int(end_parts[1]) * 60) + int(end_parts[2]) + (int(end_parts[3]) / 1000)
        
        segments.append({
            'start': start_seconds,
            'end': end_seconds,
            'text': text.strip()
        })
    
    return segments 