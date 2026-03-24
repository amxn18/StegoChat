import importlib.util
from steganography import encode_message
from aes import aes_encrypt
from chacha import chacha_encrypt

# Safe import function
def load_function(module_name, file_path, func_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, func_name)

# # Load encryption functions safely
# aes_encrypt = load_function("aes_encrypt", "./aes_encrypt.py", "aes_encrypt")
# chacha_encrypt = load_function("chacha_encrypt", "./chacha_encrypt.py", "chacha_encrypt")
# Agar RSA ya hybrid bhi ho, to waise hi add kar sakte ho


def main():
    print("=== Encrypt + Steganography Tool ===")
    print("Choose encryption algorithm:")
    print("1. AES")
    print("2. ChaCha")

    choice = input("Enter choice (1/2): ").strip()

    plaintext = input("Enter the message to encrypt: ").strip()
    password = input("Enter password/key: ").strip()

    if choice == "1":
        print("[*] Using AES encryption...")
        ciphertext = aes_encrypt(plaintext, password)
    elif choice == "2":
        print("[*] Using ChaCha encryption...")
        ciphertext = chacha_encrypt(plaintext, password)
    else:
        print("Invalid choice")
        return

    # Ciphertext ko hex string bana do stego ke liye
    hex_message = ciphertext.hex()

    image_path = input("Enter path to PNG image: ").strip()
    output_path = input("Enter output image path (default: stego_image.png): ").strip()
    if not output_path:
        output_path = "stego_image.png"

    encode_message(image_path, hex_message, output_path)
    print(f"[+] Successfully encrypted and hidden message in {output_path}")


if __name__ == "__main__":
    main()