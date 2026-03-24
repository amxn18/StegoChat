import os
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from aes import aes_encrypt, aes_decrypt  # Your existing AES module

def encrypt_message(message: str, public_key) -> bytes:
    """Hybrid RSA-AES encryption"""
    aes_key = os.urandom(32)
    aes_ciphertext = aes_encrypt(message, aes_key.hex())
    
    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_key + aes_ciphertext

def decrypt_message(ciphertext: bytes, private_key) -> str:
    """Hybrid RSA-AES decryption"""
    encrypted_key = ciphertext[:256]
    aes_ciphertext = ciphertext[256:]
    
    aes_key = private_key.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return aes_decrypt(aes_ciphertext, aes_key.hex())