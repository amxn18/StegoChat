from aes import aes_decrypt

#Decrypt
cipher_text = input("Enter the encrypted hex string: ")
password = input("Enter the password: ")
encrypted_hex = cipher_text 
encrypted_bytes = bytes.fromhex(encrypted_hex)

print(aes_decrypt(encrypted_bytes, password))
