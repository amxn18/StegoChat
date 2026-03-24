# integration_api.py
import os
import tempfile
import importlib.utilpip
import binascii
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app)  # allow local dev calls from Flutter

# --- CONFIG: set to your actual module files if names differ ---
LSB_STEGO_PATH = "./steganography.py"       # LSB implementation
DCT_STEGO_PATH = "./dct_steganography.py"   # DCT implementation
AES_MODULE_PATH = "./aes.py"                # file that defines aes_encrypt/aes_decrypt
CHACHA_MODULE_PATH = "./chacha.py"          # file that defines chacha_encrypt/chacha_decrypt
# ----------------------------------------------------------------

# Safe loader to import a function without running CLI blocks in the module
def load_function(module_name, file_path, func_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, func_name)

def validate_png_file(path):
    try:
        with Image.open(path) as img:
            return img.format == "PNG"
    except Exception:
        return False

# Helper to get encrypt/decrypt fns for an algorithm name
def get_crypto_functions(algo_name):
    name = algo_name.lower()
    if name == "aes":
        encrypt_fn = load_function("aes_encrypt_mod", AES_MODULE_PATH, "aes_encrypt")
        decrypt_fn = load_function("aes_decrypt_mod", AES_MODULE_PATH, "aes_decrypt")
    elif name in ("chacha", "chacha20"):
        encrypt_fn = load_function("chacha_encrypt_mod", CHACHA_MODULE_PATH, "chacha_encrypt")
        decrypt_fn = load_function("chacha_decrypt_mod", CHACHA_MODULE_PATH, "chacha_decrypt")
    else:
        raise ValueError("Unsupported algorithm")
    return encrypt_fn, decrypt_fn

# Helper to pick stego module
def get_stego_functions(stego_type):
    st = (stego_type or "lsb").lower()
    if st == "dct":
        encode_fn = load_function("dct_stego_mod", DCT_STEGO_PATH, "encode_message")
        decode_fn = load_function("dct_stego_mod2", DCT_STEGO_PATH, "decode_message")
    else:
        encode_fn = load_function("lsb_stego_mod", LSB_STEGO_PATH, "encode_message")
        decode_fn = load_function("lsb_stego_mod2", LSB_STEGO_PATH, "decode_message")
    return encode_fn, decode_fn

# ---------------------- Endpoint: Encrypt + Hide ----------------------
@app.route("/encrypt_hide", methods=["POST"])
def encrypt_hide():
    try:
        text = request.form.get("text", None)
        key = request.form.get("key", None)
        algo = request.form.get("algo", "aes")
        stego = request.form.get("stego", "lsb")  # lsb or dct
        image_file = request.files.get("image", None)

        if not text or not key or not image_file:
            return jsonify({"error": "Missing required fields (text/key/image)"}), 400

        # Save upload to temp
        tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        image_file.save(tmp_in.name)
        tmp_in.close()

        # Validate PNG
        if not validate_png_file(tmp_in.name):
            os.unlink(tmp_in.name)
            return jsonify({"error": "Only valid PNG images allowed"}), 400

        # Load crypto functions
        encrypt_fn, _ = get_crypto_functions(algo)

        # Encrypt (function expected to return bytes)
        ciphertext = encrypt_fn(text, key)
        if isinstance(ciphertext, str):
            # if the encrypt function returns hex string, convert to bytes
            try:
                ciphertext = bytes.fromhex(ciphertext)
            except Exception:
                ciphertext = ciphertext.encode()

        hex_message = ciphertext.hex()

        # Select stego encode function
        encode_fn, _ = get_stego_functions(stego)

        # Output temp file
        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp_out.close()
        encode_fn(tmp_in.name, hex_message, tmp_out.name)

        # Send file back as attachment
        return send_file(tmp_out.name, as_attachment=True, download_name="stego.png", mimetype="image/png")
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {e}"}), 500
    finally:
        # cleanup - safe: keep files for a small while if still being sent
        try:
            if 'tmp_in' in locals() and os.path.exists(tmp_in.name):
                os.unlink(tmp_in.name)
        except:
            pass

# ---------------------- Endpoint: Unhide + Decrypt ----------------------
@app.route("/unhide_decrypt", methods=["POST"])
def unhide_decrypt():
    try:
        key = request.form.get("key", None)
        algo = request.form.get("algo", "aes")
        stego = request.form.get("stego", "lsb")
        image_file = request.files.get("image", None)

        if not key or not image_file:
            return jsonify({"error": "Missing required fields (key/image)"}), 400

        tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        image_file.save(tmp_in.name)
        tmp_in.close()

        if not validate_png_file(tmp_in.name):
            os.unlink(tmp_in.name)
            return jsonify({"error": "Only valid PNG images allowed"}), 400

        # pick stego decode function
        _, decode_fn = get_stego_functions(stego)

        ciphertext_hex = decode_fn(tmp_in.name)
        if not ciphertext_hex or ciphertext_hex.startswith("No message"):
            os.unlink(tmp_in.name)
            return jsonify({"error": "No hidden message found or message incomplete"}), 400

        try:
            ciphertext = bytes.fromhex(ciphertext_hex)
        except Exception:
            return jsonify({"error": "Hidden data is not valid hex"}), 400

        # pick crypto decrypt fn
        _, decrypt_fn = get_crypto_functions(algo)

        plaintext = decrypt_fn(ciphertext, key)
        # normalize plaintext type
        if isinstance(plaintext, (bytes, bytearray)):
            try:
                plaintext = plaintext.decode("utf-8")
            except:
                plaintext = plaintext.decode("utf-8", errors="ignore")

        return jsonify({"message": plaintext})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {e}"}), 500
    finally:
        try:
            if 'tmp_in' in locals() and os.path.exists(tmp_in.name):
                os.unlink(tmp_in.name)
        except:
            pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
