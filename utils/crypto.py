"""
Utility functions for encryption and decryption of sensitive data.
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