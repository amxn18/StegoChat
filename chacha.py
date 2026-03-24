import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend
from crypto_utils import derive_key, generate_salt  # Reusing your AES utilities

def chacha_encrypt(plaintext: str, password: str) -> bytes:
    """Encrypts with ChaCha20-Poly1305 (reusing AES's key derivation)"""
    salt = generate_salt()  # From crypto_utils
    key = derive_key(password, salt, 32)  # 256-bit key for ChaCha20
    iv = os.urandom(16)  # ChaCha20 uses 16-byte IVs
    
    cipher = Cipher(
        algorithms.ChaCha20(key, iv),
        mode=None,  # ChaCha20 has built-in authentication
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode())
    return salt + iv + ciphertext  # Format: [salt][IV][ciphertext]

def chacha_decrypt(ciphertext: bytes, password: str) -> str:
    """Decrypts ChaCha20 ciphertext"""
    salt = ciphertext[:16]
    iv = ciphertext[16:32]
    encrypted_data = ciphertext[32:]
    
    key = derive_key(password, salt, 32)
    cipher = Cipher(
        algorithms.ChaCha20(key, iv),
        mode=None,
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_data).decode()
