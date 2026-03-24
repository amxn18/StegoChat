import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

KEY_DIR = "assets"

def generate_and_display_keys():
    """Generate keys and print them"""
    os.makedirs(KEY_DIR, exist_ok=True)
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    
    # Serialize keys
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Save keys
    with open(f"{KEY_DIR}/private_key.pem", "wb") as f:
        f.write(private_pem)
    
    with open(f"{KEY_DIR}/public_key.pem", "wb") as f:
        f.write(public_pem)
    
    # Display keys
    print("\n🔑 PRIVATE KEY:")
    print(private_pem.decode('utf-8'))
    
    print("\n🔐 PUBLIC KEY:")
    print(public_pem.decode('utf-8'))
    
    return private_key, public_key

def load_key(key_type: str):
    """Load key from file"""
    if key_type == "private":
        with open(f"{KEY_DIR}/private_key.pem", "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)
    else:
        with open(f"{KEY_DIR}/public_key.pem", "rb") as f:
            return serialization.load_pem_public_key(f.read())