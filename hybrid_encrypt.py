from cryptography.hazmat.primitives.serialization import load_pem_public_key
from crypto_engine import encrypt_message

def encrypt_with_public_key():
    """Encrypt using provided public key"""
    public_pem = input("Paste PUBLIC KEY (PEM format):\n")
    message = input("Message to encrypt: ")
    
    public_key = load_pem_public_key(public_pem.encode())
    encrypted = encrypt_message(message, public_key)
    
    print("\n🔒 ENCRYPTED MESSAGE (hex):")
    print(encrypted.hex())
    
    # to Save to file
    # with open("encrypted.msg", "wb") as f:
    #     f.write(encrypted)
    # print("\nSaved to 'encrypted.msg'")

if __name__ == "__main__":
    encrypt_with_public_key()