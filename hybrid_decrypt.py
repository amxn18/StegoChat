from cryptography.hazmat.primitives.serialization import load_pem_private_key
from crypto_engine import decrypt_message
def decrypt_with_private_key():
    """Decrypt using provided private key"""
    private_pem = input("Paste PRIVATE KEY (PEM format):\n")
    ciphertext_hex = input("Paste encrypted message (hex): ")
    
    private_key = load_pem_private_key(private_pem.encode(), password=None)
    ciphertext = bytes.fromhex(ciphertext_hex)
    
    decrypted = decrypt_message(ciphertext, private_key)
    print("\n🔓 DECRYPTED MESSAGE:")
    print(decrypted)

if __name__ == "__main__":
    decrypt_with_private_key()