#!/usr/bin/env python3
"""
Crypt Chat - Unified Backend Server
A complete Flask server that integrates all encryption and steganography functionality
"""

import os
import tempfile
import binascii
import numpy as np
from PIL import Image
from flask import Flask, request, send_file, jsonify, render_template_string
from flask_cors import CORS
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from scipy.fft import dct, idct

app = Flask(__name__)
CORS(app)

# =============================================================================
# CRYPTO UTILITIES
# =============================================================================

def derive_key(password: str, salt: bytes, key_length: int = 32) -> bytes:
    """Derive a key from password using PBKDF2"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_length,
        salt=salt,
        iterations=310000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def generate_salt() -> bytes:
    """Generate 16-byte random salt"""
    return os.urandom(16)

# =============================================================================
# ENCRYPTION MODULES
# =============================================================================

def aes_encrypt(plaintext: str, password: str) -> bytes:
    """AES-GCM encryption"""
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
    """AES-GCM decryption"""
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

def chacha_encrypt(plaintext: str, password: str) -> bytes:
    """ChaCha20-Poly1305 encryption"""
    salt = generate_salt()
    key = derive_key(password, salt, 32)  # 256-bit key for ChaCha20
    iv = os.urandom(16)  # ChaCha20 uses 16-byte IVs
    
    cipher = Cipher(
        algorithms.ChaCha20(key, iv),
        mode=None,  # ChaCha20 has built-in authentication
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode())
    return salt + iv + ciphertext

def chacha_decrypt(ciphertext: bytes, password: str) -> str:
    """ChaCha20-Poly1305 decryption"""
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

def hybrid_encrypt(message: str, public_key_obj) -> bytes:
    """Hybrid RSA-AES encryption. Expects a public key OBJECT."""
    aes_key = os.urandom(32)
    # Internally, we use AES with a random, single-use key (in hex format)
    aes_ciphertext = aes_encrypt(message, aes_key.hex())
    
    encrypted_key = public_key_obj.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_key + aes_ciphertext

def hybrid_decrypt(ciphertext: bytes, private_key_obj) -> str:
    """Hybrid RSA-AES decryption. Expects a private key OBJECT."""
    encrypted_key = ciphertext[:256] # RSA 2048-bit key is 256 bytes
    aes_ciphertext = ciphertext[256:]
    
    aes_key = private_key_obj.decrypt(
        encrypted_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    # The decrypted AES key is used (in hex format) to decrypt the actual message
    return aes_decrypt(aes_ciphertext, aes_key.hex())


# =============================================================================
# STEGANOGRAPHY MODULES
# =============================================================================

def validate_png(image_path):
    """Validate PNG file"""
    if not image_path.lower().endswith(".png"):
        raise ValueError("Only PNG images are supported to avoid compression.")

def lsb_encode_message(image_path, hex_message, output_path):
    """LSB steganography encoding"""
    validate_png(image_path)
    
    img = Image.open(image_path)
    
    if img.mode not in ['RGB', 'RGBA']:
        img = img.convert('RGB')

    # Remove any spaces or '0x' prefix from hex input
    hex_message = hex_message.replace(' ', '').replace('0x', '')
    
    # Validate hex input
    try:
        # Convert hex to binary
        binary_message = bin(int(hex_message, 16))[2:]  # Remove '0b' prefix
        # Pad with leading zeros to ensure proper byte alignment
        binary_message = binary_message.zfill(len(hex_message) * 4)
    except ValueError:
        raise ValueError("Invalid hex input. Please enter valid hexadecimal characters (0-9, A-F)")

    # Add end marker (5 bytes = 40 bits)
    end_marker = '#####'
    end_binary = ''.join(format(ord(char), '08b') for char in end_marker)
    binary_message += end_binary

    required_pixels = (len(binary_message) + 2) // 3
    if required_pixels > img.width * img.height:
        raise ValueError("Message is too long for the image")

    pixels = list(img.getdata())
    new_pixels = []

    for i in range(len(pixels)):
        pixel = list(pixels[i])
        
        if i * 3 < len(binary_message):
            # Embed bits into each color channel (R, G, B)
            for j in range(3):
                if i * 3 + j < len(binary_message):
                    # Get the LSB of the pixel channel
                    lsb = int(binary_message[i * 3 + j])
                    # Modify the pixel value to embed the bit
                    pixel[j] = (pixel[j] & ~1) | lsb
        
        new_pixels.append(tuple(pixel))

    # Create and save the new image and making sure no compression is applied
    new_img = Image.new(img.mode, img.size)
    new_img.putdata(new_pixels)
    new_img.save(output_path, format="PNG", optimize=False, compress_level=0)

def lsb_decode_message(image_path):
    """LSB steganography decoding"""
    validate_png(image_path)
    
    img = Image.open(image_path)
    
    if img.mode not in ['RGB', 'RGBA']:
        raise ValueError("Image must be in RGB or RGBA format")
    
    pixels = list(img.getdata())
    binary_message = ""
    
    # Extracting LSB from each pixel channel
    for pixel in pixels:
        for j in range(3):
            binary_message += str(pixel[j] & 1)
    
    # Look for end marker in binary
    end_marker = '#####'
    end_binary = ''.join(format(ord(char), '08b') for char in end_marker)
    
    end_pos = binary_message.find(end_binary)
    if end_pos == -1:
        return "No message found or message incomplete"
    
    message_binary = binary_message[:end_pos]
    
    # Convert binary to hex
    if len(message_binary) % 4 != 0:
        message_binary = '0' * (4 - len(message_binary) % 4) + message_binary
        
    try:
        hex_output = f'{int(message_binary, 2):X}'
        return hex_output
    except ValueError:
        return "No message found or message incomplete"

def dct_encode_message(image_path, hex_message, output_path):
    """DCT steganography encoding"""
    img = Image.open(image_path)
    
    if img.mode not in ['RGB', 'RGBA']:
        img = img.convert('RGB')

    # Remove any spaces or '0x' prefix from hex input
    hex_message = hex_message.replace(' ', '').replace('0x', '')
    
    # Validate hex input
    try:
        # Convert hex to binary
        binary_message = bin(int(hex_message, 16))[2:]  # Remove '0b' prefix
        # Pad with leading zeros to ensure proper byte alignment
        binary_message = binary_message.zfill(len(hex_message) * 4)
    except ValueError:
        raise ValueError("Invalid hex input. Please enter valid hexadecimal characters (0-9, A-F)")

    # Add end marker (5 bytes = 40 bits)
    end_marker = '#####'
    end_binary = ''.join(format(ord(char), '08b') for char in end_marker)
    binary_message += end_binary

    # Convert image to numpy array
    img_array = np.array(img)
    if img.mode == 'RGBA':
        img_array = img_array[:, :, :3]  # Remove alpha channel for DCT
    
    # Calculate required blocks (8x8 blocks, 1 bit per block)
    block_size = 8
    blocks_needed = len(binary_message)
    max_blocks = (img_array.shape[0] // block_size) * (img_array.shape[1] // block_size) * 3
    
    if blocks_needed > max_blocks:
        raise ValueError(f"Message is too long for the image. Needs space for {blocks_needed} bits, but only {max_blocks} are available.")

    bit_index = 0
    # Process each color channel
    for channel in range(3):
        if bit_index >= len(binary_message): break
        channel_data = img_array[:, :, channel].astype(np.float32)
        
        # Process 8x8 blocks
        for i in range(0, channel_data.shape[0] - block_size + 1, block_size):
            if bit_index >= len(binary_message): break
            for j in range(0, channel_data.shape[1] - block_size + 1, block_size):
                if bit_index >= len(binary_message): break
                
                block = channel_data[i:i+block_size, j:j+block_size]
                dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
                
                bit_to_embed = int(binary_message[bit_index])
                
                # Use coefficient at position (4,4) for embedding
                if bit_to_embed == 1:
                    dct_block[4, 4] = abs(dct_block[4, 4]) + 10
                else:
                    dct_block[4, 4] = -abs(dct_block[4, 4]) - 10
                
                idct_block = idct(idct(dct_block.T, norm='ortho').T, norm='ortho')
                img_array[i:i+block_size, j:j+block_size, channel] = np.clip(idct_block, 0, 255)
                bit_index += 1

    # Convert back to PIL Image
    new_img = Image.fromarray(img_array.astype(np.uint8))
    new_img.save(output_path, format="PNG", optimize=False, compress_level=0)


def dct_decode_message(image_path):
    """DCT steganography decoding"""
    img = Image.open(image_path)
    
    if img.mode not in ['RGB', 'RGBA']:
        raise ValueError("Image must be in RGB or RGBA format")
    
    # Convert image to numpy array
    img_array = np.array(img)
    if img.mode == 'RGBA':
        img_array = img_array[:, :, :3]  # Remove alpha channel for DCT
    
    binary_message = ""
    block_size = 8
    
    # Process each color channel to extract bits
    for channel in range(3):
        channel_data = img_array[:, :, channel].astype(np.float32)
        
        # Process 8x8 blocks
        for i in range(0, channel_data.shape[0] - block_size + 1, block_size):
            for j in range(0, channel_data.shape[1] - block_size + 1, block_size):
                block = channel_data[i:i+block_size, j:j+block_size]
                dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
                
                coefficient = dct_block[4, 4]
                binary_message += '1' if coefficient > 0 else '0'
    
    # Look for end marker in binary
    end_marker = '#####'
    end_binary = ''.join(format(ord(char), '08b') for char in end_marker)
    
    end_pos = binary_message.find(end_binary)
    if end_pos == -1:
        return "No message found or message incomplete"
    
    message_binary = binary_message[:end_pos]
    
    if not message_binary:
        return "No message found or message incomplete"

    # Convert binary to hex
    if len(message_binary) % 4 != 0:
        message_binary = '0' * (4 - len(message_binary) % 4) + message_binary
        
    hex_output = f'{int(message_binary, 2):X}'
    return hex_output


# =============================================================================
# KEY MANAGEMENT
# =============================================================================

def generate_key_pair():
    """Generate RSA key pair"""
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
    
    return {
        'private_key': private_pem.decode('utf-8'),
        'public_key': public_pem.decode('utf-8'),
    }

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def validate_png_file(path):
    """Validate PNG file"""
    try:
        with Image.open(path) as img:
            return img.format == "PNG"
    except Exception:
        return False

def get_crypto_functions(algo_name):
    """Get encryption/decryption functions for algorithm"""
    name = (algo_name or "aes").lower()
    if name == "aes":
        return aes_encrypt, aes_decrypt
    elif name in ("chacha", "chacha20"):
        return chacha_encrypt, chacha_decrypt
    elif name == "hybrid":
        return hybrid_encrypt, hybrid_decrypt
    else:
        raise ValueError(f"Unsupported algorithm: {algo_name}")

def get_stego_functions(stego_type):
    """Get steganography functions"""
    st = (stego_type or "lsb").lower()
    if st == "dct":
        return dct_encode_message, dct_decode_message
    else:
        return lsb_encode_message, lsb_decode_message

# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/')
def index():
    """Serve the main HTML page"""
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/encrypt_hide', methods=['POST'])
def encrypt_hide():
    """Encrypt message and hide in image"""
    tmp_in_path = None
    try:
        text = request.form.get("text")
        key = request.form.get("key")
        algo = request.form.get("algo", "aes")
        stego = request.form.get("stego", "lsb")
        image_file = request.files.get("image")

        if not all([text, key, image_file]):
            return jsonify({"error": "Missing required fields (text, key, or image)"}), 400

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_in:
            image_file.save(tmp_in.name)
            tmp_in_path = tmp_in.name

        if not validate_png_file(tmp_in_path):
            return jsonify({"error": "Only valid PNG images are allowed"}), 400

        encrypt_fn, _ = get_crypto_functions(algo)

        # === FIX IS HERE: Load key string into a key object for hybrid mode ===
        if algo == 'hybrid':
            try:
                public_key_obj = serialization.load_pem_public_key(
                    key.encode('utf-8'),
                    backend=default_backend()
                )
                ciphertext = encrypt_fn(text, public_key_obj)
            except Exception as e:
                return jsonify({"error": f"Invalid Public Key. Details: {e}"}), 400
        else:
            ciphertext = encrypt_fn(text, key)
        # === END OF FIX ===

        hex_message = ciphertext.hex()
        encode_fn, _ = get_stego_functions(stego)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_out:
            encode_fn(tmp_in_path, hex_message, tmp_out.name)
            return send_file(tmp_out.name, as_attachment=True, download_name="encrypted.png", mimetype="image/png")

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected server error occurred."}), 500
    finally:
        if tmp_in_path and os.path.exists(tmp_in_path):
            os.unlink(tmp_in_path)


@app.route('/unhide_decrypt', methods=['POST'])
def unhide_decrypt():
    """Extract and decrypt message from image"""
    tmp_in_path = None
    try:
        key = request.form.get("key")
        algo = request.form.get("algo", "aes")
        stego = request.form.get("stego", "lsb")
        image_file = request.files.get("image")

        if not all([key, image_file]):
            return jsonify({"error": "Missing required fields (key or image)"}), 400

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_in:
            image_file.save(tmp_in.name)
            tmp_in_path = tmp_in.name

        if not validate_png_file(tmp_in_path):
            return jsonify({"error": "Only valid PNG images are allowed"}), 400

        _, decode_fn = get_stego_functions(stego)
        ciphertext_hex = decode_fn(tmp_in_path)

        if "No message found" in ciphertext_hex:
            return jsonify({"error": "No hidden message found or it is incomplete."}), 400

        try:
            ciphertext = bytes.fromhex(ciphertext_hex)
        except (ValueError, TypeError):
            return jsonify({"error": "Could not decode the hidden data from hex."}), 400

        _, decrypt_fn = get_crypto_functions(algo)

        # === FIX IS HERE: Load key string into a key object for hybrid mode ===
        if algo == 'hybrid':
            try:
                private_key_obj = serialization.load_pem_private_key(
                    key.encode('utf-8'),
                    password=None,
                    backend=default_backend()
                )
                plaintext = decrypt_fn(ciphertext, private_key_obj)
            except Exception as e:
                return jsonify({"error": f"Decryption failed. Check key. Details: {e}"}), 400
        else:
            plaintext = decrypt_fn(ciphertext, key)
        # === END OF FIX ===
            
        return jsonify({"message": plaintext})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected server error occurred. Check password/key."}), 500
    finally:
        if tmp_in_path and os.path.exists(tmp_in_path):
            os.unlink(tmp_in_path)

@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    """Generate RSA key pair"""
    try:
        keys = generate_key_pair()
        return jsonify({
            "private_key": keys['private_key'],
            "public_key": keys['public_key']
        })
    except Exception as e:
        return jsonify({"error": f"Key generation error: {e}"}), 500

if __name__ == "__main__":
    print("🚀 Starting Crypt Chat Server...")
    print("📱 Frontend: http://localhost:5000")
    print("🔧 API Endpoints:")
    print("   POST /encrypt_hide - Encrypt and hide message")
    print("   POST /unhide_decrypt - Extract and decrypt message")
    print("   POST /generate_keys - Generate RSA key pair")
    print("\nPress Ctrl+C to stop the server")
    app.run(host="0.0.0.0", port=5000, debug=True)