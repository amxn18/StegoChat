import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from crypto_utils import derive_key, generate_salt
from cryptography.hazmat.backends import default_backend  # <-- Missing import

def aes_encrypt(plaintext: str, password: str) -> bytes:
    salt = generate_salt()
    key = derive_key(password, salt)
    iv = os.urandom(12)
    
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
    return salt + iv + encryptor.tag + ciphertext

def aes_decrypt(ciphertext: bytes, password: str) -> str:
    salt = ciphertext[:16]
    iv = ciphertext[16:28]
    tag = ciphertext[28:44]
    encrypted_data = ciphertext[44:]
    
    key = derive_key(password, salt)
    cipher = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    return (decryptor.update(encrypted_data) + decryptor.finalize()).decode()