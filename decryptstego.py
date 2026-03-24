import sys
from aes import aes_decrypt
from chacha import chacha_decrypt
from steganography import decode_message

def stego_decrypt():
    print("\n=== Stego Decrypt Tool ===")
    
    # Inputs from user
    image_path = input("Enter stego PNG image path: ").strip()
    password = input("Enter your password/key: ").strip()
    algo_choice = input("Choose algorithm (AES / ChaCha20): ").strip().upper()

    try:
        # Step 1: Extract ciphertext (hex) from stego image
        print("[+] Extracting hidden ciphertext from image...")
        ciphertext_hex = decode_message(image_path)

        if ciphertext_hex == "No message found or message incomplete":
            print("[-] No hidden message found in the image.")
            return

        # Step 2: Convert hex → bytes
        ciphertext = bytes.fromhex(ciphertext_hex)

        # Step 3: Decrypt with chosen algorithm
        if algo_choice == "AES":
            plaintext = aes_decrypt(ciphertext, password)
        elif algo_choice == "CHACHA20":
            plaintext = chacha_decrypt(ciphertext, password)
        else:
            print("[-] Invalid algorithm choice!")
            return

        # Step 4: Show original message
        print(f"\n✅ Decryption successful! Original message: {plaintext}")

    except Exception as e:
        print(f"[!] Error: {e}")


if __name__ == "__main__":
    stego_decrypt()
