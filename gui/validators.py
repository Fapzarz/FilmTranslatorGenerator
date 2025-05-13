"""
Custom validators for the Film Translator Generator application.
"""
import re

# Based on Tkinter documentation and common usage.
# Modifiers are case-insensitive for matching here, but canonical form (e.g., "Control") is preferred.
VALID_MODIFIERS = [
    "control", "ctrl", 
    "alt", "option", # Option is often Alt on macOS
    "shift", 
    "mod1", "mod2", "mod3", "mod4", "mod5", # Generic modifiers
    "meta", "command", "cmd" # Command/Cmd often Meta or Control on macOS
]

# Common non-alphanumeric KeySyms. This is not exhaustive but covers many typical cases.
# Tkinter KeySyms are case-sensitive.
# See: https://www.tcl.tk/man/tcl8.6/TkCmd/keysyms.htm (remove XK_ prefix)
COMMON_KEYSYMS = [
    "BackSpace", "Tab", "Return", "Enter", "Escape", "Delete", "Home", "End", 
    "Prior", "Next", "Up", "Down", "Left", "Right",
    "Insert", "Print", "Scroll_Lock", "Pause", "Caps_Lock", "Num_Lock",
    "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
    "space", "comma", "period", "slash", "backslash", "semicolon", "apostrophe",
    "bracketleft", "bracketright", "minus", "equal", "grave" # `~ , . / \ ; ' [ ] - = `
    # Note: 'space' is a common KeySym for the spacebar.
]


def is_valid_shortcut_string(shortcut_string: str) -> tuple[bool, str]:
    """
    Validates a Tkinter-style shortcut string.

    Args:
        shortcut_string: The shortcut string to validate (e.g., "Control-o", "F5", "Alt-Shift-Delete").

    Returns:
        A tuple (is_valid: bool, message: str). 
        `is_valid` is True if the string is considered valid, False otherwise.
        `message` provides a reason if invalid, or "Valid" if valid.
    """
    if not shortcut_string or not isinstance(shortcut_string, str) or not shortcut_string.strip():
        return False, "Shortcut cannot be empty."

    parts = shortcut_string.split('-')
    
    if not parts: # Should not happen if shortcut_string is not empty and stripped
        return False, "Shortcut cannot be empty after parsing."

    keysym_part = parts[-1]
    modifier_parts = parts[:-1]

    # Validate modifiers
    if modifier_parts:
        for mod in modifier_parts:
            if not mod: # Handles cases like "Control--o" or "-o"
                return False, f"Empty modifier part found in '{shortcut_string}'."
            if mod.lower() not in VALID_MODIFIERS:
                return False, f"Invalid modifier '{mod}'. Valid are: Control, Alt, Shift, etc."
        
        # Check for duplicate modifiers (e.g., "Control-Control-o")
        # Lowercase for case-insensitive duplicate check
        normalized_modifiers = [mod.lower() for mod in modifier_parts]
        if len(normalized_modifiers) != len(set(normalized_modifiers)):
            # Map common synonyms for a more accurate duplicate check (e.g. Control and Ctrl)
            mapped_mods = []
            for mod in normalized_modifiers:
                if mod in ["control", "ctrl"]: mapped_mods.append("control")
                elif mod in ["alt", "option"]: mapped_mods.append("alt")
                elif mod in ["command", "cmd", "meta"]: mapped_mods.append("meta") # Group these
                else: mapped_mods.append(mod)
            
            if len(mapped_mods) != len(set(mapped_mods)):
                 return False, "Duplicate modifiers (e.g., Control-Control-o or Ctrl-Control-O)."


    # Validate KeySym
    if not keysym_part:
        return False, "Key part cannot be empty (e.g., 'Control-')."

    if ' ' in keysym_part and keysym_part.lower() != 'space':
        return False, "Key part contains a space but is not 'space' (e.g., 'Control-o p')."
    
    # Check if KeySym is a single alphanumeric character (case matters for Tkinter binding, but validation can be more lenient on input if desired)
    # For validation, we assume standard English alphabet and numbers.
    # A single character KeySym for Tkinter does not need to be in COMMON_KEYSYMS.
    if len(keysym_part) == 1:
        if not keysym_part.isalnum(): # Simple check, allows a-z, A-Z, 0-9
            # Could be a symbol like '<', '>', ',', '.'. Some of these are in COMMON_KEYSYMS.
            # If it is not alnum and not in COMMON_KEYSYMS (like 'comma', 'period'), it might be problematic.
            # For now, if it's a single char and not alnum, let's check COMMON_KEYSYMS.
            # This might be too restrictive, Tkinter might bind to e.g. '<' directly.
            # Let's assume single char should ideally be alnum or a recognized KeySym like 'space'.
             if keysym_part.lower() not in COMMON_KEYSYMS and keysym_part not in ['<', '>', '?', '/', ';', ':', '"', "'", '[', ']', '{', '}', '|', '\\', '`', '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '-', '=']: # Allow common symbols
                return False, f"Single character key '{keysym_part}' must be alphanumeric or a common symbol/KeySym."
    elif keysym_part not in COMMON_KEYSYMS and keysym_part.capitalize() not in COMMON_KEYSYMS and keysym_part.lower() not in COMMON_KEYSYMS:
        # Try a simple regex for F-keys as they are very common and might be F13, F24 etc.
        if not re.match(r"^F([1-9]|[1][0-9]|2[0-4])$", keysym_part): # Matches F1-F24
            return False, f"Invalid key '{keysym_part}'. Not a recognized common KeySym (e.g., Delete, F5, Return, Space) or single character."

    # Check for leading/trailing hyphens or multiple hyphens together
    if shortcut_string.startswith('-') or shortcut_string.endswith('-'):
        return False, "Shortcut cannot start or end with a hyphen."
    if '--' in shortcut_string:
        return False, "Shortcut cannot contain consecutive hyphens."
        
    # Overall structure check: if multiple parts, last is key, rest are modifiers.
    # If one part, it must be a valid KeySym (single char, or in COMMON_KEYSYMS).
    if not modifier_parts: # Single part, e.g., "F5" or "o" or "Delete"
        if len(keysym_part) == 1:
            if not keysym_part.isalnum():
                if keysym_part.lower() not in COMMON_KEYSYMS and keysym_part not in ['<', '>', '?', '/', ';', ':', '"', "'", '[', ']', '{', '}', '|', '\\', '`', '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '-', '=']:
                     return False, f"Single key '{keysym_part}' must be alphanumeric or a common symbol/KeySym."
        elif keysym_part not in COMMON_KEYSYMS and keysym_part.capitalize() not in COMMON_KEYSYMS and keysym_part.lower() not in COMMON_KEYSYMS:
            if not re.match(r"^F([1-9]|[1][0-9]|2[0-4])$", keysym_part):
                return False, f"Key '{keysym_part}' is not a recognized common KeySym or F-key."
                
    return True, "Valid"

if __name__ == '__main__':
    # Test cases
    test_shortcuts = [
        ("Control-o", True),
        ("Ctrl-O", True), # Assuming Ctrl is mapped to Control
        ("Alt-F4", True),
        ("Shift-Delete", True),
        ("F5", True),
        ("Delete", True),
        ("Return", True),
        ("Control-Shift-s", True),
        ("Cmd-C", True), # Common on Mac
        ("Command-V", True),
        ("Option-Left", True), # Common on Mac
        ("Control-Alt-Delete", True),
        ("space", True),
        ("Control-space", True),
        ("comma", True),
        ("Control-comma", True), # Used for settings
        ("Control-Shift-Alt-P", True), # Max 3 standard modifiers + one other (Mod1-5)
        ("Control--S", False), # Double hyphen
        ("-S", False), # Starts with hyphen
        ("Control-", False), # Ends with hyphen
        ("Controll-S", False), # Misspelled modifier
        ("Control-S-T", False), # Key in the middle
        ("InvalidKey", False), # Not a recognized key or single char
        ("Control-InvalidKey", False),
        ("Control-S T", False), # Space in key part not 'space'
        ("", False), # Empty
        ("   ", False), # Empty after strip
        ("Control-Control-S", False), # Duplicate modifier
        ("Ctrl-Control-S", False), # Duplicate modifier (synonym)
        ("Control-Shift-SHIFT-s", False), # Duplicate modifier (case insensitive)
        ("F13", True), # F-keys up to F24 should be okay by regex
        ("F25", False), # F-key out of common range
        ("a", True),
        ("A", True),
        ("7", True),
        ("Control-a", True),
        ("Control-<", True), # Common symbols
        ("Control->", True),
        ("Control-plus", False), # 'plus' is not common, 'equal' for '=' with shift, or just '+'
        ("Control-+", True), # Direct symbol
        ("Control-Shift-=", True), # Shift-= is typically '+'
        ("&", True), # Single symbol
        ("Control-&", True)
    ]

    print("Running shortcut validation tests:")
    for sc, expected in test_shortcuts:
        is_valid, msg = is_valid_shortcut_string(sc)
        result = "PASS" if is_valid == expected else "FAIL"
        print(f'Test: "{sc}" -> Expected: {expected}, Got: {is_valid} ({msg}) - {result}') 