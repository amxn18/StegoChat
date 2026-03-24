# Crypt Chat - Secure Image Steganography

A complete web application for securely hiding messages inside images using multiple encryption and steganography techniques.

## Features

- **Multiple Encryption Algorithms**:
  - AES-GCM (symmetric encryption)
  - ChaCha20-Poly1305 (symmetric encryption)
  - Hybrid RSA-AES (asymmetric + symmetric encryption)

- **Two Steganography Methods**:
  - LSB (Least Significant Bit) - Hides data in pixel LSBs
  - DCT (Discrete Cosine Transform) - Hides data in frequency domain

- **Modern Web Interface**:
  - Responsive design with glassmorphism effects
  - Real-time image preview
  - Drag & drop file upload
  - Key generation and management

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python server.py
```

### 3. Open in Browser

Navigate to: http://localhost:5000

## Usage

### Encrypt & Hide Message
1. Select an image file (PNG format recommended)
2. Enter your secret message
3. Choose encryption algorithm (AES, ChaCha20, or Hybrid)
4. Choose steganography method (LSB or DCT)
5. Enter a password
6. Click "Encrypt Image" - the encrypted image will download automatically

### Decrypt & Extract Message
1. Upload the encrypted image
2. Select the same encryption algorithm and steganography method used
3. Enter the correct password
4. Click "Decrypt" - the hidden message will be displayed

### Generate Keys (for Hybrid encryption)
1. Go to "Key Generation" section
2. Click "Public" or "Private" to generate RSA key pairs
3. Copy the generated keys for use with Hybrid encryption

## Technical Details

- **Security**: Uses industry-standard encryption (AES-GCM, ChaCha20-Poly1305, RSA-OAEP)
- **Key Derivation**: PBKDF2 with SHA-256 (310,000 iterations)
- **Image Format**: PNG only (prevents compression artifacts)
- **Steganography**: LSB and DCT methods for different use cases

## File Structure

```
├── server.py              # Unified backend server
├── index.html             # Frontend interface
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## API Endpoints

- `GET /` - Serves the main web interface
- `POST /encrypt_hide` - Encrypts message and hides in image
- `POST /unhide_decrypt` - Extracts and decrypts message from image
- `POST /generate_keys` - Generates RSA key pairs

## Security Notes

- Always use strong passwords
- Keep private keys secure
- PNG format is required to prevent compression artifacts
- The application runs locally - no data is sent to external servers

## Troubleshooting

- **"Only PNG images allowed"**: Convert your image to PNG format
- **"Message too long for image"**: Use a larger image or shorter message
- **"No message found"**: Ensure you're using the correct password and algorithms
- **Network errors**: Make sure the server is running on port 5000

