from chacha import chacha_decrypt

# Paste your hex here (no spaces or extra characters)
encrypted_hex = input("Enter the cipher text: ")
password = input("Enter the password: ")  # Get user input for the password
# Convert hex to bytes and decrypt
encrypted_bytes = bytes.fromhex(encrypted_hex)
  # Replace with the password used during encryption
decrypted = chacha_decrypt(encrypted_bytes, password)

print("Your message:", decrypted)