from PIL import Image
import numpy as np
from scipy.fft import dct, idct

def encode_message(image_path, hex_message, output_path):
    img = Image.open(image_path)
    
    if img.mode not in ['RGB', 'RGBA']:
        raise ValueError("Image must be in RGB or RGBA format")

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
    max_blocks = (img_array.shape[0] // block_size) * (img_array.shape[1] // block_size)
    
    if blocks_needed > max_blocks:
        raise ValueError("Message is too long for the image")

    # Process each color channel
    for channel in range(3):
        channel_data = img_array[:, :, channel].astype(np.float32)
        
        # Process 8x8 blocks
        for i in range(0, channel_data.shape[0] - block_size + 1, block_size):
            for j in range(0, channel_data.shape[1] - block_size + 1, block_size):
                block_index = (i // block_size) * (channel_data.shape[1] // block_size) + (j // block_size)
                
                if block_index < len(binary_message):
                    # Extract 8x8 block
                    block = channel_data[i:i+block_size, j:j+block_size]
                    
                    # Apply DCT
                    dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
                    
                    # Embed bit in DCT coefficient (using middle frequency coefficient)
                    bit_to_embed = int(binary_message[block_index])
                    
                    # Use coefficient at position (4,4) for embedding
                    if bit_to_embed == 1:
                        dct_block[4, 4] = abs(dct_block[4, 4]) + 10  # Positive value
                    else:
                        dct_block[4, 4] = -abs(dct_block[4, 4]) - 10  # Negative value
                    
                    # Apply inverse DCT
                    idct_block = idct(idct(dct_block.T, norm='ortho').T, norm='ortho')
                    
                    # Update the image array
                    img_array[i:i+block_size, j:j+block_size, channel] = np.clip(idct_block, 0, 255)

    # Convert back to PIL Image
    new_img = Image.fromarray(img_array.astype(np.uint8))
    new_img.save(output_path)
    print(f"Hex message successfully hidden in '{output_path}' using DCT")
    print(f"Binary message length: {len(binary_message)} bits")
    print(f"End marker binary: {end_binary}")

def decode_message(image_path):
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
                # Extract 8x8 block
                block = channel_data[i:i+block_size, j:j+block_size]
                
                # Apply DCT
                dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
                
                # Extract bit from DCT coefficient at position (4,4)
                coefficient = dct_block[4, 4]
                if coefficient > 0:
                    binary_message += '1'
                else:
                    binary_message += '0'
    
    # Look for end marker in binary
    end_marker = '#####'
    end_binary = ''.join(format(ord(char), '08b') for char in end_marker)
    
    # Find the end marker position
    end_pos = binary_message.find(end_binary)
    if end_pos == -1:
        return "No message found or message incomplete"
    
    # Extract only the message part (before end marker)
    message_binary = binary_message[:end_pos]
    
    # Convert binary to hex
    if len(message_binary) % 4 != 0:
        # Pad to make it divisible by 4
        message_binary = message_binary.zfill(((len(message_binary) + 3) // 4) * 4)
    
    hex_output = ""
    for i in range(0, len(message_binary), 4):
        if i + 4 <= len(message_binary):
            nibble = message_binary[i:i+4]
            hex_digit = hex(int(nibble, 2))[2:].upper()
            hex_output += hex_digit
    
    # Remove leading zeros but keep at least one digit
    hex_output = hex_output.lstrip('0') or '0'
    
    return hex_output

# Place these lines at the bottom of the steganography.py file
if __name__ == "__main__":
    print("=== Image Steganography Tool (Hex Mode) ===")
    print("1. Encode a hex message in an image")
    print("2. Decode a hex message from an image")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        # Encode message
        image_path = input("Enter the path to your input image: ").strip()
        hex_message = input("Enter the hex message to hide (e.g., 48656C6C6F): ").strip()
        output_path = input("Enter the output image path (or press Enter for 'stego_image.png'): ").strip()
        
        if not output_path:
            output_path = "stego_image.png"
        
        try:
            encode_message(image_path, hex_message, output_path)
        except FileNotFoundError:
            print(f"Error: '{image_path}' not found. Please check the file path.")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    elif choice == "2":
        # Decode message
        image_path = input("Enter the path to the stego image: ").strip()
        
        try:
            decoded_hex = decode_message(image_path)
            print(f"Decoded hex message: {decoded_hex}")
        except FileNotFoundError:
            print(f"Error: '{image_path}' not found. Please check the file path.")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    else:
        print("Invalid choice. Please run the script again and select 1 or 2.")