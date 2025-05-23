"""
Utility functions for encryption and decryption of sensitive data.

This module provides comprehensive cryptographic utilities including:
- Data encryption/decryption using Fernet (AES 128)
- Machine-specific key generation for additional security
- Automated security checks and API key protection
- Integration with the application's configuration system

Functions:
    encrypt_data, decrypt_data: Core encryption/decryption
    is_encrypted: Check if data is encrypted
    fix_exposed_api_keys: Encrypt any plain text API keys
    run_security_check: Complete security audit and fix
"""
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_machine_id():
    """Get a unique machine identifier to use as encryption seed."""
    import platform
    system = platform.system()
    if system == "Windows":
        try:
            # Windows-specific machine ID
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Cryptography")
            machine_guid = winreg.QueryValueEx(key, "MachineGuid")[0]
            return machine_guid
        except Exception:
            pass
    
    # Fallback for all platforms or if Windows-specific method fails
    try:
        machine = platform.node() + platform.machine() + platform.processor()
        return hashlib.sha256(machine.encode()).hexdigest()
    except Exception:
        # Last resort - use a fixed salt but remind this is less secure
        return "FTG_DEFAULT_MACHINE_SALT_LOW_SECURITY"

def generate_key(user_password=""):
    """
    Generate an encryption key based on machine ID and optional user password.
    
    Args:
        user_password: Optional user-provided password for additional security
        
    Returns:
        A bytes key suitable for Fernet encryption
    """
    # Combine machine ID with user password for the salt
    machine_id = get_machine_id()
    if user_password:
        salt = (machine_id + user_password).encode()
    else:
        salt = machine_id.encode()
    
    # Create a key derivation function
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    # Use the machine ID as the base password if no user password
    password = (user_password or machine_id).encode()
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key

def encrypt_data(data, user_password=""):
    """
    Encrypt sensitive data.
    
    Args:
        data: String data to encrypt
        user_password: Optional user password for additional security
        
    Returns:
        Encrypted data as string
    """
    if not data:
        return ""
    
    try:
        key = generate_key(user_password)
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return ""

def decrypt_data(encrypted_data, user_password=""):
    """
    Decrypt sensitive data.
    
    Args:
        encrypted_data: Encrypted string data
        user_password: Optional user password that was used for encryption
        
    Returns:
        Decrypted data as string or empty string on failure
    """
    if not encrypted_data:
        return ""
    
    try:
        key = generate_key(user_password)
        f = Fernet(key)
        decoded = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = f.decrypt(decoded).decode()
        return decrypted_data
    except Exception as e:
        print(f"Decryption error: {e}")
        return ""

def is_encrypted(data):
    """
    Check if data appears to be encrypted by our system.
    
    Args:
        data: String data to check
        
    Returns:
        Boolean indicating if data appears to be encrypted
    """
    if not data:
        return False
    
    try:
        # Try to decode as base64 first (all our encrypted data is base64)
        decoded = base64.urlsafe_b64decode(data.encode())
        # Further checks could be added here if needed
        return True
    except Exception:
        return False

def fix_exposed_api_keys():
    """
    Fix exposed API keys by encrypting them if they are currently in plain text.
    Integrated security fix functionality within the crypto module.
    
    Returns:
        Boolean indicating if any keys were encrypted
    """
    import json
    from config import CONFIG_FILE, load_config, save_config
    
    if not os.path.exists(CONFIG_FILE):
        print("Config file not found. Nothing to fix.")
        return False

    # Load current configuration
    config = load_config()
    
    # Check which API keys need to be encrypted
    api_keys = ['gemini_api_key', 'openai_api_key', 'anthropic_api_key', 'deepseek_api_key']
    keys_encrypted = False
    
    for key_name in api_keys:
        if key_name in config and config[key_name]:
            # Check if the key is already encrypted
            if not is_encrypted(config[key_name]):
                print(f"Encrypting {key_name}...")
                # Encrypt the API key
                encrypted_key = encrypt_data(config[key_name])
                if encrypted_key:
                    config[key_name] = encrypted_key
                    keys_encrypted = True
                    print(f"✓ {key_name} encrypted successfully")
                else:
                    print(f"✗ Failed to encrypt {key_name}")
            else:
                print(f"✓ {key_name} is already encrypted")
    
    # Mark keys as encrypted in config
    if keys_encrypted:
        config['keys_encrypted'] = True
        save_config(config)
        print("\n✓ Configuration updated with encrypted API keys")
        print("✓ Security vulnerability fixed!")
        return True
    else:
        print("\n✓ No unencrypted API keys found. Configuration is secure.")
        return False

def run_security_check():
    """
    Run a complete security check and fix for the application.
    This is the main function to call for security maintenance.
    """
    print("Film Translator Generator - Security Check")
    print("=" * 50)
    print("Checking for exposed API keys in configuration...")
    
    try:
        keys_fixed = fix_exposed_api_keys()
        if keys_fixed:
            print("\nSecurity vulnerabilities found and fixed!")
        else:
            print("\nNo security issues found. Configuration is secure.")
        print("Security check completed successfully!")
        return True
    except Exception as e:
        print(f"\nError during security check: {e}")
        print("Please check the configuration manually.")
        return False 